from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyQuery
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
import math
import re
import asyncio
import logging

from database import get_db, engine as async_engine
from models import OhlcvData, SP500Constituent, Asset, TickerAlias, Ticker
from schemas import (
    OhlcvDataCreate, OhlcvDataUpdate, OhlcvDataResponse,
    OhlcvDataBulkCreate, PaginatedResponse, OhlcvStatsResponse,
    BatchLatestResponse, BulkInsertResponse,
    SP500ConstituentResponse, SP500ListResponse,
    SP500LatestItem, SP500LatestResponse,
    SP500HistoryItem, SP500HistoryResponse,
    TickerAliasCreate, TickerAliasUpdate, TickerAliasResponse, TickerAliasListResponse,
    SqlQueryRequest, SqlQueryResponse
)

API_KEY = os.getenv("API_KEY", "ohlcv-api-key-2024-secure")

api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

logger = logging.getLogger("ohlcv-api")

MAX_STARTUP_RETRIES = 5
STARTUP_RETRY_DELAY_S = 3


async def _ensure_tickers_table():
    """
    Ensure the tickers lookup table, sync triggers, and backfill exist.
    Retries on DB connection failure with exponential backoff.

    The tickers table provides an Index Only Scan (~5ms) as the driving row
    source for LATERAL joins, replacing SELECT DISTINCT on 43M+ rows (~8.6s).
    The triggers keep it in sync as ohlcv_data rows are inserted/deleted.
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
                            SELECT 1 FROM ohlcv_data WHERE ticker = OLD.ticker
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
                        AFTER INSERT ON ohlcv_data
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
                        AFTER DELETE ON ohlcv_data
                        FOR EACH ROW
                        EXECUTE FUNCTION sync_tickers_on_delete()
                    """))

                # 6. Backfill if the table is empty
                count_result = await conn.execute(text("SELECT count(*) FROM tickers"))
                count = count_result.scalar()
                if count == 0:
                    await conn.execute(text("""
                        INSERT INTO tickers (ticker)
                        SELECT DISTINCT ticker FROM ohlcv_data
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


@app.get("/ohlcv/", response_model=PaginatedResponse)
async def get_ohlcv_data(
    ticker: Optional[str] = Query(None, description="Single ticker (e.g., AAPL)"),
    tickers: Optional[str] = Query(None, description="Comma-separated tickers (e.g., AAPL,MSFT,GOOGL)"),
    asset_isin: Optional[str] = Query(None),
    asset_isins: Optional[str] = Query(None, description="Comma-separated ISINs"),
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
    api_key: str = Depends(verify_api_key)
):
    ticker_list = parse_comma_separated(tickers) or ([ticker.upper()] if ticker else None)
    isin_list = parse_comma_separated(asset_isins) or ([asset_isin.upper()] if asset_isin else None)
    
    query = select(OhlcvData)
    count_query = select(func.count(OhlcvData.id))
    
    if ticker_list:
        if len(ticker_list) == 1:
            query = query.where(OhlcvData.ticker == ticker_list[0])
            count_query = count_query.where(OhlcvData.ticker == ticker_list[0])
        else:
            query = query.where(OhlcvData.ticker.in_(ticker_list))
            count_query = count_query.where(OhlcvData.ticker.in_(ticker_list))
    
    if isin_list:
        if len(isin_list) == 1:
            query = query.where(OhlcvData.asset_isin == isin_list[0])
            count_query = count_query.where(OhlcvData.asset_isin == isin_list[0])
        else:
            query = query.where(OhlcvData.asset_isin.in_(isin_list))
            count_query = count_query.where(OhlcvData.asset_isin.in_(isin_list))
    
    if year:
        query = query.where(func.extract("year", OhlcvData.date) == year)
        count_query = count_query.where(func.extract("year", OhlcvData.date) == year)
    
    if month:
        query = query.where(func.extract("month", OhlcvData.date) == month)
        count_query = count_query.where(func.extract("month", OhlcvData.date) == month)
    
    if start_date:
        query = query.where(OhlcvData.date >= start_date)
        count_query = count_query.where(OhlcvData.date >= start_date)
    
    if end_date:
        query = query.where(OhlcvData.date <= end_date)
        count_query = count_query.where(OhlcvData.date <= end_date)
    
    if open_min is not None:
        query = query.where(OhlcvData.open >= open_min)
        count_query = count_query.where(OhlcvData.open >= open_min)
    if open_max is not None:
        query = query.where(OhlcvData.open <= open_max)
        count_query = count_query.where(OhlcvData.open <= open_max)
    
    if close_min is not None:
        query = query.where(OhlcvData.close >= close_min)
        count_query = count_query.where(OhlcvData.close >= close_min)
    if close_max is not None:
        query = query.where(OhlcvData.close <= close_max)
        count_query = count_query.where(OhlcvData.close <= close_max)
    
    if volume_min is not None:
        query = query.where(OhlcvData.volume >= volume_min)
        count_query = count_query.where(OhlcvData.volume >= volume_min)
    if volume_max is not None:
        query = query.where(OhlcvData.volume <= volume_max)
        count_query = count_query.where(OhlcvData.volume <= volume_max)
    
    sort_column = getattr(OhlcvData, sort_by or "date")
    query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return PaginatedResponse(
        data=data,  # type: ignore[arg-type]
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


@app.get("/ohlcv/latest/", response_model=BatchLatestResponse)
async def get_batch_latest_ohlcv(
    tickers: Optional[str] = Query(None, description="Comma-separated tickers (e.g., AAPL,MSFT,GOOGL). If omitted, returns latest for all tickers."),
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    ticker_list = parse_comma_separated(tickers)

    # LATERAL join approach: ~50-100ms vs 30s+ with GROUP BY/MAX subquery.
    # Each LATERAL does a single Index Scan Backward on
    # ohlcv_data_ticker_date_key to fetch the latest row per ticker.
    if ticker_list:
        # Specific tickers: use a VALUES list as the driving row source
        ticker_values = ", ".join(f"('{t}')" for t in ticker_list)
        query = text(f"""
            SELECT t.ticker, o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume, o.asset_isin,
                   o.created_at, o.updated_at
            FROM (VALUES {ticker_values}) AS t(ticker)
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close,
                       volume, asset_isin, created_at, updated_at
                FROM ohlcv_data
                WHERE ticker = t.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            ORDER BY t.ticker ASC
        """)
    else:
        # All tickers: LATERAL join driven by the tickers lookup table.
        # ~313ms for 12.5K tickers vs ~10.4s with SELECT DISTINCT subquery
        # (which scans 43M index entries) vs 51-56s with DISTINCT ON.
        # The tickers table (kept in sync via trigger) provides an
        # Index Only Scan (5ms) as the driving row source, and each
        # LATERAL does a single Index Scan Backward on
        # ohlcv_data_ticker_date_key to fetch the latest row per ticker.
        query = text("""
            SELECT d.ticker, o.id, o.date, o.open, o.high, o.low, o.close,
                   o.adjusted_close, o.volume, o.asset_isin,
                   o.created_at, o.updated_at
            FROM tickers d
            CROSS JOIN LATERAL (
                SELECT id, date, open, high, low, close, adjusted_close,
                       volume, asset_isin, created_at, updated_at
                FROM ohlcv_data
                WHERE ticker = d.ticker
                ORDER BY date DESC
                LIMIT 1
            ) o
            ORDER BY d.ticker ASC
        """)

    result = await db.execute(query)
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
            asset_isin=row.asset_isin,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
        for row in rows
    ]

    return BatchLatestResponse(
        data=items,
        count=len(items)
    )


@app.get("/ohlcv/latest/{ticker}", response_model=OhlcvDataResponse)
async def get_latest_ohlcv(ticker: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvData).where(
        OhlcvData.ticker == ticker.upper()
    ).order_by(OhlcvData.date.desc()).limit(1)
    
    result = await db.execute(query)
    ohlcv = result.scalar_one_or_none()
    
    if not ohlcv:
        raise HTTPException(status_code=404, detail=f"No OHLCV data found for ticker: {ticker}")
    
    return ohlcv


@app.get("/ohlcv/stats/{ticker}", response_model=OhlcvStatsResponse)
async def get_ohlcv_stats(ticker: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    ticker = ticker.upper()
    
    stats_query = select(
        func.count(OhlcvData.id).label("count"),
        func.min(OhlcvData.date).label("earliest_date"),
        func.max(OhlcvData.date).label("latest_date"),
        func.avg(OhlcvData.volume).label("avg_volume"),
        func.min(OhlcvData.close).label("min_close"),
        func.max(OhlcvData.close).label("max_close"),
        func.avg(OhlcvData.close).label("avg_close")
    ).where(OhlcvData.ticker == ticker)
    
    result = await db.execute(stats_query)
    stats = result.one()
    
    # Access Row fields by index to avoid collision with tuple's .count() method
    stats_count = stats[0]
    if stats_count == 0:
        raise HTTPException(status_code=404, detail=f"No OHLCV data found for ticker: {ticker}")
    
    fifty_two_weeks_ago = date.today() - timedelta(weeks=52)
    fifty_two_week_query = select(
        func.max(OhlcvData.close).label("high"),
        func.min(OhlcvData.close).label("low")
    ).where(
        and_(
            OhlcvData.ticker == ticker,
            OhlcvData.date >= fifty_two_weeks_ago
        )
    )
    
    fw_result = await db.execute(fifty_two_week_query)
    fw_stats = fw_result.one()
    
    return OhlcvStatsResponse(
        ticker=ticker,
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


@app.get("/tickers/", response_model=List[str])
async def get_all_tickers(db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    # Uses the tickers lookup table (kept in sync via trigger) instead of
    # SELECT DISTINCT on ohlcv_data (43M rows) — ~5ms vs ~8.6s.
    query = text("SELECT ticker FROM tickers ORDER BY ticker ASC")
    result = await db.execute(query)
    return [row[0] for row in result.all()]


@app.get("/ohlcv/{ohlcv_id}", response_model=OhlcvDataResponse)
async def get_ohlcv_by_id(ohlcv_id: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvData).where(OhlcvData.id == ohlcv_id)
    result = await db.execute(query)
    ohlcv = result.scalar_one_or_none()
    if not ohlcv:
        raise HTTPException(status_code=404, detail="OHLCV data not found")
    return ohlcv


@app.post("/ohlcv/", response_model=OhlcvDataResponse, status_code=201)
async def create_ohlcv_data(ohlcv: OhlcvDataCreate, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    db_ohlcv = OhlcvData(**ohlcv.model_dump())
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
            db_ohlcv = OhlcvData(**record.model_dump())
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


@app.put("/ohlcv/{ohlcv_id}", response_model=OhlcvDataResponse)
async def update_ohlcv_data(
    ohlcv_id: str,
    ohlcv: OhlcvDataUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    query = select(OhlcvData).where(OhlcvData.id == ohlcv_id)
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


@app.delete("/ohlcv/{ohlcv_id}", status_code=204)
async def delete_ohlcv_data(ohlcv_id: str, db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvData).where(OhlcvData.id == ohlcv_id)
    result = await db.execute(query)
    db_ohlcv = result.scalar_one_or_none()
    
    if not db_ohlcv:
        raise HTTPException(status_code=404, detail="OHLCV data not found")
    
    await db.delete(db_ohlcv)
    await db.commit()
    return None


# ── S&P 500 Endpoints ────────────────────────────────────────────────────────

@app.get("/sp500/", response_model=SP500ListResponse)
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

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

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


@app.get("/sp500/latest/", response_model=SP500LatestResponse)
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


@app.get("/sp500/history/", response_model=SP500HistoryResponse)
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

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

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

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

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

@app.get("/aliases/", response_model=TickerAliasListResponse)
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


@app.get("/aliases/{sp500_ticker}", response_model=TickerAliasResponse)
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


@app.post("/aliases/", response_model=TickerAliasResponse, status_code=201)
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


@app.put("/aliases/{sp500_ticker}", response_model=TickerAliasResponse)
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


@app.delete("/aliases/{sp500_ticker}", status_code=204)
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


# ── SQL Query Endpoint ───────────────────────────────────────────────────────

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
    "ohlcv_data", "assets", "sp500_constituents", "ticker_aliases", "tickers",
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
         `ohlcv_data`, `assets`, `sp500_constituents`, `ticker_aliases`, `tickers`.
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
