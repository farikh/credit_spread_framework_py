from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import sqlalchemy as sa
import urllib
import pandas as pd
from threading import current_thread
import logging

# Reduce SQLAlchemy engine verbosity:
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

engine = get_engine()

def save_indicator_values_to_db(values, indicator_name, timeframe):
    thread_name = current_thread().name

    # Determine day (if possible)
    day = values['timestamp_start'].iloc[0].date() if not values.empty else 'N/A'

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Start saving...")

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :short_name"),
            {"short_name": indicator_name}
        ).fetchone()

        if result is None:
            print(f"[{thread_name}] [ERROR] Indicator '{indicator_name}' not found in database.")
            return

        indicator_id = result[0]

        insert_stmt = text("""
            INSERT INTO indicator_values (BarId, Timeframe, IndicatorId, Value, TimestampStart)
            VALUES (:bar_id, :timeframe, :indicator_id, :value, :timestamp_start)
        """)

        rows_inserted = 0
        for _, row in values.iterrows():
            value = row['rsi']
            if pd.isna(value):
                continue  # Skip NaNs

            bar_id = f"{row['timestamp_start'].strftime('%Y%m%d%H%M')}_SPX"
            conn.execute(insert_stmt, {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(value),
                "timestamp_start": row['timestamp_start']
            })
            rows_inserted += 1

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Inserted {rows_inserted} rows.")
