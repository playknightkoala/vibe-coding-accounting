from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Dict

class TransactionBase(BaseModel):
    description: str
    amount: float
    transaction_type: str
    category: Optional[str] = None
    note: Optional[str] = None
    transaction_date: datetime

class TransactionCreate(TransactionBase):
    account_id: int

class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    note: Optional[str] = None
    transaction_date: Optional[datetime] = None

class Transaction(TransactionBase):
    id: int
    account_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DailyStats(BaseModel):
    date: str
    credit: float
    debit: float

class MonthlyStats(BaseModel):
    daily_stats: List[DailyStats]
