from pydantic import BaseModel, EmailStr, validator
import re


class PasswordResetRequest(BaseModel):
    """請求密碼重設"""
    email: EmailStr
    turnstile_token: str | None = None


class PasswordResetConfirm(BaseModel):
    """確認密碼重設"""
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        """驗證密碼強度"""
        if len(v) < 8:
            raise ValueError('密碼至少需要 8 個字元')
        if not re.search(r'[A-Z]', v):
            raise ValueError('密碼必須包含至少一個大寫字母')
        if not re.search(r'[a-z]', v):
            raise ValueError('密碼必須包含至少一個小寫字母')
        if not re.search(r'[0-9]', v):
            raise ValueError('密碼必須包含至少一個數字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密碼必須包含至少一個特殊字元 (!@#$%^&*(),.?":{}|<>)')
        return v


class PasswordResetResponse(BaseModel):
    """密碼重設回應"""
    message: str
