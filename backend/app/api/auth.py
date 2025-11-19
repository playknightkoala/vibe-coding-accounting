from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, User as UserSchema, Token, TwoFactorVerify, TwoFactorLogin
import pyotp

router = APIRouter()

@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        two_factor_enabled=False,
        two_factor_secret=None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 如果啟用了 2FA，返回需要 2FA 驗證的標記
    if user.two_factor_enabled:
        # 創建臨時 token（包含 pending_2fa 標記）
        temp_token = create_access_token(
            data={"sub": user.username, "pending_2fa": True}
        )
        return {"access_token": temp_token, "token_type": "bearer", "requires_2fa": True}

    # 正常登入
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False}

@router.post("/login/2fa/verify", response_model=Token)
def verify_2fa_login(
    login_data: TwoFactorLogin,
    db: Session = Depends(get_db)
):
    """驗證 2FA 並完成登入"""
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.two_factor_enabled or not user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled for this user"
        )

    # 驗證 TOTP token
    totp = pyotp.TOTP(user.two_factor_secret)
    if not totp.verify(login_data.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )

    # 創建正常的 access token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False}

@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_db)):
    return current_user
