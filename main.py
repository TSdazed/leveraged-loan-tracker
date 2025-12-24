from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from database import get_db, init_db, engine
from models import MarketData, RecessionPeriod, DataFetchLog
from schemas import (
    SeriesData, RecessionPeriodSchema, MarketOverview,
    DataFetchStatus, HealthCheck, DataRefreshResponse,
    HistoricalDataRequest, MarketDataPoint
)
from fred_service import FredDataService
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Leveraged Loan Market API",
    description="API for tracking leveraged loan market data with recession indicators",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("Starting up API server...")
    init_db()
    logger.info("Database initialized successfully")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Leveraged Loan Market API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database status
    """
    try:
        # Check database connection
        total_records = db.query(func.count(MarketData.id)).scalar()
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False
        total_records = 0
    
    fred_configured = bool(settings.fred_api_key and settings.fred_api_key != "your_fred_api_key_here")
    
    return HealthCheck(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.utcnow(),
        database_connected=db_connected,
        fred_api_configured=fred_configured,
        total_records=total_records
    )


@app.get("/api/series/{series_id}", response_model=SeriesData, tags=["Market Data"])
async def get_series_data(
    series_id: str,
    start_date: Optional[str] = Query("1980-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get time-series data for a specific FRED series
    
    - **series_id**: FRED series identifier (e.g., 'DRBLACBS' for delinquency rate)
    - **start_date**: Start date for data range
    - **end_date**: End date for data range (defaults to latest)
    """
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.utcnow()
        
        # Query data
        query = db.query(MarketData).filter(
            MarketData.series_id == series_id,
            MarketData.date >= start,
            MarketData.date <= end
        ).order_by(MarketData.date)
        
        records = query.all()
        
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for series {series_id}"
            )
        
        # Get series name from first record
        series_name = records[0].series_name
        
        # Convert to response format
        data_points = [
            MarketDataPoint(date=r.date, value=r.value)
            for r in records
        ]
        
        return SeriesData(
            series_id=series_id,
            series_name=series_name,
            data=data_points,
            start_date=records[0].date,
            end_date=records[-1].date,
            total_points=len(data_points)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error fetching series data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/series", tags=["Market Data"])
async def list_available_series():
    """
    List all available FRED series configured in the system
    """
    return {
        "series": settings.fred_series,
        "total": len(settings.fred_series)
    }


@app.post("/api/data/refresh", response_model=DataRefreshResponse, tags=["Data Management"])
async def refresh_market_data(
    start_date: str = Query("1980-01-01", description="Start date for data fetch"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a refresh of all market data from FRED
    
    This will fetch the latest data for all configured series
    """
    try:
        fred_service = FredDataService()
        
        logger.info("Starting manual data refresh...")
        results = fred_service.fetch_and_store_all_series(db, start_date)
        
        # Process recession indicators
        fred_service.process_recession_indicators(db)
        
        return DataRefreshResponse(
            status="success",
            message="Data refresh completed",
            results=results,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error during data refresh: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recessions", response_model=List[RecessionPeriodSchema], tags=["Recession Data"])
async def get_recession_periods(
    start_date: Optional[str] = Query("1980-01-01", description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """
    Get all recession periods for overlaying on charts
    
    Returns NBER-defined recession periods within the specified date range
    """
    try:
        query = db.query(RecessionPeriod)
        
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(
                (RecessionPeriod.end_date >= start) | (RecessionPeriod.end_date == None)
            )
        
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(RecessionPeriod.start_date <= end)
        
        recessions = query.order_by(RecessionPeriod.start_date).all()
        
        return recessions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error fetching recession periods: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overview/current", response_model=MarketOverview, tags=["Market Overview"])
async def get_current_market_overview(db: Session = Depends(get_db)):
    """
    Get current snapshot of key market metrics
    
    Returns the most recent values for all major indicators
    """
    try:
        overview = MarketOverview(
            date=datetime.utcnow(),
            in_recession=False
        )
        
        # Get latest values for key metrics
        metrics = {
            'delinquency_rate': 'DRBLACBS',
            'charge_off_rate': 'CORBLACBS',
            'high_yield_spread': 'BAMLH0A0HYM2',
            'bbb_yield_spread': 'BAMLC0A4CBBB',
            'unemployment_rate': 'UNRATE'
        }
        
        for field_name, series_id in metrics.items():
            latest = db.query(MarketData).filter(
                MarketData.series_id == series_id
            ).order_by(MarketData.date.desc()).first()
            
            if latest:
                setattr(overview, field_name, latest.value)
                overview.date = latest.date
        
        # Check if currently in recession
        latest_recession = db.query(MarketData).filter(
            MarketData.series_id == 'USREC'
        ).order_by(MarketData.date.desc()).first()
        
        if latest_recession and latest_recession.value == 1:
            overview.in_recession = True
        
        return overview
        
    except Exception as e:
        logger.error(f"Error fetching market overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overview/historical", tags=["Market Overview"])
async def get_historical_overview(
    start_date: str = Query("1980-01-01"),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get historical overview with all key metrics combined
    
    Returns time-series data for all major indicators for easy charting
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.utcnow()
        
        # Key series to include
        key_series = [
            'DRBLACBS',  # Delinquency rate
            'CORBLACBS',  # Charge-off rate
            'BAMLH0A0HYM2',  # High yield spread
            'BAMLC0A4CBBB',  # BBB spread
            'UNRATE',  # Unemployment
            'FEDFUNDS', # Fed Funds Rate
            'USREC'  # Recession indicator
        ]
        
        result = {}
        
        for series_id in key_series:
            records = db.query(MarketData).filter(
                MarketData.series_id == series_id,
                MarketData.date >= start,
                MarketData.date <= end
            ).order_by(MarketData.date).all()
            
            if records:
                result[series_id] = {
                    'name': records[0].series_name,
                    'data': [
                        {'date': r.date.isoformat(), 'value': r.value}
                        for r in records
                    ]
                }
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Error fetching historical overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", tags=["Statistics"])
async def get_data_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about the data stored in the system
    """
    try:
        stats = {}
        
        # Total records
        stats['total_records'] = db.query(func.count(MarketData.id)).scalar()
        
        # Records per series
        series_counts = db.query(
            MarketData.series_id,
            MarketData.series_name,
            func.count(MarketData.id).label('count'),
            func.min(MarketData.date).label('earliest'),
            func.max(MarketData.date).label('latest')
        ).group_by(
            MarketData.series_id,
            MarketData.series_name
        ).all()
        
        stats['series'] = [
            {
                'series_id': s.series_id,
                'series_name': s.series_name,
                'record_count': s.count,
                'earliest_date': s.earliest.isoformat() if s.earliest else None,
                'latest_date': s.latest.isoformat() if s.latest else None
            }
            for s in series_counts
        ]
        
        # Recession periods
        stats['recession_periods'] = db.query(func.count(RecessionPeriod.id)).scalar()
        
        # Last fetch logs
        last_fetches = db.query(DataFetchLog).order_by(
            DataFetchLog.fetch_date.desc()
        ).limit(10).all()
        
        stats['recent_fetches'] = [
            {
                'series_id': f.series_id,
                'status': f.status,
                'records_fetched': f.records_fetched,
                'fetch_date': f.fetch_date.isoformat()
            }
            for f in last_fetches
        ]
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
