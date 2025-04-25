
import os
import pandas as pd
import argparse
import logging
from sqlalchemy import text
from sqlalchemy.types import String, Float, DateTime
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from data.db_engine import engine

# ----------------------------
# Configure logging
# ----------------------------
def setup_logging(logfile=None):
    handlers = []
    if logfile:
        handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
    
    # Reduce SQLAlchemy engine verbosity
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
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
    query = text("SELECT MIN(timestamp) as [start], MAX(timestamp) as [end] FROM spx_ohlcv_1m")
    with engine.begin() as conn:
        result = conn.execute(query).fetchone()
        logger.info(f"1m data range: {result.start} to {result.end}")
        return pd.to_datetime(result.start).tz_localize("UTC"), pd.to_datetime(result.end).tz_localize("UTC")

def load_raw_data(start, end):
    query = text("""
        SELECT * FROM spx_ohlcv_1m
        WHERE timestamp BETWEEN :start AND :end
        ORDER BY timestamp ASC
    """)
    with engine.begin() as conn:
        df = pd.read_sql(query, conn, params={"start": start, "end": end})
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    logger.info(f"Loaded {len(df)} 1m bars.")
    return df

def resample_bars(df, rule):
    df.set_index("timestamp", inplace=True)
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "spy_volume": "sum"
    }
    resampled = df.resample(rule).agg(agg).dropna().reset_index()
    resampled["ticker"] = "SPX"
    resampled["bar_id"] = resampled["timestamp"].dt.strftime("%Y%m%d%H%M")
    return resampled[["bar_id", "timestamp", "ticker", "open", "high", "low", "close", "spy_volume"]]

def delete_existing_data(table_name, start, end, interval):
    logger.info(f"Deleting aligned bars from {table_name} for {interval}-minute intervals between {start} and {end}...")
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
    with engine.begin() as conn:
        conn.execute(
            text(delete_sql),
            {"interval": interval, "start": start, "end": end}
        )

def insert_to_db(table_name, df):
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
    try:
        logger.info(f"Inserting {len(df)} rows into {table_name}...")
        with engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists="append", index=False, schema="dbo", dtype=dtypes)
    except Exception as e:
        logger.error(f"Failed to insert into {table_name}: {e}", exc_info=True)

def run_for_timeframe(timeframe, df, start, end, debug, step_num, total_steps):
    try:
        if timeframe not in TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        rule = TIMEFRAMES[timeframe]
        table_name = TABLE_MAP[timeframe]
        interval = INTERVAL_MAP[timeframe]

        logger.info(f"[{step_num}/{total_steps}] Processing timeframe: {timeframe}...")
        result = resample_bars(df.copy(), rule)
        logger.info(f"Resampled {len(result)} bars for {timeframe}.")

        if debug:
            logger.debug(result.head().to_string())
        else:
            delete_existing_data(table_name, start, end, interval)
            insert_to_db(table_name, result)
        logger.info(f"✅ Done with {timeframe}.")
    except Exception as e:
        logger.error(f"[ERROR] Exception in timeframe {timeframe}: {e}", exc_info=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", choices=TIMEFRAMES.keys(), help="Optional: single timeframe to process")
    parser.add_argument("--start", help="UTC start datetime (e.g. 2025-04-04T00:00:00)")
    parser.add_argument("--end", help="UTC end datetime (e.g. 2025-04-04T23:59:59)")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--logfile", help="Optional log file path")
    args = parser.parse_args()

    setup_logging(logfile=args.logfile)
    full_start, full_end = get_full_range()
    start = pd.to_datetime(args.start).tz_localize("UTC") if args.start else full_start
    end = pd.to_datetime(args.end).tz_localize("UTC") if args.end else full_end

    logger.info(f"Using range: {start} to {end}")
    raw = load_raw_data(start, end)

    if args.timeframe:
        run_for_timeframe(args.timeframe, raw, start, end, args.debug, 1, 1)
    else:
        total = len(TIMEFRAMES)
        with ThreadPoolExecutor() as executor:
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
