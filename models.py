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

    instrument_id = Column("instrumentId", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    isin = Column(String)
    code = Column(String, nullable=False)
    type = Column(String)
    name = Column(String)
    exchange = Column(String)
    currency_code = Column("currencyCode", String)
    currency_name = Column("currencyName", String)
    currency_symbol = Column("currencySymbol", String)
    country_name = Column("countryName", String)
    country_iso = Column("countryISO", String)
    open_figi = Column("openFigi", String)
    lei = Column(String)
    primary_ticker = Column("primaryTicker", String)
    cusip = Column(String)
    cik = Column(String)
    employer_id_number = Column("employerIdNumber", String)
    fiscal_year_end = Column("fiscalYearEnd", String)
    ipo_date = Column("ipoDate", Date)
    international_domestic = Column("internationalDomestic", String)
    sector = Column(String)
    industry = Column(String)
    gic_sector = Column("gicSector", String)
    gic_group = Column("gicGroup", String)
    gic_industry = Column("gicIndustry", String)
    gic_sub_industry = Column("gicSubIndustry", String)
    home_category = Column("homeCategory", String)
    is_delisted = Column("isDelisted", Boolean)
    description = Column(String)
    address = Column(String)
    address_street = Column("addressStreet", String)
    address_city = Column("addressCity", String)
    address_state = Column("addressState", String)
    address_country = Column("addressCountry", String)
    address_zip = Column("addressZip", String)
    phone = Column(String)
    web_url = Column("webURL", String)
    logo_url = Column("logoURL", String)
    full_time_employees = Column("fullTimeEmployees", String)
    updated_at = Column("updatedAt", DateTime)


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


class UkOhlcvData(Base):
    __tablename__ = "ohlcv_data_uk"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), ForeignKey("uk_assets.code", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UkAsset(Base):
    __tablename__ = "uk_assets"

    code = Column(String, primary_key=True)
    name = Column(String)
    exchange = Column(String, nullable=False)
    type = Column(String, nullable=False)
    sector = Column(String)
    industry = Column(String)
    isin = Column(String)
    currency = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Ftse100Constituent(Base):
    __tablename__ = "ftse100_constituents"

    code = Column(String, primary_key=True)
    name = Column(String)
    sector = Column(String)
    industry = Column(String)
    isin = Column(String)
    currency = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class CryptoOhlcvData(Base):
    __tablename__ = "ohlcv_data_crypto"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(50), ForeignKey("crypto_assets.code", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class CryptoAsset(Base):
    __tablename__ = "crypto_assets"

    code = Column(String(50), primary_key=True)
    name = Column(String(500))
    exchange = Column(String(50), nullable=False)
    base_currency = Column(String(50))
    quote_currency = Column(String(50))
    type = Column(String(20), nullable=False)
    currency = Column(String(10))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class OhlcvUnified(Base):
    __tablename__ = "ohlcv_unified"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    asset_type = Column(String(50))
    date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    instrument_id = Column(UUID(as_uuid=True))


class CommodityEOD(Base):
    __tablename__ = "commodities_eod"

    date = Column(Date, primary_key=True)
    symbol = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    adjusted_close = Column(Numeric(18, 4))
    volume = Column(BigInteger)
    category = Column(String(50))
    ingestion_ts = Column(DateTime)
