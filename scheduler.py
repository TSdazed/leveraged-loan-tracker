#!/usr/bin/env python3
"""
Scheduled data updater for Leveraged Loan Market data

Run this script to automatically update data on a schedule.
Can be run as a background service or via cron job.
"""

import schedule
import time
import logging
from datetime import datetime

from database import SessionLocal
from fred_service import FredDataService
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def update_market_data():
    """
    Fetch latest market data from FRED and update database
    """
    logger.info("=" * 70)
    logger.info("Starting scheduled data update")
    logger.info("=" * 70)
    
    db = SessionLocal()
    
    try:
        fred_service = FredDataService()
        
        # Fetch data from the last 30 days to catch any updates
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Fetching data from {start_date} to present")
        results = fred_service.fetch_and_store_all_series(db, start_date)
        
        # Process recession indicators
        fred_service.process_recession_indicators(db)
        
        # Log results
        success_count = sum(1 for r in results.values() if r['status'] == 'success')
        failed_count = sum(1 for r in results.values() if r['status'] == 'failed')
        total_records = sum(r.get('records', 0) for r in results.values() if r['status'] == 'success')
        
        logger.info("-" * 70)
        logger.info(f"Update complete:")
        logger.info(f"  Success: {success_count}")
        logger.info(f"  Failed: {failed_count}")
        logger.info(f"  Total records: {total_records}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error during scheduled update: {e}", exc_info=True)
    finally:
        db.close()


def main():
    """
    Main function to run the scheduler
    """
    logger.info("Leveraged Loan Market Data Updater")
    logger.info("=" * 70)
    
    settings = get_settings()
    
    # Check configuration
    if not settings.fred_api_key or settings.fred_api_key == "your_fred_api_key_here":
        logger.error("FRED API key not configured!")
        logger.error("Please set FRED_API_KEY in your .env file")
        return
    
    # Run immediately on startup
    logger.info("Running initial update...")
    update_market_data()
    
    # Schedule daily updates at 6 AM
    schedule.every().day.at("06:00").do(update_market_data)
    logger.info("Scheduled daily updates at 06:00 AM")
    
    # Also run every 12 hours as backup
    schedule.every(12).hours.do(update_market_data)
    logger.info("Scheduled updates every 12 hours")
    
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    logger.info("=" * 70)
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")


if __name__ == "__main__":
    main()
