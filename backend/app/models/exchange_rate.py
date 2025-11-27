from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    bank = Column(String, nullable=False, default='bot', index=True)  # bot: 臺灣銀行, esun: 玉山銀行
    currency_code = Column(String, index=True, nullable=False)
    currency_name = Column(String, nullable=False)
    buying_rate = Column(Float, nullable=True)
    selling_rate = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 每個銀行的每種幣別只能有一筆記錄
    __table_args__ = (
        UniqueConstraint('bank', 'currency_code', name='uix_bank_currency'),
    )
