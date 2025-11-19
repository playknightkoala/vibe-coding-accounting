from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.api import auth, accounts, transactions, budgets, users, categories

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Accounting API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])

@app.get("/")
def root():
    return {"message": "Accounting API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
