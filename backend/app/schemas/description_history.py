from pydantic import BaseModel
from datetime import datetime
from typing import List


class DescriptionHistoryBase(BaseModel):
    description: str


class DescriptionHistoryCreate(DescriptionHistoryBase):
    pass


class DescriptionHistoryUpdate(BaseModel):
    last_used_at: datetime


class DescriptionHistory(DescriptionHistoryBase):
    id: int
    user_id: int
    last_used_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DescriptionHistoryList(BaseModel):
    """返回敘述列表，按照 last_used_at 排序"""
    descriptions: List[str]
