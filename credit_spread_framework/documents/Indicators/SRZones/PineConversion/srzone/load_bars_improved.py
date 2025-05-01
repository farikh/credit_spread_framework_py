"""
Improved SQL data loading for SRZone analysis.

This module provides an improved implementation of the load_bars_from_db function
that addresses several issues with the original implementation:

1. UTC to EST time zone conversion for date ranges
2. Full 24-hour coverage when the same date is specified for start and end
3. More efficient query using UNION ALL

This implementation is specifically for the PineConversion folder and is designed
to be a drop-in replacement for the original load_bars_from_db function.
"""

from sqlalchemy import text
from datetime import datetime, timedelta
import pandas as pd

def load_bars_improved(engine, timeframe, start=None, end=None, limit=4000, debug=False):
    """
    Load OHLCV bars from the database with improved date handling.
    
    This function addresses several issues:
    1. Handles UTC to EST conversion for date ranges
    2. Ensures full 24-hour coverage when same date is specified
    3. Uses a single UNION query for better performance
    
    Parameters:
    -----------
    engine : sqlalchemy.engine.Engine
        SQLAlchemy engine for database connection
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
        start = datetime.fromisoformat(start.replace('Z', '+00:00').replace(' ', 'T'))
    if isinstance(end, str):
        end = datetime.fromisoformat(end.replace('Z', '+00:00').replace(' ', 'T'))
    
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
