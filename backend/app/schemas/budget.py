from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional, List

class BudgetBase(BaseModel):
    name: str
    category_names: List[str] = []  # 改為類別名稱列表，空列表表示「全部」
    amount: float
    daily_limit: Optional[float] = None
    daily_limit_mode: str = 'manual'  # 'auto' (系統自動計算) or 'manual' (手動填寫)
    range_mode: str  # 'custom' or 'recurring'
    period: Optional[str] = None  # 'monthly', 'quarterly', 'yearly' (僅在 recurring 時需要)
    start_date: Optional[datetime] = None  # recurring 模式可為空，由系統自動計算
    end_date: Optional[datetime] = None    # recurring 模式可為空，由系統自動計算
    account_ids: List[int] = []  # 改為帳戶ID列表，空列表表示不綁定帳戶

    @field_validator('range_mode')
    @classmethod
    def validate_range_mode(cls, v):
        if v not in ['custom', 'recurring']:
            raise ValueError('range_mode must be either "custom" or "recurring"')
        return v

    @field_validator('period')
    @classmethod
    def validate_period(cls, v, info):
        if info.data.get('range_mode') == 'recurring' and v not in ['monthly', 'quarterly', 'yearly']:
            raise ValueError('period must be "monthly", "quarterly", or "yearly" when range_mode is "recurring"')
        return v

    @field_validator('daily_limit_mode')
    @classmethod
    def validate_daily_limit_mode(cls, v):
        if v not in ['auto', 'manual']:
            raise ValueError('daily_limit_mode must be either "auto" or "manual"')
        return v

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    category_names: Optional[List[str]] = None  # 改為類別名稱列表
    amount: Optional[float] = None
    daily_limit: Optional[float] = None
    daily_limit_mode: Optional[str] = None
    spent: Optional[float] = None
    range_mode: Optional[str] = None
    period: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    account_ids: Optional[List[int]] = None  # 改為帳戶ID列表

class Budget(BaseModel):
    id: int
    name: str
    category_names: List[str] = []  # 改為類別名稱列表
    amount: float
    daily_limit: Optional[float] = None
    daily_limit_mode: str = 'manual'
    spent: float
    range_mode: str
    period: Optional[str] = None
    start_date: datetime
    end_date: datetime
    account_ids: List[int] = []  # 改為帳戶ID列表
    user_id: int
    parent_budget_id: Optional[int] = None
    is_latest_period: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
