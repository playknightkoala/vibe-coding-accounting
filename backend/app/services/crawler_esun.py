import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

def fetch_esun_exchange_rates(db: Session):
    """
    抓取玉山銀行網銀/App優惠匯率 (Web Scraping)
    """
    url = "https://www.esunbank.com/zh-tw/personal/deposit/rate/forex/foreign-exchange-rates"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='l-exchangeRate__block')
        
        if not table:
            logger.error("找不到玉山銀行匯率表 (table.l-exchangeRate__block)")
            return

        tbody = table.find('tbody', class_='l-exchangeRate__table')
        if not tbody:
            logger.error("找不到玉山銀行匯率表內容 (tbody.l-exchangeRate__table)")
            return

        rows = tbody.find_all('tr', class_='currency')
        
        for row in rows:
            try:
                # 提取幣別代碼
                code_div = row.find('div', class_='title-en')
                if not code_div:
                    continue
                currency_code = code_div.get_text(strip=True)
                
                # 提取幣別名稱
                # 名稱在 div.title-item 裡面，但有多個 title-item，通常是第二個 (index 1) 包含中文名稱
                # 結構: <div class="col-auto px-3 col-lg-5 title-item"> 美元 </div>
                title_items = row.find_all('div', class_='title-item')
                currency_name = ""
                for item in title_items:
                    text = item.get_text(strip=True)
                    # 簡單判斷：不是英文代碼且長度大於0
                    if text and text != currency_code and not re.match(r'^[A-Z]{3}$', text):
                        currency_name = text
                        break
                
                if not currency_name:
                    currency_name = currency_code # Fallback

                # 提取匯率
                # 優先使用網銀/App優惠 (BuyIncreaseRate, SellDecreaseRate)
                # 如果沒有，使用即期匯率 (BBoardRate, SBoardRate)
                
                buying_rate = None
                selling_rate = None
                
                # 嘗試取得網銀優惠匯率
                buy_increase_div = row.find('div', class_='BuyIncreaseRate')
                sell_decrease_div = row.find('div', class_='SellDecreaseRate')
                
                if buy_increase_div and buy_increase_div.get_text(strip=True):
                    try:
                        buying_rate = float(buy_increase_div.get_text(strip=True))
                    except ValueError:
                        pass
                        
                if sell_decrease_div and sell_decrease_div.get_text(strip=True):
                    try:
                        selling_rate = float(sell_decrease_div.get_text(strip=True))
                    except ValueError:
                        pass
                
                # 如果沒有網銀優惠，嘗試即期匯率
                if buying_rate is None:
                    bboard_div = row.find('div', class_='BBoardRate')
                    if bboard_div and bboard_div.get_text(strip=True):
                        try:
                            buying_rate = float(bboard_div.get_text(strip=True))
                        except ValueError:
                            pass

                if selling_rate is None:
                    sboard_div = row.find('div', class_='SBoardRate')
                    if sboard_div and sboard_div.get_text(strip=True):
                        try:
                            selling_rate = float(sboard_div.get_text(strip=True))
                        except ValueError:
                            pass

                # 更新或插入資料庫
                existing_rate = db.query(ExchangeRate).filter(
                    ExchangeRate.bank == 'esun',
                    ExchangeRate.currency_code == currency_code
                ).first()

                if existing_rate:
                    if buying_rate is not None:
                        existing_rate.buying_rate = buying_rate
                    if selling_rate is not None:
                        existing_rate.selling_rate = selling_rate
                    existing_rate.currency_name = currency_name
                    existing_rate.updated_at = datetime.now()
                else:
                    new_rate = ExchangeRate(
                        bank='esun',
                        currency_code=currency_code,
                        currency_name=currency_name,
                        buying_rate=buying_rate,
                        selling_rate=selling_rate
                    )
                    db.add(new_rate)

            except Exception as e:
                logger.error(f"處理幣別 {currency_code} 時發生錯誤: {e}")
                continue

        db.commit()
        logger.info("玉山銀行匯率更新成功 (Web Scraping)")

    except Exception as e:
        logger.error(f"抓取玉山銀行匯率時發生錯誤: {e}")
        db.rollback()
        raise e
