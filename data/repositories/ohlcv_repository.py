import pandas as pd
import sqlalchemy as sa
import urllib
from sqlalchemy import create_engine, text
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING

def load_bars_from_db(timeframe, start=None, end=None):
    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    # Map timeframe to correct table name based on schema
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

    query = """
        SELECT timestamp_start, [close], spy_volume
        FROM spx_15min_data
        WHERE timeframe = :timeframe
        AND (:start IS NULL OR timestamp_start >= :start)
        AND (:end IS NULL OR timestamp_start <= :end)
        ORDER BY timestamp_start
    """

    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "start": start,
                "end": end
            }
        )
        df = pd.DataFrame(result.fetchall(), columns=["timestamp", "close"])

    if df.empty:
        print(f"[WARNING] No bars found in {table_name} for the selected range.")
    return df
