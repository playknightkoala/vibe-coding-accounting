from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'debit', 'credit', or 'installment'
    category = Column(String)
    note = Column(String, nullable=True)
    foreign_amount = Column(Float, nullable=True)
    foreign_currency = Column(String, nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    # Installment specific fields
    is_installment = Column(Boolean, default=False, nullable=False)
    installment_group_id = Column(String, nullable=True, index=True)  # UUID to group installments
    installment_number = Column(Integer, nullable=True)  # Current installment (1, 2, 3...)
    total_installments = Column(Integer, nullable=True)  # Total number of installments
    total_amount = Column(Float, nullable=True)  # Total original amount before splitting
    remaining_amount = Column(Float, nullable=True)  # Remaining amount to be paid
    exclude_from_budget = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("Account", back_populates="transactions")
