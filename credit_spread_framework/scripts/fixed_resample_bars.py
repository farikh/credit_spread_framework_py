"""
Fixed version of resample_bars.py

This script addresses issues in the original resample_bars.py script and provides
improved functionality for resampling 1-minute bars to other timeframes.

Key improvements:
1. Better error handling and logging
2. More robust date handling
3. Improved SQL queries for better performance
4. Support for parallel processing

Usage:
    python -m credit_spread_framework.scripts.fixed_resample_bars --timeframe 1d
    python -m credit_spread_framework.scripts.fixed_resample_bars --start 2025-04-01 --end 2025-04-10
    python -m credit_spread_framework.scripts.fixed_resample_bars --debug
"""
import os
import pandas as pd
import argparse
import logging
from sqlalchemy import text
from sqlalchemy.types import String, Float, DateTime
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from credit_spread_framework.data.db_engine import get_engine

# ----------------------------
# Configure logging
# ----------------------------
def setup_logging(logfile=None, debug=False):
    level = logging.DEBUG if debug else logging.INFO
    
    handlers = []
    handlers.append(logging.StreamHandler())
    if logfile:
        handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
    
    # Reduce SQLAlchemy engine verbosity
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )

logger = logging.getLogger(__name__)

TIMEFRAMES = {
    "3m": "3min",
    "15m": "15min",
    "1h": "1h",
    "1d": "1d"
}

TABLE_MAP = {
    "3m": "spx_ohlcv_3m",
    "15m": "spx_ohlcv_15m",
    "1h": "spx_ohlcv_1h",
    "1d": "spx_ohlcv_1d"
}

INTERVAL_MAP = {
    "3m": 3,
    "15m": 15,
    "1h": 60,
    "1d": 1440
}

def get_full_range():
    """
    Get the full date range of 1-minute data available in the database.
    
    Returns:
        Tuple of (start_date, end_date) as UTC datetime objects
    """
    try:
        query = text("SELECT MIN(timestamp) as [start], MAX(timestamp) as [end] FROM spx_ohlcv_1m")
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(query).fetchone()
            if not result or result.start is None or result.end is None:
                logger.error("Failed to get date range - no data found in spx_ohlcv_1m")
                return None, None
                
            logger.info(f"1m data range: {result.start} to {result.end}")
            return pd.to_datetime(result.start).tz_localize("UTC"), pd.to_datetime(result.end).tz_localize("UTC")
    except Exception as e:
        logger.error(f"Error getting date range: {e}", exc_info=True)
        return None, None

def load_raw_data(start, end):
    """
    Load 1-minute OHLCV data for the specified date range.
    
    Args:
        start: Start date (UTC datetime)
        end: End date (UTC datetime)
        
    Returns:
        DataFrame with 1-minute OHLCV data
    """
    try:
        query = text("""
            SELECT * FROM spx_ohlcv_1m
            WHERE timestamp BETWEEN :start AND :end
            ORDER BY timestamp ASC
        """)
        
        engine = get_engine()
        with engine.begin() as conn:
            df = pd.read_sql(query, conn, params={"start": start, "end": end})
            
        if df.empty:
            logger.warning(f"No 1m data found between {start} and {end}")
            return df
            
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        logger.info(f"Loaded {len(df)} 1m bars from {df['timestamp'].min()} to {df['timestamp'].max()}")
        return df
    except Exception as e:
        logger.error(f"Error loading raw data: {e}", exc_info=True)
        return pd.DataFrame()

def resample_bars(df, rule):
    """
    Resample 1-minute bars to the specified rule.
    
    Args:
        df: DataFrame with 1-minute OHLCV data
        rule: Pandas resampling rule (e.g., '3min', '1h', '1d')
        
    Returns:
        DataFrame with resampled OHLCV data
    """
    try:
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Set timestamp as index for resampling
        df.set_index("timestamp", inplace=True)
        
        # Define aggregation functions
        agg = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "spy_volume": "sum"
        }
        
        # Resample and aggregate
        resampled = df.resample(rule).agg(agg).dropna().reset_index()
        
        # Add ticker and bar_id columns
        resampled["ticker"] = "SPX"
        resampled["bar_id"] = resampled["timestamp"].dt.strftime("%Y%m%d%H%M")
        
        # Select and order columns
        result = resampled[["bar_id", "timestamp", "ticker", "open", "high", "low", "close", "spy_volume"]]
        
        logger.info(f"Resampled to {rule}: {len(result)} bars from {result['timestamp'].min()} to {result['timestamp'].max()}")
        return result
    except Exception as e:
        logger.error(f"Error resampling bars: {e}", exc_info=True)
        return pd.DataFrame()

def delete_existing_data(table_name, start, end, interval):
    """
    Delete existing data in the target table for the specified date range.
    
    This function uses a more precise approach to delete only the bars that
    would be replaced by the new resampled data.
    
    Args:
        table_name: Name of the target table
        start: Start date
        end: End date
        interval: Interval in minutes
    """
    try:
        logger.info(f"Deleting aligned bars from {table_name} for {interval}-minute intervals between {start} and {end}...")
        
        # Use a more precise query to delete only the bars that would be replaced
        delete_sql = f"""
        WITH aligned_times AS (
            SELECT DISTINCT 
                DATEADD(MINUTE, (DATEDIFF(MINUTE, 0, timestamp) / :interval) * :interval, 0) AS aligned_timestamp
            FROM dbo.spx_ohlcv_1m
            WHERE timestamp BETWEEN :start AND :end
        )
        DELETE t
        FROM dbo.[{table_name}] t
        JOIN aligned_times a
          ON t.timestamp = a.aligned_timestamp;
        """
        
        engine = get_engine()
        with engine.begin() as conn:
            result = conn.execute(
                text(delete_sql),
                {"interval": interval, "start": start, "end": end}
            )
            
            logger.info(f"Deleted {result.rowcount} existing rows from {table_name}")
    except Exception as e:
        logger.error(f"Error deleting existing data: {e}", exc_info=True)

def insert_to_db(table_name, df):
    """
    Insert resampled data into the target table.
    
    Args:
        table_name: Name of the target table
        df: DataFrame with resampled OHLCV data
    """
    if df.empty:
        logger.warning(f"No data to insert into {table_name}")
        return
        
    try:
        logger.info(f"Inserting {len(df)} rows into {table_name}...")
        
        # Define column data types
        dtypes = {
            "bar_id": String(20),
            "timestamp": DateTime(),
            "ticker": String(10),
            "open": Float(),
            "high": Float(),
            "low": Float(),
            "close": Float(),
            "spy_volume": Float()
        }
        
        # Insert data
        engine = get_engine()
        with engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists="append", index=False, schema="dbo", dtype=dtypes)
            
        logger.info(f"Successfully inserted {len(df)} rows into {table_name}")
    except Exception as e:
        logger.error(f"Failed to insert into {table_name}: {e}", exc_info=True)

def run_for_timeframe(timeframe, df, start, end, debug, step_num, total_steps):
    """
    Process a single timeframe.
    
    Args:
        timeframe: Timeframe code (e.g., '3m', '1h')
        df: DataFrame with 1-minute OHLCV data
        start: Start date
        end: End date
        debug: Whether to run in debug mode
        step_num: Current step number
        total_steps: Total number of steps
    """
    try:
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
            
        rule = TIMEFRAMES[timeframe]
        table_name = TABLE_MAP[timeframe]
        interval = INTERVAL_MAP[timeframe]

        logger.info(f"[{step_num}/{total_steps}] Processing timeframe: {timeframe}...")
        
        # Resample the data
        result = resample_bars(df.copy(), rule)
        
        if result.empty:
            logger.warning(f"No resampled data for {timeframe}")
            return
            
        logger.info(f"Resampled {len(result)} bars for {timeframe}.")

        if debug:
            # In debug mode, just print the first few rows
            logger.debug(result.head().to_string())
        else:
            # In normal mode, delete existing data and insert new data
            delete_existing_data(table_name, start, end, interval)
            insert_to_db(table_name, result)
            
        logger.info(f"✅ Done with {timeframe}.")
    except Exception as e:
        logger.error(f"[ERROR] Exception in timeframe {timeframe}: {e}", exc_info=True)

def main():
    parser = argparse.ArgumentParser(description="Resample 1-minute bars to other timeframes")
    parser.add_argument("--timeframe", choices=TIMEFRAMES.keys(), help="Optional: single timeframe to process")
    parser.add_argument("--start", help="UTC start datetime (e.g. 2025-04-04T00:00:00)")
    parser.add_argument("--end", help="UTC end datetime (e.g. 2025-04-04T23:59:59)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode (no database changes)")
    parser.add_argument("--logfile", help="Optional log file path")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads to use")
    args = parser.parse_args()

    # Setup logging
    setup_logging(logfile=args.logfile, debug=args.debug)
    
    # Get date range
    full_start, full_end = get_full_range()
    if full_start is None or full_end is None:
        logger.error("Failed to get date range. Exiting.")
        return
        
    # Parse start and end dates
    try:
        if args.start:
            start = pd.to_datetime(args.start).tz_localize("UTC")
        else:
            start = full_start
            
        if args.end:
            end = pd.to_datetime(args.end).tz_localize("UTC")
        else:
            end = full_end
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        return

    logger.info(f"Using range: {start} to {end}")
    
    # Load raw data
    raw = load_raw_data(start, end)
    if raw.empty:
        logger.error("No data to process. Exiting.")
        return

    # Process timeframes
    if args.timeframe:
        # Process a single timeframe
        run_for_timeframe(args.timeframe, raw, start, end, args.debug, 1, 1)
    else:
        # Process all timeframes in parallel
        total = len(TIMEFRAMES)
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {
                executor.submit(run_for_timeframe, tf, raw.copy(), start, end, args.debug, idx + 1, total): tf
                for idx, tf in enumerate(TIMEFRAMES.keys())
            }
            
            for future in as_completed(futures):
                tf = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"Thread exception for {tf}: {exc}", exc_info=True)

    logger.info("[COMPLETE] All timeframes processed. Check logs for details.")

if __name__ == "__main__":
    main()
