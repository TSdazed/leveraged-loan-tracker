#!/usr/bin/env python3
"""
Initial setup script for the Leveraged Loan Market backend

This script will:
1. Create database tables
2. Fetch historical data from FRED (from 1980 to present)
3. Process recession indicators
4. Display statistics
"""

import sys
import logging
from datetime import datetime

from database import init_db, SessionLocal
from fred_service import FredDataService
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main initialization function
    """
    logger.info("=" * 70)
    logger.info("Leveraged Loan Market Backend - Initial Setup")
    logger.info("=" * 70)
    
    # Check configuration
    settings = get_settings()
    
    if not settings.fred_api_key or settings.fred_api_key == "your_fred_api_key_here":
        logger.error("FRED API key not configured!")
        logger.error("Please set FRED_API_KEY in your .env file")
        sys.exit(1)
    
    logger.info(f"FRED API Key: {'*' * 20}{settings.fred_api_key[-4:]}")
    logger.info(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url}")
    
    # Step 1: Initialize database
    logger.info("\n" + "=" * 70)
    logger.info("Step 1: Initializing Database")
    logger.info("=" * 70)
    
    try:
        init_db()
        logger.info("✓ Database tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        sys.exit(1)
    
    # Step 2: Fetch historical data
    logger.info("\n" + "=" * 70)
    logger.info("Step 2: Fetching Historical Data from FRED")
    logger.info("=" * 70)
    logger.info("This may take several minutes...")
    
    db = SessionLocal()
    fred_service = FredDataService()
    
    try:
        start_time = datetime.now()
        
        results = fred_service.fetch_and_store_all_series(
            db=db,
            start_date="1980-01-01"
        )
        
        # Display results
        logger.info("\nData Fetch Results:")
        logger.info("-" * 70)
        
        success_count = 0
        failed_count = 0
        total_records = 0
        
        for series_key, result in results.items():
            status_symbol = "✓" if result['status'] == 'success' else "✗"
            logger.info(f"{status_symbol} {series_key}: {result.get('series_name', 'Unknown')}")
            
            if result['status'] == 'success':
                success_count += 1
                total_records += result.get('records', 0)
                logger.info(f"  → {result.get('records', 0)} records stored")
            else:
                failed_count += 1
                logger.error(f"  → Error: {result.get('error', 'Unknown error')}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("-" * 70)
        logger.info(f"Summary: {success_count} successful, {failed_count} failed")
        logger.info(f"Total records stored: {total_records}")
        logger.info(f"Time elapsed: {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"✗ Failed to fetch data: {e}")
        db.close()
        sys.exit(1)
    
    # Step 3: Process recession indicators
    logger.info("\n" + "=" * 70)
    logger.info("Step 3: Processing Recession Indicators")
    logger.info("=" * 70)
    
    try:
        fred_service.process_recession_indicators(db)
        logger.info("✓ Recession periods identified and stored")
        
        # Display recession periods
        from models import RecessionPeriod
        recessions = db.query(RecessionPeriod).order_by(RecessionPeriod.start_date).all()
        
        if recessions:
            logger.info(f"\nIdentified {len(recessions)} recession periods:")
            logger.info("-" * 70)
            for rec in recessions:
                end_str = rec.end_date.strftime("%Y-%m-%d") if rec.end_date else "Ongoing"
                logger.info(f"  • {rec.name or 'Unnamed'}")
                logger.info(f"    {rec.start_date.strftime('%Y-%m-%d')} to {end_str}")
        
    except Exception as e:
        logger.error(f"✗ Failed to process recession indicators: {e}")
        db.close()
        sys.exit(1)
    
    # Step 4: Display final statistics
    logger.info("\n" + "=" * 70)
    logger.info("Step 4: Database Statistics")
    logger.info("=" * 70)
    
    try:
        from models import MarketData
        from sqlalchemy import func
        
        # Count records by series
        series_stats = db.query(
            MarketData.series_id,
            MarketData.series_name,
            func.count(MarketData.id).label('count'),
            func.min(MarketData.date).label('earliest'),
            func.max(MarketData.date).label('latest')
        ).group_by(
            MarketData.series_id,
            MarketData.series_name
        ).all()
        
        logger.info("\nData by Series:")
        logger.info("-" * 70)
        for stat in series_stats:
            logger.info(f"\n{stat.series_name} ({stat.series_id}):")
            logger.info(f"  Records: {stat.count}")
            logger.info(f"  Range: {stat.earliest.strftime('%Y-%m-%d')} to {stat.latest.strftime('%Y-%m-%d')}")
        
    except Exception as e:
        logger.error(f"Warning: Could not generate statistics: {e}")
    
    finally:
        db.close()
    
    # Success!
    logger.info("\n" + "=" * 70)
    logger.info("✓ Setup Complete!")
    logger.info("=" * 70)
    logger.info("\nYou can now start the API server:")
    logger.info("  python main.py")
    logger.info("\nOr use uvicorn directly:")
    logger.info("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    logger.info("\nAPI documentation will be available at:")
    logger.info("  http://localhost:8000/docs")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
