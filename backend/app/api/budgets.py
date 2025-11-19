from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date
from app.core.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import Budget as BudgetSchema, BudgetCreate, BudgetUpdate
from app.api.deps import get_current_user

router = APIRouter()

def calculate_budget_spent(db: Session, budget: Budget) -> float:
    """計算預算已使用金額（只計算支出類型的交易）

    邏輯說明：
    - 如果預算類別是「全部」：計算該帳戶所有支出
    - 如果預算類別是特定類別：只計算該類別 + 沒有類別的交易（視為未分類支出）
    """
    # 建立基礎查詢
    query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'debit',  # 只計算支出
        Transaction.transaction_date >= budget.start_date,
        Transaction.transaction_date <= budget.end_date,
        Transaction.account_id == budget.account_id  # 只計算綁定帳戶的交易
    )

    # 如果預算指定了類別（且不是「全部」），則計算：該類別的交易 + 未分類的交易
    if budget.category and budget.category != '全部':
        query = query.filter(
            (Transaction.category == budget.category) |
            (Transaction.category == None) |
            (Transaction.category == '')
        )

    spent = query.scalar()
    return spent or 0.0

@router.get("/", response_model=List[BudgetSchema])
def get_budgets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()

    # 自動更新每個預算的已使用金額
    for budget in budgets:
        budget.spent = calculate_budget_spent(db, budget)
    db.commit()

    return budgets

@router.post("/", response_model=BudgetSchema)
def create_budget(
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_budget = Budget(**budget.dict(), user_id=current_user.id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/{budget_id}", response_model=BudgetSchema)
def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    # 自動更新已使用金額
    budget.spent = calculate_budget_spent(db, budget)
    db.commit()

    return budget

@router.put("/{budget_id}", response_model=BudgetSchema)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    for key, value in budget_update.dict(exclude_unset=True).items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)
    return budget

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}
