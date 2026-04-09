from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from typing import Optional, List


class OhlcvDataBase(BaseModel):
    ticker: str
    date: date
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
    date: Optional[date] = None
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
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None
    avg_volume: Optional[float] = None
    min_close: Optional[Decimal] = None
    max_close: Optional[Decimal] = None
    avg_close: Optional[Decimal] = None
    fifty_two_week_high: Optional[Decimal] = None
    fifty_two_week_low: Optional[Decimal] = None


class BulkInsertResponse(BaseModel):
    inserted: int
    failed: int
    errors: List[str] = Field(default_factory=list)
