from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.transaction import Transaction as TransactionSchema, TransactionCreate, TransactionUpdate
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[TransactionSchema])
def get_transactions(
    account_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).join(Account).filter(Account.user_id == current_user.id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    transactions = query.all()
    return transactions

@router.post("/", response_model=TransactionSchema)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(Account).filter(
        Account.id == transaction.account_id,
        Account.user_id == current_user.id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)

    # Update account balance
    if transaction.transaction_type == "credit":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    old_amount = transaction.amount
    old_type = transaction.transaction_type

    for key, value in transaction_update.dict(exclude_unset=True).items():
        setattr(transaction, key, value)

    # Update account balance if amount changed
    account = transaction.account
    if old_type == "credit":
        account.balance -= old_amount
    else:
        account.balance += old_amount

    if transaction.transaction_type == "credit":
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update account balance
    account = transaction.account
    if transaction.transaction_type == "credit":
        account.balance -= transaction.amount
    else:
        account.balance += transaction.amount

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}
