from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.category import Category
from app.schemas.category import (
    Category as CategorySchema,
    CategoryCreate,
    CategoryUpdate,
    CategoryOrderUpdate
)

router = APIRouter()


@router.get("/", response_model=List[CategorySchema])
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得目前使用者的所有類別"""
    categories = db.query(Category).filter(
        Category.user_id == current_user.id
    ).order_by(Category.order_index).all()

    # 如果使用者沒有類別，初始化預設類別
    if not categories:
        default_categories = ["飲食", "交通", "購物", "醫療", "娛樂"]
        for idx, name in enumerate(default_categories):
            category = Category(
                name=name,
                user_id=current_user.id,
                order_index=idx
            )
            db.add(category)
        db.commit()
        categories = db.query(Category).filter(
            Category.user_id == current_user.id
        ).order_by(Category.order_index).all()

    return categories


@router.post("/", response_model=CategorySchema)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新增類別"""
    # 檢查是否已存在相同名稱的類別
    existing = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.name == category_data.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="類別名稱已存在"
        )

    # 取得最大的 order_index
    max_order = db.query(Category).filter(
        Category.user_id == current_user.id
    ).count()

    category = Category(
        name=category_data.name,
        user_id=current_user.id,
        order_index=max_order
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新類別"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="類別不存在"
        )

    # 如果要更新名稱，檢查是否重複
    if category_data.name and category_data.name != category.name:
        existing = db.query(Category).filter(
            Category.user_id == current_user.id,
            Category.name == category_data.name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="類別名稱已存在"
            )
        category.name = category_data.name

    if category_data.order_index is not None:
        category.order_index = category_data.order_index

    db.commit()
    db.refresh(category)
    return category


@router.post("/reorder")
def reorder_categories(
    orders: List[CategoryOrderUpdate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批次更新類別順序"""
    for order_data in orders:
        category = db.query(Category).filter(
            Category.id == order_data.category_id,
            Category.user_id == current_user.id
        ).first()

        if category:
            category.order_index = order_data.order_index

    db.commit()
    return {"message": "類別順序已更新"}


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除類別"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="類別不存在"
        )

    db.delete(category)
    db.commit()
    return {"message": "類別已刪除"}
