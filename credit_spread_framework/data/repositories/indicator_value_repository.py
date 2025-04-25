from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
from sqlalchemy import text
import pandas as pd
from threading import current_thread
import logging

# Alias create_engine for easier testing/monkeypatching
create_engine = get_engine

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def save_indicator_values_to_db(values: pd.DataFrame, indicator_name: str, timeframe: str, metadata=None):
    """
    Save indicator values to the database. Fetches the IndicatorId dynamically.
    """
    # Create a new engine/connection (monkeypatchable via create_engine)
    engine = create_engine(SQLSERVER_CONN_STRING)

    thread_name = current_thread().name
    day = values['timestamp_start'].iloc[0].date() if not values.empty else 'N/A'
    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Start saving...")

    insert_stmt = text("""
        INSERT INTO indicator_values (BarId, Timeframe, IndicatorId, Value, TimestampStart)
        VALUES (:bar_id, :timeframe, :indicator_id, :value, :timestamp_start)
    """)

    with engine.begin() as conn:
        # Fetch the numeric IndicatorId from the DB
        result = conn.execute(
            text("SELECT IndicatorId FROM indicator_metadata WHERE Name = :name AND Timeframe = :timeframe"),
            {"name": indicator_name, "timeframe": timeframe}
        )
        indicator_id = result.fetchone()[0]

        rows_inserted = 0
        for _, row in values.iterrows():
            # Determine which column holds the value (e.g. 'value' or 'rsi')
            value_col = 'value' if 'value' in row.index else 'rsi'
            val = row[value_col]
            if pd.isna(val):
                continue

            bar_id = f"{row['timestamp_start'].strftime('%Y%m%d%H%M')}_SPX"
            conn.execute(insert_stmt, {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(val),
                "timestamp_start": row['timestamp_start']
            })
            rows_inserted += 1

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Inserted {rows_inserted} rows.")
