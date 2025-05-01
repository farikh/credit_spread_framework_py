import os
import sys
from sqlalchemy import text
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ''))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the database engine
from credit_spread_framework.data.db_engine import get_engine

def load_bars_improved(timeframe, start=None, end=None, limit=4000, debug=False):
    """
    Load OHLCV bars from the database with improved date handling.
    
    This function addresses several issues:
    1. Handles UTC to EST conversion for date ranges
    2. Ensures full 24-hour coverage when same date is specified
    3. Uses a single UNION query for better performance
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start : str or datetime, optional
        Start date for data range (in EST)
    end : str or datetime, optional
        End date for data range (in EST)
    limit : int, optional
        Maximum number of historical bars to return (default: 4000)
    debug : bool, optional
        Whether to print debug information
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    engine = get_engine()

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
    
    # Convert string dates to datetime objects if needed
    if isinstance(start, str):
        start = datetime.fromisoformat(start.replace('Z', '+00:00'))
    if isinstance(end, str):
        end = datetime.fromisoformat(end.replace('Z', '+00:00'))
    
    # If the same date is specified for both start and end, ensure full 24-hour coverage
    if start and end and start.date() == end.date():
        # Set start to beginning of day (00:00:00)
        start = datetime.combine(start.date(), datetime.min.time())
        # Set end to end of day (23:59:59)
        end = datetime.combine(end.date(), datetime.max.time())
        
        if debug:
            print(f"Adjusted date range to cover full 24 hours: {start} to {end}")
    
    # Adjust for UTC to EST conversion (approximately -5 hours)
    # This is a simplified approach - for production, use proper timezone libraries
    utc_offset = timedelta(hours=5)  # EST is UTC-5 (ignoring daylight saving)
    
    if start:
        start_utc = start + utc_offset
        if debug:
            print(f"Adjusted start date from EST {start} to UTC {start_utc}")
    else:
        start_utc = None
        
    if end:
        end_utc = end + utc_offset
        if debug:
            print(f"Adjusted end date from EST {end} to UTC {end_utc}")
    else:
        end_utc = None
    
    # Build a single UNION query that handles all cases
    if start_utc is None and end_utc is not None:
        # Case 1: Only end date specified
        query = f"""
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open]   AS open_price,
                    [high]   AS high,
                    [low]    AS low,
                    [close]  AS close_price,
                    spy_volume
                FROM dbo.{table_name}
                WHERE timestamp <= :end
                ORDER BY timestamp DESC
            ) sub
            ORDER BY timestamp ASC
        """
        params = {"end": end_utc}
        
    elif start_utc is not None:
        # Case 2 & 3: Start date specified (with or without end date)
        # Use a UNION query to get both the range data and historical data in one query
        query = f"""
            -- Get records in the date range
            SELECT
                bar_id,
                timestamp,
                [open]   AS open_price,
                [high]   AS high,
                [low]    AS low,
                [close]  AS close_price,
                spy_volume
            FROM dbo.{table_name}
            WHERE timestamp >= :start
              AND (:end IS NULL OR timestamp <= :end)
            
            UNION ALL
            
            -- Get historical records before the start date
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open]   AS open_price,
                    [high]   AS high,
                    [low]    AS low,
                    [close]  AS close_price,
                    spy_volume
                FROM dbo.{table_name}
                WHERE timestamp < :start
                ORDER BY timestamp DESC
            ) sub
            
            -- Order the combined results
            ORDER BY timestamp ASC
        """
        params = {"start": start_utc, "end": end_utc}
    
    else:
        # Case 4: No dates specified, get the most recent data
        query = f"""
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open]   AS open_price,
                    [high]   AS high,
                    [low]    AS low,
                    [close]  AS close_price,
                    spy_volume
                FROM dbo.{table_name}
                ORDER BY timestamp DESC
            ) sub
            ORDER BY timestamp ASC
        """
        params = {}
    
    if debug:
        print(f"Executing query on table {table_name}:")
        print(query)
        print(f"With parameters: {params}")
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(text(query), params)
        df = pd.DataFrame(result.fetchall(), columns=[
            "bar_id", "timestamp", "open_price", "high", "low", "close_price", "spy_volume"
        ])
    
    if debug:
        print(f"Query returned {len(df)} rows")
        if not df.empty:
            print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    if df.empty:
        print(f"[WARNING] No bars found in {table_name} for the selected range.")
    
    # Convert UTC timestamps back to EST for consistency
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'] - utc_offset
        if debug:
            print(f"Converted timestamps from UTC back to EST")
            print(f"Adjusted date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    return df

def test_query(timeframe, start=None, end=None, limit=4000):
    """Test the improved query with the given parameters."""
    print(f"\nTesting improved query with:")
    print(f"  Timeframe: {timeframe}")
    print(f"  Start date: {start}")
    print(f"  End date: {end}")
    print(f"  Limit: {limit}")
    
    try:
        df = load_bars_improved(timeframe, start, end, limit, debug=True)
        
        if not df.empty:
            print("\nResults summary:")
            print(f"  Total rows: {len(df)}")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            print("\nFirst 5 rows:")
            print(df.head().to_string())
            print("\nLast 5 rows:")
            print(df.tail().to_string())
        else:
            print("No data returned.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test improved OHLCV query')
    parser.add_argument('--timeframe', type=str, default='1d', 
                        choices=['1m', '3m', '15m', '1h', '1d'],
                        help='Timeframe for data')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--limit', type=int, default=4000, 
                        help='Maximum number of bars to return')
    
    args = parser.parse_args()
    
    test_query(args.timeframe, args.start, args.end, args.limit)
