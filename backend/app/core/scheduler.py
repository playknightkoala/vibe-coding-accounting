from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.services.crawler import fetch_exchange_rates
from app.services.crawler_esun import fetch_esun_exchange_rates
from app.services.recurring_expense_processor import process_recurring_expenses
from app.services.budget_stats import update_all_active_budgets_stats
from app.tasks.budget_recurring import create_next_period_budgets
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def run_bot_crawler_job():
    """臺灣銀行匯率爬蟲"""
    logger.info("Starting BOT exchange rate update")
    db = SessionLocal()
    try:
        fetch_exchange_rates(db)
    except Exception as e:
        logger.error(f"BOT crawler job failed: {e}")
    finally:
        db.close()

def run_esun_crawler_job():
    """玉山銀行匯率爬蟲"""
    logger.info("Starting E.SUN exchange rate update")
    db = SessionLocal()
    try:
        fetch_esun_exchange_rates(db)
    except Exception as e:
        logger.error(f"E.SUN crawler job failed: {e}")
    finally:
        db.close()

def run_recurring_expense_job():
    """處理固定支出 - 建立到期的固定支出交易"""
    logger.info("Starting recurring expense processing")
    db = SessionLocal()
    try:
        transactions_created = process_recurring_expenses(db)
        logger.info(f"Recurring expense job completed. Created {transactions_created} transactions")
    except Exception as e:
        logger.error(f"Recurring expense job failed: {e}")
    finally:
        db.close()

def run_budget_recurring_job():
    """處理週期預算 - 建立下一個週期的預算"""
    logger.info("Starting budget recurring processing")
    try:
        create_next_period_budgets()
        logger.info("Budget recurring job completed")
    except Exception as e:
        logger.error(f"Budget recurring job failed: {e}")

def run_budget_stats_job():
    """更新預算統計 - 計算超支天數和預算內天數"""
    logger.info("Starting budget stats update")
    db = SessionLocal()
    try:
        updated_count = update_all_active_budgets_stats(db)
        logger.info(f"Budget stats job completed. Updated {updated_count} budgets")
    except Exception as e:
        logger.error(f"Budget stats job failed: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()

def start_scheduler():
    # 臺灣銀行：每小時執行一次（與玉山銀行同步）
    bot_trigger = IntervalTrigger(hours=1)
    scheduler.add_job(run_bot_crawler_job, trigger=bot_trigger, id="bot_exchange_rate_crawler", replace_existing=True)

    # 玉山銀行：每小時執行一次（資料更新頻率較高）
    esun_trigger = IntervalTrigger(hours=1)
    scheduler.add_job(run_esun_crawler_job, trigger=esun_trigger, id="esun_exchange_rate_crawler", replace_existing=True)

    # 固定支出處理：每天凌晨 00:01 執行
    recurring_trigger = CronTrigger(hour=0, minute=1)
    scheduler.add_job(run_recurring_expense_job, trigger=recurring_trigger, id="recurring_expense_processor", replace_existing=True)

    # 週期預算處理：每天凌晨 00:05 執行
    budget_trigger = CronTrigger(hour=0, minute=5)
    scheduler.add_job(run_budget_recurring_job, trigger=budget_trigger, id="budget_recurring_processor", replace_existing=True)

    # 預算統計更新：每天凌晨 00:10 執行
    budget_stats_trigger = CronTrigger(hour=0, minute=10)
    scheduler.add_job(run_budget_stats_job, trigger=budget_stats_trigger, id="budget_stats_updater", replace_existing=True)

    scheduler.start()
    logger.info("Scheduler started - BOT (hourly), E.SUN (hourly), Recurring Expenses (daily at 00:01), Budget Recurring (daily at 00:05), Budget Stats (daily at 00:10)")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler shut down")
