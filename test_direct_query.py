"""
Test script for directly executing the improved SQL query.

This script demonstrates how to use the improved SQL query to retrieve data
for a specific date range, with proper handling of time zones and date ranges.
"""

import os
import sys
import argparse
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_engine():
    """Get a SQLAlchemy engine for connecting to the database."""
    import urllib
    from sqlalchemy import create_engine
    
    conn_str = os.getenv("SQLSERVER_CONN_STRING")
    if not conn_str:
        raise RuntimeError("No SQL connection string found! Check your .env file.")
    
    conn_str_encoded = urllib.parse.quote_plus(conn_str)
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={conn_str_encoded}",
        echo=False,
        connect_args={"autocommit": True}
    )

def execute_improved_query(timeframe, start_date=None, end_date=None, limit=4000):
    """
    Execute the improved SQL query directly.
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start_date : str, optional
        Start date for data range (YYYY-MM-DD)
    end_date : str, optional
        End date for data range (YYYY-MM-DD)
    limit : int, optional
        Maximum number of bars to return (default: 4000)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    # Table mapping
    table_map = {
        "1m": "spx_ohlcv_1m",
        "3m": "spx_ohlcv_3m",
        "15m": "spx_ohlcv_15m",
        "1h": "spx_ohlcv_1h",
        "1d": "spx_ohlcv_1d",
    }
    
    if timeframe not in table_map:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Must be one of {list(table_map.keys())}")
    
    table_name = table_map[timeframe]
    
    # Convert string dates to datetime objects
    if start_date:
        start = datetime.fromisoformat(start_date)
        # Set to beginning of day
        start = datetime.combine(start.date(), datetime.min.time())
    else:
        start = None
        
    if end_date:
        end = datetime.fromisoformat(end_date)
        # Set to end of day
        end = datetime.combine(end.date(), datetime.max.time())
    else:
        end = None
    
    print(f"Date range: {start} to {end}")
    
    # Build the query
    if start is None and end is not None:
        # Case 1: Only end date specified
        query = f"""
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open],
                    [high],
                    [low],
                    [close],
                    spy_volume
                FROM dbo.{table_name}
                WHERE CONVERT(date, timestamp) <= CONVERT(date, :end)
                ORDER BY timestamp DESC
            ) sub
            ORDER BY timestamp ASC
        """
        params = {"end": end}
    elif start is not None:
        # Case 2 & 3: Start date specified (with or without end date)
        query = f"""
            -- Get records in the date range
            SELECT
                bar_id,
                timestamp,
                [open],
                [high],
                [low],
                [close],
                spy_volume
            FROM dbo.{table_name}
            WHERE CONVERT(date, timestamp) >= CONVERT(date, :start)
              AND (:end IS NULL OR CONVERT(date, timestamp) <= CONVERT(date, :end))
            
            UNION ALL
            
            -- Get historical records before the start date
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open],
                    [high],
                    [low],
                    [close],
                    spy_volume
                FROM dbo.{table_name}
                WHERE CONVERT(date, timestamp) < CONVERT(date, :start)
                ORDER BY timestamp DESC
            ) sub
            
            -- Order the combined results
            ORDER BY timestamp ASC
        """
        params = {"start": start, "end": end}
    else:
        # Case 4: No dates specified
        query = f"""
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open],
                    [high],
                    [low],
                    [close],
                    spy_volume
                FROM dbo.{table_name}
                ORDER BY timestamp DESC
            ) sub
            ORDER BY timestamp ASC
        """
        params = {}
    
    print(f"Executing query on table {table_name}:")
    print(query)
    print(f"With parameters: {params}")
    
    # Get the engine and execute the query
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=[
            "bar_id", "timestamp", "open", "high", "low", "close", "spy_volume"
        ])
    
    print(f"Query returned {len(df)} rows")
    if not df.empty:
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def main():
    """Main function to parse arguments and execute the query."""
    parser = argparse.ArgumentParser(description='Test improved SQL query')
    parser.add_argument('--timeframe', type=str, required=True,
                        choices=['1m', '3m', '15m', '1h', '1d'],
                        help='Timeframe for data')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=4000,
                        help='Maximum number of bars to return')
    parser.add_argument('--output', type=str, help='Output CSV file path')
    
    args = parser.parse_args()
    
    try:
        # Execute the query
        df = execute_improved_query(
            timeframe=args.timeframe,
            start_date=args.start,
            end_date=args.end,
            limit=args.limit
        )
        
        # Print summary
        print("\nData Summary:")
        print(f"  - Total rows: {len(df)}")
        
        if not df.empty:
            print(f"  - Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print(f"  - Columns: {df.columns.tolist()}")
            
            # Print first and last few rows
            print(f"\nFirst 5 rows:")
            print(df.head().to_string())
            print(f"\nLast 5 rows:")
            print(df.tail().to_string())
            
            # Save to CSV if output path is specified
            if args.output:
                df.to_csv(args.output, index=False)
                print(f"\nData saved to {args.output}")
        else:
            print("No data found for the specified parameters.")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
