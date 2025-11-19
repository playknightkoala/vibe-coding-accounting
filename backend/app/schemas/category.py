from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None


class Category(CategoryBase):
    id: int
    user_id: int
    order_index: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryOrderUpdate(BaseModel):
    category_id: int
    order_index: int
