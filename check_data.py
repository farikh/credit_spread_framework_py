"""
Script to check if there's data in the database for a specific date.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd

def check_data_for_date(date_str, timeframe):
    """
    Check if there's data in the database for a specific date and timeframe.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        timeframe: Timeframe (e.g., '1m', '3m', '15m', '1h', '1d')
    """
    engine = get_engine()
    
    # Determine the table name based on the timeframe
    table_name = f"spx_ohlcv_{timeframe}"
    
    # Build the query
    query = text(f"""
        SELECT COUNT(*) as count
        FROM dbo.{table_name}
        WHERE CAST(timestamp AS DATE) = :date
    """)
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(query, {"date": date_str})
        count = result.scalar()
        
    print(f"Found {count} rows in {table_name} for date {date_str}")
    
    # If there's data, show a sample
    if count > 0:
        sample_query = text(f"""
            SELECT TOP 5 *
            FROM dbo.{table_name}
            WHERE CAST(timestamp AS DATE) = :date
            ORDER BY timestamp
        """)
        
        with engine.begin() as conn:
            result = conn.execute(sample_query, {"date": date_str})
            rows = result.fetchall()
            
            print("\nSample data:")
            for row in rows:
                print(row)

def check_date_range():
    """Check the date range available in the database."""
    engine = get_engine()
    
    timeframes = ['1m', '3m', '15m', '1h', '1d']
    
    for timeframe in timeframes:
        table_name = f"spx_ohlcv_{timeframe}"
        
        query = text(f"""
            SELECT 
                MIN(CAST(timestamp AS DATE)) as min_date,
                MAX(CAST(timestamp AS DATE)) as max_date,
                COUNT(*) as total_rows
            FROM dbo.{table_name}
        """)
        
        with engine.begin() as conn:
            result = conn.execute(query)
            row = result.fetchone()
            
            if row and row.min_date and row.max_date:
                print(f"{table_name}: {row.min_date} to {row.max_date} ({row.total_rows} rows)")
            else:
                print(f"{table_name}: No data found")

if __name__ == "__main__":
    # Check date range
    print("Checking date range in the database...")
    check_date_range()
    
    # Check specific dates
    print("\nChecking data for specific dates...")
    dates_to_check = ["2025-04-03", "2025-04-02", "2025-04-01"]
    timeframes = ['1m', '3m', '15m', '1h', '1d']
    
    for date_str in dates_to_check:
        print(f"\nChecking data for {date_str}:")
        for timeframe in timeframes:
            check_data_for_date(date_str, timeframe)
