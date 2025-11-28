from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # 'cash', 'bank', 'credit_card', 'stored_value', 'securities', 'other'
    balance = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    description = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")
    recurring_expenses = relationship("RecurringExpense", back_populates="account", cascade="all, delete-orphan")
