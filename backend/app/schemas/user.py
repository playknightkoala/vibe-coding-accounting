from pydantic import BaseModel, field_validator, field_serializer, EmailStr, computed_field, Field, AliasChoices
from datetime import datetime
from typing import Optional
import re

class UserBase(BaseModel):
    email: EmailStr = Field(validation_alias=AliasChoices('email', 'username'))

class UserCreate(UserBase):
    password: str
    turnstile_token: str | None = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密碼長度至少需要 8 個字元')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密碼必須包含至少一個數字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密碼必須包含至少一個特殊字元 (!@#$%^&*(),.?":{}|<>)')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr = Field(validation_alias=AliasChoices('email', 'username'))
    is_google_user: bool = False
    two_factor_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class UserUpdate(BaseModel):
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('密碼長度至少需要 8 個字元')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密碼必須包含至少一個數字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密碼必須包含至少一個特殊字元 (!@#$%^&*(),.?":{}|<>)')
        return v

class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str

class TwoFactorVerify(BaseModel):
    token: str

class TwoFactorLogin(BaseModel):
    email: EmailStr
    password: str
    token: str

class Token(BaseModel):
    access_token: str
    token_type: str
    requires_2fa: bool = False

class TokenData(BaseModel):
    email: Optional[str] = None
