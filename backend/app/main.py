from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import engine, Base
from app.core.config import settings
from app.api import auth, accounts, transactions, budgets, users, categories, reports, description_history, exchange_rates, password_reset, google_auth, admin, recurring_expenses
from app.core.scheduler import start_scheduler, stop_scheduler, run_bot_crawler_job, run_esun_crawler_job, run_recurring_expense_job
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import threading
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables from SQLAlchemy models
# This will create all tables defined in models if they don't exist
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler
    start_scheduler()

    # Run BOT crawler immediately on startup to ensure we have data
    threading.Thread(target=run_bot_crawler_job, daemon=True).start()
    # E.SUN crawler will run on schedule (hourly)

    # Send startup notification email
    print(f"DEBUG: Startup emails list: {settings.startup_notification_emails_list}", file=sys.stderr)
    if settings.startup_notification_emails_list:
        from app.core.email import send_email
        
        def send_startup_email():
            print("DEBUG: Attempting to send startup email...", file=sys.stderr)
            try:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                env_name = settings.ENVIRONMENT.upper()
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;
                            color: #e0e0e0;
                            background-color: #1a1a2e;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 40px auto;
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            border-radius: 12px;
                            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
                            overflow: hidden;
                        }}
                        .header {{
                            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
                            padding: 40px 20px;
                            text-align: center;
                            border-bottom: 2px solid #00d4ff;
                        }}
                        .header h1 {{
                            color: #00d4ff;
                            margin: 0;
                            font-size: 28px;
                            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
                        }}
                        .content {{
                            padding: 40px 30px;
                        }}
                        .content p {{
                            margin: 0 0 20px;
                            color: #a0aec0;
                        }}
                        .info-box {{
                            background-color: rgba(0, 212, 255, 0.1);
                            border-left: 4px solid #00d4ff;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 4px;
                        }}
                        .footer {{
                            background-color: #0f3460;
                            padding: 20px;
                            text-align: center;
                            color: #6b7280;
                            font-size: 14px;
                            border-top: 1px solid #00d4ff;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🚀 系統啟動通知</h1>
                        </div>
                        <div class="content">
                            <p>管理員您好，</p>
                            <p>Accounting System 後端服務已經重新啟動。</p>

                            <div class="info-box">
                                <p style="margin: 0;"><strong>📌 啟動資訊：</strong></p>
                                <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #a0aec0;">
                                    <li><strong>環境：</strong> {env_name}</li>
                                    <li><strong>時間：</strong> {current_time}</li>
                                </ul>
                            </div>
                            
                            <p>系統目前運作正常。</p>
                        </div>
                        <div class="footer">
                            <p style="margin: 0;">© 2025 Accounting System. All rights reserved.</p>
                            <p style="margin: 5px 0 0 0;">此為系統自動發送的通知。</p>
                        </div>
                    </div>
                </body>
                </html>
                """

                result = send_email(
                    to_email=settings.startup_notification_emails_list,
                    subject=f"[{env_name}] 系統啟動通知 - Accounting System",
                    html_content=html_content
                )
                print(f"DEBUG: Email send result: {result}", file=sys.stderr)
            except Exception as e:
                print(f"Failed to send startup email: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc(file=sys.stderr)

        threading.Thread(target=send_startup_email, daemon=True).start()

    yield
    # Stop scheduler
    stop_scheduler()

app = FastAPI(
    title="Accounting API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True, rate_limit: int = 60):
        super().__init__(app)
        self.enabled = enabled
        self.rate_limit = rate_limit
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Clean old requests
        now = datetime.now()
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < timedelta(minutes=1)
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.rate_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

        # Add current request
        self.requests[client_ip].append(now)

        response = await call_next(request)
        return response

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if settings.ENABLE_SECURITY_HEADERS:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://challenges.cloudflare.com https://cloudflareinsights.com; frame-src 'self' https://challenges.cloudflare.com"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            # response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# ...

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add ProxyHeadersMiddleware to trust X-Forwarded-Proto from Nginx/Synology
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Add SessionMiddleware for OAuth
# IMPORTANT: max_age=3600 (1 hour) ensures sessions persist during OAuth flow
# same_site="lax" allows cookies to work with OAuth redirects
# https_only should be True in production (Synology handles HTTPS)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,  # 1 hour session lifetime
    same_site="lax",  # Allow OAuth redirects
    https_only=settings.ENVIRONMENT == "production"  # HTTPS cookies in production
)

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.RATE_LIMIT_ENABLED,
        rate_limit=settings.RATE_LIMIT_PER_MINUTE
    )

# CORS middleware - use dynamic origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(google_auth.router, prefix="/api", tags=["google-auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(description_history.router, prefix="/api/description-history", tags=["description-history"])
app.include_router(exchange_rates.router, prefix="/api/exchange-rates", tags=["exchange-rates"])
app.include_router(password_reset.router, prefix="/api/password-reset", tags=["password-reset"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(recurring_expenses.router, prefix="/api/recurring-expenses", tags=["recurring-expenses"])

@app.get("/")
def root():
    return {"message": "Accounting API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
