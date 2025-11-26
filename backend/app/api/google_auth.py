from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
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
    try:
        # Manually construct redirect_uri to match what we sent
        redirect_uri = request.url_for('auth_google_callback')
        if settings.ENVIRONMENT == "production" or "yshongcode.com" in str(redirect_uri):
             redirect_uri = str(redirect_uri).replace("http://", "https://")
             
        token = await oauth.google.authorize_access_token(request, redirect_uri=redirect_uri)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=f"OAuth Error: {error.description}")
    
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
        # Create new user
        user = User(
            username=email,
            hashed_password=None, # No password for OAuth users
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
        
    # Generate JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    # Redirect to frontend with token
    # In production, this should be a secure cookie or a temporary code exchange
    # For simplicity, we'll redirect with the token in the URL fragment
    frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
    return RedirectResponse(url=f"{frontend_url}/google-callback?token={access_token}")

from fastapi.responses import RedirectResponse
