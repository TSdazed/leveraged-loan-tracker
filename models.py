from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class MarketData(Base):
    """
    Time-series data for leveraged loan market metrics
    """
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    series_id = Column(String(50), nullable=False, index=True)
    series_name = Column(String(200), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_date_series', 'date', 'series_id'),
    )


class RecessionPeriod(Base):
    """
    NBER recession periods for overlay on charts
    """
    __tablename__ = "recession_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True, index=True)
    name = Column(String(100))  # e.g., "Great Recession", "COVID-19 Recession"
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataFetchLog(Base):
    """
    Log of data fetch operations for monitoring
    """
    __tablename__ = "data_fetch_log"
    
    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(String(50), nullable=False)
    fetch_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # 'success', 'failed', 'partial'
    records_fetched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
