from sqlalchemy import Column, String, Date, Numeric, BigInteger, DateTime, ForeignKey
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
