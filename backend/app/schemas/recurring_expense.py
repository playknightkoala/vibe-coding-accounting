from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RecurringExpenseBase(BaseModel):
    """固定支出基礎 schema"""
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    category: Optional[str] = None
    note: Optional[str] = None
    day_of_month: int = Field(..., ge=1, le=31, description="每月執行的日期 (1-31)")
    account_id: int

class RecurringExpenseCreate(RecurringExpenseBase):
    """建立固定支出的 schema"""
    pass

class RecurringExpenseUpdate(BaseModel):
    """更新固定支出的 schema"""
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    note: Optional[str] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None

class RecurringExpense(RecurringExpenseBase):
    """完整的固定支出 schema (包含所有欄位)"""
    id: int
    recurring_group_id: str
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool
    last_executed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
