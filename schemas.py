from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class MarketDataPoint(BaseModel):
    """Single data point for time-series"""
    date: datetime
    value: float
    
    class Config:
        from_attributes = True


class SeriesData(BaseModel):
    """Complete time-series for a metric"""
    series_id: str
    series_name: str
    data: List[MarketDataPoint]
    start_date: datetime
    end_date: datetime
    total_points: int


class RecessionPeriodSchema(BaseModel):
    """Recession period information"""
    id: int
    start_date: datetime
    end_date: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class MarketOverview(BaseModel):
    """Overview of current market conditions"""
    date: datetime
    delinquency_rate: Optional[float] = None
    charge_off_rate: Optional[float] = None
    high_yield_spread: Optional[float] = None
    bbb_yield_spread: Optional[float] = None
    unemployment_rate: Optional[float] = None
    in_recession: bool = False


class DataFetchStatus(BaseModel):
    """Status of data fetch operation"""
    series_id: str
    status: str
    records_fetched: int
    error_message: Optional[str] = None
    fetch_date: datetime
    
    class Config:
        from_attributes = True


class HistoricalDataRequest(BaseModel):
    """Request parameters for historical data"""
    series_ids: Optional[List[str]] = None
    start_date: Optional[str] = "1980-01-01"
    end_date: Optional[str] = None


class HealthCheck(BaseModel):
    """API health check response"""
    status: str
    timestamp: datetime
    database_connected: bool
    fred_api_configured: bool
    total_records: int


class DataRefreshResponse(BaseModel):
    """Response from data refresh operation"""
    status: str
    message: str
    results: dict
    timestamp: datetime
