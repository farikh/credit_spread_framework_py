import sqlalchemy as sa
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
import urllib
from sqlalchemy import create_engine, text
import pandas as pd

def save_indicator_values_to_db(values, indicator_name, timeframe):
    print(f"[INFO] Saving values for {indicator_name} on timeframe {timeframe}...")

    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :short_name"),
            {"short_name": indicator_name}
        ).fetchone()

        if result is None:
            print(f"[ERROR] Indicator '{indicator_name}' not found in database.")
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

    print(f"[SUCCESS] Inserted {rows_inserted} indicator values.")
