
import os
import pandas as pd
import argparse
from sqlalchemy import text
from sqlalchemy.types import String, Float, DateTime
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from data.db_engine import engine
import sys
import io

os.environ["PYTHONIOENCODING"] = "utf-8"

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

log_file = open("resample_output.log", "w", buffering=1, encoding="utf-8")
sys.stdout = io.TextIOWrapper(log_file.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(log_file.buffer, encoding="utf-8", line_buffering=True)

def clean_text(s):
    try:
        return str(s)
    except Exception as e:
        return f"[ENCODE ERROR] {e} | Raw: {repr(s)}"

def log(message):
    encoded = clean_text(message)
    debugged = encoded.encode("utf-8", errors="backslashreplace").decode("utf-8")
    print(debugged, flush=True)

def get_full_range():
    query = text("SELECT MIN(timestamp) as [start], MAX(timestamp) as [end] FROM spx_ohlcv_1m")
    with engine.begin() as conn:
        result = conn.execute(query).fetchone()
        log(f"[DEBUG] Full 1m range: {result.start} to {result.end}")
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
    log(f"[DEBUG] Loaded {len(df)} 1m bars")
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

def delete_existing_data(table_name, start, end):
    log(f"[INFO] Deleting rows from {table_name} between {start} and {end}")
    with engine.begin() as conn:
        conn.execute(
            text(f"""DELETE FROM [dbo].[{table_name}] WHERE timestamp >= :start AND timestamp < :end"""), 
            {"start": start, "end": end}
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
        log(f"[INFO] Inserting {len(df)} rows into {table_name}...")
        with engine.begin() as conn:
            df.to_sql(table_name, con=conn, if_exists="append", index=False, schema="dbo", dtype=dtypes)
            count = conn.execute(
                text(f"""SELECT COUNT(*) FROM [dbo].[{table_name}] WHERE timestamp BETWEEN :start AND :end"""), 
                {"start": df['timestamp'].min(), "end": df['timestamp'].max()}
            ).scalar()
            log(f"[VERIFY] {count} rows now in {table_name} for that range.")
    except Exception as e:
        log(f"[ERROR] Failed to insert into {table_name}: {e}")

def run_for_timeframe(timeframe, df, start, end, debug):
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"[ERROR] Invalid timeframe: {timeframe}")
    rule = TIMEFRAMES[timeframe]
    table_name = TABLE_MAP[timeframe]

    log(f"[{timeframe}] Resampling...")
    result = resample_bars(df.copy(), rule)
    log(f"[{timeframe}] Resampled to {len(result)} bars")

    if debug:
        log(f"[{timeframe}] DEBUG preview:")
        log(result.head().to_string())
        log(f"[{timeframe}] Would insert {len(result)} rows into {table_name}")
    else:
        delete_existing_data(table_name, start, end)
        insert_to_db(table_name, result)
        log(f"[{timeframe}] ✅ Done.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeframe", choices=TIMEFRAMES.keys(), help="Optional: single timeframe to process")
    parser.add_argument("--start", help="UTC start datetime (e.g. 2025-04-04T00:00:00)")
    parser.add_argument("--end", help="UTC end datetime (e.g. 2025-04-04T23:59:59)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    full_start, full_end = get_full_range()
    start = pd.to_datetime(args.start).tz_localize("UTC") if args.start else full_start
    end = pd.to_datetime(args.end).tz_localize("UTC") if args.end else full_end

    log(f"[INFO] Using range: {start} to {end}")
    raw = load_raw_data(start, end)

    if args.timeframe:
        run_for_timeframe(args.timeframe, raw, start, end, args.debug)
    else:
        log("[INFO] Running all timeframes in parallel...")
        with ThreadPoolExecutor() as executor:
            for tf in TIMEFRAMES.keys():
                executor.submit(run_for_timeframe, tf, raw.copy(), start, end, args.debug)

if __name__ == "__main__":
    main()