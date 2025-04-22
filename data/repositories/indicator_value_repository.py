import sqlalchemy as sa
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
import urllib
from sqlalchemy import create_engine, text
import pandas as pd

def save_indicator_values_to_db(values, indicator_name, timeframe):
    print(f"[INFO] Saving values for {indicator_name} on timeframe {timeframe}...")

    # Setup DB engine
    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    # Resolve IndicatorId from indicators table
    with engine.begin() as conn:  # Safely starts transaction, handles commit/rollback automatically
        result = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :short_name"),
            {"short_name": indicator_name}
        ).fetchone()

        if result is None:
            print(f"[ERROR] Indicator '{indicator_name}' not found in database.")
            return
        indicator_id = result[0]

        insert_stmt = text("""
            INSERT INTO indicator_values (BarId, Timeframe, IndicatorId, Value, TimestampStart, TimestampEnd)
            VALUES (:bar_id, :timeframe, :indicator_id, :value, :timestamp_start, :timestamp_end)
        """)

        rows_inserted = 0
        for i, (timestamp, value) in enumerate(values.items()):
            if pd.isna(value):
                continue  # Skip NaNs

            bar_id = f"{timestamp.strftime('%Y%m%d%H%M')}_SPX"
            conn.execute(insert_stmt, {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(value),
                "timestamp_start": timestamp,
                "timestamp_end": None
            })
            rows_inserted += 1

    print(f"[SUCCESS] Inserted {rows_inserted} indicator values.")
