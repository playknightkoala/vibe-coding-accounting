from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.timezone import get_taipei_now
from app.models.user import User
from app.models.account import Account
from app.schemas.user import Token
import secrets

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for('auth_google_callback')
    # Force HTTPS in production or if behind a proxy that terminates SSL
    if settings.ENVIRONMENT == "production" or "yshongcode.com" in str(redirect_uri):
        redirect_uri = str(redirect_uri).replace("http://", "https://")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback", name="auth_google_callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    # Check if user cancelled the OAuth flow or other OAuth errors occurred
    if request.query_params.get('error'):
        error = request.query_params.get('error')
        error_description = request.query_params.get('error_description', '')
        frontend_url = settings.FRONTEND_URL or "http://localhost:5173"

        # Map OAuth 2.0 error codes to user-friendly messages (based on RFC 6749 and Google's implementation)
        error_messages = {
            # Standard OAuth 2.0 errors
            'access_denied': '您已取消 Google 登入授權',
            'invalid_request': '登入請求格式錯誤,請重試',
            'unauthorized_client': '應用程式未獲授權使用此登入方式',
            'unsupported_response_type': '不支援的回應類型',
            'invalid_scope': '請求的權限範圍無效',
            'server_error': 'Google 伺服器發生錯誤,請稍後再試',
            'temporarily_unavailable': 'Google 服務暫時無法使用,請稍後再試',

            # Google-specific errors
            'invalid_client': '應用程式設定錯誤,請聯絡管理員',
            'invalid_grant': '授權碼已過期或無效,請重新登入',
            'redirect_uri_mismatch': '重定向網址不符,請聯絡管理員',
            'unsupported_grant_type': '不支援的授權類型',

            # Additional errors
            'org_internal': '此 Google 帳號僅限組織內部使用',
            'disallowed_useragent': '不支援的瀏覽器或裝置,請使用其他瀏覽器',
            'admin_policy_enforced': '組織政策限制了此登入方式',
            'invalid_token': '無效的授權令牌',
            'token_expired': '授權令牌已過期,請重新登入',
        }

        error_message = error_messages.get(error, f'Google 登入失敗: {error}')

        # If there's a detailed description and it's not a user cancellation, include it
        if error_description and error != 'access_denied':
            error_message = f"{error_message} ({error_description})"

        return RedirectResponse(url=f"{frontend_url}/login?error={error_message}")

    try:
        # Manually construct redirect_uri to match what we sent
        redirect_uri = request.url_for('auth_google_callback')
        if settings.ENVIRONMENT == "production" or "yshongcode.com" in str(redirect_uri):
             redirect_uri = str(redirect_uri).replace("http://", "https://")

        # Update the redirect_uri in the session to match the one we used
        # This is required because Authlib restores it from session, and if we pass it as kwarg
        # it causes a collision in fetch_access_token(**params, **kwargs)
        # The key format is usually '{name}_authorize_redirect_uri'
        # Convert to string for JSON serialization
        request.session['google_authorize_redirect_uri'] = str(redirect_uri)

        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
        error_message = f"Google 登入失敗: {error.description}"
        return RedirectResponse(url=f"{frontend_url}/login?error={error_message}")
    
    user_info = token.get('userinfo')
    if not user_info:
        # Sometimes userinfo is not in the token, fetch it manually
        user_info = await oauth.google.userinfo(token=token)
        
    email = user_info.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google account")
        
    # Check if user exists
    user = db.query(User).filter(User.username == email).first()

    if not user:
        # 檢查是否是被封鎖的 email
        blocked_user = db.query(User).filter(
            User.username == email,
            User.is_blocked == True
        ).first()
        if blocked_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此電子郵件已被封鎖,無法登入"
            )

        # Create new user
        user = User(
            username=email,
            hashed_password=None, # No password for OAuth users
            is_google_user=True,
            two_factor_enabled=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create default accounts
        default_accounts = [
            Account(
                name="現金",
                account_type="cash",
                currency="TWD",
                description="預設現金帳戶",
                balance=0.0,
                user_id=user.id
            ),
            Account(
                name="預設銀行",
                account_type="bank",
                currency="TWD",
                description="預設銀行帳戶",
                balance=0.0,
                user_id=user.id
            )
        ]
        for account in default_accounts:
            db.add(account)
        db.commit()
    else:
        # 檢查現有使用者是否被封鎖
        if user.is_blocked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此帳號已被封鎖,無法登入"
            )

    # 更新最後登入時間
    user.last_login_at = get_taipei_now()
    db.commit()

    # Generate JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    # Redirect to frontend with token
    # In production, this should be a secure cookie or a temporary code exchange
    # For simplicity, we'll redirect with the token in the URL fragment
    frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
    return RedirectResponse(url=f"{frontend_url}/google-callback?token={access_token}")

from fastapi.responses import RedirectResponse
