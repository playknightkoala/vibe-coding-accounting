from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    daily_limit = Column(Float, nullable=True)
    spent = Column(Float, default=0.0)
    period = Column(String, nullable=False)  # 'monthly', 'quarterly', 'yearly'
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)  # 綁定帳戶
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="budgets")
    account = relationship("Account")
