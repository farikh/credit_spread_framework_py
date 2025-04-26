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
    engine = create_engine()

    thread_name = current_thread().name
    day = values['timestamp_start'].iloc[0].date() if not values.empty else 'N/A'
    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Start saving...")

    insert_stmt = text("""
        INSERT INTO indicator_values (BarId, Timeframe, IndicatorId, Value, TimestampStart, TimestampEnd, Qualifier, ParametersJson)
        VALUES (:bar_id, :timeframe, :indicator_id, :value, :timestamp_start, :timestamp_end, :qualifier, :parameters_json)
    """)

    with engine.begin() as conn:
        # Determine the numeric IndicatorId: prefer metadata from factory, else query DB
        if metadata and "IndicatorId" in metadata:
            indicator_id = metadata["IndicatorId"]
        else:
            indicator_id = conn.execute(
                text("SELECT IndicatorId FROM indicators WHERE ShortName = :name AND IsActive = 1"),
                {"name": indicator_name}
            ).scalar()

        rows_inserted = 0
        for _, row in values.iterrows():
            # Determine which column holds the value (e.g. 'value' or 'rsi')
            value_col = 'value' if 'value' in row.index else 'rsi'
            val = row[value_col]
            if pd.isna(val):
                continue
            # Build BarId and normalize timestamp
            bar_id = f"{row['timestamp_start'].strftime('%Y%m%d%H%M%S')}_{int(val)}_SPX"
            ts = row['timestamp_start']
            try:
                ts = ts.to_pydatetime()
            except AttributeError:
                pass
            # Remove timezone for SQLite compatibility
            if hasattr(ts, 'tzinfo') and ts.tzinfo:
                ts = ts.replace(tzinfo=None)

            # Execute insert for this row
            conn.execute(insert_stmt, {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(val),
                "timestamp_start": ts,
                "timestamp_end": ts,
                "qualifier": row.get("qualifier"),
                "parameters_json": row.get("parameters_json")
            })
            rows_inserted += 1

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Inserted {rows_inserted} rows.")
