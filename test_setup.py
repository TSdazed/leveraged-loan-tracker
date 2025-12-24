#!/usr/bin/env python3
"""
Test script to verify the Leveraged Loan Market backend setup

This script performs basic tests to ensure everything is configured correctly.
"""

import sys
from datetime import datetime

def test_imports():
    """Test that all required packages can be imported"""
    print("Testing imports...")
    try:
        import fastapi
        import sqlalchemy
        import pandas
        import fredapi
        from pydantic import BaseModel
        print("✓ All packages imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    try:
        from config import get_settings
        settings = get_settings()
        
        # Check FRED API key
        if not settings.fred_api_key or settings.fred_api_key == "your_fred_api_key_here":
            print("✗ FRED API key not configured")
            print("Please set FRED_API_KEY in your .env file")
            return False
        
        print(f"✓ FRED API key configured: {'*' * 20}{settings.fred_api_key[-4:]}")
        
        # Check database URL
        if "your_database_url" in settings.database_url.lower():
            print("✗ Database URL not configured")
            return False
        
        print(f"✓ Database URL configured")
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False


def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        from database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        print("✓ Database connection successful")
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nMake sure PostgreSQL is running and credentials are correct.")
        print("If using Docker: docker-compose up -d postgres")
        return False


def test_fred_api():
    """Test FRED API connection"""
    print("\nTesting FRED API connection...")
    try:
        from fredapi import Fred
        from config import get_settings
        
        settings = get_settings()
        fred = Fred(api_key=settings.fred_api_key)
        
        # Try to fetch a simple series
        data = fred.get_series('GDP', observation_start='2020-01-01', observation_end='2020-12-31')
        
        if len(data) > 0:
            print(f"✓ FRED API connection successful (fetched {len(data)} data points)")
            return True
        else:
            print("✗ FRED API returned no data")
            return False
            
    except Exception as e:
        print(f"✗ FRED API connection failed: {e}")
        print("\nCheck your API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        return False


def test_database_tables():
    """Test if database tables exist"""
    print("\nTesting database tables...")
    try:
        from database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['market_data', 'recession_periods', 'data_fetch_log']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"✗ Missing tables: {missing_tables}")
            print("Run: python init_db.py")
            return False
        
        print(f"✓ All required tables exist: {required_tables}")
        return True
        
    except Exception as e:
        print(f"✗ Table check failed: {e}")
        return False


def test_data_exists():
    """Test if data has been loaded"""
    print("\nTesting data availability...")
    try:
        from database import SessionLocal
        from models import MarketData
        from sqlalchemy import func
        
        db = SessionLocal()
        
        count = db.query(func.count(MarketData.id)).scalar()
        
        if count == 0:
            print("✗ No data in database")
            print("Run: python init_db.py")
            db.close()
            return False
        
        # Check date range
        earliest = db.query(func.min(MarketData.date)).scalar()
        latest = db.query(func.max(MarketData.date)).scalar()
        
        print(f"✓ Database contains {count:,} records")
        print(f"  Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"✗ Data check failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Leveraged Loan Market Backend - System Test")
    print("=" * 70)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Database Connection", test_database_connection),
        ("FRED API", test_fred_api),
        ("Database Tables", test_database_tables),
        ("Data Availability", test_data_exists),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Your backend is ready to use.")
        print("\nStart the API server with:")
        print("  python main.py")
        print("\nOr with Docker:")
        print("  docker-compose up")
        print("=" * 70)
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
