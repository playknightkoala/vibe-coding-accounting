from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from app.core.database import engine, Base
from app.core.config import settings
from app.api import auth, accounts, transactions, budgets, users, categories, reports, description_history, exchange_rates, password_reset, google_auth
from app.core.scheduler import start_scheduler, stop_scheduler, run_crawler_job
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import threading

# Create database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler
    start_scheduler()
    
    # Run crawler immediately on startup to ensure we have data
    threading.Thread(target=run_crawler_job, daemon=True).start()
    
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
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

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

@app.get("/")
def root():
    return {"message": "Accounting API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
