from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class BudgetBase(BaseModel):
    name: str
    category: str
    amount: float
    daily_limit: Optional[float] = None
    period: str
    start_date: datetime
    end_date: datetime
    account_id: int

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    daily_limit: Optional[float] = None
    spent: Optional[float] = None
    period: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    account_id: Optional[int] = None

class Budget(BudgetBase):
    id: int
    spent: float
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
