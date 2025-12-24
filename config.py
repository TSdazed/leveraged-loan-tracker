from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # FRED API
    fred_api_key: str
    
    # Database
    database_url: str
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # FRED Series IDs for Leveraged Loan Market
    # These are the main series we'll track
    fred_series: dict = {
        # Commercial Bank Delinquency Rates
        "commercial_delinquency": "DRBLACBS",  # Delinquency Rate on Business Loans, All Commercial Banks
        "charge_off_rate": "CORBLACBS",  # Charge-Off Rate on Business Loans, All Commercial Banks
        
        # Credit Standards and Lending
        "credit_standards": "DRTSCILM",  # Net Percentage of Banks Tightening Standards for C&I Loans to Large and Medium Firms
        "loan_demand": "DRTSCIS",  # Net Percentage of Banks Reporting Stronger Demand for C&I Loans to Small Firms
        
        # Corporate Credit and Spreads
        "bbb_yield": "BAMLC0A4CBBB",  # ICE BofA BBB US Corporate Index Option-Adjusted Spread
        "high_yield_spread": "BAMLH0A0HYM2",  # ICE BofA US High Yield Index Option-Adjusted Spread
        
        # Economic Indicators
        "gdp": "GDP",  # Gross Domestic Product
        "unemployment": "UNRATE",  # Unemployment Rate
        "fed_funds": "FEDFUNDS",  # Federal Funds Effective Rate
        
        # NBER Recession Indicator
        "recession": "USREC",  # NBER based Recession Indicators for the United States
        
        # Total Credit Market Debt
        "nonfinancial_debt": "TCMDO",  # Total Credit Market Debt Owed by Nonfinancial Sectors
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
