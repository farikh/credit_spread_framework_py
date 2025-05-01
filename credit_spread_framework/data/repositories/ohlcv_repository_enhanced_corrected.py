from credit_spread_framework.data.db_engine import get_engine
import pandas as pd
from sqlalchemy import text

def load_bars_from_db(timeframe, start=None, end=None, limit=4000):
    """
    Load OHLCV bars from the database with enhanced date range handling.
    
    This function implements the following logic:
    1. When only start date is specified:
       - All records on or after the start date
       - PLUS additional records before the start date up to 4000 records total
       - Total could be more than 4000 if there are many records after the start date
    
    2. When only end date is specified:
       - All records on or before the end date, up to 4000 bars total
    
    3. When both start and end date are specified:
       - All records between start date and end date (inclusive)
       - PLUS additional records before the start date up to 4000 records total
       - Total could be more than 4000 if there are many records between start and end date
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start : str or datetime, optional
        Start date for data range
    end : str or datetime, optional
        End date for data range
    limit : int, optional
        Maximum number of bars to return before the start date (default: 4000)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    engine = get_engine()

    # Correct mapping based on your confirmed schema
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

    # Case 1: Only end date is specified
    if start is None and end is not None:
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
        params = {"end": end}
        
        with engine.begin() as conn:
            result = conn.execute(text(query), params)
            df = pd.DataFrame(result.fetchall(), columns=[
                "bar_id", "timestamp", "open_price", "high", "low", "close_price", "spy_volume"
            ])
    
    # Case 2 & 3: Only start date is specified or both dates are specified
    else:
        # First, get all records between start and end date (or after start date if end is None)
        range_query = f"""
            SELECT
                bar_id,
                timestamp,
                [open]   AS open_price,
                [high]   AS high,
                [low]    AS low,
                [close]  AS close_price,
                spy_volume
            FROM dbo.{table_name}
            WHERE (:start IS NULL OR timestamp >= :start)
              AND (:end IS NULL OR timestamp <= :end)
            ORDER BY timestamp
        """
        
        with engine.begin() as conn:
            range_result = conn.execute(
                text(range_query),
                {
                    "start": start,
                    "end": end
                }
            )
            range_df = pd.DataFrame(range_result.fetchall(), columns=[
                "bar_id", "timestamp", "open_price", "high", "low", "close_price", "spy_volume"
            ])
        
        # Get additional bars before the start date (always up to 'limit' additional bars)
        if start is not None:
            history_query = f"""
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
            """
            
            with engine.begin() as conn:
                history_result = conn.execute(
                    text(history_query),
                    {"start": start}
                )
                history_df = pd.DataFrame(history_result.fetchall(), columns=[
                    "bar_id", "timestamp", "open_price", "high", "low", "close_price", "spy_volume"
                ])
            
            # Combine the dataframes
            if not history_df.empty:
                # Sort history_df in ascending order
                history_df = history_df.sort_values("timestamp")
                # Concatenate history_df and range_df
                df = pd.concat([history_df, range_df])
            else:
                df = range_df
        else:
            df = range_df

    if df.empty:
        print(f"[WARNING] No bars found in {table_name} for the selected range.")

    return df
