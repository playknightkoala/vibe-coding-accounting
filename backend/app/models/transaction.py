from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.encryption import encrypt_field, decrypt_field

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    _description = Column("description", String, nullable=False)  # 加密儲存
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # 'debit', 'credit', or 'installment'
    category = Column(String)
    _note = Column("note", String, nullable=True)  # 加密儲存

    @hybrid_property
    def description(self):
        """解密 description"""
        return decrypt_field(self._description)

    @description.setter
    def description(self, value):
        """加密 description"""
        self._description = encrypt_field(value)

    @hybrid_property
    def note(self):
        """解密 note"""
        return decrypt_field(self._note)

    @note.setter
    def note(self, value):
        """加密 note"""
        self._note = encrypt_field(value)
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
    annual_interest_rate = Column(Float, nullable=True)  # Annual interest rate (e.g., 2.68 for 2.68%)
    exclude_from_budget = Column(Boolean, default=False, nullable=False)

    # Recurring expense fields
    recurring_group_id = Column(String, nullable=True, index=True)  # Links to RecurringExpense.recurring_group_id
    is_from_recurring = Column(Boolean, default=False, nullable=False)  # True if this transaction was auto-generated from recurring expense

    # Transfer pairing
    transfer_pair_id = Column(String, nullable=True, index=True)  # UUID to link transfer_out and transfer_in

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    account = relationship("Account", back_populates="transactions")
