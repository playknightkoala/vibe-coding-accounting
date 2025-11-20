from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # 保留 category 欄位用於向後相容，但改為可選
    category = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    daily_limit = Column(Float, nullable=True)
    spent = Column(Float, default=0.0)

    # 週期模式: 'custom' (自訂區間) 或 'recurring' (週期)
    range_mode = Column(String, nullable=False, default='custom')

    # 週期類型: 'monthly', 'quarterly', 'yearly' (僅在 range_mode='recurring' 時有效)
    period = Column(String, nullable=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    # 移除單一帳戶綁定，改用多對多關係
    # account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 週期相關欄位
    parent_budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=True)  # 上一個週期的預算ID
    is_latest_period = Column(Boolean, default=True)  # 是否為最新週期

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="budgets")

    # 多對多關係：預算可以綁定多個帳戶（也可以不綁定）
    accounts = relationship(
        "Account",
        secondary="budget_accounts",
        backref="budgets"
    )

    # 自引用關係: 用於追蹤週期鏈
    parent_budget = relationship("Budget", remote_side=[id], foreign_keys=[parent_budget_id])
