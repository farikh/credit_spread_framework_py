from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
from sqlalchemy import text
import pandas as pd
from threading import current_thread
import logging

# Alias create_engine for easier testing/monkeypatching
create_engine = get_engine

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def save_indicator_values_to_db(values: pd.DataFrame, indicator_name: str, timeframe: str, metadata=None, start_dt=None, end_dt=None):
    """
    Save indicator values to the database. Fetches the IndicatorId dynamically.
    """
    engine = create_engine()
    thread_name = current_thread().name
    day = values['timestamp_start'].iloc[0].date() if not values.empty else 'N/A'
    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Start saving...")

    insert_stmt = text("""
        INSERT INTO indicator_values
          (BarId, Timeframe, IndicatorId, Value, AuxValue, TimestampStart, TimestampEnd, Qualifier, ParametersJson)
        VALUES
          (:bar_id, :timeframe, :indicator_id, :value, :aux_value, :timestamp_start, :timestamp_end, :qualifier, :parameters_json)
    """)

    with engine.begin() as conn:
        # Determine numeric IndicatorId
        indicator_id = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :name AND IsActive = 1"),
            {"name": indicator_name}
        ).scalar()

        # Purge existing entries for this indicator/timeframe within the specified date window
        delete_sql = """
            DELETE FROM indicator_values
            WHERE IndicatorId = :id
              AND Timeframe = :tf
        """
        params = {"id": indicator_id, "tf": timeframe}
        if start_dt is not None:
            delete_sql += " AND TimestampStart >= :start_dt"
            params["start_dt"] = start_dt
        if end_dt is not None:
            delete_sql += " AND TimestampEnd <= :end_dt"
            params["end_dt"] = end_dt
        conn.execute(text(delete_sql), params)

        rows_inserted = 0
        for _, row in values.iterrows():
            # Choose value column
            val = row.get("value", row.get("rsi"))
            if pd.isna(val):
                continue

            # Build BarId and normalize timestamps
            bar_id = f"{row['timestamp_start'].strftime('%Y%m%d%H%M%S')}_{int(val)}_SPX"

            ts_start = row['timestamp_start']
            try:
                ts_start = ts_start.to_pydatetime()
            except AttributeError:
                pass
            if hasattr(ts_start, 'tzinfo') and ts_start.tzinfo:
                ts_start = ts_start.replace(tzinfo=None)

            ts_end = row.get('timestamp_end', row['timestamp_start'])
            try:
                ts_end = ts_end.to_pydatetime()
            except AttributeError:
                pass
            if hasattr(ts_end, 'tzinfo') and ts_end.tzinfo:
                ts_end = ts_end.replace(tzinfo=None)

            # Insert row
            conn.execute(insert_stmt, {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(val),
                "aux_value": int(row.get("aux_value", 0)),
                "timestamp_start": ts_start,
                "timestamp_end": ts_end,
                "qualifier": row.get("qualifier"),
                "parameters_json": row.get("parameters_json")
            })
            rows_inserted += 1

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Inserted {rows_inserted} rows.")
