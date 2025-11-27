from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.exchange_rate import ExchangeRate
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ExchangeRateResponse(BaseModel):
    id: int
    bank: str
    currency_code: str
    currency_name: str
    buying_rate: float | None
    selling_rate: float | None
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/latest", response_model=List[ExchangeRateResponse])
def get_latest_rates(
    bank: Optional[str] = Query(None, description="銀行代碼：bot (臺灣銀行), esun (玉山銀行)"),
    db: Session = Depends(get_db)
):
    """
    取得最新匯率資料
    - 不指定 bank 參數：返回所有銀行的匯率
    - 指定 bank='bot'：僅返回臺灣銀行匯率
    - 指定 bank='esun'：僅返回玉山銀行匯率
    """
    query = db.query(ExchangeRate)

    if bank:
        query = query.filter(ExchangeRate.bank == bank)

    rates = query.order_by(ExchangeRate.bank, ExchangeRate.currency_code).all()
    return rates
