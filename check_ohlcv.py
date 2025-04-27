"""
Script to check OHLCV data for a specific date.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd

def main():
    engine = get_engine()
    
    # Query the OHLCV data for April 3, 2025
    query = text("""
        SELECT *, CONVERT(VARCHAR, timestamp, 121) as timestamp_str
        FROM dbo.spx_ohlcv_1d
        WHERE CAST(timestamp AS DATE) = :date
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {"date": "2025-04-04"})
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall())
        
        if df.empty:
            print("No OHLCV data found for April 3, 2025 in spx_ohlcv_1d table")
        else:
            print(f"Found {len(df)} OHLCV bars for April 3, 2025 in spx_ohlcv_1d table:")
            print(df)
    
    # Also check the 1m table
    query = text("""
        SELECT *
        FROM dbo.spx_ohlcv_1m
        WHERE CAST(timestamp AS DATE) = :date
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {"date": "2025-04-03"})
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall())
        
        if df.empty:
            print("\nNo OHLCV data found for April 3, 2025 in spx_ohlcv_1m table")
        else:
            print(f"\nFound {len(df)} OHLCV bars for April 3, 2025 in spx_ohlcv_1m table")
            print(f"First few rows:")
            print(df.head())

if __name__ == "__main__":
    main()
