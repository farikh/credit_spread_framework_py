from credit_spread_framework.data.db_engine import get_engine
import pandas as pd
from sqlalchemy import text

def load_bars_from_db(timeframe, start=None, end=None, limit=None):
    engine = get_engine()

    # Correct mapping based on your confirmed schema
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

    # If limit is provided, use a more efficient query that gets the most recent bars
    # relative to the end date in descending order, then reverses them back to ascending
    if limit is not None:
        # Modified query to get bars up to end_date going backwards, ignoring start_date
        query = f"""
            SELECT * FROM (
                SELECT TOP {limit}
                    bar_id,
                    timestamp,
                    [open]   AS open_price,
                    [high]   AS high,
                    [low]    AS low,
                    [close]  AS close_price,
                    spy_volume
                FROM dbo.{table_name}
                WHERE (:end IS NULL OR timestamp <= :end)
                ORDER BY timestamp DESC
            ) sub
            ORDER BY timestamp ASC
        """
    else:
        # Original query without limit
        query = f"""
            SELECT 
                bar_id,
                timestamp,
                [open]   AS open_price,
                [high]   AS high,
                [low]    AS low,
                [close]  AS close_price,
                spy_volume
            FROM dbo.{table_name}
            WHERE (:start IS NULL OR timestamp >= :start)
              AND (:end IS NULL OR timestamp <= :end)
            ORDER BY timestamp
        """

    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "start": start,
                "end": end
            }
        )
        df = pd.DataFrame(result.fetchall(), columns=[
            "bar_id", "timestamp", "open_price", "high", "low", "close_price", "spy_volume"
        ])

    if df.empty:
        print(f"[WARNING] No bars found in {table_name} for the selected range.")

    return df
