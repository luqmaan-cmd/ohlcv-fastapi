from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import text
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from contextlib import asynccontextmanager
import os
import hmac
import math
import re
import time
import asyncio
import logging

import httpx

from database import get_db, engine as async_engine
from models import (
    Asset, Ticker, CommodityEOD, OhlcvUnified
)
from schemas import (
    OhlcvDataCreate, OhlcvDataResponse, UnifiedOhlcvResponse, OhlcvDataBulkCreate,
    PaginatedResponse, BulkInsertResponse, SqlQueryRequest, SqlQueryResponse,
    UstRateItem, UstPaginatedResponse, CommodityPaginatedResponse, CommoditySymbolItem,
    CommoditySymbolResponse, RealTimeOhlcvItem, RealTimeOhlcvResponse
)


API_KEY = os.getenv("API_KEY", "ohlcv-api-key-2024-secure")
API_KEYS = os.getenv("API_KEYS", "")
EODHD_API_TOKEN = os.getenv("EODHD_API_TOKEN", "")
EODHD_BASE_URL = "https://eodhd.com/api/real-time"
EODHD_TIMEOUT_S = 15
COMMODITY_EXCHANGE = "COMM"


def _parse_api_keys(raw: Optional[str]) -> tuple[tuple[str, str], ...]:
    """Parse 'key[:label],key[:label]' into (label, key) pairs."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for segment in (raw or "").split(","):
        segment = segment.strip()
        if not segment:
            continue
        if ":" in segment:
            key, label = segment.rsplit(":", 1)
            key, label = key.strip(), label.strip()
        else:
            key, label = segment, "unnamed"
        if not key:
            continue
        if label in seen:
            raise ValueError(f"Duplicate API key label: {label}")
        seen.add(label)
        pairs.append((label, key))
    return tuple(pairs)


def _build_key_set(primary: Optional[str], extras: Optional[str]) -> tuple[tuple[str, str], ...]:
    keys: list[tuple[str, str]] = []
    if primary:
        keys.append(("primary", primary))
    keys.extend(_parse_api_keys(extras or ""))
    return tuple(keys)


def _match_api_key(candidate: Optional[str], key_set: tuple[tuple[str, str], ...]) -> Optional[str]:
    """Return the label of the matching key, or None. Compares every key in constant time."""
    if not candidate:
        return None
    matched: Optional[str] = None
    for label, key in key_set:
        if hmac.compare_digest(candidate, key) and matched is None:
            matched = label
    return matched


_API_KEY_SET = _build_key_set(API_KEY, API_KEYS)

api_key_query = APIKeyQuery(name="api_key", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_query),
    header_key: Optional[str] = Security(api_key_header),
):
    label = _match_api_key(header_key, _API_KEY_SET) or _match_api_key(api_key, _API_KEY_SET)
    if label is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    logger.info("api_key_label=%s", label)
    return label

logger = logging.getLogger("ohlcv-api")

_count_cache: dict[str, tuple[int, float]] = {}
COUNT_CACHE_TTL_S = 3600


def _get_cached_count(cache_key: str) -> Optional[int]:
    entry = _count_cache.get(cache_key)
    if entry:
        count, ts = entry
        if time.time() - ts < COUNT_CACHE_TTL_S:
            return count
        del _count_cache[cache_key]
    return None


def _set_cached_count(cache_key: str, count: int) -> None:
    _count_cache[cache_key] = (count, time.time())


async def fetch_eodhd_realtime(ticker: str, exchange: str) -> dict:
    """Fetch a single real-time quote from EODHD for {ticker}.{exchange}."""
    symbol = f"{ticker}.{exchange}"
    url = f"{EODHD_BASE_URL}/{symbol}"
    params = {"api_token": EODHD_API_TOKEN, "fmt": "json"}
    try:
        async with httpx.AsyncClient(timeout=EODHD_TIMEOUT_S) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            close_val = data.get("close")
            if not data or close_val is None or close_val == "NA":
                raise HTTPException(
                    status_code=404,
                    detail=f"No real-time data found for {symbol}",
                )
            return data
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"EODHD request timed out for {symbol}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"EODHD returned {exc.response.status_code} for {symbol}",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"EODHD request failed for {symbol}: {exc}",
        )


def _clean_eodhd_val(val):
    """Return None for EODHD 'NA' placeholders, otherwise the raw value."""
    if val is None or val == "NA":
        return None
    return val


def parse_eodhd_response(data: dict, ticker: str, exchange: str) -> RealTimeOhlcvItem:
    """Map EODHD JSON response to RealTimeOhlcvItem."""
    ts_raw = _clean_eodhd_val(data.get("timestamp"))
    gmt_offset = _clean_eodhd_val(data.get("gmtoffset")) or 0
    dt = None
    if ts_raw is not None:
        dt = datetime.utcfromtimestamp(ts_raw + gmt_offset) if gmt_offset else datetime.utcfromtimestamp(ts_raw)
    return RealTimeOhlcvItem(
        ticker=ticker,
        exchange=exchange,
        timestamp=ts_raw,
        datetime=dt,
        open=Decimal(str(_clean_eodhd_val(data.get("open")))) if _clean_eodhd_val(data.get("open")) is not None else None,
        high=Decimal(str(_clean_eodhd_val(data.get("high")))) if _clean_eodhd_val(data.get("high")) is not None else None,
        low=Decimal(str(_clean_eodhd_val(data.get("low")))) if _clean_eodhd_val(data.get("low")) is not None else None,
        close=Decimal(str(_clean_eodhd_val(data.get("close")))) if _clean_eodhd_val(data.get("close")) is not None else None,
        adjusted_close=Decimal(str(_clean_eodhd_val(data.get("adjusted_close")))) if _clean_eodhd_val(data.get("adjusted_close")) is not None else None,
        volume=_clean_eodhd_val(data.get("volume")),
    )


async def fetch_eodhd_realtime_multi(symbols: list[str]) -> dict[str, dict]:
    """Fetch live quotes for several fully-qualified EODHD symbols in one request.

    Returns a mapping of uppercased EODHD code -> raw payload. Symbols the
    provider has no live data for are still present, with "NA" placeholders.
    """
    if not symbols:
        return {}
    url = f"{EODHD_BASE_URL}/{','.join(symbols)}"
    params = {"api_token": EODHD_API_TOKEN, "fmt": "json"}
    try:
        async with httpx.AsyncClient(timeout=EODHD_TIMEOUT_S) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="EODHD request timed out")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"EODHD returned {exc.response.status_code}")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"EODHD request failed: {exc}")

    rows = data if isinstance(data, list) else [data]
    return {
        str(row.get("code", "")).upper(): row
        for row in rows
        if isinstance(row, dict)
    }


async def fetch_eodhd_realtime_batch(
    ticker_exchange_pairs: list[tuple[str, str]],
) -> list[RealTimeOhlcvItem]:
    """Fetch real-time quotes for multiple tickers concurrently."""
    async def _fetch_one(ticker: str, exchange: str) -> RealTimeOhlcvItem:
        data = await fetch_eodhd_realtime(ticker, exchange)
        return parse_eodhd_response(data, ticker, exchange)

    results = await asyncio.gather(
        *(_fetch_one(t, e) for t, e in ticker_exchange_pairs),
        return_exceptions=True,
    )
    items: list[RealTimeOhlcvItem] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("EODHD batch fetch error: %s", result)
        else:
            items.append(result)
    return items


MAX_STARTUP_RETRIES = 5
STARTUP_RETRY_DELAY_S = 3


async def _ensure_tickers_table():
    """
    Ensure the tickers lookup table, sync triggers, and backfill exist.
    Retries on DB connection failure with exponential backoff.

    The tickers table provides an Index Only Scan (~5ms) as the driving row
    source for LATERAL joins, replacing SELECT DISTINCT on ohlcv_unified.
    The triggers keep it in sync as ohlcv_unified rows are inserted/deleted.
    """
    for attempt in range(1, MAX_STARTUP_RETRIES + 1):
        try:
            async with async_engine.begin() as conn:
                # 1. Create the tickers table if it doesn't exist
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tickers (
                        ticker VARCHAR(20) PRIMARY KEY
                    )
                """))

                # 2. Create the INSERT sync trigger function
                await conn.execute(text("""
                    CREATE OR REPLACE FUNCTION sync_tickers()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        INSERT INTO tickers (ticker) VALUES (NEW.ticker)
                        ON CONFLICT DO NOTHING;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                """))

                # 3. Create the DELETE sync trigger function
                await conn.execute(text("""
                    CREATE OR REPLACE FUNCTION sync_tickers_on_delete()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        DELETE FROM tickers
                        WHERE ticker = OLD.ticker
                        AND NOT EXISTS (
                            SELECT 1 FROM ohlcv_unified WHERE ticker = OLD.ticker
                        );
                        RETURN OLD;
                    END;
                    $$ LANGUAGE plpgsql
                """))

                # 4. Create the INSERT trigger if it doesn't exist
                trigger_exists = await conn.execute(text("""
                    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_sync_tickers'
                """))
                if not trigger_exists.scalar():
                    await conn.execute(text("""
                        CREATE TRIGGER trg_sync_tickers
                        AFTER INSERT ON ohlcv_unified
                        FOR EACH ROW
                        EXECUTE FUNCTION sync_tickers()
                    """))

                # 5. Create the DELETE trigger if it doesn't exist
                del_trigger_exists = await conn.execute(text("""
                    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_sync_tickers_on_delete'
                """))
                if not del_trigger_exists.scalar():
                    await conn.execute(text("""
                        CREATE TRIGGER trg_sync_tickers_on_delete
                        AFTER DELETE ON ohlcv_unified
                        FOR EACH ROW
                        EXECUTE FUNCTION sync_tickers_on_delete()
                    """))

                # 6. Backfill if the table is empty
                count_result = await conn.execute(text("SELECT count(*) FROM tickers"))
                count = count_result.scalar()
                if count == 0:
                    await conn.execute(text("""
                        INSERT INTO tickers (ticker)
                        SELECT DISTINCT ticker FROM ohlcv_unified
                        ON CONFLICT DO NOTHING
                    """))

                # 7. Analyze for optimal query plans
                await conn.execute(text("ANALYZE tickers"))

            logger.info("Tickers table ensured successfully")
            return
        except Exception as e:
            if attempt < MAX_STARTUP_RETRIES:
                delay = STARTUP_RETRY_DELAY_S * (2 ** (attempt - 1))
                logger.warning(
                    "Tickers table setup attempt %d/%d failed: %s. Retrying in %ds...",
                    attempt, MAX_STARTUP_RETRIES, e, delay
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Tickers table setup failed after %d attempts: %s",
                    MAX_STARTUP_RETRIES, e
                )
                raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tickers table, triggers, and backfill
    await _ensure_tickers_table()
    yield
    # Shutdown: dispose of the DB engine pool
    await async_engine.dispose()


app = FastAPI(title="OHLCV Data API", version="1.0.0", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)

def parse_comma_separated(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [v.strip().upper() for v in value.split(",") if v.strip()]


def parse_comma_separated_preserve(value: Optional[str]) -> Optional[List[str]]:
    """Like parse_comma_separated but preserves original case (for case-sensitive DB values)."""
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_ticker_exchange(ticker_input: str) -> tuple[str, str]:
    """Parse 'AAPL.US' → ('AAPL', 'US'). Returns (ticker, exchange).
    Raises ValueError if no exchange suffix is provided."""
    if "." in ticker_input:
        parts = ticker_input.rsplit(".", 1)
        return parts[0].strip().upper(), parts[1].strip().upper()
    raise ValueError(f"Ticker '{ticker_input}' must include exchange (e.g., {ticker_input}.US)")


@app.get("/ohlcv/", response_model=PaginatedResponse)
async def get_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single ticker with exchange suffix (e.g., AAPL.US)"),
    tickers: Optional[str] = Query(None, description="Comma-separated tickers with exchange suffix (e.g., AAPL.US,MSFT.US,BP.LSE)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange (e.g., US, LSE, CC). Used when no tickers specified."),
    asset_type: Optional[str] = Query(None, description="Filter by asset type (e.g., ETF, INDEX, FOREX, Cryptocurrencies, Government Bonds)"),
    start_date: Optional[date] = Query(None, description="Inclusive start date. To get the latest close for an asset, set start_date and end_date to the most recent trading day for that exchange."),
    end_date: Optional[date] = Query(None, description="Inclusive end date. A ticker absent from the latest trading day is no longer trading."),
    year: Optional[int] = Query(None, ge=1900, le=2100, description="Year for partition pruning (optional)"),
    month: Optional[int] = Query(None, ge=1, le=12),
    open_min: Optional[Decimal] = Query(None),
    open_max: Optional[Decimal] = Query(None),
    close_min: Optional[Decimal] = Query(None),
    close_max: Optional[Decimal] = Query(None),
    volume_min: Optional[int] = Query(None),
    volume_max: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|volume|close|open|high|low)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    realtime: bool = Query(False, description="Return real-time quotes from EODHD instead of stored rows (requires ticker or tickers)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List paginated OHLCV data for any asset class from the unified table.

    Tickers are addressed as TICKER.EXCHANGE (e.g. AAPL.US, BP.LSE, BTC-USD.CC).
    The exchange suffix is required. Use `exchange` (and optionally
    `asset_type`) to query a venue instead of naming tickers.

    To get the latest close, filter to the most recent trading day for that
    exchange, e.g. start_date=end_date=<latest trading day>. A ticker absent
    from that day's results is no longer trading. Set per_page high enough to
    cover a full trading day (one venue can exceed the 1000-row default).
    """
    # Parse tickers — accept both TICKER.EXCHANGE and bare tickers (auto-append US)
    raw_tickers = parse_comma_separated_preserve(tickers) or ([ticker] if ticker else None)
    ticker_exchange_pairs: list[tuple[str, str]] = []
    if raw_tickers:
        for t in raw_tickers:
            try:
                ticker_exchange_pairs.append(parse_ticker_exchange(t))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    if realtime:
        if not ticker_exchange_pairs:
            raise HTTPException(
                status_code=400,
                detail="realtime=true requires ticker or tickers",
            )
        quotes = await fetch_eodhd_realtime_batch(ticker_exchange_pairs)
        items = [
            UnifiedOhlcvResponse(
                ticker=q.ticker,
                date=(q.datetime.date() if q.datetime else date.today()),
                open=q.open,
                high=q.high,
                low=q.low,
                close=q.close,
                adjusted_close=q.adjusted_close,
                volume=q.volume,
                exchange=q.exchange,
            )
            for q in quotes
        ]
        return PaginatedResponse(
            data=items,
            total=len(items),
            page=1,
            per_page=len(items) or 1,
            total_pages=1,
            has_next=False,
            has_prev=False,
        )

    query = select(OhlcvUnified)
    count_query = select(func.count(OhlcvUnified.id))

    if ticker_exchange_pairs:
        if len(ticker_exchange_pairs) == 1:
            t, ex = ticker_exchange_pairs[0]
            query = query.where(OhlcvUnified.ticker == t, OhlcvUnified.exchange == ex)
            count_query = count_query.where(OhlcvUnified.ticker == t, OhlcvUnified.exchange == ex)
        else:
            # Build OR conditions for multiple ticker+exchange pairs
            pair_conditions = [
                and_(OhlcvUnified.ticker == t, OhlcvUnified.exchange == ex)
                for t, ex in ticker_exchange_pairs
            ]
            query = query.where(or_(*pair_conditions))
            count_query = count_query.where(or_(*pair_conditions))
    elif exchange:
        query = query.where(OhlcvUnified.exchange == exchange.upper())
        count_query = count_query.where(OhlcvUnified.exchange == exchange.upper())
    else:
        query = query.where(OhlcvUnified.exchange == "US")
        count_query = count_query.where(OhlcvUnified.exchange == "US")

    if asset_type:
        query = query.where(OhlcvUnified.asset_type == asset_type)
        count_query = count_query.where(OhlcvUnified.asset_type == asset_type)
    
    if year:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        query = query.where(OhlcvUnified.date >= year_start, OhlcvUnified.date <= year_end)
        count_query = count_query.where(OhlcvUnified.date >= year_start, OhlcvUnified.date <= year_end)
    
    if month:
        query = query.where(func.extract("month", OhlcvUnified.date) == month)
        count_query = count_query.where(func.extract("month", OhlcvUnified.date) == month)
    
    if start_date:
        query = query.where(OhlcvUnified.date >= start_date)
        count_query = count_query.where(OhlcvUnified.date >= start_date)
    
    if end_date:
        query = query.where(OhlcvUnified.date <= end_date)
        count_query = count_query.where(OhlcvUnified.date <= end_date)
    
    if open_min is not None:
        query = query.where(OhlcvUnified.open >= open_min)
        count_query = count_query.where(OhlcvUnified.open >= open_min)
    if open_max is not None:
        query = query.where(OhlcvUnified.open <= open_max)
        count_query = count_query.where(OhlcvUnified.open <= open_max)
    
    if close_min is not None:
        query = query.where(OhlcvUnified.close >= close_min)
        count_query = count_query.where(OhlcvUnified.close >= close_min)
    if close_max is not None:
        query = query.where(OhlcvUnified.close <= close_max)
        count_query = count_query.where(OhlcvUnified.close <= close_max)
    
    if volume_min is not None:
        query = query.where(OhlcvUnified.volume >= volume_min)
        count_query = count_query.where(OhlcvUnified.volume >= volume_min)
    if volume_max is not None:
        query = query.where(OhlcvUnified.volume <= volume_max)
        count_query = count_query.where(OhlcvUnified.volume <= volume_max)
    
    sort_column = getattr(OhlcvUnified, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"ohlcv|pairs={ticker_exchange_pairs}|exchange={exchange}|asset_type={asset_type}|year={year}|month={month}|start={start_date}|end={end_date}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@app.get("/ohlcv/latest/", response_model=RealTimeOhlcvResponse)
async def get_realtime_latest_ohlcv(
    tickers: str = Query(..., description="Comma-separated tickers in TICKER.EXCHANGE format (e.g., AAPL.US,MSFT.US,BP.LSE). The exchange suffix is required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified tickers.
    Ticker format: TICKER.EXCHANGE (e.g., AAPL.US, BP.LSE, BTC-USD.CC). The exchange suffix is required.
    Unknown tickers are reported in `missing` and do not fail the request; a
    ticker with no live quote comes back with null prices.
    """
    raw_tickers = parse_comma_separated_preserve(tickers)
    if not raw_tickers:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    pairs = []
    for t in raw_tickers:
        try:
            pairs.append(parse_ticker_exchange(t))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    ticker_codes = [t for t, _ in pairs]
    asset_query = select(Asset.code).where(Asset.code.in_(ticker_codes))
    result = await db.execute(asset_query)
    found_codes = {row[0] for row in result.all()}

    resolvable = [(t, e) for t, e in pairs if t in found_codes]
    missing = [f"{t}.{e}" for t, e in pairs if t not in found_codes]

    if not resolvable:
        raise HTTPException(
            status_code=404,
            detail=f"No asset found with tickers: {', '.join(missing)}",
        )

    quotes = await fetch_eodhd_realtime_multi([f"{t}.{e}" for t, e in resolvable])
    items = [
        parse_eodhd_response(quotes.get(f"{t}.{e}".upper(), {}), t, e)
        for t, e in resolvable
    ]

    return RealTimeOhlcvResponse(data=items, count=len(items), missing=missing)


@app.post("/ohlcv/", response_model=OhlcvDataResponse, status_code=201)
async def create_ohlcv_data(ohlcv: OhlcvDataCreate, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    db_ohlcv = OhlcvUnified(**ohlcv.model_dump())
    db.add(db_ohlcv)
    try:
        await db.commit()
        await db.refresh(db_ohlcv)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_ohlcv


@app.post("/ohlcv/bulk/", response_model=BulkInsertResponse, status_code=201)
async def bulk_create_ohlcv_data(
    bulk_data: OhlcvDataBulkCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    inserted = 0
    failed = 0
    errors = []
    
    for i, record in enumerate(bulk_data.records):
        try:
            db_ohlcv = OhlcvUnified(**record.model_dump())
            db.add(db_ohlcv)
            await db.flush()
            inserted += 1
        except Exception as e:
            failed += 1
            errors.append(f"Record {i}: {str(e)}")
            await db.rollback()
    
    if inserted > 0:
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=400, detail=f"Commit failed: {str(e)}")
    
    return BulkInsertResponse(inserted=inserted, failed=failed, errors=errors)


# ── S&P 500 Endpoints ────────────────────────────────────────────────────────

# ── Ticker Alias Endpoints ───────────────────────────────────────────────────

# ── ETF / Index Endpoints ─────────────────────────────────────────────────────



# ── Government Bond Endpoints ────────────────────────────────────────────────



# ── Foreign Exchange (FX) Endpoints ──────────────────────────────────────────


# ── Crypto Endpoints ─────────────────────────────────────────────────────────



# ── UK Stock (LSE) Endpoints ─────────────────────────────────────────────



# ── FTSE 100 Endpoints ─────────────────────────────────────────────────────



# ── US Treasury Rate Endpoints ───────────────────────────────────────────────

# --- UST Bill Rates ---


# --- UST Long-Term Rates ---


# --- UST Real Yield Rates ---


# --- UST Yield Rates ---

_UAT_UST_SERIES = ("bill", "long_term", "real_yield", "yield")

_UAT_UST_TENORS = {
    "bill": ("4WK", "6WK", "8WK", "13WK", "17WK", "26WK", "52WK"),
    "yield": (
        "1M", "1.5M", "2M", "3M", "4M", "6M",
        "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y",
    ),
    "real_yield": ("5Y", "7Y", "10Y", "20Y", "30Y"),
}

_UAT_UST_RATE_TYPES = ("BC_20year", "Over_10_Years", "Real_Rate")

_UAT_UST_TENOR_SERIES = tuple(_UAT_UST_TENORS)
_UAT_UST_RATE_TYPE_SERIES = ("long_term",)

_UAT_UST_COLUMNS = {
    "bill": "NULL::numeric AS rate, discount, coupon, avg_discount, avg_coupon, maturity_date, cusip, NULL::numeric AS extrapolation_factor",
    "long_term": "rate, NULL::numeric AS discount, NULL::numeric AS coupon, NULL::numeric AS avg_discount, NULL::numeric AS avg_coupon, NULL::date AS maturity_date, NULL::varchar AS cusip, extrapolation_factor",
    "real_yield": "rate, NULL::numeric AS discount, NULL::numeric AS coupon, NULL::numeric AS avg_discount, NULL::numeric AS avg_coupon, NULL::date AS maturity_date, NULL::varchar AS cusip, NULL::numeric AS extrapolation_factor",
    "yield": "rate, NULL::numeric AS discount, NULL::numeric AS coupon, NULL::numeric AS avg_discount, NULL::numeric AS avg_coupon, NULL::date AS maturity_date, NULL::varchar AS cusip, NULL::numeric AS extrapolation_factor",
}

_UAT_UST_TABLES = {
    "bill": ("ust_bill_rates", "tenor", None),
    "long_term": ("ust_long_term_rates", None, "rate_type"),
    "real_yield": ("ust_real_yield_rates", "tenor", None),
    "yield": ("ust_yield_rates", "tenor", None),
}


@app.get("/ust/", response_model=UstPaginatedResponse)
async def get_ust_rates(
    series: Optional[str] = Query(None, description="Comma-separated series: bill, long_term, real_yield, yield (default all)"),
    tenor: Optional[str] = Query(None, description="Single tenor (e.g., 4WK, 13WK, 2Y, 10Y)"),
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 13WK,2Y,10Y)"),
    rate_type: Optional[str] = Query(None, description="Single long-term rate type (e.g., BC_20year)"),
    rate_types: Optional[str] = Query(None, description="Comma-separated rate types (e.g., BC_20year,Over_10_Years)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    latest: bool = Query(False, description="Return one row per series and tenor/rate type"),
    sort_by: Optional[str] = Query("date", pattern="^(date|rate|discount|coupon)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    US Treasury rates across all series in one response.

    Consolidates the former per-series endpoints: filter by `series`,
    tenor or rate type, date range, and page through one envelope.
    `latest=true` returns the most recent row per series and tenor/rate type.
    """
    requested = [x.lower() for x in parse_comma_separated(series)] if series else list(_UAT_UST_SERIES)
    selected = [name for name in _UAT_UST_SERIES if name in requested]
    if not selected:
        raise HTTPException(
            status_code=400,
            detail="series must be one of: bill, long_term, real_yield, yield",
        )

    tenor_list = parse_comma_separated(tenors) or ([tenor.upper()] if tenor else None)
    rate_type_list = (
        parse_comma_separated_preserve(rate_types) or ([rate_type] if rate_type else None)
    )

    if tenor_list:
        tenor_series = [name for name in selected if name in _UAT_UST_TENOR_SERIES]
        if not tenor_series:
            raise HTTPException(
                status_code=400,
                detail=(
                    "tenor only applies to series: "
                    f"{', '.join(_UAT_UST_TENOR_SERIES)}"
                ),
            )
        accepted = []
        for name in tenor_series:
            for value in _UAT_UST_TENORS[name]:
                if value not in accepted:
                    accepted.append(value)
        invalid = [t for t in tenor_list if t not in accepted]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid tenor(s): {', '.join(invalid)}. "
                    f"Accepted for {', '.join(tenor_series)}: {', '.join(accepted)}"
                ),
            )

    if rate_type_list:
        if not any(name in _UAT_UST_RATE_TYPE_SERIES for name in selected):
            raise HTTPException(
                status_code=400,
                detail=(
                    "rate_type only applies to series: "
                    f"{', '.join(_UAT_UST_RATE_TYPE_SERIES)}"
                ),
            )
        invalid = [r for r in rate_type_list if r not in _UAT_UST_RATE_TYPES]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid rate_type(s): {', '.join(invalid)}. "
                    f"Accepted: {', '.join(_UAT_UST_RATE_TYPES)}"
                ),
            )

    params = {}

    def _branch(name):
        table, tenor_col, rate_type_col = _UAT_UST_TABLES[name]
        filters = []
        if start_date:
            filters.append("date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("date <= :end_date")
            params["end_date"] = end_date
        if tenor_col and tenor_list:
            keys = []
            for i, value in enumerate(tenor_list):
                key = f"tenor_{name}_{i}"
                params[key] = value
                keys.append(f":{key}")
            filters.append(f"{tenor_col} IN ({', '.join(keys)})")
        if rate_type_col and rate_type_list:
            keys = []
            for i, value in enumerate(rate_type_list):
                key = f"rtype_{name}_{i}"
                params[key] = value
                keys.append(f":{key}")
            filters.append(f"{rate_type_col} IN ({', '.join(keys)})")
        where = " WHERE " + " AND ".join(filters) if filters else ""
        cols = _UAT_UST_COLUMNS[name]
        tenor_expr = tenor_col or "NULL::varchar"
        rate_type_expr = rate_type_col or "NULL::varchar"
        return (
            f"SELECT '{name}' AS series, date, {tenor_expr} AS tenor, "
            f"{rate_type_expr} AS rate_type, {cols} FROM {table}{where}"
        )

    union_sql = " UNION ALL ".join(_branch(name) for name in selected)

    if latest:
        count_sql = (
            "SELECT count(*) FROM ("
            "SELECT DISTINCT ON (series, coalesce(tenor, rate_type)) series "
            f"FROM ({union_sql}) AS u "
            "ORDER BY series, coalesce(tenor, rate_type), date DESC"
            ") AS l"
        )
        data_sql = (
            "SELECT * FROM ("
            "SELECT DISTINCT ON (series, coalesce(tenor, rate_type)) * "
            f"FROM ({union_sql}) AS u "
            "ORDER BY series, coalesce(tenor, rate_type), date DESC"
            ") AS l ORDER BY date DESC LIMIT :limit OFFSET :offset"
        )
    else:
        sort_column = sort_by if sort_by in ("date", "rate", "discount", "coupon") else "date"
        direction = "DESC" if sort_order == "desc" else "ASC"
        count_sql = f"SELECT count(*) FROM ({union_sql}) AS u"
        data_sql = (
            f"SELECT * FROM ({union_sql}) AS u "
            f"ORDER BY {sort_column} {direction} NULLS LAST, date DESC "
            "LIMIT :limit OFFSET :offset"
        )

    cache_key = (
        f"ust|series={selected}|tenors={tenor_list}|rtypes={rate_type_list}"
        f"|start={start_date}|end={end_date}|latest={latest}"
    )
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(text(count_sql), params)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page
    result = await db.execute(text(data_sql), params)
    rows = result.fetchall()

    data = [
        UstRateItem(
            series=row.series,
            date=row.date,
            tenor=row.tenor,
            rate_type=row.rate_type,
            rate=row.rate,
            discount=row.discount,
            coupon=row.coupon,
            avg_discount=row.avg_discount,
            avg_coupon=row.avg_coupon,
            maturity_date=row.maturity_date,
            cusip=row.cusip,
            extrapolation_factor=row.extrapolation_factor,
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UstPaginatedResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )



# --- Commodities ---

@app.get("/commodity/", response_model=CommodityPaginatedResponse)
async def get_commodity_ohlcv_data(
    symbol: Optional[str] = Query(None, description="Single commodity symbol (e.g., LGOc3)"),
    symbols: Optional[str] = Query(None, description="Comma-separated commodity symbols (e.g., LGOc3,NICKEL,GDK)"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., Energy, Metals, Grains, Softs, Livestock, Other)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    open_min: Optional[Decimal] = Query(None),
    open_max: Optional[Decimal] = Query(None),
    close_min: Optional[Decimal] = Query(None),
    close_max: Optional[Decimal] = Query(None),
    volume_min: Optional[int] = Query(None),
    volume_max: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|volume|close|open|high|low)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    latest: bool = Query(False, description="Return only the most recent bar per symbol"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for commodities.
    Supports filtering by symbol(s), category, date range, and price/volume bounds.
    Set `latest=true` to return only the most recent bar per symbol.
    """
    symbol_list = parse_comma_separated_preserve(symbols) or ([symbol] if symbol else None)

    conditions = []
    if symbol_list:
        if len(symbol_list) == 1:
            conditions.append(CommodityEOD.symbol == symbol_list[0])
        else:
            conditions.append(CommodityEOD.symbol.in_(symbol_list))
    if category:
        conditions.append(CommodityEOD.category == category)
    if start_date:
        conditions.append(CommodityEOD.date >= start_date)
    if end_date:
        conditions.append(CommodityEOD.date <= end_date)
    if year:
        conditions.append(func.extract("year", CommodityEOD.date) == year)
    if month:
        conditions.append(func.extract("month", CommodityEOD.date) == month)
    if open_min is not None:
        conditions.append(CommodityEOD.open >= open_min)
    if open_max is not None:
        conditions.append(CommodityEOD.open <= open_max)
    if close_min is not None:
        conditions.append(CommodityEOD.close >= close_min)
    if close_max is not None:
        conditions.append(CommodityEOD.close <= close_max)
    if volume_min is not None:
        conditions.append(CommodityEOD.volume >= volume_min)
    if volume_max is not None:
        conditions.append(CommodityEOD.volume <= volume_max)

    query = select(CommodityEOD).where(*conditions)
    count_query = select(func.count()).select_from(CommodityEOD).where(*conditions)

    if latest:
        query = query.distinct(CommodityEOD.symbol).order_by(
            CommodityEOD.symbol.asc(), CommodityEOD.date.desc()
        )
        count_query = (
            select(func.count(func.distinct(CommodityEOD.symbol)))
            .select_from(CommodityEOD)
            .where(*conditions)
        )
    else:
        sort_column = getattr(CommodityEOD, sort_by or "date")
        query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"commodities|latest={latest}|symbols={symbol_list}|category={category}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return CommodityPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@app.get("/commodity/latest/", response_model=RealTimeOhlcvResponse)
async def get_commodity_latest_realtime(
    symbols: str = Query(..., description="Comma-separated commodity symbols (e.g., LGOc3,NICKEL,GDK). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified commodity symbols.
    Symbols resolve as SYMBOL.COMM. Unknown symbols are reported in `missing`
    and do not fail the request; a known symbol without a live quote comes back
    with null price fields.
    """
    symbol_list = parse_comma_separated_preserve(symbols)
    if not symbol_list:
        raise HTTPException(status_code=400, detail="symbols parameter is required")

    known_result = await db.execute(
        select(CommodityEOD.symbol).distinct().where(CommodityEOD.symbol.in_(symbol_list))
    )
    known = {row[0] for row in known_result.fetchall()}
    resolvable = [sym for sym in symbol_list if sym in known]
    missing = [sym for sym in symbol_list if sym not in known]

    if not resolvable:
        raise HTTPException(
            status_code=404,
            detail=f"No commodity found with symbols: {', '.join(missing)}",
        )

    quotes = await fetch_eodhd_realtime_multi(
        [f"{sym}.{COMMODITY_EXCHANGE}" for sym in resolvable]
    )

    items = [
        parse_eodhd_response(
            quotes.get(f"{sym}.{COMMODITY_EXCHANGE}".upper(), {}),
            sym,
            COMMODITY_EXCHANGE,
        )
        for sym in resolvable
    ]

    return RealTimeOhlcvResponse(data=items, count=len(items), missing=missing)


@app.get("/commodity/symbols/", response_model=CommoditySymbolResponse)
async def get_commodity_symbols(
    category: Optional[str] = Query(None, description="Filter by category (e.g., Energy, Metals)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns all commodity symbols with their latest metadata (name, category).
    """
    category_clause = f"AND category = '{category}'" if category else ""

    query = text(f"""
        SELECT DISTINCT ON (symbol) symbol, name, category
        FROM commodities_eod
        WHERE 1=1 {category_clause}
        ORDER BY symbol, date DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        CommoditySymbolItem(
            symbol=row.symbol,
            name=row.name,
            category=row.category,
        )
        for row in rows
    ]

    return CommoditySymbolResponse(data=items, count=len(items))


# Guardrail 1: Only SELECT statements are allowed
_SELECT_KEYWORDS = {"SELECT", "WITH"}
_FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "REPLACE", "GRANT", "REVOKE", "COPY", "VACUUM", "REINDEX", "CLUSTER",
    "COMMENT", "LOCK", "ABORT", "RESET", "SET", "SHOW", "DISCARD",
    "LISTEN", "NOTIFY", "LOAD", "EXECUTE", "EXPLAIN", "PREPARE",
    "DEALLOCATE", "BEGIN", "COMMIT", "ROLLBACK",
    "SAVEPOINT", "RELEASE", "CHECKPOINT", "REASSIGN", "SECURITY",
}
# NOTE: CLOSE, FETCH, and MOVE are SQL cursor commands but are excluded from
# the forbidden list because they collide with common column names (e.g. the
# `close` column in ohlcv_data).  These commands are only meaningful as
# standalone statements (CLOSE cursor_name / FETCH ... / MOVE ...), never
# inside a SELECT, so the first-keyword check (only SELECT/WITH allowed)
# already prevents their use as commands.

# Guardrail 2: Allowed tables (whitelist)
ALLOWED_TABLES = {
    "ohlcv_unified", "assets", "ticker_aliases", "tickers",
    "ust_bill_rates", "ust_long_term_rates", "ust_real_yield_rates", "ust_yield_rates",
    "commodities_eod",
}

# Guardrail 3: Maximum rows returned
SQL_MAX_ROWS = int(os.getenv("SQL_MAX_ROWS", "5000"))

# Guardrail 4: Query timeout in seconds
SQL_TIMEOUT_S = int(os.getenv("SQL_TIMEOUT_S", "30"))

# Regex to extract table names from FROM / JOIN clauses
_TABLE_RE = re.compile(
    r"\b(?:FROM|JOIN)\s+\"?(\w+)\"?", re.IGNORECASE
)


def _serialize_value(val):
    """Convert non-JSON-serializable types to safe primitives."""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    return val


def _validate_sql(sql: str) -> None:
    """
    Validate that a SQL query is read-only and targets only allowed tables.

    Guardrails:
      1. Read-only — only SELECT / WITH (CTE) statements permitted
      2. Allowed tables — all referenced tables must be in ALLOWED_TABLES
      3. Forbidden keywords — blocks DML/DDL/utility statements
    """
    stripped = sql.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    # Check the first keyword to ensure it's a SELECT or WITH (CTE)
    first_word = stripped.split()[0].upper() if stripped.split() else ""
    if first_word not in _SELECT_KEYWORDS:
        raise HTTPException(
            status_code=400,
            detail=f"Only SELECT queries are allowed. Statement starts with '{first_word}'."
        )

    # Check for forbidden keywords anywhere in the query
    upper_sql = stripped.upper()
    # Tokenise on word boundaries to avoid false positives (e.g. "SELECTED")
    tokens = set(re.findall(r"[A-Za-z_]\w*", upper_sql))
    forbidden_found = tokens & _FORBIDDEN_KEYWORDS
    if forbidden_found:
        raise HTTPException(
            status_code=400,
            detail=f"Forbidden keyword(s) in query: {', '.join(sorted(forbidden_found))}. "
                   f"Only read-only SELECT queries are allowed."
        )

    # Extract table names from FROM / JOIN clauses
    referenced_tables = {t.lower() for t in _TABLE_RE.findall(stripped)}

    # If the query uses CTEs, extract CTE names and exclude them from
    # the table check — they are query-local aliases, not real tables.
    cte_names = set()
    for m in re.finditer(r"\b(\w+)\s+AS\s*\(", stripped, re.IGNORECASE):
        # Only count CTE names that appear after WITH or a comma
        cte_names.add(m.group(1).lower())

    real_tables = referenced_tables - cte_names
    disallowed = real_tables - ALLOWED_TABLES
    if disallowed:
        raise HTTPException(
            status_code=400,
            detail=f"Table(s) not allowed: {', '.join(sorted(disallowed))}. "
                   f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}."
        )


@app.post("/sql/", response_model=SqlQueryResponse)
async def execute_sql(
    body: SqlQueryRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Execute a read-only SQL SELECT query against the database.

    Guardrails:
      1. **Read-only** — Only SELECT / WITH (CTE) statements are permitted.
         DML (INSERT, UPDATE, DELETE) and DDL (CREATE, DROP, ALTER) are blocked.
      2. **Timeout** — Queries are cancelled after SQL_TIMEOUT_S seconds (default 30).
      3. **Row limit** — At most SQL_MAX_ROWS rows are returned (default 5000).
         If the query produces more rows, the response is truncated and
         `truncated` is set to `true`.
      4. **Allowed tables** — Only the following tables may be referenced:
         `ohlcv_unified`, `assets`, `ticker_aliases`, `tickers`, `commodities_eod`,
         `ust_bill_rates`, `ust_long_term_rates`, `ust_real_yield_rates`, `ust_yield_rates`.
    """
    # Guardrails 1, 2 (table whitelist), 3 (forbidden keywords)
    _validate_sql(body.query)

    # Guardrail 3 (timeout): set a statement timeout for this session.
    # We use an explicit transaction block so that SET LOCAL (which only
    # works inside BEGIN/COMMIT) takes effect.  The transaction is
    # read-only so there are no side-effects on commit.
    limited_query = text(f"SELECT * FROM ({body.query}) AS _sql_subq LIMIT {SQL_MAX_ROWS + 1}")
    timeout_sql = text(f"SET LOCAL statement_timeout = '{SQL_TIMEOUT_S}s'")

    try:
        async with db.begin():
            await db.execute(timeout_sql)
            result = await db.execute(limited_query)
            rows = result.fetchall()
    except Exception as e:
        err_msg = str(e)
        # Detect timeout errors from PostgreSQL
        if "cancel" in err_msg.lower() or "timeout" in err_msg.lower():
            raise HTTPException(
                status_code=408,
                detail=f"Query timed out after {SQL_TIMEOUT_S}s. Simplify your query or add more filters."
            )
        raise HTTPException(status_code=400, detail=f"Query execution error: {err_msg}")

    # Determine if results were truncated
    truncated = len(rows) > SQL_MAX_ROWS
    if truncated:
        rows = rows[:SQL_MAX_ROWS]

    # Build column names from the cursor description
    columns = list(result.keys())

    # Convert rows to list of dicts, serializing non-JSON types
    row_dicts = [
        {col: _serialize_value(val) for col, val in zip(columns, row)}
        for row in rows
    ]

    return SqlQueryResponse(
        columns=columns,
        rows=row_dicts,
        row_count=len(row_dicts),
        truncated=truncated
    )
