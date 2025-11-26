from pydantic import BaseModel, field_serializer
from datetime import datetime, date
from typing import Optional, List, Dict
from app.core.timezone import format_for_frontend

class TransactionBase(BaseModel):
    description: str
    amount: float
    transaction_type: str
    category: Optional[str] = None
    note: Optional[str] = None
    foreign_amount: Optional[float] = None
    foreign_currency: Optional[str] = None
    transaction_date: datetime

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    note: Optional[str] = None
    foreign_amount: Optional[float] = None
    foreign_currency: Optional[str] = None
    transaction_date: Optional[datetime] = None

class Transaction(TransactionBase):
    id: int
    account_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_serializer('transaction_date', 'created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """序列化日期時間為台北時間的 ISO 格式字串"""
        return format_for_frontend(dt) if dt else None

    class Config:
        from_attributes = True

class DailyStats(BaseModel):
    date: str
    credit: float
    debit: float

class MonthlyStats(BaseModel):
    daily_stats: List[DailyStats]
