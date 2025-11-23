from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.exchange_rate import ExchangeRate
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ExchangeRateResponse(BaseModel):
    currency_code: str
    currency_name: str
    buying_rate: float | None
    selling_rate: float | None
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/latest", response_model=List[ExchangeRateResponse])
def get_latest_rates(db: Session = Depends(get_db)):
    rates = db.query(ExchangeRate).all()
    return rates
