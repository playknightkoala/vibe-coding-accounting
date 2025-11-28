from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class RecurringExpense(Base):
    """固定支出模型 - 每月定期產生的支出"""
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    note = Column(String, nullable=True)

    # 每月的幾號執行 (1-31)
    day_of_month = Column(Integer, nullable=False)

    # 關聯帳戶
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # 固定支出群組 ID (用於識別同一個固定支出的所有交易)
    recurring_group_id = Column(String, nullable=False, index=True, unique=True)

    # 開始日期 (第一次執行的日期)
    start_date = Column(DateTime(timezone=True), nullable=False)

    # 結束日期 (可選，如果為 None 則永久執行)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # 是否啟用
    is_active = Column(Boolean, default=True, nullable=False)

    # 最後執行日期 (記錄上次建立交易的日期)
    last_executed_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("Account", back_populates="recurring_expenses")
