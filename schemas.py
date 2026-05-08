from __future__ import annotations

from pydantic import BaseModel, Field
import datetime as _dt
from datetime import date as date_type, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional, List


class OhlcvDataBase(BaseModel):
    ticker: str
    date: date_type
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    asset_isin: Optional[str] = None


class OhlcvDataCreate(OhlcvDataBase):
    pass


class OhlcvDataBulkCreate(BaseModel):
    records: List[OhlcvDataCreate]


class OhlcvDataUpdate(BaseModel):
    ticker: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    asset_isin: Optional[str] = None


class OhlcvDataResponse(OhlcvDataBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    data: List[OhlcvDataResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class OhlcvStatsResponse(BaseModel):
    ticker: str
    count: int
    earliest_date: Optional[date_type] = None
    latest_date: Optional[date_type] = None
    avg_volume: Optional[float] = None
    min_close: Optional[Decimal] = None
    max_close: Optional[Decimal] = None
    avg_close: Optional[Decimal] = None
    fifty_two_week_high: Optional[Decimal] = None
    fifty_two_week_low: Optional[Decimal] = None


class BatchLatestResponse(BaseModel):
    data: List[OhlcvDataResponse]
    count: int


class BulkInsertResponse(BaseModel):
    inserted: int
    failed: int
    errors: List[str] = Field(default_factory=list)


# S&P 500 Schemas

class SP500ConstituentResponse(BaseModel):
    """Single S&P 500 constituent with metadata from sp500_constituents + assets."""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    weight: Optional[Decimal] = None
    is_active: Optional[bool] = None
    isin: Optional[str] = None
    gic_sector: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None


class SP500ListResponse(BaseModel):
    """Paginated list of S&P 500 constituents."""
    data: List[SP500ConstituentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class SP500LatestItem(BaseModel):
    """Single S&P 500 constituent with latest OHLCV data."""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    weight: Optional[Decimal] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    asset_isin: Optional[str] = None


class SP500LatestResponse(BaseModel):
    """Latest OHLCV for all S&P 500 constituents."""
    data: List[SP500LatestItem]
    count: int


class SP500HistoryItem(BaseModel):
    """Single OHLCV record for an S&P 500 constituent, enriched with metadata."""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    weight: Optional[Decimal] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    asset_isin: Optional[str] = None


class SP500HistoryResponse(BaseModel):
    """Paginated historical OHLCV for S&P 500 constituents."""
    data: List[SP500HistoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Ticker Alias Schemas

class TickerAliasBase(BaseModel):
    sp500_ticker: str
    ohlcv_ticker: str


class TickerAliasCreate(TickerAliasBase):
    pass


class TickerAliasUpdate(BaseModel):
    ohlcv_ticker: str


class TickerAliasResponse(TickerAliasBase):

    class Config:
        from_attributes = True


class TickerAliasListResponse(BaseModel):
    data: List[TickerAliasResponse]
    total: int
