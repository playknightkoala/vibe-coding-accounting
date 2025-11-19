from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AccountBase(BaseModel):
    name: str
    account_type: str
    currency: str = "USD"
    description: Optional[str] = None

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Account(AccountBase):
    id: int
    balance: float
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
