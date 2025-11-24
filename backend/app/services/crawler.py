import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def fetch_exchange_rates(db: Session):
    url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rows = soup.find('table', title='牌告匯率').find('tbody').find_all('tr')
        
        for row in rows:
            currency_cell = row.find('div', class_='visible-phone')
            if not currency_cell:
                continue
                
            currency_text = currency_cell.text.strip()
            # Format usually: "美金 (USD)"
            # We want to extract "USD" and "美金"
            
            parts = currency_text.split()
            if len(parts) >= 2:
                currency_name = parts[0]
                currency_code = parts[1].strip('()')
            else:
                continue

            # Rates are in cells with class 'rate-content-cash' (cash) and 'rate-content-sight' (spot)
            # We usually want Spot Rate (即期匯率) for digital transactions, but let's check the columns.
            # Column 0: Currency
            # Column 1: Cash Buying
            # Column 2: Cash Selling
            # Column 3: Spot Buying
            # Column 4: Spot Selling
            
            # The structure might be different in mobile view vs desktop, but bs4 sees the raw HTML.
            # Let's rely on the data-table attributes if possible, or index.
            # The table headers are: 幣別, 現金匯率(本行買入, 本行賣出), 即期匯率(本行買入, 本行賣出)
            
            cells = row.find_all('td')
            
            # Spot Buying (即期買入) - Index 3
            spot_buying_rate_str = cells[3].text.strip()
            # Spot Selling (即期賣出) - Index 4
            spot_selling_rate_str = cells[4].text.strip()
            
            # Handle cases where rate is '-' (e.g. some currencies don't have spot rates?)
            try:
                buying_rate = float(spot_buying_rate_str) if spot_buying_rate_str != '-' else None
                selling_rate = float(spot_selling_rate_str) if spot_selling_rate_str != '-' else None
            except ValueError:
                buying_rate = None
                selling_rate = None
                
            # Update or Insert into DB
            existing_rate = db.query(ExchangeRate).filter(ExchangeRate.currency_code == currency_code).first()
            
            if existing_rate:
                if buying_rate is not None:
                    existing_rate.buying_rate = buying_rate
                if selling_rate is not None:
                    existing_rate.selling_rate = selling_rate
                
                existing_rate.currency_name = currency_name
                existing_rate.updated_at = datetime.now()
            else:
                new_rate = ExchangeRate(
                    currency_code=currency_code,
                    currency_name=currency_name,
                    buying_rate=buying_rate,
                    selling_rate=selling_rate
                )
                db.add(new_rate)
        
        db.commit()
        logger.info("Exchange rates updated successfully")
        
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}")
        db.rollback()
        raise e
