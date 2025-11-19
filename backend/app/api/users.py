from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate, TwoFactorSetup, TwoFactorVerify
import pyotp
import qrcode
import io
import base64

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def get_user_profile(current_user: User = Depends(get_current_user)):
    """取得目前使用者資訊"""
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新使用者資訊（密碼）"""
    if user_update.new_password:
        if not user_update.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必須提供目前密碼才能變更密碼"
            )

        # 驗證目前密碼
        if not verify_password(user_update.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="目前密碼不正確"
            )

        # 更新密碼
        current_user.hashed_password = get_password_hash(user_update.new_password)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/2fa/setup", response_model=TwoFactorSetup)
def setup_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """設定 2FA（生成 QR code）"""
    # 生成新的 secret
    secret = pyotp.random_base32()

    # 暫時儲存 secret（等待驗證）
    current_user.two_factor_secret = secret
    db.commit()

    # 生成 TOTP URI
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(
        name=current_user.username,
        issuer_name="Accounting App"
    )

    # 生成 QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return TwoFactorSetup(
        secret=secret,
        qr_code=f"data:image/png;base64,{qr_code_base64}"
    )

@router.post("/me/2fa/verify")
def verify_two_factor(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """驗證並啟用 2FA"""
    if not current_user.two_factor_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請先設定 2FA"
        )

    # 驗證 TOTP token
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verification.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證碼錯誤"
        )

    # 啟用 2FA
    current_user.two_factor_enabled = True
    db.commit()

    return {"message": "2FA 已成功啟用"}

@router.post("/me/2fa/disable")
def disable_two_factor(
    verification: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停用 2FA"""
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 尚未啟用"
        )

    # 驗證 TOTP token
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(verification.token, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="驗證碼錯誤"
        )

    # 停用 2FA
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.commit()

    return {"message": "2FA 已停用"}
