from fredapi import Fred
from sqlalchemy.orm import Session
from models import MarketData, RecessionPeriod, DataFetchLog
from config import get_settings
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


class FredDataService:
    """
    Service for fetching and storing data from FRED API
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.fred_api_key
        self.fred = Fred(api_key=self.api_key)
        self.series_config = settings.fred_series
    
    def fetch_series_data(
        self, 
        series_id: str, 
        start_date: str = "1980-01-01",
        end_date: str = None
    ) -> pd.Series:
        """
        Fetch data for a specific FRED series
        
        Args:
            series_id: FRED series identifier
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)
        
        Returns:
            pandas Series with date index and values
        """
        try:
            logger.info(f"Fetching data for series {series_id} from {start_date}")
            
            data = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            
            logger.info(f"Successfully fetched {len(data)} records for {series_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching series {series_id}: {e}")
            raise
    
    def get_series_info(self, series_id: str) -> dict:
        """
        Get metadata about a FRED series
        """
        try:
            info = self.fred.get_series_info(series_id)
            return {
                'id': info['id'],
                'title': info['title'],
                'units': info['units'],
                'frequency': info['frequency'],
                'seasonal_adjustment': info['seasonal_adjustment'],
                'last_updated': info['last_updated']
            }
        except Exception as e:
            logger.error(f"Error getting info for series {series_id}: {e}")
            return {}
    
    def store_series_data(
        self, 
        db: Session, 
        series_id: str, 
        series_name: str,
        data: pd.Series
    ) -> int:
        """
        Store fetched data in the database
        
        Args:
            db: Database session
            series_id: FRED series identifier
            series_name: Human-readable series name
            data: pandas Series with data
        
        Returns:
            Number of records stored
        """
        records_stored = 0
        
        try:
            for date, value in data.items():
                # Skip NaN values
                if pd.isna(value):
                    continue
                
                # Check if record already exists
                existing = db.query(MarketData).filter(
                    MarketData.date == date,
                    MarketData.series_id == series_id
                ).first()
                
                if existing:
                    # Update existing record
                    existing.value = float(value)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    record = MarketData(
                        date=date,
                        series_id=series_id,
                        series_name=series_name,
                        value=float(value)
                    )
                    db.add(record)
                
                records_stored += 1
            
            db.commit()
            logger.info(f"Stored {records_stored} records for {series_id}")
            return records_stored
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing data for {series_id}: {e}")
            raise
    
    def fetch_and_store_all_series(
        self, 
        db: Session,
        start_date: str = "1980-01-01"
    ) -> dict:
        """
        Fetch and store all configured FRED series
        
        Returns:
            Dictionary with results for each series
        """
        results = {}
        
        for series_key, series_id in self.series_config.items():
            try:
                logger.info(f"Processing {series_key} ({series_id})")
                
                # Get series info
                info = self.get_series_info(series_id)
                series_name = info.get('title', series_key)
                
                # Fetch data
                data = self.fetch_series_data(series_id, start_date)
                
                # Store data
                records_stored = self.store_series_data(
                    db, series_id, series_name, data
                )
                
                # Log the fetch
                log_entry = DataFetchLog(
                    series_id=series_id,
                    status='success',
                    records_fetched=records_stored,
                    start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                    end_date=datetime.utcnow()
                )
                db.add(log_entry)
                db.commit()
                
                results[series_key] = {
                    'status': 'success',
                    'records': records_stored,
                    'series_name': series_name
                }
                
            except Exception as e:
                logger.error(f"Failed to process {series_key}: {e}")
                
                # Log the failure
                log_entry = DataFetchLog(
                    series_id=series_id,
                    status='failed',
                    records_fetched=0,
                    error_message=str(e),
                    start_date=datetime.strptime(start_date, "%Y-%m-%d")
                )
                db.add(log_entry)
                db.commit()
                
                results[series_key] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return results
    
    def process_recession_indicators(self, db: Session):
        """
        Process USREC series to identify recession periods
        """
        try:
            # Get recession indicator data
            recession_data = db.query(MarketData).filter(
                MarketData.series_id == 'USREC'
            ).order_by(MarketData.date).all()
            
            if not recession_data:
                logger.warning("No recession indicator data found")
                return
            
            # Find recession periods (when value changes from 0 to 1 and back)
            in_recession = False
            recession_start = None
            
            for i, record in enumerate(recession_data):
                if record.value == 1 and not in_recession:
                    # Recession start
                    recession_start = record.date
                    in_recession = True
                elif record.value == 0 and in_recession:
                    # Recession end
                    # Check if this period already exists
                    existing = db.query(RecessionPeriod).filter(
                        RecessionPeriod.start_date == recession_start
                    ).first()
                    
                    if not existing:
                        recession_period = RecessionPeriod(
                            start_date=recession_start,
                            end_date=record.date,
                            name=self._get_recession_name(recession_start)
                        )
                        db.add(recession_period)
                    
                    in_recession = False
                    recession_start = None
            
            # Handle ongoing recession
            if in_recession and recession_start:
                existing = db.query(RecessionPeriod).filter(
                    RecessionPeriod.start_date == recession_start
                ).first()
                
                if not existing:
                    recession_period = RecessionPeriod(
                        start_date=recession_start,
                        end_date=None,  # Ongoing
                        name=self._get_recession_name(recession_start)
                    )
                    db.add(recession_period)
            
            db.commit()
            logger.info("Recession periods processed successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing recession indicators: {e}")
            raise
    
    def _get_recession_name(self, start_date: datetime) -> str:
        """
        Get a name for a recession based on its start date
        """
        year = start_date.year
        
        recession_names = {
            1980: "Early 1980s Recession",
            1981: "1981-1982 Recession",
            1990: "Early 1990s Recession",
            2001: "Early 2000s Recession",
            2007: "Great Recession",
            2020: "COVID-19 Recession"
        }
        
        # Find closest year
        for recession_year, name in recession_names.items():
            if abs(year - recession_year) <= 1:
                return name
        
        return f"{year} Recession"
