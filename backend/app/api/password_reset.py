from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import secrets
import httpx
from app.core.database import get_db
from app.core.security import get_password_hash
from app.core.email import send_password_reset_email
from app.core.config import settings
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.password_reset import (
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)

router = APIRouter()


@router.post("/request", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    請求密碼重設

    - 檢查用戶是否存在
    - 生成重設 token
    - 發送重設郵件
    """
    # 查找用戶（使用 email 作為 username）
    user = db.query(User).filter(User.username == request.email).first()

    # Cloudflare Turnstile Verification
    if request.turnstile_token:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": request.turnstile_token
                }
            )
            result = response.json()
            if not result.get("success"):
                raise HTTPException(status_code=400, detail="Turnstile verification failed")
    elif settings.ENVIRONMENT == "production":
         # In production, require Turnstile
         raise HTTPException(status_code=400, detail="Turnstile token is missing")

    # 安全考量：無論用戶是否存在都返回相同訊息，防止郵箱枚舉攻擊
    if not user:
        return PasswordResetResponse(
            message="如果該郵箱已註冊，您將收到密碼重設郵件"
        )

    # 生成安全的隨機 token
    token = secrets.token_urlsafe(32)

    # 計算過期時間
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    # 建立 token 記錄
    reset_token = PasswordResetToken(
        email=request.email,
        token=token,
        is_used=False,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    # 發送郵件
    email_sent = send_password_reset_email(request.email, token)

    if not email_sent:
        # 如果郵件發送失敗，刪除 token
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法發送郵件，請稍後再試"
        )

    return PasswordResetResponse(
        message="如果該郵箱已註冊，您將收到密碼重設郵件"
    )


@router.post("/confirm", response_model=PasswordResetResponse)
def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    確認密碼重設

    - 驗證 token 有效性
    - 更新用戶密碼
    - 標記 token 為已使用
    """
    # 查找 token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的重設連結"
        )

    # 檢查 token 是否已使用
    if reset_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此重設連結已被使用"
        )

    # 檢查 token 是否過期
    if datetime.now(timezone.utc) > reset_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重設連結已過期，請重新申請"
        )

    # 查找用戶
    user = db.query(User).filter(User.username == reset_token.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )

    # 更新密碼
    user.hashed_password = get_password_hash(request.new_password)
    user.updated_at = datetime.now(timezone.utc)

    # 標記 token 為已使用
    reset_token.is_used = True

    db.commit()

    return PasswordResetResponse(
        message="密碼已成功重設，請使用新密碼登入"
    )


@router.get("/verify-token/{token}")
def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """
    驗證重設 token 是否有效（前端用於檢查連結有效性）

    Returns:
        - valid: bool - token 是否有效
        - message: str - 訊息
    """
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not reset_token:
        return {"valid": False, "message": "無效的重設連結"}

    if reset_token.is_used:
        return {"valid": False, "message": "此重設連結已被使用"}

    if datetime.now(timezone.utc) > reset_token.expires_at:
        return {"valid": False, "message": "重設連結已過期"}

    return {"valid": True, "message": "連結有效"}
