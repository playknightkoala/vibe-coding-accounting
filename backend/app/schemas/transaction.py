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
    exclude_from_budget: Optional[bool] = False

class TransactionCreate(TransactionBase):
    account_id: int
    # Installment specific fields
    is_installment: Optional[bool] = False
    total_installments: Optional[int] = None
    billing_day: Optional[int] = None  # Day of month for billing (1-31)
    annual_interest_rate: Optional[float] = None  # Annual interest rate (e.g., 2.68 for 2.68%)

class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    transaction_date: datetime
    description: str
    note: Optional[str] = None

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
    # Installment fields
    is_installment: bool = False
    installment_group_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    total_amount: Optional[float] = None
    remaining_amount: Optional[float] = None
    annual_interest_rate: Optional[float] = None

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
