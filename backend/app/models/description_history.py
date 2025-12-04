from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.encryption import encrypt_field, decrypt_field


class DescriptionHistory(Base):
    """交易敘述歷史記錄表"""
    __tablename__ = "description_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    _description = Column("description", String, nullable=False, index=True)  # 加密儲存
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @hybrid_property
    def description(self):
        """解密 description"""
        return decrypt_field(self._description)

    @description.setter
    def description(self, value):
        """加密 description"""
        self._description = encrypt_field(value)
