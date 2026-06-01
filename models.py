from sqlalchemy import Column, String, Date, Numeric, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base


class OhlcvData(Base):
    __tablename__ = "ohlcv_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    asset_isin = Column(String(50), ForeignKey("assets.isin"))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Asset(Base):
    __tablename__ = "assets"

    isin = Column(String, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String)
    gic_sector = Column("gicSector", String)
    description = Column(String)
    country_name = Column("countryName", String)


class SP500Constituent(Base):
    __tablename__ = "sp500_constituents"

    code = Column(String(20), primary_key=True)
    name = Column(String(255))
    exchange = Column(String(10))
    sector = Column(String(100))
    industry = Column(String(255))
    weight = Column(Numeric(10, 6))
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime)


class TickerAlias(Base):
    __tablename__ = "ticker_aliases"

    sp500_ticker = Column(String(20), primary_key=True)
    ohlcv_ticker = Column(String(20), nullable=False)


class Ticker(Base):
    __tablename__ = "tickers"

    ticker = Column(String(20), primary_key=True)


class EtfIndexOhlcvData(Base):
    __tablename__ = "ohlcv_data_etf_index"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class EtfIndexAsset(Base):
    __tablename__ = "etf_index_assets"

    code = Column(String, primary_key=True)
    name = Column(String)
    exchange = Column(String, nullable=False)
    type = Column(String, nullable=False)
    isin = Column(String)
    currency = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GovBondOhlcvData(Base):
    __tablename__ = "ohlcv_data_gov_bonds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class GovBondAsset(Base):
    __tablename__ = "gov_bond_assets"

    code = Column(String(50), primary_key=True)
    name = Column(String(500))
    exchange = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    currency = Column(String(10))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    country = Column(String(10))


class UstBillRate(Base):
    __tablename__ = "ust_bill_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    tenor = Column(String(10), nullable=False)
    discount = Column(Numeric(18, 6))
    coupon = Column(Numeric(18, 6))
    avg_discount = Column(Numeric(18, 6))
    avg_coupon = Column(Numeric(18, 6))
    maturity_date = Column(Date)
    cusip = Column(String(20))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UstLongTermRate(Base):
    __tablename__ = "ust_long_term_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    rate_type = Column(String(30), nullable=False)
    rate = Column(Numeric(18, 6))
    extrapolation_factor = Column(Numeric(18, 6))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UstRealYieldRate(Base):
    __tablename__ = "ust_real_yield_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    tenor = Column(String(10), nullable=False)
    rate = Column(Numeric(18, 6))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UstYieldRate(Base):
    __tablename__ = "ust_yield_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    tenor = Column(String(10), nullable=False)
    rate = Column(Numeric(18, 6))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class FxOhlcvData(Base):
    __tablename__ = "ohlcv_data_fx"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), ForeignKey("fx_assets.code", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class FxAsset(Base):
    __tablename__ = "fx_assets"

    code = Column(String(20), primary_key=True)
    name = Column(String)
    exchange = Column(String, nullable=False)
    base_currency = Column(String(3))
    quote_currency = Column(String(3))
    type = Column(String)
    currency = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
