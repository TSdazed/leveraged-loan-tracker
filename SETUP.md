# Quick Setup Guide

## Prerequisites
1. Get a FREE FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html
2. Have PostgreSQL installed OR use Docker

## Setup Steps

### Step 1: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your FRED API key
nano .env  # or use any text editor
```

Your `.env` should have:
```
FRED_API_KEY=your_actual_fred_api_key_here
DATABASE_URL=postgresql://username:password@localhost:5432/leveraged_loans
```

### Step 2: Choose Your Setup Method

#### Option A: Docker (Easiest)
```bash
# Start PostgreSQL and API
docker-compose up -d

# Initialize database (first time only)
docker-compose exec api python init_db.py

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down
```

#### Option B: Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create PostgreSQL database
createdb leveraged_loans
# Or: psql -U postgres -c "CREATE DATABASE leveraged_loans;"

# Initialize database
python init_db.py

# Start API server
python main.py
```

### Step 3: Verify Setup
```bash
# Run tests
python test_setup.py

# Check API health
curl http://localhost:8000/health

# View API docs
# Open browser to: http://localhost:8000/docs
```

### Step 4: Optional - Set Up Auto-Updates
```bash
# Run the scheduler (keeps running in background)
python scheduler.py

# Or add to crontab for daily updates
crontab -e
# Add: 0 6 * * * curl -X POST "http://localhost:8000/api/data/refresh"
```

## What Gets Created

After running `init_db.py`:
- ✅ Database tables created
- ✅ ~10-15 years of historical data fetched
- ✅ All recession periods identified
- ✅ Ready for API queries

This takes about 5-10 minutes on first run.

## Common Issues

### "FRED API key not configured"
→ Make sure you copied `.env.example` to `.env` and added your key

### "Database connection failed"
→ Make sure PostgreSQL is running
→ Check DATABASE_URL in .env is correct

### "No module named 'fastapi'"
→ Run `pip install -r requirements.txt`

### Docker issues
→ Make sure Docker is running
→ Try `docker-compose down -v` then `docker-compose up -d`

## Next Steps

1. ✅ Test endpoints at http://localhost:8000/docs
2. ✅ Build your frontend to visualize the data
3. ✅ Schedule automated updates with `scheduler.py`

## API Examples

### Get delinquency rate data
```bash
curl "http://localhost:8000/api/series/DRBLACBS?start_date=1980-01-01"
```

### Get current market snapshot
```bash
curl "http://localhost:8000/api/overview/current"
```

### Get all recession periods
```bash
curl "http://localhost:8000/api/recessions"
```

### Get all historical data for charting
```bash
curl "http://localhost:8000/api/overview/historical?start_date=1980-01-01"
```

## Need Help?

1. Check the full README.md
2. Look at API docs: http://localhost:8000/docs
3. Check logs: `docker-compose logs api` or check terminal output

Good luck! 🚀
