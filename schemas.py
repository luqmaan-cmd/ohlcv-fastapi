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


# SQL Query Schemas

class SqlQueryRequest(BaseModel):
    """Request body for the read-only SQL query endpoint."""
    query: str = Field(..., min_length=1, description="SQL SELECT query to execute")


class SqlQueryResponse(BaseModel):
    """Response for the read-only SQL query endpoint."""
    columns: List[str] = Field(..., description="Column names in the result set")
    rows: List[dict] = Field(..., description="Result rows as list of dicts")
    row_count: int = Field(..., description="Number of rows returned")
    truncated: bool = Field(
        default=False,
        description="True if the result was truncated due to the row limit"
    )


# ── ETF / Index Schemas ──────────────────────────────────────────────────────

class EtfIndexOhlcvResponse(BaseModel):
    """Single OHLCV record from ohlcv_data_etf_index (no asset_isin column)."""
    id: UUID
    ticker: str
    date: date_type
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EtfIndexPaginatedResponse(BaseModel):
    """Paginated list of ETF/Index OHLCV records."""
    data: List[EtfIndexOhlcvResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class EtfIndexAssetResponse(BaseModel):
    """Metadata for an ETF or Index asset from etf_index_assets."""
    code: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    isin: Optional[str] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True


class EtfIndexLatestItem(BaseModel):
    """Single ETF/Index with latest OHLCV data, enriched with asset metadata."""
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    isin: Optional[str] = None
    currency: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class EtfIndexLatestResponse(BaseModel):
    """Latest OHLCV for ETFs or Indices."""
    data: List[EtfIndexLatestItem]
    count: int


# ── Government Bond Schemas ──────────────────────────────────────────────────

class GovBondOhlcvResponse(BaseModel):
    """Single OHLCV record from ohlcv_data_gov_bonds (no asset_isin column)."""
    id: UUID
    ticker: str
    date: date_type
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GovBondPaginatedResponse(BaseModel):
    """Paginated list of government bond OHLCV records."""
    data: List[GovBondOhlcvResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class GovBondLatestItem(BaseModel):
    """Single government bond with latest OHLCV data, enriched with asset metadata."""
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class GovBondLatestResponse(BaseModel):
    """Latest OHLCV for government bonds."""
    data: List[GovBondLatestItem]
    count: int


# ── US Treasury Bill Rate Schemas ────────────────────────────────────────────

class UstBillRateResponse(BaseModel):
    """Single US Treasury bill rate record."""
    id: UUID
    date: date_type
    tenor: str
    discount: Optional[Decimal] = None
    coupon: Optional[Decimal] = None
    avg_discount: Optional[Decimal] = None
    avg_coupon: Optional[Decimal] = None
    maturity_date: Optional[date_type] = None
    cusip: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UstBillPaginatedResponse(BaseModel):
    """Paginated list of US Treasury bill rate records."""
    data: List[UstBillRateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UstBillLatestItem(BaseModel):
    """Latest US Treasury bill rate for a single tenor."""
    tenor: str
    date: Optional[date_type] = None
    discount: Optional[Decimal] = None
    coupon: Optional[Decimal] = None
    avg_discount: Optional[Decimal] = None
    avg_coupon: Optional[Decimal] = None
    maturity_date: Optional[date_type] = None
    cusip: Optional[str] = None


class UstBillLatestResponse(BaseModel):
    """Latest US Treasury bill rates for all tenors."""
    data: List[UstBillLatestItem]
    count: int


# ── US Treasury Long-Term Rate Schemas ──────────────────────────────────────

class UstLongTermRateResponse(BaseModel):
    """Single US Treasury long-term rate record."""
    id: UUID
    date: date_type
    rate_type: str
    rate: Optional[Decimal] = None
    extrapolation_factor: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UstLongTermPaginatedResponse(BaseModel):
    """Paginated list of US Treasury long-term rate records."""
    data: List[UstLongTermRateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UstLongTermLatestItem(BaseModel):
    """Latest US Treasury long-term rate for a single rate type."""
    rate_type: str
    date: Optional[date_type] = None
    rate: Optional[Decimal] = None
    extrapolation_factor: Optional[Decimal] = None


class UstLongTermLatestResponse(BaseModel):
    """Latest US Treasury long-term rates for all rate types."""
    data: List[UstLongTermLatestItem]
    count: int


# ── US Treasury Real Yield Rate Schemas ─────────────────────────────────────

class UstRealYieldRateResponse(BaseModel):
    """Single US Treasury real yield rate record."""
    id: UUID
    date: date_type
    tenor: str
    rate: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UstRealYieldPaginatedResponse(BaseModel):
    """Paginated list of US Treasury real yield rate records."""
    data: List[UstRealYieldRateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UstRealYieldLatestItem(BaseModel):
    """Latest US Treasury real yield rate for a single tenor."""
    tenor: str
    date: Optional[date_type] = None
    rate: Optional[Decimal] = None


class UstRealYieldLatestResponse(BaseModel):
    """Latest US Treasury real yield rates for all tenors."""
    data: List[UstRealYieldLatestItem]
    count: int


# ── US Treasury Yield Rate Schemas ──────────────────────────────────────────

class UstYieldRateResponse(BaseModel):
    """Single US Treasury yield rate record."""
    id: UUID
    date: date_type
    tenor: str
    rate: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UstYieldPaginatedResponse(BaseModel):
    """Paginated list of US Treasury yield rate records."""
    data: List[UstYieldRateResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UstYieldLatestItem(BaseModel):
    """Latest US Treasury yield rate for a single tenor."""
    tenor: str
    date: Optional[date_type] = None
    rate: Optional[Decimal] = None


class UstYieldLatestResponse(BaseModel):
    """Latest US Treasury yield rates for all tenors."""
    data: List[UstYieldLatestItem]
    count: int


# ── Foreign Exchange (FX) Schemas ─────────────────────────────────────────────

class FxOhlcvResponse(BaseModel):
    """Single OHLCV record from ohlcv_data_fx (no asset_isin column)."""
    id: UUID
    ticker: str
    date: date_type
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FxPaginatedResponse(BaseModel):
    """Paginated list of FX OHLCV records."""
    data: List[FxOhlcvResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class FxLatestItem(BaseModel):
    """Single FX pair with latest OHLCV data, enriched with asset metadata."""
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    currency: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class FxLatestResponse(BaseModel):
    """Latest OHLCV for FX pairs."""
    data: List[FxLatestItem]
    count: int


# ── UK Stock (LSE) Schemas ──────────────────────────────────────────────

class UkOhlcvResponse(BaseModel):
    """Single OHLCV record from ohlcv_data_uk (no asset_isin column)."""
    id: UUID
    ticker: str
    date: date_type
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UkPaginatedResponse(BaseModel):
    """Paginated list of UK stock OHLCV records."""
    data: List[UkOhlcvResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UkLatestItem(BaseModel):
    """Single UK stock with latest OHLCV data, enriched with asset metadata."""
    ticker: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    type: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    currency: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class UkLatestResponse(BaseModel):
    """Latest OHLCV for UK stocks (LSE)."""
    data: List[UkLatestItem]
    count: int


# ── FTSE 100 Schemas ──────────────────────────────────────────────────────

class Ftse100LatestItem(BaseModel):
    """Single FTSE 100 constituent with latest OHLCV data, enriched with metadata."""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    currency: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class Ftse100LatestResponse(BaseModel):
    """Latest OHLCV for FTSE 100 constituents."""
    data: List[Ftse100LatestItem]
    count: int


class Ftse100HistoryItem(BaseModel):
    """Single OHLCV record for a FTSE 100 constituent, enriched with metadata."""
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    isin: Optional[str] = None
    currency: Optional[str] = None
    date: Optional[date_type] = None
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adjusted_close: Optional[Decimal] = None
    volume: Optional[int] = None


class Ftse100PaginatedResponse(BaseModel):
    """Paginated historical OHLCV for FTSE 100 constituents."""
    data: List[Ftse100HistoryItem]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
