# Leveraged Loan Market Backend

A comprehensive backend API for tracking the leveraged loan market with historical data from the 1980s to present, including delinquency rates, charge-off rates, and recession indicators.

## Features

- 📊 **Historical Market Data** - Track leveraged loan metrics from 1980 to present
- 🔴 **Recession Indicators** - NBER-defined recession periods for context
- 📈 **Key Metrics**:
  - Delinquency rates on business loans
  - Charge-off rates
  - High yield spreads
  - Corporate credit spreads
  - Economic indicators (GDP, unemployment, Fed funds rate)
- 🔄 **Auto-updating** - Fetch latest data from FRED API
- 🚀 **RESTful API** - Easy integration with frontend applications
- 📦 **Docker Support** - One-command deployment

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- FRED API Key (get one free at https://fred.stlouisfed.org/docs/api/api_key.html)

## Quick Start

### Option 1: Docker (Recommended)

1. **Clone and setup**:
```bash
cd leveraged-loan-backend
cp .env.example .env
```

2. **Add your FRED API key** to `.env`:
```env
FRED_API_KEY=your_actual_api_key_here
```

3. **Start everything**:
```bash
docker-compose up -d
```

4. **Initialize the database** (first time only):
```bash
docker-compose exec api python init_db.py
```

5. **Access the API**:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Local Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Setup PostgreSQL**:
```bash
# Create database
createdb leveraged_loans

# Or using psql
psql -U postgres
CREATE DATABASE leveraged_loans;
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

Your `.env` should look like:
```env
FRED_API_KEY=your_fred_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/leveraged_loans
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

4. **Initialize database and fetch data**:
```bash
python init_db.py
```

This will:
- Create all database tables
- Fetch historical data from 1980 to present (takes 5-10 minutes)
- Process recession indicators
- Display statistics

5. **Start the API server**:
```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health & Status
- `GET /` - Root endpoint
- `GET /health` - Health check with database status
- `GET /api/stats` - Database statistics

### Market Data
- `GET /api/series` - List all available data series
- `GET /api/series/{series_id}` - Get time-series data for specific metric
- `GET /api/overview/current` - Current market snapshot
- `GET /api/overview/historical` - Historical overview (all metrics combined)

### Recession Data
- `GET /api/recessions` - Get all recession periods

### Data Management
- `POST /api/data/refresh` - Manually trigger data refresh from FRED

## Key Data Series

### Default & Delinquency Rates (Most Important)
- **DRBLACBS** - Delinquency Rate on Business Loans, All Commercial Banks
- **CORBLACBS** - Charge-Off Rate on Business Loans, All Commercial Banks

### Credit Market Indicators
- **BAMLH0A0HYM2** - High Yield Corporate Bond Spread
- **BAMLC0A4CBBB** - BBB Corporate Bond Spread
- **DRTSCILM** - Net % of Banks Tightening Credit Standards

### Economic Context
- **GDP** - Gross Domestic Product
- **UNRATE** - Unemployment Rate
- **FEDFUNDS** - Federal Funds Rate
- **USREC** - NBER Recession Indicator

## Example API Usage

### Get Delinquency Rate Data
```bash
curl "http://localhost:8000/api/series/DRBLACBS?start_date=1980-01-01"
```

### Get Current Market Overview
```bash
curl "http://localhost:8000/api/overview/current"
```

### Get Recession Periods
```bash
curl "http://localhost:8000/api/recessions?start_date=1980-01-01"
```

### Refresh Data
```bash
curl -X POST "http://localhost:8000/api/data/refresh"
```

## Database Schema

### MarketData Table
Stores time-series data for all metrics:
- `id` - Primary key
- `date` - Data point date
- `series_id` - FRED series identifier
- `series_name` - Human-readable name
- `value` - Metric value
- `created_at`, `updated_at` - Timestamps

### RecessionPeriod Table
Stores NBER recession periods:
- `id` - Primary key
- `start_date` - Recession start
- `end_date` - Recession end (NULL if ongoing)
- `name` - Recession name (e.g., "Great Recession")
- `description` - Additional details

### DataFetchLog Table
Logs all data fetch operations for monitoring

## Updating Data

The system is designed to be updated regularly:

### Manual Update
```bash
# Using the API
curl -X POST "http://localhost:8000/api/data/refresh"

# Or directly with Python
python -c "from database import SessionLocal; from fred_service import FredDataService; db = SessionLocal(); FredDataService().fetch_and_store_all_series(db)"
```

### Automated Updates
Set up a cron job to update daily:

```bash
# Edit crontab
crontab -e

# Add this line to update at 6 AM daily
0 6 * * * curl -X POST "http://localhost:8000/api/data/refresh"
```

Or use a separate scheduler script:

```python
import schedule
import time
from database import SessionLocal
from fred_service import FredDataService

def update_data():
    db = SessionLocal()
    try:
        service = FredDataService()
        service.fetch_and_store_all_series(db)
        service.process_recession_indicators(db)
    finally:
        db.close()

schedule.every().day.at("06:00").do(update_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Frontend Integration

### Example: Fetch Historical Data
```javascript
async function getDelinquencyData() {
  const response = await fetch(
    'http://localhost:8000/api/series/DRBLACBS?start_date=1980-01-01'
  );
  const data = await response.json();
  
  // data.data contains array of {date, value} objects
  return data;
}
```

### Example: Get All Metrics for Charting
```javascript
async function getAllMetrics() {
  const response = await fetch(
    'http://localhost:8000/api/overview/historical?start_date=1980-01-01'
  );
  const data = await response.json();
  
  // Returns object with all series data
  // data.DRBLACBS.data, data.CORBLACBS.data, etc.
  return data;
}
```

### Example: Overlay Recession Periods
```javascript
async function getRecessions() {
  const response = await fetch(
    'http://localhost:8000/api/recessions?start_date=1980-01-01'
  );
  const recessions = await response.json();
  
  // Array of {start_date, end_date, name}
  return recessions;
}
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready

# For Docker
docker-compose ps
docker-compose logs postgres
```

### FRED API Issues
```bash
# Verify API key is set
python -c "from config import get_settings; print(get_settings().fred_api_key)"

# Test FRED connection
python -c "from fredapi import Fred; f = Fred('YOUR_KEY'); print(f.get_series('GDP').tail())"
```

### Data Not Appearing
```bash
# Check fetch logs
curl "http://localhost:8000/api/stats"

# Re-run initialization
python init_db.py
```

## Production Deployment

For production:

1. **Change database password** in `docker-compose.yml` and `.env`
2. **Set DEBUG=False** in `.env`
3. **Configure CORS** in `main.py` (set specific origins)
4. **Use environment variables** for sensitive data
5. **Set up reverse proxy** (nginx) for HTTPS
6. **Enable rate limiting** and authentication
7. **Schedule regular backups**:
```bash
pg_dump -U loantracker leveraged_loans > backup_$(date +%Y%m%d).sql
```

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (React/etc)    │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ├─────────────┐
         │             │
┌────────▼────────┐   │
│  PostgreSQL     │   │
│  Time-series DB │   │
└─────────────────┘   │
                      │
                 ┌────▼─────┐
                 │ FRED API │
                 └──────────┘
```

## License

MIT License - feel free to use for your projects!

## Support

For issues or questions:
1. Check the API docs at `/docs`
2. Review the logs: `docker-compose logs api`
3. Check FRED API status: https://fred.stlouisfed.org/

## Next Steps

After getting the backend running:
1. ✅ Test all API endpoints using `/docs`
2. ✅ Verify data is being fetched correctly
3. ✅ Build your frontend to visualize the data
4. ✅ Set up automated data updates
5. ✅ Deploy to production

Good luck with your leveraged loan market tracker! 🚀
