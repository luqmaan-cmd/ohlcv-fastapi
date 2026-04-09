from fastapi import FastAPI, Depends, HTTPException, Query, Security
from fastapi.security import APIKeyQuery
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import text
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
import os
import math

from database import get_db
from models import OhlcvData
from schemas import (
    OhlcvDataCreate, OhlcvDataUpdate, OhlcvDataResponse,
    OhlcvDataBulkCreate, PaginatedResponse, OhlcvStatsResponse,
    BulkInsertResponse
)

API_KEY = os.getenv("API_KEY", "ohlcv-api-key-2024-secure")

api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_query)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

app = FastAPI(title="OHLCV Data API", version="1.0.0")
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
    per_page: int = Query(100, ge=1, le=1000),
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
    total = total_result.scalar()
    
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
    
    if stats.count == 0:
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
        count=stats.count,
        earliest_date=stats.earliest_date,
        latest_date=stats.latest_date,
        avg_volume=float(stats.avg_volume) if stats.avg_volume else None,
        min_close=stats.min_close,
        max_close=stats.max_close,
        avg_close=stats.avg_close,
        fifty_two_week_high=fw_stats.high,
        fifty_two_week_low=fw_stats.low
    )


@app.get("/tickers/", response_model=List[str])
async def get_all_tickers(db: AsyncSession = Depends(get_db), api_key: str = Depends(verify_api_key)):
    query = select(OhlcvData.ticker).distinct().order_by(OhlcvData.ticker)
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
