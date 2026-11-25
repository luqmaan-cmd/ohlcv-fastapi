from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import text
from typing import List, Optional
from datetime import date, datetime, timedelta
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
    OhlcvData, SP500Constituent, Asset, TickerAlias, Ticker,
    EtfIndexOhlcvData, EtfIndexAsset,
    GovBondOhlcvData, GovBondAsset,
    FxOhlcvData, FxAsset,
    UkOhlcvData, UkAsset,
    Ftse100Constituent,
    UstBillRate, UstLongTermRate, UstRealYieldRate, UstYieldRate,
    CryptoOhlcvData, CryptoAsset,
    CommodityEOD,
    OhlcvUnified,
)
from schemas import (
    OhlcvDataCreate, OhlcvDataUpdate, OhlcvDataResponse, UnifiedOhlcvResponse,
    OhlcvDataBulkCreate, PaginatedResponse, OhlcvStatsResponse,
    BatchLatestResponse, BulkInsertResponse,
    SP500ConstituentResponse, SP500ListResponse,
    SP500LatestItem, SP500LatestResponse,
    SP500HistoryItem, SP500HistoryResponse,
    TickerAliasCreate, TickerAliasUpdate, TickerAliasResponse, TickerAliasListResponse,
    SqlQueryRequest, SqlQueryResponse,
    EtfIndexOhlcvResponse, EtfIndexPaginatedResponse,
    EtfIndexAssetResponse, EtfIndexLatestItem, EtfIndexLatestResponse,
    GovBondOhlcvResponse, GovBondPaginatedResponse,
    GovBondLatestItem, GovBondLatestResponse,
    FxOhlcvResponse, FxPaginatedResponse,
    FxLatestItem, FxLatestResponse,
    FxAssetItem, FxAssetResponse,
    UkOhlcvResponse, UkPaginatedResponse,
    UkLatestItem, UkLatestResponse,
    UkAssetItem, UkAssetResponse,
    Ftse100LatestItem, Ftse100LatestResponse,
    Ftse100HistoryItem, Ftse100PaginatedResponse,
    Ftse100ConstituentItem, Ftse100ConstituentResponse,
    GovBondAssetItem, GovBondAssetResponse,
    EtfIndexAssetListResponse,
    UstBillRateResponse, UstBillPaginatedResponse,
    UstBillLatestItem, UstBillLatestResponse,
    UstLongTermRateResponse, UstLongTermPaginatedResponse,
    UstLongTermLatestItem, UstLongTermLatestResponse,
    UstRealYieldRateResponse, UstRealYieldPaginatedResponse,
    UstRealYieldLatestItem, UstRealYieldLatestResponse,
    UstYieldRateResponse, UstYieldPaginatedResponse,
    UstYieldLatestItem, UstYieldLatestResponse,
    UstRateItem, UstPaginatedResponse,
    CryptoOhlcvResponse, CryptoPaginatedResponse,
    CryptoLatestItem, CryptoLatestResponse,
    CryptoHistoryItem, CryptoHistoryPaginatedResponse,
    CryptoTop100Item, CryptoTop100Response,
    CryptoAssetItem, CryptoAssetResponse,
    CommodityOhlcvResponse, CommodityPaginatedResponse,
    CommodityLatestItem, CommodityLatestResponse,
    CommoditySymbolItem, CommoditySymbolResponse,
    CommodityCategoryResponse,
    RealTimeOhlcvItem, RealTimeOhlcvResponse,
    AssetLookupItem, AssetLookupResponse,
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

_IS_UAT = os.getenv("APP_ENV", "").lower() == "uat"


def _uat_only(path: str, **kwargs):
    """Register a route only on the UAT service (APP_ENV=uat)."""
    def decorator(func):
        if _IS_UAT:
            app.add_api_route(path, func, **kwargs)
        return func
    return decorator


def _prod_only(path: str, **kwargs):
    """Register a route everywhere except the UAT service."""
    def decorator(func):
        if not _IS_UAT:
            app.add_api_route(path, func, **kwargs)
        return func
    return decorator


_RETIRED_ENABLED = os.getenv("ENABLE_RETIRED_ROUTES", "") == "1"


def _retired(path: str, **kwargs):
    """Register a retired route only when ENABLE_RETIRED_ROUTES=1."""
    def decorator(func):
        if _RETIRED_ENABLED:
            app.add_api_route(path, func, **kwargs)
        return func
    return decorator


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


@_retired("/ohlcv/latest_close/", methods=["GET"], response_model=BatchLatestResponse)
async def get_batch_latest_close_ohlcv(
    tickers: Optional[str] = Query(None, description="Comma-separated tickers with exchange suffix (e.g., AAPL.US,MSFT.US). If omitted, returns latest for all tickers."),
    exchange: Optional[str] = Query(None, description="Filter by exchange (e.g., US, LSE, CC). Used when no specific tickers are given."),
    asset_type: Optional[str] = Query(None, description="Filter by asset type (e.g., ETF, INDEX, FOREX, Cryptocurrencies, Government Bonds)"),
    sort_by: Optional[str] = Query(None, pattern="^(ticker|volume|close|open|high|low)$"),
    per_page: Optional[int] = Query(None, ge=1, le=5000, description="Limit number of results (e.g., 100 for top-100 by volume)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Parse tickers — accept both TICKER.EXCHANGE and bare tickers (auto-append US)
    raw_tickers = parse_comma_separated_preserve(tickers)
    ticker_exchange_pairs: list[tuple[str, str]] = []
    if raw_tickers:
        for t in raw_tickers:
            try:
                ticker_exchange_pairs.append(parse_ticker_exchange(t))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

    cutoff = date.today() - timedelta(days=7)

    ex_filter = f"AND exchange = '{exchange.upper()}'" if exchange else ("AND exchange = 'US'" if not ticker_exchange_pairs else "")
    at_filter = f"AND asset_type = '{asset_type}'" if asset_type else ""

    if ticker_exchange_pairs:
        # Build VALUES list with (ticker, exchange) pairs
        ticker_values = ", ".join(f"('{t}','{ex}')" for t, ex in ticker_exchange_pairs)
        query = text(f"""
            SELECT t.ticker, o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume, o.instrument_id,
                   o.exchange, o.asset_type,
                   o.created_at, o.updated_at
            FROM (VALUES {ticker_values}) AS t(ticker, exchange)
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close,
                       volume, instrument_id, exchange, asset_type,
                       created_at, updated_at
                FROM ohlcv_unified
                WHERE ticker = t.ticker
                      AND exchange = t.exchange
                      {at_filter}
                      AND date >= :cutoff
                ORDER BY date DESC
                LIMIT 1
            ) o
            ORDER BY t.ticker ASC
        """)
    else:
        sort_clause = "d.ticker ASC"
        limit_clause = ""
        if sort_by == "volume":
            sort_clause = "o.volume DESC NULLS LAST"
        elif sort_by:
            sort_col_map = {
                "close": "o.close", "open": "o.open",
                "high": "o.high", "low": "o.low",
            }
            sort_clause = f"{sort_col_map.get(sort_by, 'o.close')} DESC NULLS LAST"
        if sort_by == "volume" and per_page:
            limit_clause = f"LIMIT {per_page}"

        query = text(f"""
            SELECT d.ticker, o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume, o.instrument_id,
                   o.exchange, o.asset_type,
                   o.created_at, o.updated_at
            FROM tickers d
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close,
                       volume, instrument_id, exchange, asset_type,
                       created_at, updated_at
                FROM ohlcv_unified
                WHERE ticker = d.ticker
                      {ex_filter}
                      {at_filter}
                      AND date >= :cutoff
                ORDER BY date DESC
                LIMIT 1
            ) o
            ORDER BY {sort_clause}
            {limit_clause}
        """)

    result = await db.execute(query, {"cutoff": cutoff})
    rows = result.fetchall()

    items = [
        OhlcvDataResponse(
            id=row.id,
            ticker=row.ticker,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
            instrument_id=row.instrument_id,
            exchange=row.exchange,
            asset_type=row.asset_type,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in rows
    ]

    return BatchLatestResponse(
        data=items,
        count=len(items)
    )


@_retired("/ohlcv/latest_close/{ticker}", methods=["GET"], response_model=OhlcvDataResponse)
async def get_latest_close_ohlcv(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Returns the latest OHLCV record for a single ticker.
    Ticker format: TICKER.EXCHANGE (e.g., AAPL.US, BP.LSE). The exchange suffix is required.
    """
    try:
        t, ex = parse_ticker_exchange(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    query = select(OhlcvUnified).where(
        and_(
            OhlcvUnified.ticker == t,
            OhlcvUnified.exchange == ex,
            OhlcvUnified.date >= date.today() - timedelta(days=7)
        )
    ).order_by(OhlcvUnified.date.desc()).limit(1)
    
    result = await db.execute(query)
    ohlcv = result.scalar_one_or_none()
    
    if not ohlcv:
        raise HTTPException(status_code=404, detail=f"No OHLCV data found for ticker: {ticker}")
    
    return ohlcv


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


@_retired("/ohlcv/stats/{ticker}", methods=["GET"], response_model=OhlcvStatsResponse)
async def get_ohlcv_stats(
    ticker: str,
    start_date: Optional[date] = Query(None, description="Start date for stats (enables partition pruning)"),
    end_date: Optional[date] = Query(None, description="End date for stats (enables partition pruning)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Returns OHLCV statistics for a ticker.
    Ticker format: TICKER.EXCHANGE (e.g., AAPL.US, BP.LSE). The exchange suffix is required.
    """
    try:
        t, ex = parse_ticker_exchange(ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    stats_conditions = [OhlcvUnified.ticker == t, OhlcvUnified.exchange == ex]
    if start_date:
        stats_conditions.append(OhlcvUnified.date >= start_date)
    if end_date:
        stats_conditions.append(OhlcvUnified.date <= end_date)

    stats_query = select(
        func.count(OhlcvUnified.id).label("count"),
        func.min(OhlcvUnified.date).label("earliest_date"),
        func.max(OhlcvUnified.date).label("latest_date"),
        func.avg(OhlcvUnified.volume).label("avg_volume"),
        func.min(OhlcvUnified.close).label("min_close"),
        func.max(OhlcvUnified.close).label("max_close"),
        func.avg(OhlcvUnified.close).label("avg_close")
    ).where(and_(*stats_conditions))
    
    result = await db.execute(stats_query)
    stats = result.one()
    
    # Access Row fields by index to avoid collision with tuple's .count() method
    stats_count = stats[0]
    if stats_count == 0:
        raise HTTPException(status_code=404, detail=f"No OHLCV data found for ticker: {t}.{ex}")
    
    fifty_two_weeks_ago = date.today() - timedelta(weeks=52)
    fifty_two_week_query = select(
        func.max(OhlcvUnified.close).label("high"),
        func.min(OhlcvUnified.close).label("low")
    ).where(
        and_(
            OhlcvUnified.ticker == t,
            OhlcvUnified.exchange == ex,
            OhlcvUnified.date >= fifty_two_weeks_ago
        )
    )
    
    fw_result = await db.execute(fifty_two_week_query)
    fw_stats = fw_result.one()
    
    return OhlcvStatsResponse(
        ticker=f"{t}.{ex}",
        count=stats_count,
        earliest_date=stats[1],
        latest_date=stats[2],
        avg_volume=float(stats[3]) if stats[3] else None,
        min_close=stats[4],
        max_close=stats[5],
        avg_close=stats[6],
        fifty_two_week_high=fw_stats[0],
        fifty_two_week_low=fw_stats[1]
    )


@_retired("/tickers/", methods=["GET"], response_model=List[str])
async def get_all_tickers(db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    # Uses the tickers lookup table (kept in sync via trigger) instead of
    # SELECT DISTINCT on ohlcv_data (43M rows) — ~5ms vs ~8.6s.
    query = text("SELECT ticker FROM tickers ORDER BY ticker ASC")
    result = await db.execute(query)
    return [row[0] for row in result.all()]


@_retired("/assets/{ticker}", methods=["GET"], response_model=AssetLookupResponse)
async def lookup_asset(
    ticker: str,
    exchange: Optional[str] = Query(None, description="Filter by exchange (e.g., NASDAQ, LSE, CC)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Look up asset metadata by ticker across all asset tables.
    Returns matching assets from the unified assets table first, then falls
    back to per-class tables (crypto, FX, UK, ETF/index, gov bonds, FTSE 100).
    Use `exchange` to disambiguate tickers that exist on multiple exchanges.
    """
    ticker = ticker.upper()
    items: list[AssetLookupItem] = []

    # 1. Unified assets table
    q = select(Asset).where(Asset.code == ticker)
    if exchange:
        q = q.where(Asset.exchange == exchange.upper())
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                           # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type=row.type,                    # type: ignore[arg-type]
            isin=row.isin,                          # type: ignore[arg-type]
            currency=row.currency_code,             # type: ignore[arg-type]
            description=row.description,            # type: ignore[arg-type]
            sector=row.sector,                      # type: ignore[arg-type]
            industry=row.industry,                  # type: ignore[arg-type]
            country=row.country_name,               # type: ignore[arg-type]
            gic_sector=row.gic_sector,             # type: ignore[arg-type]
        ))

    # 2. UK stocks
    q = select(UkAsset).where(UkAsset.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type="stock",                     # type: ignore[arg-type]
            sector=row.sector,                      # type: ignore[arg-type]
            industry=row.industry,                  # type: ignore[arg-type]
            isin=row.isin,                          # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        ))

    # 3. ETFs and Indices
    q = select(EtfIndexAsset).where(EtfIndexAsset.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type=row.type,                    # type: ignore[arg-type]
            isin=row.isin,                          # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        ))

    # 4. Government bonds
    q = select(GovBondAsset).where(GovBondAsset.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type=row.type,                    # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
            country=row.country,                    # type: ignore[arg-type]
        ))

    # 5. FX
    q = select(FxAsset).where(FxAsset.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type="fx",                         # type: ignore[arg-type]
            base_currency=row.base_currency,        # type: ignore[arg-type]
            quote_currency=row.quote_currency,      # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        ))

    # 6. Crypto
    q = select(CryptoAsset).where(CryptoAsset.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            asset_type="crypto",                    # type: ignore[arg-type]
            base_currency=row.base_currency,        # type: ignore[arg-type]
            quote_currency=row.quote_currency,      # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        ))

    # 7. FTSE 100 constituents
    q = select(Ftse100Constituent).where(Ftse100Constituent.code == ticker)
    result = await db.execute(q)
    for row in result.scalars().all():
        items.append(AssetLookupItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange="LSE",                          # type: ignore[arg-type]
            asset_type="stock",                     # type: ignore[arg-type]
            sector=row.sector,                      # type: ignore[arg-type]
            industry=row.industry,                  # type: ignore[arg-type]
            isin=row.isin,                          # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        ))

    if not items:
        raise HTTPException(status_code=404, detail=f"No asset found with ticker: {ticker}")

    return AssetLookupResponse(data=items, count=len(items))


@_retired("/ohlcv/{ohlcv_id}", methods=["GET"], response_model=OhlcvDataResponse)
async def get_ohlcv_by_id(ohlcv_id: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvUnified).where(OhlcvUnified.id == ohlcv_id)
    result = await db.execute(query)
    ohlcv = result.scalar_one_or_none()
    if not ohlcv:
        raise HTTPException(status_code=404, detail="OHLCV data not found")
    return ohlcv


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


@_retired("/ohlcv/{ohlcv_id}", methods=["PUT"], response_model=OhlcvDataResponse)
async def update_ohlcv_data(
    ohlcv_id: str,
    ohlcv: OhlcvDataUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = select(OhlcvUnified).where(OhlcvUnified.id == ohlcv_id)
    result = await db.execute(query)
    db_ohlcv = result.scalar_one_or_none()
    
    if not db_ohlcv:
        raise HTTPException(status_code=404, detail="OHLCV data not found")
    
    update_data = ohlcv.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_ohlcv, key, value)
    
    try:
        await db.commit()
        await db.refresh(db_ohlcv)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
    return db_ohlcv


@_retired("/ohlcv/{ohlcv_id}", methods=["DELETE"], status_code=204)
async def delete_ohlcv_data(ohlcv_id: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvUnified).where(OhlcvUnified.id == ohlcv_id)
    result = await db.execute(query)
    db_ohlcv = result.scalar_one_or_none()
    
    if not db_ohlcv:
        raise HTTPException(status_code=404, detail="OHLCV data not found")
    
    await db.delete(db_ohlcv)
    await db.commit()
    return None


# ── S&P 500 Endpoints ────────────────────────────────────────────────────────

@_retired("/sp500/", methods=["GET"], response_model=SP500ListResponse)
async def list_sp500_constituents(
    sector: Optional[str] = Query(None, description="Filter by GIC sector (e.g., Information Technology)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List all S&P 500 constituents with enriched metadata from the assets table.
    Paginated and filterable by sector and active status.
    """
    # Base query: sp500_constituents LEFT JOIN assets on code
    base_where = []
    if sector:
        base_where.append(SP500Constituent.sector == sector)
    if is_active is not None:
        base_where.append(SP500Constituent.is_active == is_active)

    # Count query
    count_query = select(func.count(SP500Constituent.code))
    for w in base_where:
        count_query = count_query.where(w)

    cache_key = f"sp500|sector={sector}|is_active={is_active}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    # Data query with LEFT JOIN to assets for enrichment
    data_query = select(
        SP500Constituent.code.label("ticker"),
        SP500Constituent.name,
        SP500Constituent.sector,
        SP500Constituent.industry,
        SP500Constituent.weight,
        SP500Constituent.is_active,
        Asset.isin.label("isin"),
        Asset.gic_sector,
        Asset.description,
        Asset.country_name.label("country")
    ).outerjoin(
        Asset, SP500Constituent.code == Asset.code
    )

    for w in base_where:
        data_query = data_query.where(w)

    data_query = data_query.order_by(SP500Constituent.code.asc())
    offset = (page - 1) * per_page
    data_query = data_query.offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.all()

    items = [
        SP500ConstituentResponse(
            ticker=row.ticker,
            name=row.name,
            sector=row.sector,
            industry=row.industry,
            weight=row.weight,
            is_active=row.is_active,
            isin=row.isin,
            gic_sector=row.gic_sector,
            description=row.description,
            country=row.country
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return SP500ListResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@_retired("/sp500/latest/", methods=["GET"], response_model=SP500LatestResponse)
async def get_sp500_latest(
    tickers: Optional[str] = Query(None, description="Comma-separated S&P 500 tickers (e.g., AAPL,MSFT,GOOGL). If omitted, returns latest for all constituents."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Returns the latest OHLCV record for S&P 500 constituents that have
    price data in ohlcv_data. Enriched with name, sector, industry, and weight
    from the sp500_constituents table.

    Optionally filter by specific tickers using the `tickers` query parameter.
    Ticker alias resolution is applied automatically (e.g. FISV→FI, MRSH→MMC).
    """
    ticker_list = parse_comma_separated(tickers)

    # Build the WHERE clause for filtering by specific tickers
    ticker_filter = ""
    if ticker_list:
        ticker_values = ", ".join(f"'{t}'" for t in ticker_list)
        ticker_filter = f"AND s.code IN ({ticker_values})"

    # LATERAL join approach: ~23ms vs ~3.3s with GROUP BY/MAX subquery.
    # Each LATERAL does a single Index Scan Backward on
    # ohlcv_data_ticker_date_key to fetch the latest row per ticker.
    # COALESCE(ta.ohlcv_ticker, s.code) resolves ticker mismatches via
    # the ticker_aliases table (e.g. FISV→FI, MRSH→MMC).
    query = text(f"""
        WITH resolved_tickers AS (
            SELECT
                s.code AS sp500_ticker,
                COALESCE(ta.ohlcv_ticker, s.code) AS ohlcv_ticker,
                s.name,
                s.sector,
                s.industry,
                s.weight
            FROM sp500_constituents s
            LEFT JOIN ticker_aliases ta ON ta.sp500_ticker = s.code
            WHERE s.is_active = true
            {ticker_filter}
        )
        SELECT
            rt.sp500_ticker AS ticker,
            rt.name,
            rt.sector   AS sp_sector,
            rt.industry AS sp_industry,
            rt.weight,
            o.date,
            o.open,
            o.high,
            o.low,
            o.close,
            o.adjusted_close,
            o.volume,
            o.asset_isin
        FROM resolved_tickers rt
        CROSS JOIN LATERAL (
            SELECT date, open, high, low, close, adjusted_close, volume, asset_isin
            FROM ohlcv_data
            WHERE ticker = rt.ohlcv_ticker
            ORDER BY date DESC
            LIMIT 1
        ) o
        ORDER BY rt.weight DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        SP500LatestItem(
            ticker=row.ticker,
            name=row.name,
            sector=row.sp_sector,
            industry=row.sp_industry,
            weight=row.weight,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
            asset_isin=row.asset_isin
        )
        for row in rows
    ]

    return SP500LatestResponse(data=items, count=len(items))


@_retired("/sp500/history/", methods=["GET"], response_model=SP500HistoryResponse)
async def get_sp500_batch_history(
    tickers: Optional[str] = Query(None, description="Comma-separated S&P 500 tickers (e.g., AAPL,MSFT,GOOGL). If omitted, returns history for all active constituents."),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    sort_by: Optional[str] = Query("date", pattern="^(date|volume|close|open|high|low)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Returns paginated historical OHLCV data for S&P 500 constituents.
    Verifies all requested tickers are active S&P 500 members and resolves
    ticker aliases automatically (e.g. FISV→FI, MRSH→MMC).

    If `tickers` is omitted, returns history for all active S&P 500 constituents.
    Results are enriched with name, sector, industry, and weight from
    sp500_constituents.
    """
    ticker_list = parse_comma_separated(tickers)

    # Build date filter clauses for the raw SQL
    date_filters = []
    if start_date:
        date_filters.append(f"o.date >= '{start_date}'")
    if end_date:
        date_filters.append(f"o.date <= '{end_date}'")
    if year:
        date_filters.append(f"EXTRACT(year FROM o.date) = {year}")
    if month:
        date_filters.append(f"EXTRACT(month FROM o.date) = {month}")

    date_where = ""
    if date_filters:
        date_where = "AND " + " AND ".join(date_filters)

    # Map sort_by to the SQL column name
    sort_col_map = {
        "date": "o.date", "volume": "o.volume", "close": "o.close",
        "open": "o.open", "high": "o.high", "low": "o.low"
    }
    sort_col = sort_col_map.get(sort_by or "date", "o.date")
    sort_dir = "DESC" if sort_order == "desc" else "ASC"

    if ticker_list:
        # Specific tickers: verify all are active S&P 500 constituents
        check_query = select(SP500Constituent.code).where(
            and_(
                SP500Constituent.code.in_(ticker_list),
                SP500Constituent.is_active == True
            )
        )
        check_result = await db.execute(check_query)
        valid_tickers = {row[0] for row in check_result.all()}

        invalid_tickers = [t for t in ticker_list if t not in valid_tickers]
        if invalid_tickers:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker(s) not active S&P 500 constituents: {', '.join(invalid_tickers)}"
            )

        # Resolve ticker aliases: build VALUES list with (sp500_ticker, ohlcv_ticker)
        alias_query = select(
            TickerAlias.sp500_ticker, TickerAlias.ohlcv_ticker
        ).where(TickerAlias.sp500_ticker.in_(ticker_list))
        alias_result = await db.execute(alias_query)
        alias_map = {row[0]: row[1] for row in alias_result.all()}

        # Build resolved ticker pairs: (sp500_ticker, ohlcv_ticker)
        resolved_pairs = []
        for t in ticker_list:
            ohlcv_ticker = alias_map.get(t, t)
            resolved_pairs.append((t, ohlcv_ticker))

        ticker_values = ", ".join(f"('{sp}', '{oh}')" for sp, oh in resolved_pairs)

        # Count query — specific tickers with VALUES list
        count_query = text(f"""
            WITH resolved_tickers AS (
                SELECT v.sp500_ticker, v.ohlcv_ticker
                FROM (VALUES {ticker_values}) AS v(sp500_ticker, ohlcv_ticker)
            ),
            sp500_meta AS (
                SELECT code, name, sector, industry, weight
                FROM sp500_constituents
                WHERE code IN ({', '.join(f"'{t}'" for t in ticker_list)}) AND is_active = true
            )
            SELECT count(*)
            FROM resolved_tickers rt
            JOIN sp500_meta sm ON sm.code = rt.sp500_ticker
            JOIN ohlcv_data o ON o.ticker = rt.ohlcv_ticker
            WHERE 1=1 {date_where}
        """)

        cache_key = f"sp500_hist_t|tickers={ticker_list}|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        # Data query with pagination — specific tickers
        offset = (page - 1) * per_page

        data_query = text(f"""
            WITH resolved_tickers AS (
                SELECT v.sp500_ticker, v.ohlcv_ticker
                FROM (VALUES {ticker_values}) AS v(sp500_ticker, ohlcv_ticker)
            ),
            sp500_meta AS (
                SELECT code, name, sector, industry, weight
                FROM sp500_constituents
                WHERE code IN ({', '.join(f"'{t}'" for t in ticker_list)}) AND is_active = true
            )
            SELECT
                rt.sp500_ticker AS ticker,
                sm.name,
                sm.sector   AS sp_sector,
                sm.industry AS sp_industry,
                sm.weight,
                o.date,
                o.open,
                o.high,
                o.low,
                o.close,
                o.adjusted_close,
                o.volume,
                o.asset_isin
            FROM resolved_tickers rt
            JOIN sp500_meta sm ON sm.code = rt.sp500_ticker
            JOIN ohlcv_data o ON o.ticker = rt.ohlcv_ticker
            WHERE 1=1 {date_where}
            ORDER BY {sort_col} {sort_dir}, rt.sp500_ticker ASC
            LIMIT {per_page} OFFSET {offset}
        """)
    else:
        # All active S&P 500 constituents: use sp500_constituents as driving row source
        # with LATERAL join for efficient per-ticker lookups (mirrors /sp500/latest/ pattern).
        # COALESCE(ta.ohlcv_ticker, s.code) resolves ticker aliases automatically.
        count_query = text(f"""
            WITH resolved_tickers AS (
                SELECT
                    s.code AS sp500_ticker,
                    COALESCE(ta.ohlcv_ticker, s.code) AS ohlcv_ticker
                FROM sp500_constituents s
                LEFT JOIN ticker_aliases ta ON ta.sp500_ticker = s.code
                WHERE s.is_active = true
            )
            SELECT count(*)
            FROM resolved_tickers rt
            JOIN ohlcv_data o ON o.ticker = rt.ohlcv_ticker
            WHERE 1=1 {date_where}
        """)

        cache_key = f"sp500_hist_all|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        # Data query with pagination — all constituents
        offset = (page - 1) * per_page

        data_query = text(f"""
            WITH resolved_tickers AS (
                SELECT
                    s.code AS sp500_ticker,
                    COALESCE(ta.ohlcv_ticker, s.code) AS ohlcv_ticker
                FROM sp500_constituents s
                LEFT JOIN ticker_aliases ta ON ta.sp500_ticker = s.code
                WHERE s.is_active = true
            )
            SELECT
                rt.sp500_ticker AS ticker,
                sm.name,
                sm.sector   AS sp_sector,
                sm.industry AS sp_industry,
                sm.weight,
                o.date,
                o.open,
                o.high,
                o.low,
                o.close,
                o.adjusted_close,
                o.volume,
                o.asset_isin
            FROM resolved_tickers rt
            JOIN sp500_constituents sm ON sm.code = rt.sp500_ticker
            JOIN ohlcv_data o ON o.ticker = rt.ohlcv_ticker
            WHERE 1=1 {date_where}
            ORDER BY {sort_col} {sort_dir}, rt.sp500_ticker ASC
            LIMIT {per_page} OFFSET {offset}
        """)

    result = await db.execute(data_query)
    rows = result.fetchall()

    items = [
        SP500HistoryItem(
            ticker=row.ticker,
            name=row.name,
            sector=row.sp_sector,
            industry=row.sp_industry,
            weight=row.weight,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
            asset_isin=row.asset_isin
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return SP500HistoryResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


# ── Ticker Alias Endpoints ───────────────────────────────────────────────────

@_retired("/aliases/", methods=["GET"], response_model=TickerAliasListResponse)
async def list_ticker_aliases(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    List all ticker aliases. These map S&P 500 tickers to their OHLCV data
    equivalents when the ticker symbols differ (e.g. FISV→FI, MRSH→MMC).
    """
    count_query = select(func.count(TickerAlias.sp500_ticker))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = select(TickerAlias).order_by(TickerAlias.sp500_ticker.asc())
    result = await db.execute(query)
    aliases = result.scalars().all()

    return TickerAliasListResponse(data=aliases, total=total)  # type: ignore[arg-type]


@_retired("/aliases/{sp500_ticker}", methods=["GET"], response_model=TickerAliasResponse)
async def get_ticker_alias(
    sp500_ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get a single ticker alias by its S&P 500 ticker."""
    query = select(TickerAlias).where(TickerAlias.sp500_ticker == sp500_ticker.upper())
    result = await db.execute(query)
    alias = result.scalar_one_or_none()

    if not alias:
        raise HTTPException(status_code=404, detail=f"No alias found for ticker: {sp500_ticker}")

    return alias


@_retired("/aliases/", methods=["POST"], response_model=TickerAliasResponse, status_code=201)
async def create_ticker_alias(
    alias: TickerAliasCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Create a new ticker alias mapping."""
    db_alias = TickerAlias(**alias.model_dump())
    db.add(db_alias)
    try:
        await db.commit()
        await db.refresh(db_alias)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_alias


@_retired("/aliases/{sp500_ticker}", methods=["PUT"], response_model=TickerAliasResponse)
async def update_ticker_alias(
    sp500_ticker: str,
    alias: TickerAliasUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Update the OHLCV ticker for an existing alias."""
    query = select(TickerAlias).where(TickerAlias.sp500_ticker == sp500_ticker.upper())
    result = await db.execute(query)
    db_alias = result.scalar_one_or_none()

    if not db_alias:
        raise HTTPException(status_code=404, detail=f"No alias found for ticker: {sp500_ticker}")

    db_alias.ohlcv_ticker = alias.ohlcv_ticker  # type: ignore[assignment]
    try:
        await db.commit()
        await db.refresh(db_alias)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return db_alias


@_retired("/aliases/{sp500_ticker}", methods=["DELETE"], status_code=204)
async def delete_ticker_alias(
    sp500_ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Delete a ticker alias."""
    query = select(TickerAlias).where(TickerAlias.sp500_ticker == sp500_ticker.upper())
    result = await db.execute(query)
    db_alias = result.scalar_one_or_none()

    if not db_alias:
        raise HTTPException(status_code=404, detail=f"No alias found for ticker: {sp500_ticker}")

    await db.delete(db_alias)
    await db.commit()
    return None


# ── ETF / Index Endpoints ─────────────────────────────────────────────────────

async def _get_etf_index_ohlcv(
    asset_type: str,
    ticker: Optional[str],
    tickers: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    year: Optional[int],
    month: Optional[int],
    open_min: Optional[Decimal],
    open_max: Optional[Decimal],
    close_min: Optional[Decimal],
    close_max: Optional[Decimal],
    volume_min: Optional[int],
    volume_max: Optional[int],
    sort_by: Optional[str],
    sort_order: Optional[str],
    page: int,
    per_page: int,
    db: AsyncSession,
):
    """
    Shared logic for GET /etf/ and GET /index/.
    Filters ohlcv_data_etf_index by joining to etf_index_assets where type = asset_type.
    """
    ticker_list = parse_comma_separated(tickers) or ([ticker.upper()] if ticker else None)

    # Build WHERE clauses
    conditions = [EtfIndexAsset.type == asset_type]
    count_conditions = [EtfIndexAsset.type == asset_type]

    if ticker_list:
        if len(ticker_list) == 1:
            conditions.append(EtfIndexOhlcvData.ticker == ticker_list[0])
            count_conditions.append(EtfIndexOhlcvData.ticker == ticker_list[0])
        else:
            conditions.append(EtfIndexOhlcvData.ticker.in_(ticker_list))
            count_conditions.append(EtfIndexOhlcvData.ticker.in_(ticker_list))

    if start_date:
        conditions.append(EtfIndexOhlcvData.date >= start_date)
        count_conditions.append(EtfIndexOhlcvData.date >= start_date)
    if end_date:
        conditions.append(EtfIndexOhlcvData.date <= end_date)
        count_conditions.append(EtfIndexOhlcvData.date <= end_date)
    if year:
        conditions.append(func.extract("year", EtfIndexOhlcvData.date) == year)
        count_conditions.append(func.extract("year", EtfIndexOhlcvData.date) == year)
    if month:
        conditions.append(func.extract("month", EtfIndexOhlcvData.date) == month)
        count_conditions.append(func.extract("month", EtfIndexOhlcvData.date) == month)
    if open_min is not None:
        conditions.append(EtfIndexOhlcvData.open >= open_min)
        count_conditions.append(EtfIndexOhlcvData.open >= open_min)
    if open_max is not None:
        conditions.append(EtfIndexOhlcvData.open <= open_max)
        count_conditions.append(EtfIndexOhlcvData.open <= open_max)
    if close_min is not None:
        conditions.append(EtfIndexOhlcvData.close >= close_min)
        count_conditions.append(EtfIndexOhlcvData.close >= close_min)
    if close_max is not None:
        conditions.append(EtfIndexOhlcvData.close <= close_max)
        count_conditions.append(EtfIndexOhlcvData.close <= close_max)
    if volume_min is not None:
        conditions.append(EtfIndexOhlcvData.volume >= volume_min)
        count_conditions.append(EtfIndexOhlcvData.volume >= volume_min)
    if volume_max is not None:
        conditions.append(EtfIndexOhlcvData.volume <= volume_max)
        count_conditions.append(EtfIndexOhlcvData.volume <= volume_max)

    # Count query — only count OHLCV rows that have a matching asset of the right type
    count_query = select(func.count(EtfIndexOhlcvData.id)).join(
        EtfIndexAsset, EtfIndexOhlcvData.ticker == EtfIndexAsset.code
    )
    for c in count_conditions:
        count_query = count_query.where(c)

    cache_key = f"{asset_type}|tickers={ticker_list}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    # Data query
    sort_column = getattr(EtfIndexOhlcvData, sort_by or "date")
    offset = (page - 1) * per_page

    data_query = select(EtfIndexOhlcvData).join(
        EtfIndexAsset, EtfIndexOhlcvData.ticker == EtfIndexAsset.code
    )
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_column.desc() if sort_order == "desc" else sort_column.asc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return EtfIndexPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/etf/", methods=["GET"], response_model=EtfIndexPaginatedResponse)
async def get_etf_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single ETF ticker (e.g., SPY)"),
    tickers: Optional[str] = Query(None, description="Comma-separated ETF tickers (e.g., SPY,QQQ,IWM)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for ETFs.
    Only returns data for tickers that exist in etf_index_assets with type='etf'.
    """
    return await _get_etf_index_ohlcv(
        asset_type="etf", ticker=ticker, tickers=tickers,
        start_date=start_date, end_date=end_date, year=year, month=month,
        open_min=open_min, open_max=open_max,
        close_min=close_min, close_max=close_max,
        volume_min=volume_min, volume_max=volume_max,
        sort_by=sort_by, sort_order=sort_order,
        page=page, per_page=per_page, db=db,
    )


@_retired("/index/", methods=["GET"], response_model=EtfIndexPaginatedResponse)
async def get_index_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single index ticker (e.g., GSPC)"),
    tickers: Optional[str] = Query(None, description="Comma-separated index tickers (e.g., GSPC,DJI,IXIC)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for indices.
    Only returns data for tickers that exist in etf_index_assets with type='index'.
    """
    return await _get_etf_index_ohlcv(
        asset_type="index", ticker=ticker, tickers=tickers,
        start_date=start_date, end_date=end_date, year=year, month=month,
        open_min=open_min, open_max=open_max,
        close_min=close_min, close_max=close_max,
        volume_min=volume_min, volume_max=volume_max,
        sort_by=sort_by, sort_order=sort_order,
        page=page, per_page=per_page, db=db,
    )


async def _get_etf_index_latest_batch(
    asset_type: str,
    tickers: Optional[str],
    db: AsyncSession,
):
    """
    Shared logic for GET /etf/latest/ and GET /index/latest/.
    Uses LATERAL join driven by etf_index_assets (filtered by type) for efficient
    per-ticker latest-row lookups. Enriched with name, exchange, isin, currency.
    """
    ticker_list = parse_comma_separated(tickers)

    if ticker_list:
        # Specific tickers: VALUES list as driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.isin, a.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN etf_index_assets a ON a.code = t.ticker AND a.type = :asset_type
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_etf_index
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            ORDER BY t.ticker ASC
        """)
    else:
        # All tickers of the given type: etf_index_assets as driving row source
        query = text("""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.isin, a.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM etf_index_assets a
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_etf_index
                WHERE ticker = a.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE a.type = :asset_type
            ORDER BY a.code ASC
        """)

    result = await db.execute(query, {"asset_type": asset_type})
    rows = result.fetchall()

    items = [
        EtfIndexLatestItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            isin=row.isin,
            currency=row.currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return EtfIndexLatestResponse(data=items, count=len(items))


@_retired("/etf/latest_close/", methods=["GET"], response_model=EtfIndexLatestResponse)
async def get_etf_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated ETF tickers (e.g., SPY,QQQ,IWM). If omitted, returns latest for all ETFs."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for ETFs.
    Enriched with name, exchange, isin, and currency from etf_index_assets.
    Optionally filter by specific tickers.
    """
    return await _get_etf_index_latest_batch(asset_type="etf", tickers=tickers, db=db)


@_retired("/etf/latest_close/{ticker}", methods=["GET"], response_model=EtfIndexLatestItem)
async def get_etf_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single ETF, enriched with asset metadata.
    """
    ticker = ticker.upper()

    # Verify the ticker is an ETF
    asset_query = select(EtfIndexAsset).where(
        and_(EtfIndexAsset.code == ticker, EtfIndexAsset.type == "etf")
    )
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No ETF found with ticker: {ticker}")

    # Get latest OHLCV
    ohlcv_query = select(EtfIndexOhlcvData).where(
        EtfIndexOhlcvData.ticker == ticker
    ).order_by(EtfIndexOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for ETF ticker: {ticker}. "
                   f"The asset exists in etf_index_assets but has no price data in ohlcv_data_etf_index."
        )

    return EtfIndexLatestItem(
        ticker=ticker,
        name=asset.name,          # type: ignore[arg-type]
        exchange=asset.exchange,  # type: ignore[arg-type]
        type=asset.type,          # type: ignore[arg-type]
        isin=asset.isin,          # type: ignore[arg-type]
        currency=asset.currency,  # type: ignore[arg-type]
        date=ohlcv.date,          # type: ignore[arg-type]
        open=ohlcv.open,          # type: ignore[arg-type]
        high=ohlcv.high,          # type: ignore[arg-type]
        low=ohlcv.low,            # type: ignore[arg-type]
        close=ohlcv.close,        # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,      # type: ignore[arg-type]
    )


@_retired("/etf/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_etf_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated ETF tickers (e.g., SPY,QQQ,IWM). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified ETF tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(EtfIndexAsset).where(
        and_(EtfIndexAsset.code.in_(ticker_list), EtfIndexAsset.type == "etf")
    )
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No ETF found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))



@_retired("/index/latest_close/", methods=["GET"], response_model=EtfIndexLatestResponse)
async def get_index_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated index tickers (e.g., GSPC,DJI,IXIC). If omitted, returns latest for all indices."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for indices.
    Enriched with name, exchange, isin, and currency from etf_index_assets.
    Optionally filter by specific tickers.
    """
    return await _get_etf_index_latest_batch(asset_type="index", tickers=tickers, db=db)


@_retired("/index/latest_close/{ticker}", methods=["GET"], response_model=EtfIndexLatestItem)
async def get_index_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single index, enriched with asset metadata.
    """
    ticker = ticker.upper()

    # Verify the ticker is an index
    asset_query = select(EtfIndexAsset).where(
        and_(EtfIndexAsset.code == ticker, EtfIndexAsset.type == "index")
    )
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No index found with ticker: {ticker}")

    # Get latest OHLCV
    ohlcv_query = select(EtfIndexOhlcvData).where(
        EtfIndexOhlcvData.ticker == ticker
    ).order_by(EtfIndexOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for index ticker: {ticker}. "
                   f"The asset exists in etf_index_assets but has no price data in ohlcv_data_etf_index."
        )

    return EtfIndexLatestItem(
        ticker=ticker,
        name=asset.name,          # type: ignore[arg-type]
        exchange=asset.exchange,  # type: ignore[arg-type]
        type=asset.type,          # type: ignore[arg-type]
        isin=asset.isin,          # type: ignore[arg-type]
        currency=asset.currency,  # type: ignore[arg-type]
        date=ohlcv.date,          # type: ignore[arg-type]
        open=ohlcv.open,          # type: ignore[arg-type]
        high=ohlcv.high,          # type: ignore[arg-type]
        low=ohlcv.low,            # type: ignore[arg-type]
        close=ohlcv.close,        # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,      # type: ignore[arg-type]
    )


@_retired("/index/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_index_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated index tickers (e.g., GSPC,DJI,IXIC). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified index tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(EtfIndexAsset).where(
        and_(EtfIndexAsset.code.in_(ticker_list), EtfIndexAsset.type == "index")
    )
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No index found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))



# ── Government Bond Endpoints ────────────────────────────────────────────────

@_retired("/gov-bond/", methods=["GET"], response_model=GovBondPaginatedResponse)
async def get_gov_bond_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single government bond ticker (e.g., UK10Y)"),
    tickers: Optional[str] = Query(None, description="Comma-separated government bond tickers (e.g., UK10Y,US10Y,DE10Y)"),
    country: Optional[str] = Query(None, description="Filter by single country code (e.g., US, DE, JP)"),
    countries: Optional[str] = Query(None, description="Comma-separated country codes (e.g., US,DE,JP)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for government bonds.
    Only returns data for tickers that exist in gov_bond_assets.
    Supports filtering by ticker(s) and country/countries.
    """
    ticker_list = parse_comma_separated(tickers) or ([ticker.upper()] if ticker else None)
    country_list = parse_comma_separated(countries) or ([country.upper()] if country else None)

    # Build WHERE clauses
    conditions = []
    count_conditions = []

    if ticker_list:
        if len(ticker_list) == 1:
            conditions.append(GovBondOhlcvData.ticker == ticker_list[0])
            count_conditions.append(GovBondOhlcvData.ticker == ticker_list[0])
        else:
            conditions.append(GovBondOhlcvData.ticker.in_(ticker_list))
            count_conditions.append(GovBondOhlcvData.ticker.in_(ticker_list))

    if country_list:
        if len(country_list) == 1:
            conditions.append(GovBondAsset.country == country_list[0])
            count_conditions.append(GovBondAsset.country == country_list[0])
        else:
            conditions.append(GovBondAsset.country.in_(country_list))
            count_conditions.append(GovBondAsset.country.in_(country_list))

    if start_date:
        conditions.append(GovBondOhlcvData.date >= start_date)
        count_conditions.append(GovBondOhlcvData.date >= start_date)
    if end_date:
        conditions.append(GovBondOhlcvData.date <= end_date)
        count_conditions.append(GovBondOhlcvData.date <= end_date)
    if year:
        conditions.append(func.extract("year", GovBondOhlcvData.date) == year)
        count_conditions.append(func.extract("year", GovBondOhlcvData.date) == year)
    if month:
        conditions.append(func.extract("month", GovBondOhlcvData.date) == month)
        count_conditions.append(func.extract("month", GovBondOhlcvData.date) == month)
    if open_min is not None:
        conditions.append(GovBondOhlcvData.open >= open_min)
        count_conditions.append(GovBondOhlcvData.open >= open_min)
    if open_max is not None:
        conditions.append(GovBondOhlcvData.open <= open_max)
        count_conditions.append(GovBondOhlcvData.open <= open_max)
    if close_min is not None:
        conditions.append(GovBondOhlcvData.close >= close_min)
        count_conditions.append(GovBondOhlcvData.close >= close_min)
    if close_max is not None:
        conditions.append(GovBondOhlcvData.close <= close_max)
        count_conditions.append(GovBondOhlcvData.close <= close_max)
    if volume_min is not None:
        conditions.append(GovBondOhlcvData.volume >= volume_min)
        count_conditions.append(GovBondOhlcvData.volume >= volume_min)
    if volume_max is not None:
        conditions.append(GovBondOhlcvData.volume <= volume_max)
        count_conditions.append(GovBondOhlcvData.volume <= volume_max)

    # Count query — only count OHLCV rows that have a matching asset
    count_query = select(func.count(GovBondOhlcvData.id)).join(
        GovBondAsset, GovBondOhlcvData.ticker == GovBondAsset.code
    )
    for c in count_conditions:
        count_query = count_query.where(c)

    cache_key = f"gov_bond|tickers={ticker_list}|country={country}|countries={country_list}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    # Data query
    sort_column = getattr(GovBondOhlcvData, sort_by or "date")
    offset = (page - 1) * per_page

    data_query = select(GovBondOhlcvData).join(
        GovBondAsset, GovBondOhlcvData.ticker == GovBondAsset.code
    )
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_column.desc() if sort_order == "desc" else sort_column.asc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return GovBondPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/gov-bond/latest_close/", methods=["GET"], response_model=GovBondLatestResponse)
async def get_gov_bond_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated government bond tickers (e.g., UK10Y,US10Y,DE10Y). If omitted, returns latest for all government bonds."),
    country: Optional[str] = Query(None, description="Filter by single country code (e.g., US, DE, JP)"),
    countries: Optional[str] = Query(None, description="Comma-separated country codes (e.g., US,DE,JP)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for government bonds.
    Uses LATERAL join driven by gov_bond_assets for efficient per-ticker
    latest-row lookups. Enriched with name, exchange, type, currency, country.
    Optionally filter by specific tickers and/or country/countries.
    """
    ticker_list = parse_comma_separated(tickers)
    country_list = parse_comma_separated(countries) or ([country.upper()] if country else None)

    # Build country filter SQL fragment
    country_where = ""
    if country_list:
        country_values = ", ".join(f"'{c}'" for c in country_list)
        country_where = f"AND a.country IN ({country_values})"

    if ticker_list:
        # Specific tickers: VALUES list as driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.currency, a.country,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN gov_bond_assets a ON a.code = t.ticker
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_gov_bonds
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {country_where}
            ORDER BY t.ticker ASC
        """)
    else:
        # All government bonds: gov_bond_assets as driving row source
        query = text(f"""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.currency, a.country,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM gov_bond_assets a
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_gov_bonds
                WHERE ticker = a.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {country_where}
            ORDER BY a.code ASC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        GovBondLatestItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            currency=row.currency,
            country=row.country,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return GovBondLatestResponse(data=items, count=len(items))


@_retired("/gov-bond/latest_close/{ticker}", methods=["GET"], response_model=GovBondLatestItem)
async def get_gov_bond_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single government bond,
    enriched with asset metadata (name, exchange, type, currency, country).
    """
    ticker = ticker.upper()

    # Verify the ticker is a government bond
    asset_query = select(GovBondAsset).where(GovBondAsset.code == ticker)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No government bond found with ticker: {ticker}")

    # Get latest OHLCV
    ohlcv_query = select(GovBondOhlcvData).where(
        GovBondOhlcvData.ticker == ticker
    ).order_by(GovBondOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for government bond ticker: {ticker}. "
                   f"The asset exists in gov_bond_assets but has no price data in ohlcv_data_gov_bonds."
        )

    return GovBondLatestItem(
        ticker=ticker,
        name=asset.name,          # type: ignore[arg-type]
        exchange=asset.exchange,  # type: ignore[arg-type]
        type=asset.type,          # type: ignore[arg-type]
        currency=asset.currency,  # type: ignore[arg-type]
        country=asset.country,    # type: ignore[arg-type]
        date=ohlcv.date,          # type: ignore[arg-type]
        open=ohlcv.open,          # type: ignore[arg-type]
        high=ohlcv.high,          # type: ignore[arg-type]
        low=ohlcv.low,            # type: ignore[arg-type]
        close=ohlcv.close,        # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,      # type: ignore[arg-type]
    )


@_retired("/gov-bond/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_gov_bond_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated government bond tickers (e.g., UK10Y,US10Y,DE10Y). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified government bond tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(GovBondAsset).where(GovBondAsset.code.in_(ticker_list))
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No government bond found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))




# ── Foreign Exchange (FX) Endpoints ──────────────────────────────────────────

@_retired("/fx/", methods=["GET"], response_model=FxPaginatedResponse)
async def get_fx_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single FX ticker (e.g., EURUSD)"),
    tickers: Optional[str] = Query(None, description="Comma-separated FX tickers (e.g., EURUSD,GBPUSD,USDJPY)"),
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., EUR, GBP)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, JPY)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for foreign exchange pairs.
    Only returns data for tickers that exist in fx_assets.
    Supports filtering by ticker(s), base_currency, and quote_currency.
    """
    ticker_list = parse_comma_separated(tickers) or ([ticker.upper()] if ticker else None)

    # Build WHERE clauses
    conditions = []
    count_conditions = []

    if ticker_list:
        if len(ticker_list) == 1:
            conditions.append(FxOhlcvData.ticker == ticker_list[0])
            count_conditions.append(FxOhlcvData.ticker == ticker_list[0])
        else:
            conditions.append(FxOhlcvData.ticker.in_(ticker_list))
            count_conditions.append(FxOhlcvData.ticker.in_(ticker_list))

    if base_currency:
        conditions.append(FxAsset.base_currency == base_currency.upper())
        count_conditions.append(FxAsset.base_currency == base_currency.upper())

    if quote_currency:
        conditions.append(FxAsset.quote_currency == quote_currency.upper())
        count_conditions.append(FxAsset.quote_currency == quote_currency.upper())

    if start_date:
        conditions.append(FxOhlcvData.date >= start_date)
        count_conditions.append(FxOhlcvData.date >= start_date)
    if end_date:
        conditions.append(FxOhlcvData.date <= end_date)
        count_conditions.append(FxOhlcvData.date <= end_date)
    if year:
        conditions.append(func.extract("year", FxOhlcvData.date) == year)
        count_conditions.append(func.extract("year", FxOhlcvData.date) == year)
    if month:
        conditions.append(func.extract("month", FxOhlcvData.date) == month)
        count_conditions.append(func.extract("month", FxOhlcvData.date) == month)
    if open_min is not None:
        conditions.append(FxOhlcvData.open >= open_min)
        count_conditions.append(FxOhlcvData.open >= open_min)
    if open_max is not None:
        conditions.append(FxOhlcvData.open <= open_max)
        count_conditions.append(FxOhlcvData.open <= open_max)
    if close_min is not None:
        conditions.append(FxOhlcvData.close >= close_min)
        count_conditions.append(FxOhlcvData.close >= close_min)
    if close_max is not None:
        conditions.append(FxOhlcvData.close <= close_max)
        count_conditions.append(FxOhlcvData.close <= close_max)
    if volume_min is not None:
        conditions.append(FxOhlcvData.volume >= volume_min)
        count_conditions.append(FxOhlcvData.volume >= volume_min)
    if volume_max is not None:
        conditions.append(FxOhlcvData.volume <= volume_max)
        count_conditions.append(FxOhlcvData.volume <= volume_max)

    # Count query — only count OHLCV rows that have a matching asset
    count_query = select(func.count(FxOhlcvData.id)).join(
        FxAsset, FxOhlcvData.ticker == FxAsset.code
    )
    for c in count_conditions:
        count_query = count_query.where(c)

    cache_key = f"fx|tickers={ticker_list}|base={base_currency}|quote={quote_currency}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    # Data query
    sort_column = getattr(FxOhlcvData, sort_by or "date")
    offset = (page - 1) * per_page

    data_query = select(FxOhlcvData).join(
        FxAsset, FxOhlcvData.ticker == FxAsset.code
    )
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_column.desc() if sort_order == "desc" else sort_column.asc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return FxPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/fx/latest_close/", methods=["GET"], response_model=FxLatestResponse)
async def get_fx_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated FX tickers (e.g., EURUSD,GBPUSD,USDJPY). If omitted, returns latest for all FX pairs."),
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., EUR, GBP)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, JPY)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for foreign exchange pairs.
    Uses LATERAL join driven by fx_assets for efficient per-ticker
    latest-row lookups. Enriched with name, exchange, type, currency,
    base_currency, quote_currency.
    Optionally filter by specific tickers and/or base_currency/quote_currency.
    """
    ticker_list = parse_comma_separated(tickers)

    # Build currency filter SQL fragments
    base_where = ""
    quote_where = ""
    if base_currency:
        base_where = f"AND a.base_currency = '{base_currency.upper()}'"
    if quote_currency:
        quote_where = f"AND a.quote_currency = '{quote_currency.upper()}'"

    if ticker_list:
        # Specific tickers: VALUES list as driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN fx_assets a ON a.code = t.ticker
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_fx
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {base_where} {quote_where}
            ORDER BY t.ticker ASC
        """)
    else:
        # All FX pairs: fx_assets as driving row source
        query = text(f"""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM fx_assets a
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_fx
                WHERE ticker = a.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {base_where} {quote_where}
            ORDER BY a.code ASC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        FxLatestItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            currency=row.currency,
            base_currency=row.base_currency,
            quote_currency=row.quote_currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return FxLatestResponse(data=items, count=len(items))


@_retired("/fx/latest_close/{ticker}", methods=["GET"], response_model=FxLatestItem)
async def get_fx_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single foreign exchange pair,
    enriched with asset metadata (name, exchange, type, currency,
    base_currency, quote_currency).
    """
    ticker = ticker.upper()

    # Verify the ticker is an FX asset
    asset_query = select(FxAsset).where(FxAsset.code == ticker)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No FX pair found with ticker: {ticker}")

    # Get latest OHLCV
    ohlcv_query = select(FxOhlcvData).where(
        FxOhlcvData.ticker == ticker
    ).order_by(FxOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for FX ticker: {ticker}. "
                   f"The asset exists in fx_assets but has no price data in ohlcv_data_fx."
        )

    return FxLatestItem(
        ticker=ticker,
        name=asset.name,                    # type: ignore[arg-type]
        exchange=asset.exchange,            # type: ignore[arg-type]
        type=asset.type,                    # type: ignore[arg-type]
        currency=asset.currency,            # type: ignore[arg-type]
        base_currency=asset.base_currency,  # type: ignore[arg-type]
        quote_currency=asset.quote_currency,  # type: ignore[arg-type]
        date=ohlcv.date,                    # type: ignore[arg-type]
        open=ohlcv.open,                    # type: ignore[arg-type]
        high=ohlcv.high,                    # type: ignore[arg-type]
        low=ohlcv.low,                      # type: ignore[arg-type]
        close=ohlcv.close,                  # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,                # type: ignore[arg-type]
    )


@_retired("/fx/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_fx_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated FX tickers (e.g., EURUSD,GBPUSD,USDJPY). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified FX tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(FxAsset).where(FxAsset.code.in_(ticker_list))
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No FX pair found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))



@_retired("/fx/assets/", methods=["GET"], response_model=FxAssetResponse)
async def get_fx_assets(
    base_currency: Optional[str] = Query(None, description="Filter by base currency (e.g., EUR, GBP)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency (e.g., USD, JPY)"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = []

    if base_currency:
        conditions.append(FxAsset.base_currency == base_currency.upper())
    if quote_currency:
        conditions.append(FxAsset.quote_currency == quote_currency.upper())
    if type:
        conditions.append(FxAsset.type == type)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            (FxAsset.code.ilike(pattern)) | (FxAsset.name.ilike(pattern))
        )

    count_query = select(func.count(FxAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"fx_assets|base={base_currency}|quote={quote_currency}|type={type}|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(FxAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(FxAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        FxAssetItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            base_currency=row.base_currency,        # type: ignore[arg-type]
            quote_currency=row.quote_currency,       # type: ignore[arg-type]
            type=row.type,                          # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return FxAssetResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# ── Crypto Endpoints ─────────────────────────────────────────────────────────

@_retired("/crypto/", methods=["GET"], response_model=CryptoPaginatedResponse)
async def get_crypto_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single crypto ticker (e.g., BTC-USD)"),
    tickers: Optional[str] = Query(None, description="Comma-separated crypto tickers (e.g., BTC-USD,ETH-USD,SOL-USD)"),
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., BTC, ETH)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, USDT)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for crypto assets.
    Only returns data for tickers that exist in crypto_assets.
    Supports filtering by ticker(s), base_currency, and quote_currency.
    """
    ticker_list = parse_comma_separated_preserve(tickers) or ([ticker] if ticker else None)

    conditions = []
    count_conditions = []

    if ticker_list:
        if len(ticker_list) == 1:
            conditions.append(CryptoOhlcvData.ticker == ticker_list[0])
            count_conditions.append(CryptoOhlcvData.ticker == ticker_list[0])
        else:
            conditions.append(CryptoOhlcvData.ticker.in_(ticker_list))
            count_conditions.append(CryptoOhlcvData.ticker.in_(ticker_list))

    if base_currency:
        conditions.append(CryptoAsset.base_currency == base_currency.upper())
        count_conditions.append(CryptoAsset.base_currency == base_currency.upper())

    if quote_currency:
        conditions.append(CryptoAsset.quote_currency == quote_currency.upper())
        count_conditions.append(CryptoAsset.quote_currency == quote_currency.upper())

    if start_date:
        conditions.append(CryptoOhlcvData.date >= start_date)
        count_conditions.append(CryptoOhlcvData.date >= start_date)
    if end_date:
        conditions.append(CryptoOhlcvData.date <= end_date)
        count_conditions.append(CryptoOhlcvData.date <= end_date)
    if year:
        conditions.append(func.extract("year", CryptoOhlcvData.date) == year)
        count_conditions.append(func.extract("year", CryptoOhlcvData.date) == year)
    if month:
        conditions.append(func.extract("month", CryptoOhlcvData.date) == month)
        count_conditions.append(func.extract("month", CryptoOhlcvData.date) == month)
    if open_min is not None:
        conditions.append(CryptoOhlcvData.open >= open_min)
        count_conditions.append(CryptoOhlcvData.open >= open_min)
    if open_max is not None:
        conditions.append(CryptoOhlcvData.open <= open_max)
        count_conditions.append(CryptoOhlcvData.open <= open_max)
    if close_min is not None:
        conditions.append(CryptoOhlcvData.close >= close_min)
        count_conditions.append(CryptoOhlcvData.close >= close_min)
    if close_max is not None:
        conditions.append(CryptoOhlcvData.close <= close_max)
        count_conditions.append(CryptoOhlcvData.close <= close_max)
    if volume_min is not None:
        conditions.append(CryptoOhlcvData.volume >= volume_min)
        count_conditions.append(CryptoOhlcvData.volume >= volume_min)
    if volume_max is not None:
        conditions.append(CryptoOhlcvData.volume <= volume_max)
        count_conditions.append(CryptoOhlcvData.volume <= volume_max)

    count_query = select(func.count(CryptoOhlcvData.id)).join(
        CryptoAsset, CryptoOhlcvData.ticker == CryptoAsset.code
    )
    for c in count_conditions:
        count_query = count_query.where(c)

    cache_key = f"crypto|tickers={ticker_list}|base={base_currency}|quote={quote_currency}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    sort_column = getattr(CryptoOhlcvData, sort_by or "date")
    offset = (page - 1) * per_page

    data_query = select(CryptoOhlcvData).join(
        CryptoAsset, CryptoOhlcvData.ticker == CryptoAsset.code
    )
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_column.desc() if sort_order == "desc" else sort_column.asc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return CryptoPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/crypto/latest_close/", methods=["GET"], response_model=CryptoLatestResponse)
async def get_crypto_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated crypto tickers (e.g., BTC-USD,ETH-USD,SOL-USD). If omitted, returns latest for all crypto assets."),
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., BTC, ETH)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, USDT)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for crypto assets.
    Uses LATERAL join driven by crypto_assets for efficient per-ticker
    latest-row lookups. Enriched with name, exchange, type, currency,
    base_currency, quote_currency.
    Optionally filter by specific tickers and/or base_currency/quote_currency.
    """
    ticker_list = parse_comma_separated_preserve(tickers)

    base_where = ""
    quote_where = ""
    if base_currency:
        base_where = f"AND a.base_currency = '{base_currency.upper()}'"
    if quote_currency:
        quote_where = f"AND a.quote_currency = '{quote_currency.upper()}'"

    if ticker_list:
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN crypto_assets a ON a.code = t.ticker
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_crypto
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {base_where} {quote_where}
            ORDER BY t.ticker ASC
        """)
    else:
        query = text(f"""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM crypto_assets a
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_crypto
                WHERE ticker = a.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {base_where} {quote_where}
            ORDER BY a.code ASC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        CryptoLatestItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            currency=row.currency,
            base_currency=row.base_currency,
            quote_currency=row.quote_currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return CryptoLatestResponse(data=items, count=len(items))


@_retired("/crypto/latest_close/{ticker}", methods=["GET"], response_model=CryptoLatestItem)
async def get_crypto_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single crypto asset,
    enriched with asset metadata (name, exchange, type, currency,
    base_currency, quote_currency).
    """
    asset_query = select(CryptoAsset).where(CryptoAsset.code == ticker)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No crypto asset found with ticker: {ticker}")

    ohlcv_query = select(CryptoOhlcvData).where(
        CryptoOhlcvData.ticker == ticker
    ).order_by(CryptoOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for crypto ticker: {ticker}. "
                   f"The asset exists in crypto_assets but has no price data in ohlcv_data_crypto."
        )

    return CryptoLatestItem(
        ticker=ticker,
        name=asset.name,                    # type: ignore[arg-type]
        exchange=asset.exchange,            # type: ignore[arg-type]
        type=asset.type,                    # type: ignore[arg-type]
        currency=asset.currency,            # type: ignore[arg-type]
        base_currency=asset.base_currency,  # type: ignore[arg-type]
        quote_currency=asset.quote_currency,  # type: ignore[arg-type]
        date=ohlcv.date,                    # type: ignore[arg-type]
        open=ohlcv.open,                    # type: ignore[arg-type]
        high=ohlcv.high,                    # type: ignore[arg-type]
        low=ohlcv.low,                      # type: ignore[arg-type]
        close=ohlcv.close,                  # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,                # type: ignore[arg-type]
    )


@_retired("/crypto/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_crypto_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated crypto tickers (e.g., BTC-USD,ETH-USD,SOL-USD). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified crypto tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated_preserve(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(CryptoAsset).where(CryptoAsset.code.in_(ticker_list))
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No crypto asset found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))




@_retired("/crypto/history/", methods=["GET"], response_model=CryptoHistoryPaginatedResponse)
async def get_crypto_history(
    tickers: Optional[str] = Query(None, description="Comma-separated crypto tickers (e.g., BTC-USD,ETH-USD). If omitted, returns history for all crypto assets."),
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., BTC, ETH)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, USDT)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    year: Optional[int] = Query(None, ge=1900, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    sort_by: Optional[str] = Query("date", pattern="^(date|volume|close|open|high|low)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns paginated historical OHLCV data for crypto assets.
    Enriched with name, exchange, type, currency, base_currency, quote_currency
    from crypto_assets.
    """
    ticker_list = parse_comma_separated_preserve(tickers)

    date_filters = []
    if start_date:
        date_filters.append(f"o.date >= '{start_date}'")
    if end_date:
        date_filters.append(f"o.date <= '{end_date}'")
    if year:
        date_filters.append(f"EXTRACT(year FROM o.date) = {year}")
    if month:
        date_filters.append(f"EXTRACT(month FROM o.date) = {month}")

    date_where = ""
    if date_filters:
        date_where = "AND " + " AND ".join(date_filters)

    base_where = ""
    quote_where = ""
    if base_currency:
        base_where = f"AND a.base_currency = '{base_currency.upper()}'"
    if quote_currency:
        quote_where = f"AND a.quote_currency = '{quote_currency.upper()}'"

    sort_col_map = {
        "date": "o.date", "volume": "o.volume", "close": "o.close",
        "open": "o.open", "high": "o.high", "low": "o.low"
    }
    sort_col = sort_col_map.get(sort_by or "date", "o.date")
    sort_dir = "DESC" if sort_order == "desc" else "ASC"

    if ticker_list:
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)

        count_query = text(f"""
            SELECT count(*)
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN crypto_assets a ON a.code = t.ticker
            JOIN ohlcv_data_crypto o ON o.ticker = t.ticker
            WHERE 1=1 {base_where} {quote_where} {date_where}
        """)

        cache_key = f"crypto_lc_t|tickers={ticker_list}|base={base_currency}|quote={quote_currency}|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        offset = (page - 1) * per_page

        data_query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN crypto_assets a ON a.code = t.ticker
            JOIN ohlcv_data_crypto o ON o.ticker = t.ticker
            WHERE 1=1 {base_where} {quote_where} {date_where}
            ORDER BY {sort_col} {sort_dir}, t.ticker ASC
            LIMIT {per_page} OFFSET {offset}
        """)
    else:
        count_query = text(f"""
            SELECT count(*)
            FROM crypto_assets a
            JOIN ohlcv_data_crypto o ON o.ticker = a.code
            WHERE 1=1 {base_where} {quote_where} {date_where}
        """)

        cache_key = f"crypto_lc_all|base={base_currency}|quote={quote_currency}|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        offset = (page - 1) * per_page

        data_query = text(f"""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.currency,
                   a.base_currency, a.quote_currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM crypto_assets a
            JOIN ohlcv_data_crypto o ON o.ticker = a.code
            WHERE 1=1 {base_where} {quote_where} {date_where}
            ORDER BY {sort_col} {sort_dir}, a.code ASC
            LIMIT {per_page} OFFSET {offset}
        """)

    result = await db.execute(data_query)
    rows = result.fetchall()

    items = [
        CryptoHistoryItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            currency=row.currency,
            base_currency=row.base_currency,
            quote_currency=row.quote_currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return CryptoHistoryPaginatedResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/crypto/top100/", methods=["GET"], response_model=CryptoTop100Response)
async def get_crypto_top100(
    base_currency: Optional[str] = Query(None, description="Filter by base currency code (e.g., BTC, ETH)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency code (e.g., USD, USDT)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the top 100 crypto assets by latest volume (descending).
    Uses LATERAL join driven by crypto_assets for efficient per-ticker
    latest-row lookups. Enriched with name, exchange, type, currency,
    base_currency, quote_currency, and notional_value (close * volume).
    """
    base_where = ""
    quote_where = ""
    if base_currency:
        base_where = f"AND a.base_currency = '{base_currency.upper()}'"
    if quote_currency:
        quote_where = f"AND a.quote_currency = '{quote_currency.upper()}'"

    query = text(f"""
        SELECT a.code AS ticker, a.name, a.exchange, a.type, a.currency,
               a.base_currency, a.quote_currency,
               o.date, o.open, o.high, o.low, o.close,
               o.adjusted_close, o.volume,
               (o.close * o.volume) AS notional_value
        FROM crypto_assets a
        CROSS JOIN LATERAL (
            SELECT date, open, high, low, close, adjusted_close, volume
            FROM ohlcv_data_crypto
            WHERE ticker = a.code
            ORDER BY date DESC
            LIMIT 1
        ) o
        WHERE 1=1 {base_where} {quote_where}
        ORDER BY o.volume DESC
        LIMIT 100
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        CryptoTop100Item(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            currency=row.currency,
            base_currency=row.base_currency,
            quote_currency=row.quote_currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
            notional_value=row.notional_value,
        )
        for row in rows
    ]

    return CryptoTop100Response(data=items, count=len(items))


@_retired("/crypto/assets/", methods=["GET"], response_model=CryptoAssetResponse)
async def get_crypto_assets(
    base_currency: Optional[str] = Query(None, description="Filter by base currency (e.g., BTC, ETH)"),
    quote_currency: Optional[str] = Query(None, description="Filter by quote currency (e.g., USD, EUR)"),
    type: Optional[str] = Query(None, description="Filter by type (e.g., cryptocurrency)"),
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = []

    if base_currency:
        conditions.append(CryptoAsset.base_currency == base_currency.upper())
    if quote_currency:
        conditions.append(CryptoAsset.quote_currency == quote_currency.upper())
    if type:
        conditions.append(CryptoAsset.type == type)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            (CryptoAsset.code.ilike(pattern)) | (CryptoAsset.name.ilike(pattern))
        )

    count_query = select(func.count(CryptoAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"crypto_assets|base={base_currency}|quote={quote_currency}|type={type}|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(CryptoAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(CryptoAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        CryptoAssetItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                   # type: ignore[arg-type]
            type=row.type,                          # type: ignore[arg-type]
            base_currency=row.base_currency,        # type: ignore[arg-type]
            quote_currency=row.quote_currency,       # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return CryptoAssetResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# ── UK Stock (LSE) Endpoints ─────────────────────────────────────────────

@_retired("/uk/", methods=["GET"], response_model=UkPaginatedResponse)
async def get_uk_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single UK ticker (e.g., AZN)"),
    tickers: Optional[str] = Query(None, description="Comma-separated UK tickers (e.g., AZN,SHEL,HSBA)"),
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., Healthcare, Energy)"),
    industry: Optional[str] = Query(None, description="Filter by industry (e.g., Drug Manufacturers, Oil & Gas)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for UK stocks (LSE).
    Only returns data for tickers that exist in uk_assets.
    Supports filtering by ticker(s), sector, and industry.
    """
    # UK tickers are case-sensitive — preserve original case
    ticker_list = parse_comma_separated_preserve(tickers) or ([ticker] if ticker else None)

    # Build WHERE clauses
    conditions = []
    count_conditions = []

    if ticker_list:
        if len(ticker_list) == 1:
            conditions.append(UkOhlcvData.ticker == ticker_list[0])
            count_conditions.append(UkOhlcvData.ticker == ticker_list[0])
        else:
            conditions.append(UkOhlcvData.ticker.in_(ticker_list))
            count_conditions.append(UkOhlcvData.ticker.in_(ticker_list))

    if sector:
        conditions.append(UkAsset.sector == sector)
        count_conditions.append(UkAsset.sector == sector)

    if industry:
        conditions.append(UkAsset.industry == industry)
        count_conditions.append(UkAsset.industry == industry)

    if start_date:
        conditions.append(UkOhlcvData.date >= start_date)
        count_conditions.append(UkOhlcvData.date >= start_date)
    if end_date:
        conditions.append(UkOhlcvData.date <= end_date)
        count_conditions.append(UkOhlcvData.date <= end_date)
    if year:
        conditions.append(func.extract("year", UkOhlcvData.date) == year)
        count_conditions.append(func.extract("year", UkOhlcvData.date) == year)
    if month:
        conditions.append(func.extract("month", UkOhlcvData.date) == month)
        count_conditions.append(func.extract("month", UkOhlcvData.date) == month)
    if open_min is not None:
        conditions.append(UkOhlcvData.open >= open_min)
        count_conditions.append(UkOhlcvData.open >= open_min)
    if open_max is not None:
        conditions.append(UkOhlcvData.open <= open_max)
        count_conditions.append(UkOhlcvData.open <= open_max)
    if close_min is not None:
        conditions.append(UkOhlcvData.close >= close_min)
        count_conditions.append(UkOhlcvData.close >= close_min)
    if close_max is not None:
        conditions.append(UkOhlcvData.close <= close_max)
        count_conditions.append(UkOhlcvData.close <= close_max)
    if volume_min is not None:
        conditions.append(UkOhlcvData.volume >= volume_min)
        count_conditions.append(UkOhlcvData.volume >= volume_min)
    if volume_max is not None:
        conditions.append(UkOhlcvData.volume <= volume_max)
        count_conditions.append(UkOhlcvData.volume <= volume_max)

    # Count query — only count OHLCV rows that have a matching asset
    count_query = select(func.count(UkOhlcvData.id)).join(
        UkAsset, UkOhlcvData.ticker == UkAsset.code
    )
    for c in count_conditions:
        count_query = count_query.where(c)

    cache_key = f"uk|tickers={ticker_list}|sector={sector}|industry={industry}|start={start_date}|end={end_date}|year={year}|month={month}|omin={open_min}|omax={open_max}|cmin={close_min}|cmax={close_max}|vmin={volume_min}|vmax={volume_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    # Data query
    sort_column = getattr(UkOhlcvData, sort_by or "date")
    offset = (page - 1) * per_page

    data_query = select(UkOhlcvData).join(
        UkAsset, UkOhlcvData.ticker == UkAsset.code
    )
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_column.desc() if sort_order == "desc" else sort_column.asc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UkPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/uk/latest_close/", methods=["GET"], response_model=UkLatestResponse)
async def get_uk_latest_close_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated UK tickers (e.g., AZN,SHEL,HSBA). If omitted, returns latest for all UK stocks."),
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., Healthcare, Energy)"),
    industry: Optional[str] = Query(None, description="Filter by industry (e.g., Drug Manufacturers, Oil & Gas)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for UK stocks (LSE).
    Uses LATERAL join driven by uk_assets for efficient per-ticker
    latest-row lookups. Enriched with name, exchange, type, sector,
    industry, isin, currency.
    Optionally filter by specific tickers and/or sector/industry.
    """
    # UK tickers are case-sensitive — preserve original case
    ticker_list = parse_comma_separated_preserve(tickers)

    # Build filter SQL fragments
    sector_where = ""
    industry_where = ""
    if sector:
        sector_where = f"AND a.sector = '{sector}'"
    if industry:
        industry_where = f"AND a.industry = '{industry}'"

    if ticker_list:
        # Specific tickers: VALUES list as driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, a.name, a.exchange, a.type, a.sector,
                   a.industry, a.isin, a.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN uk_assets a ON a.code = t.ticker
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_uk
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {sector_where} {industry_where}
            ORDER BY t.ticker ASC
        """)
    else:
        # All UK stocks: uk_assets as driving row source
        query = text(f"""
            SELECT a.code AS ticker, a.name, a.exchange, a.type, a.sector,
                   a.industry, a.isin, a.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM uk_assets a
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_uk
                WHERE ticker = a.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {sector_where} {industry_where}
            ORDER BY a.code ASC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        UkLatestItem(
            ticker=row.ticker,
            name=row.name,
            exchange=row.exchange,
            type=row.type,
            sector=row.sector,
            industry=row.industry,
            isin=row.isin,
            currency=row.currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return UkLatestResponse(data=items, count=len(items))


@_retired("/uk/latest_close/{ticker}", methods=["GET"], response_model=UkLatestItem)
async def get_uk_latest_close_single(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record from the database for a single UK stock (LSE),
    enriched with asset metadata (name, exchange, type, sector,
    industry, isin, currency).
    """
    # Verify the ticker is a UK asset
    asset_query = select(UkAsset).where(UkAsset.code == ticker)
    asset_result = await db.execute(asset_query)
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail=f"No UK stock found with ticker: {ticker}")

    # Get latest OHLCV
    ohlcv_query = select(UkOhlcvData).where(
        UkOhlcvData.ticker == ticker
    ).order_by(UkOhlcvData.date.desc()).limit(1)
    ohlcv_result = await db.execute(ohlcv_query)
    ohlcv = ohlcv_result.scalar_one_or_none()

    if not ohlcv:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for UK ticker: {ticker}. "
                   f"The asset exists in uk_assets but has no price data in ohlcv_data_uk."
        )

    return UkLatestItem(
        ticker=ticker,
        name=asset.name,                    # type: ignore[arg-type]
        exchange=asset.exchange,            # type: ignore[arg-type]
        type=asset.type,                    # type: ignore[arg-type]
        sector=asset.sector,                # type: ignore[arg-type]
        industry=asset.industry,            # type: ignore[arg-type]
        isin=asset.isin,                    # type: ignore[arg-type]
        currency=asset.currency,            # type: ignore[arg-type]
        date=ohlcv.date,                    # type: ignore[arg-type]
        open=ohlcv.open,                    # type: ignore[arg-type]
        high=ohlcv.high,                    # type: ignore[arg-type]
        low=ohlcv.low,                      # type: ignore[arg-type]
        close=ohlcv.close,                  # type: ignore[arg-type]
        adjusted_close=ohlcv.adjusted_close,  # type: ignore[arg-type]
        volume=ohlcv.volume,                # type: ignore[arg-type]
    )


@_retired("/uk/latest/", methods=["GET"], response_model=RealTimeOhlcvResponse)
async def get_uk_realtime_latest_batch(
    tickers: str = Query(..., description="Comma-separated UK tickers (e.g., AZN,SHEL,HSBA). Required."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns real-time OHLCV data from EODHD for the specified UK tickers.
    The `tickers` parameter is required.
    """
    ticker_list = parse_comma_separated_preserve(tickers)
    if not ticker_list:
        raise HTTPException(status_code=400, detail="tickers parameter is required")

    assets_query = select(UkAsset).where(UkAsset.code.in_(ticker_list))
    result = await db.execute(assets_query)
    assets = result.scalars().all()

    found_tickers = {a.code for a in assets}
    missing = [t for t in ticker_list if t not in found_tickers]
    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"No UK stock found with tickers: {', '.join(missing)}",
        )

    pairs = [(str(a.code), str(a.exchange)) for a in assets]
    items = await fetch_eodhd_realtime_batch(pairs)
    return RealTimeOhlcvResponse(data=items, count=len(items))




@_retired("/uk/assets/", methods=["GET"], response_model=UkAssetResponse)
async def get_uk_assets(
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., Healthcare, Energy)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = []

    if sector:
        conditions.append(UkAsset.sector == sector)
    if industry:
        conditions.append(UkAsset.industry == industry)
    if type:
        conditions.append(UkAsset.type == type)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            (UkAsset.code.ilike(pattern)) | (UkAsset.name.ilike(pattern))
        )

    count_query = select(func.count(UkAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"uk_assets|sector={sector}|industry={industry}|type={type}|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(UkAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(UkAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        UkAssetItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                          # type: ignore[arg-type]
            exchange=row.exchange,                  # type: ignore[arg-type]
            type=row.type,                          # type: ignore[arg-type]
            sector=row.sector,                      # type: ignore[arg-type]
            industry=row.industry,                  # type: ignore[arg-type]
            isin=row.isin,                          # type: ignore[arg-type]
            currency=row.currency,                  # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return UkAssetResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# ── FTSE 100 Endpoints ─────────────────────────────────────────────────────

@_retired("/ftse100/", methods=["GET"], response_model=Ftse100PaginatedResponse)
async def get_ftse100_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single FTSE 100 ticker (e.g., AZN)"),
    tickers: Optional[str] = Query(None, description="Comma-separated FTSE 100 tickers (e.g., AZN,SHEL,HSBA)"),
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., Healthcare, Energy)"),
    industry: Optional[str] = Query(None, description="Filter by industry (e.g., Drug Manufacturers, Oil & Gas)"),
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
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated OHLCV data for FTSE 100 constituents.
    Only returns data for tickers that exist in ftse100_constituents.
    Supports filtering by ticker(s), sector, and industry.
    Enriched with name, sector, industry from ftse100_constituents and
    isin, currency from uk_assets.
    """
    # FTSE 100 tickers are case-sensitive — preserve original case
    ticker_list = parse_comma_separated_preserve(tickers) or ([ticker] if ticker else None)

    # Build date filter clauses for raw SQL
    date_filters = []
    if start_date:
        date_filters.append(f"o.date >= '{start_date}'")
    if end_date:
        date_filters.append(f"o.date <= '{end_date}'")
    if year:
        date_filters.append(f"EXTRACT(year FROM o.date) = {year}")
    if month:
        date_filters.append(f"EXTRACT(month FROM o.date) = {month}")
    if open_min is not None:
        date_filters.append(f"o.open >= {open_min}")
    if open_max is not None:
        date_filters.append(f"o.open <= {open_max}")
    if close_min is not None:
        date_filters.append(f"o.close >= {close_min}")
    if close_max is not None:
        date_filters.append(f"o.close <= {close_max}")
    if volume_min is not None:
        date_filters.append(f"o.volume >= {volume_min}")
    if volume_max is not None:
        date_filters.append(f"o.volume <= {volume_max}")

    ohlcv_where = ""
    if date_filters:
        ohlcv_where = "AND " + " AND ".join(date_filters)

    # Build sector/industry filter SQL fragments
    sector_where = ""
    industry_where = ""
    if sector:
        sector_where = f"AND f.sector = '{sector}'"
    if industry:
        industry_where = f"AND f.industry = '{industry}'"

    # Map sort_by to the SQL column name
    sort_col_map = {
        "date": "o.date", "volume": "o.volume", "close": "o.close",
        "open": "o.open", "high": "o.high", "low": "o.low"
    }
    sort_col = sort_col_map.get(sort_by or "date", "o.date")
    sort_dir = "DESC" if sort_order == "desc" else "ASC"

    if ticker_list:
        # Specific tickers: verify all are FTSE 100 constituents
        check_query = select(Ftse100Constituent.code).where(
            Ftse100Constituent.code.in_(ticker_list)
        )
        check_result = await db.execute(check_query)
        valid_tickers = {row[0] for row in check_result.all()}

        invalid_tickers = [t for t in ticker_list if t not in valid_tickers]
        if invalid_tickers:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker(s) not FTSE 100 constituents: {', '.join(invalid_tickers)}"
            )

        ticker_values = ", ".join(f"'{t}'" for t in ticker_list)

        # Count query — specific tickers
        count_query = text(f"""
            SELECT count(*)
            FROM ftse100_constituents f
            LEFT JOIN uk_assets ua ON ua.code = f.code
            JOIN ohlcv_data_uk o ON o.ticker = f.code
            WHERE f.code IN ({ticker_values})
            {sector_where} {industry_where}
            {ohlcv_where}
        """)

        cache_key = f"uk_lc_t|tickers={ticker_list}|sector={sector}|industry={industry}|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        # Data query with pagination — specific tickers
        offset = (page - 1) * per_page

        data_query = text(f"""
            SELECT f.code AS ticker, f.name, f.sector, f.industry,
                   ua.isin, ua.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM ftse100_constituents f
            LEFT JOIN uk_assets ua ON ua.code = f.code
            JOIN ohlcv_data_uk o ON o.ticker = f.code
            WHERE f.code IN ({ticker_values})
            {sector_where} {industry_where}
            {ohlcv_where}
            ORDER BY {sort_col} {sort_dir}, f.code ASC
            LIMIT {per_page} OFFSET {offset}
        """)
    else:
        # All FTSE 100 constituents
        count_query = text(f"""
            SELECT count(*)
            FROM ftse100_constituents f
            LEFT JOIN uk_assets ua ON ua.code = f.code
            JOIN ohlcv_data_uk o ON o.ticker = f.code
            WHERE 1=1
            {sector_where} {industry_where}
            {ohlcv_where}
        """)

        cache_key = f"uk_lc_all|sector={sector}|industry={industry}|start={start_date}|end={end_date}|year={year}|month={month}"
        total = _get_cached_count(cache_key)
        if total is None:
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            _set_cached_count(cache_key, total)

        # Data query with pagination — all constituents
        offset = (page - 1) * per_page

        data_query = text(f"""
            SELECT f.code AS ticker, f.name, f.sector, f.industry,
                   ua.isin, ua.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM ftse100_constituents f
            LEFT JOIN uk_assets ua ON ua.code = f.code
            JOIN ohlcv_data_uk o ON o.ticker = f.code
            WHERE 1=1
            {sector_where} {industry_where}
            {ohlcv_where}
            ORDER BY {sort_col} {sort_dir}, f.code ASC
            LIMIT {per_page} OFFSET {offset}
        """)

    result = await db.execute(data_query)
    rows = result.fetchall()

    items = [
        Ftse100HistoryItem(
            ticker=row.ticker,
            name=row.name,
            sector=row.sector,
            industry=row.industry,
            isin=row.isin,
            currency=row.currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return Ftse100PaginatedResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/ftse100/latest/", methods=["GET"], response_model=Ftse100LatestResponse)
async def get_ftse100_latest_batch(
    tickers: Optional[str] = Query(None, description="Comma-separated FTSE 100 tickers (e.g., AZN,SHEL,HSBA). If omitted, returns latest for all FTSE 100 constituents."),
    sector: Optional[str] = Query(None, description="Filter by sector (e.g., Healthcare, Energy)"),
    industry: Optional[str] = Query(None, description="Filter by industry (e.g., Drug Manufacturers, Oil & Gas)"),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest OHLCV record for FTSE 100 constituents.
    Uses LATERAL join driven by ftse100_constituents for efficient per-ticker
    latest-row lookups. Enriched with name, sector, industry from
    ftse100_constituents and isin, currency from uk_assets.
    Optionally filter by specific tickers and/or sector/industry.
    """
    # FTSE 100 tickers are case-sensitive — preserve original case
    ticker_list = parse_comma_separated_preserve(tickers)

    # Build filter SQL fragments
    sector_where = ""
    industry_where = ""
    if sector:
        sector_where = f"AND f.sector = '{sector}'"
    if industry:
        industry_where = f"AND f.industry = '{industry}'"

    if ticker_list:
        # Specific tickers: VALUES list as driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, f.name, f.sector, f.industry,
                   ua.isin, ua.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM (VALUES {ticker_values}) AS t(ticker)
            JOIN ftse100_constituents f ON f.code = t.ticker
            LEFT JOIN uk_assets ua ON ua.code = t.ticker
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_uk
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {sector_where} {industry_where}
            ORDER BY t.ticker ASC
        """)
    else:
        # All FTSE 100 constituents: ftse100_constituents as driving row source
        query = text(f"""
            SELECT f.code AS ticker, f.name, f.sector, f.industry,
                   ua.isin, ua.currency,
                   o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume
            FROM ftse100_constituents f
            LEFT JOIN uk_assets ua ON ua.code = f.code
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close, volume
                FROM ohlcv_data_uk
                WHERE ticker = f.code
                ORDER BY date DESC
                LIMIT 1
            ) o
            WHERE 1=1 {sector_where} {industry_where}
            ORDER BY f.code ASC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        Ftse100LatestItem(
            ticker=row.ticker,
            name=row.name,
            sector=row.sector,
            industry=row.industry,
            isin=row.isin,
            currency=row.currency,
            date=row.date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adjusted_close=row.adjusted_close,
            volume=row.volume,
        )
        for row in rows
    ]

    return Ftse100LatestResponse(data=items, count=len(items))




@_retired("/ftse100/constituents/", methods=["GET"], response_model=Ftse100ConstituentResponse)
async def get_ftse100_constituents(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = []

    if sector:
        conditions.append(Ftse100Constituent.sector == sector)
    if industry:
        conditions.append(Ftse100Constituent.industry == industry)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            (Ftse100Constituent.code.ilike(pattern)) | (Ftse100Constituent.name.ilike(pattern))
        )

    count_query = select(func.count(Ftse100Constituent.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"ftse100_cons|sector={sector}|industry={industry}|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(Ftse100Constituent, sort_field)
    offset = (page - 1) * per_page

    data_query = select(Ftse100Constituent)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        Ftse100ConstituentItem(
            code=row.code,                          # type: ignore[arg-type]
            name=row.name,                           # type: ignore[arg-type]
            sector=row.sector,                       # type: ignore[arg-type]
            industry=row.industry,                   # type: ignore[arg-type]
            isin=row.isin,                           # type: ignore[arg-type]
            currency=row.currency,                   # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return Ftse100ConstituentResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/etf/assets/", methods=["GET"], response_model=EtfIndexAssetListResponse)
async def get_etf_assets(
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = [EtfIndexAsset.type == "etf"]

    if search:
        pattern = f"%{search}%"
        conditions.append(
            (EtfIndexAsset.code.ilike(pattern)) | (EtfIndexAsset.name.ilike(pattern))
        )

    count_query = select(func.count(EtfIndexAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"etf_assets|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(EtfIndexAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(EtfIndexAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        EtfIndexAssetResponse(
            code=row.code,                           # type: ignore[arg-type]
            name=row.name,                           # type: ignore[arg-type]
            exchange=row.exchange,                   # type: ignore[arg-type]
            type=row.type,                           # type: ignore[arg-type]
            isin=row.isin,                           # type: ignore[arg-type]
            currency=row.currency,                   # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return EtfIndexAssetListResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/index/assets/", methods=["GET"], response_model=EtfIndexAssetListResponse)
async def get_index_assets(
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = [EtfIndexAsset.type == "index"]

    if search:
        pattern = f"%{search}%"
        conditions.append(
            (EtfIndexAsset.code.ilike(pattern)) | (EtfIndexAsset.name.ilike(pattern))
        )

    count_query = select(func.count(EtfIndexAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"index_assets|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(EtfIndexAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(EtfIndexAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        EtfIndexAssetResponse(
            code=row.code,                           # type: ignore[arg-type]
            name=row.name,                           # type: ignore[arg-type]
            exchange=row.exchange,                   # type: ignore[arg-type]
            type=row.type,                           # type: ignore[arg-type]
            isin=row.isin,                           # type: ignore[arg-type]
            currency=row.currency,                   # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return EtfIndexAssetListResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/gov-bond/assets/", methods=["GET"], response_model=GovBondAssetResponse)
async def get_gov_bond_assets(
    country: Optional[str] = Query(None, description="Filter by country (e.g., US, DE, JP)"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search code or name (case-insensitive partial match)"),
    sort: Optional[str] = Query("code", description="Sort field: code, name"),
    order: Optional[str] = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    conditions = []

    if country:
        conditions.append(GovBondAsset.country == country.upper())
    if type:
        conditions.append(GovBondAsset.type == type)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            (GovBondAsset.code.ilike(pattern)) | (GovBondAsset.name.ilike(pattern))
        )

    count_query = select(func.count(GovBondAsset.code))
    for c in conditions:
        count_query = count_query.where(c)
    cache_key = f"gov_bond_assets|country={country}|type={type}|search={search}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    allowed_sorts = {"code", "name"}
    sort_field = sort if sort in allowed_sorts else "code"
    sort_col = getattr(GovBondAsset, sort_field)
    offset = (page - 1) * per_page

    data_query = select(GovBondAsset)
    for c in conditions:
        data_query = data_query.where(c)
    data_query = data_query.order_by(
        sort_col.asc() if order == "asc" else sort_col.desc()
    ).offset(offset).limit(per_page)

    result = await db.execute(data_query)
    rows = result.scalars().all()

    items = [
        GovBondAssetItem(
            code=row.code,                           # type: ignore[arg-type]
            name=row.name,                           # type: ignore[arg-type]
            exchange=row.exchange,                   # type: ignore[arg-type]
            type=row.type,                           # type: ignore[arg-type]
            currency=row.currency,                   # type: ignore[arg-type]
            country=row.country,                      # type: ignore[arg-type]
        )
        for row in rows
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 1
    return GovBondAssetResponse(
        data=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# ── US Treasury Rate Endpoints ───────────────────────────────────────────────

# --- UST Bill Rates ---

@_retired("/ust/bill/", response_model=UstBillPaginatedResponse, methods=["GET"])
async def get_ust_bill_rates(
    tenor: Optional[str] = Query(None, description="Single tenor (e.g., 4WK, 13WK, 26WK, 52WK)"),
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 4WK,13WK,26WK)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    discount_min: Optional[Decimal] = Query(None),
    discount_max: Optional[Decimal] = Query(None),
    coupon_min: Optional[Decimal] = Query(None),
    coupon_max: Optional[Decimal] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|discount|coupon|avg_discount|avg_coupon)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated US Treasury bill rate records.
    Filter by tenor(s), date range, and discount/coupon bounds.
    """
    tenor_list = parse_comma_separated(tenors) or ([tenor.upper()] if tenor else None)

    query = select(UstBillRate)
    count_query = select(func.count(UstBillRate.id))

    if tenor_list:
        if len(tenor_list) == 1:
            query = query.where(UstBillRate.tenor == tenor_list[0])
            count_query = count_query.where(UstBillRate.tenor == tenor_list[0])
        else:
            query = query.where(UstBillRate.tenor.in_(tenor_list))
            count_query = count_query.where(UstBillRate.tenor.in_(tenor_list))

    if start_date:
        query = query.where(UstBillRate.date >= start_date)
        count_query = count_query.where(UstBillRate.date >= start_date)
    if end_date:
        query = query.where(UstBillRate.date <= end_date)
        count_query = count_query.where(UstBillRate.date <= end_date)

    if discount_min is not None:
        query = query.where(UstBillRate.discount >= discount_min)
        count_query = count_query.where(UstBillRate.discount >= discount_min)
    if discount_max is not None:
        query = query.where(UstBillRate.discount <= discount_max)
        count_query = count_query.where(UstBillRate.discount <= discount_max)
    if coupon_min is not None:
        query = query.where(UstBillRate.coupon >= coupon_min)
        count_query = count_query.where(UstBillRate.coupon >= coupon_min)
    if coupon_max is not None:
        query = query.where(UstBillRate.coupon <= coupon_max)
        count_query = count_query.where(UstBillRate.coupon <= coupon_max)

    sort_column = getattr(UstBillRate, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"ust_bill|tenors={tenor_list}|start={start_date}|end={end_date}|dmin={discount_min}|dmax={discount_max}|cmin={coupon_min}|cmax={coupon_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UstBillPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/ust/bill/latest/", response_model=UstBillLatestResponse, methods=["GET"])
async def get_ust_bill_latest(
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 4WK,13WK,26WK). If omitted, returns latest for all tenors."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest US Treasury bill rate for all or filtered tenors.
    Uses DISTINCT ON for efficient per-tenor latest-row lookups.
    """
    tenor_list = parse_comma_separated(tenors)

    if tenor_list:
        tenor_values = ", ".join(f"'{t}'" for t in tenor_list)
        query = text(f"""
            SELECT DISTINCT ON (tenor) tenor, date, discount, coupon, avg_discount, avg_coupon, maturity_date, cusip
            FROM ust_bill_rates
            WHERE tenor IN ({tenor_values})
            ORDER BY tenor, date DESC
        """)
    else:
        query = text("""
            SELECT DISTINCT ON (tenor) tenor, date, discount, coupon, avg_discount, avg_coupon, maturity_date, cusip
            FROM ust_bill_rates
            ORDER BY tenor, date DESC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        UstBillLatestItem(
            tenor=row.tenor,
            date=row.date,
            discount=row.discount,
            coupon=row.coupon,
            avg_discount=row.avg_discount,
            avg_coupon=row.avg_coupon,
            maturity_date=row.maturity_date,
            cusip=row.cusip,
        )
        for row in rows
    ]

    return UstBillLatestResponse(data=items, count=len(items))



# --- UST Long-Term Rates ---

@_retired("/ust/long-term/", response_model=UstLongTermPaginatedResponse, methods=["GET"])
async def get_ust_long_term_rates(
    rate_type: Optional[str] = Query(None, description="Single rate type (e.g., BC_20year, Over_10_Years, Real_Rate)"),
    rate_types: Optional[str] = Query(None, description="Comma-separated rate types (e.g., BC_20year,Over_10_Years)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    rate_min: Optional[Decimal] = Query(None),
    rate_max: Optional[Decimal] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|rate|extrapolation_factor)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated US Treasury long-term rate records.
    Filter by rate_type(s), date range, and rate bounds.
    """
    rt_list = parse_comma_separated_preserve(rate_types) or ([rate_type] if rate_type else None)

    query = select(UstLongTermRate)
    count_query = select(func.count(UstLongTermRate.id))

    if rt_list:
        if len(rt_list) == 1:
            query = query.where(UstLongTermRate.rate_type == rt_list[0])
            count_query = count_query.where(UstLongTermRate.rate_type == rt_list[0])
        else:
            query = query.where(UstLongTermRate.rate_type.in_(rt_list))
            count_query = count_query.where(UstLongTermRate.rate_type.in_(rt_list))

    if start_date:
        query = query.where(UstLongTermRate.date >= start_date)
        count_query = count_query.where(UstLongTermRate.date >= start_date)
    if end_date:
        query = query.where(UstLongTermRate.date <= end_date)
        count_query = count_query.where(UstLongTermRate.date <= end_date)

    if rate_min is not None:
        query = query.where(UstLongTermRate.rate >= rate_min)
        count_query = count_query.where(UstLongTermRate.rate >= rate_min)
    if rate_max is not None:
        query = query.where(UstLongTermRate.rate <= rate_max)
        count_query = count_query.where(UstLongTermRate.rate <= rate_max)

    sort_column = getattr(UstLongTermRate, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"ust_lt|rt={rt_list}|start={start_date}|end={end_date}|rmin={rate_min}|rmax={rate_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UstLongTermPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/ust/long-term/latest/", response_model=UstLongTermLatestResponse, methods=["GET"])
async def get_ust_long_term_latest(
    rate_types: Optional[str] = Query(None, description="Comma-separated rate types (e.g., BC_20year,Over_10_Years). If omitted, returns latest for all rate types."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest US Treasury long-term rate for all or filtered rate types.
    Uses DISTINCT ON for efficient per-rate-type latest-row lookups.
    """
    rt_list = parse_comma_separated_preserve(rate_types)

    if rt_list:
        rt_values = ", ".join(f"'{rt}'" for rt in rt_list)
        query = text(f"""
            SELECT DISTINCT ON (rate_type) rate_type, date, rate, extrapolation_factor
            FROM ust_long_term_rates
            WHERE rate_type IN ({rt_values})
            ORDER BY rate_type, date DESC
        """)
    else:
        query = text("""
            SELECT DISTINCT ON (rate_type) rate_type, date, rate, extrapolation_factor
            FROM ust_long_term_rates
            ORDER BY rate_type, date DESC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        UstLongTermLatestItem(
            rate_type=row.rate_type,
            date=row.date,
            rate=row.rate,
            extrapolation_factor=row.extrapolation_factor,
        )
        for row in rows
    ]

    return UstLongTermLatestResponse(data=items, count=len(items))



# --- UST Real Yield Rates ---

@_retired("/ust/real-yield/", response_model=UstRealYieldPaginatedResponse, methods=["GET"])
async def get_ust_real_yield_rates(
    tenor: Optional[str] = Query(None, description="Single tenor (e.g., 5Y, 10Y, 30Y)"),
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 5Y,10Y,30Y)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    rate_min: Optional[Decimal] = Query(None),
    rate_max: Optional[Decimal] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|rate)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated US Treasury real yield rate records.
    Filter by tenor(s), date range, and rate bounds.
    """
    tenor_list = parse_comma_separated(tenors) or ([tenor.upper()] if tenor else None)

    query = select(UstRealYieldRate)
    count_query = select(func.count(UstRealYieldRate.id))

    if tenor_list:
        if len(tenor_list) == 1:
            query = query.where(UstRealYieldRate.tenor == tenor_list[0])
            count_query = count_query.where(UstRealYieldRate.tenor == tenor_list[0])
        else:
            query = query.where(UstRealYieldRate.tenor.in_(tenor_list))
            count_query = count_query.where(UstRealYieldRate.tenor.in_(tenor_list))

    if start_date:
        query = query.where(UstRealYieldRate.date >= start_date)
        count_query = count_query.where(UstRealYieldRate.date >= start_date)
    if end_date:
        query = query.where(UstRealYieldRate.date <= end_date)
        count_query = count_query.where(UstRealYieldRate.date <= end_date)

    if rate_min is not None:
        query = query.where(UstRealYieldRate.rate >= rate_min)
        count_query = count_query.where(UstRealYieldRate.rate >= rate_min)
    if rate_max is not None:
        query = query.where(UstRealYieldRate.rate <= rate_max)
        count_query = count_query.where(UstRealYieldRate.rate <= rate_max)

    sort_column = getattr(UstRealYieldRate, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"ust_ry|tenors={tenor_list}|start={start_date}|end={end_date}|rmin={rate_min}|rmax={rate_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UstRealYieldPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/ust/real-yield/latest/", response_model=UstRealYieldLatestResponse, methods=["GET"])
async def get_ust_real_yield_latest(
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 5Y,10Y,30Y). If omitted, returns latest for all tenors."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest US Treasury real yield rate for all or filtered tenors.
    Uses DISTINCT ON for efficient per-tenor latest-row lookups.
    """
    tenor_list = parse_comma_separated(tenors)

    if tenor_list:
        tenor_values = ", ".join(f"'{t}'" for t in tenor_list)
        query = text(f"""
            SELECT DISTINCT ON (tenor) tenor, date, rate
            FROM ust_real_yield_rates
            WHERE tenor IN ({tenor_values})
            ORDER BY tenor, date DESC
        """)
    else:
        query = text("""
            SELECT DISTINCT ON (tenor) tenor, date, rate
            FROM ust_real_yield_rates
            ORDER BY tenor, date DESC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        UstRealYieldLatestItem(
            tenor=row.tenor,
            date=row.date,
            rate=row.rate,
        )
        for row in rows
    ]

    return UstRealYieldLatestResponse(data=items, count=len(items))



# --- UST Yield Rates ---

@_retired("/ust/yield/", response_model=UstYieldPaginatedResponse, methods=["GET"])
async def get_ust_yield_rates(
    tenor: Optional[str] = Query(None, description="Single tenor (e.g., 1M, 3M, 6M, 1Y, 2Y, 5Y, 10Y, 30Y)"),
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 2Y,5Y,10Y,30Y)"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    rate_min: Optional[Decimal] = Query(None),
    rate_max: Optional[Decimal] = Query(None),
    sort_by: Optional[str] = Query("date", pattern="^(date|rate)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    List paginated US Treasury yield rate records.
    Filter by tenor(s), date range, and rate bounds.
    """
    tenor_list = parse_comma_separated(tenors) or ([tenor.upper()] if tenor else None)

    query = select(UstYieldRate)
    count_query = select(func.count(UstYieldRate.id))

    if tenor_list:
        if len(tenor_list) == 1:
            query = query.where(UstYieldRate.tenor == tenor_list[0])
            count_query = count_query.where(UstYieldRate.tenor == tenor_list[0])
        else:
            query = query.where(UstYieldRate.tenor.in_(tenor_list))
            count_query = count_query.where(UstYieldRate.tenor.in_(tenor_list))

    if start_date:
        query = query.where(UstYieldRate.date >= start_date)
        count_query = count_query.where(UstYieldRate.date >= start_date)
    if end_date:
        query = query.where(UstYieldRate.date <= end_date)
        count_query = count_query.where(UstYieldRate.date <= end_date)

    if rate_min is not None:
        query = query.where(UstYieldRate.rate >= rate_min)
        count_query = count_query.where(UstYieldRate.rate >= rate_min)
    if rate_max is not None:
        query = query.where(UstYieldRate.rate <= rate_max)
        count_query = count_query.where(UstYieldRate.rate <= rate_max)

    sort_column = getattr(UstYieldRate, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    cache_key = f"ust_yield|tenors={tenor_list}|start={start_date}|end={end_date}|rmin={rate_min}|rmax={rate_max}"
    total = _get_cached_count(cache_key)
    if total is None:
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        _set_cached_count(cache_key, total)

    result = await db.execute(query)
    data = result.scalars().all()

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UstYieldPaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@_retired("/ust/yield/latest/", response_model=UstYieldLatestResponse, methods=["GET"])
async def get_ust_yield_latest(
    tenors: Optional[str] = Query(None, description="Comma-separated tenors (e.g., 2Y,5Y,10Y,30Y). If omitted, returns latest for all tenors."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns the latest US Treasury yield rate for all or filtered tenors.
    Uses DISTINCT ON for efficient per-tenor latest-row lookups.
    """
    tenor_list = parse_comma_separated(tenors)

    if tenor_list:
        tenor_values = ", ".join(f"'{t}'" for t in tenor_list)
        query = text(f"""
            SELECT DISTINCT ON (tenor) tenor, date, rate
            FROM ust_yield_rates
            WHERE tenor IN ({tenor_values})
            ORDER BY tenor, date DESC
        """)
    else:
        query = text("""
            SELECT DISTINCT ON (tenor) tenor, date, rate
            FROM ust_yield_rates
            ORDER BY tenor, date DESC
        """)

    result = await db.execute(query)
    rows = result.fetchall()

    items = [
        UstYieldLatestItem(
            tenor=row.tenor,
            date=row.date,
            rate=row.rate,
        )
        for row in rows
    ]

    return UstYieldLatestResponse(data=items, count=len(items))


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


@_retired("/commodity/categories/", response_model=CommodityCategoryResponse, methods=["GET"])
async def get_commodity_categories(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """
    Returns all distinct commodity categories.
    """
    query = select(CommodityEOD.category).distinct().where(
        CommodityEOD.category.isnot(None)
    ).order_by(CommodityEOD.category.asc())

    result = await db.execute(query)
    categories = [row[0] for row in result.fetchall()]

    return CommodityCategoryResponse(data=categories, count=len(categories))


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
    "ohlcv_unified", "assets", "sp500_constituents", "ticker_aliases", "tickers",
    "ohlcv_data", "ohlcv_data_etf_index", "etf_index_assets",
    "ohlcv_data_gov_bonds", "gov_bond_assets",
    "ohlcv_data_fx", "fx_assets",
    "ohlcv_data_uk", "uk_assets", "ftse100_constituents",
    "ust_bill_rates", "ust_long_term_rates", "ust_real_yield_rates", "ust_yield_rates",
    "ohlcv_data_crypto", "crypto_assets",
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
          `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`,
          `ohlcv_data_etf_index`, `etf_index_assets`, `ohlcv_data_gov_bonds`, `gov_bond_assets`,
          `ohlcv_data_fx`, `fx_assets`, `ohlcv_data_uk`, `uk_assets`,
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
