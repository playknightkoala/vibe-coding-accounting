from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.api import deps
from app.models.user import User
from app.models.description_history import DescriptionHistory
from app.schemas import description_history as schemas

router = APIRouter()

MAX_DESCRIPTIONS = 100


@router.get("/", response_model=schemas.DescriptionHistoryList)
def get_description_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> schemas.DescriptionHistoryList:
    """
    獲取當前使用者的敘述歷史，按照 last_used_at 降序排列
    """
    histories = db.query(DescriptionHistory).filter(
        DescriptionHistory.user_id == current_user.id
    ).order_by(
        DescriptionHistory.last_used_at.desc()
    ).all()

    descriptions = [h.description for h in histories]
    return schemas.DescriptionHistoryList(descriptions=descriptions)


@router.post("/update")
def update_description_history(
    description: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    更新或新增敘述歷史記錄
    當使用者新增交易時呼叫此 API
    如果敘述已存在，更新 last_used_at
    如果敘述不存在，新增記錄
    如果記錄數超過 100，刪除最舊的記錄
    """
    if not description or description.strip() == "":
        raise HTTPException(status_code=400, detail="敘述不能為空")

    description = description.strip()

    # 檢查是否已存在此敘述
    existing = db.query(DescriptionHistory).filter(
        DescriptionHistory.user_id == current_user.id,
        DescriptionHistory.description == description
    ).first()

    if existing:
        # 更新 last_used_at 讓它排到最前面
        existing.last_used_at = datetime.now(timezone.utc)
        db.commit()
    else:
        # 新增新記錄
        new_history = DescriptionHistory(
            user_id=current_user.id,
            description=description,
            last_used_at=datetime.now(timezone.utc)
        )
        db.add(new_history)
        db.commit()

        # 檢查是否超過上限
        count = db.query(DescriptionHistory).filter(
            DescriptionHistory.user_id == current_user.id
        ).count()

        if count > MAX_DESCRIPTIONS:
            # 刪除最舊的記錄（按 last_used_at 排序）
            oldest = db.query(DescriptionHistory).filter(
                DescriptionHistory.user_id == current_user.id
            ).order_by(
                DescriptionHistory.last_used_at.asc()
            ).limit(count - MAX_DESCRIPTIONS).all()

            for record in oldest:
                db.delete(record)

            db.commit()

    return {"message": "敘述歷史已更新"}


@router.delete("/{description_id}")
def delete_description_history(
    description_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    刪除特定的敘述歷史記錄
    """
    history = db.query(DescriptionHistory).filter(
        DescriptionHistory.id == description_id,
        DescriptionHistory.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="找不到此敘述記錄")

    db.delete(history)
    db.commit()

    return {"message": "敘述記錄已刪除"}
