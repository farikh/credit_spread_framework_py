from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
from sqlalchemy import text
import pandas as pd
from threading import current_thread
import logging
from datetime import datetime, timedelta

# Alias create_engine for easier testing/monkeypatching
create_engine = get_engine

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

def get_most_recent_indicator_values(indicator_name: str, timeframe: str, target_date: datetime, qualifier: str = None, closest_date=True):
    """
    Retrieve the most recent indicator values relative to the specified date.
    This is useful for carrying forward indicator values that don't change frequently.
    
    Args:
        indicator_name: The short name of the indicator
        timeframe: The timeframe (e.g., '1m', '1h', '1d')
        target_date: The reference date
        qualifier: Optional qualifier to filter by (e.g., 'time', 'linear', 'volume')
        closest_date: If True, find the closest date (before or after). If False, only look before the target date.
        
    Returns:
        DataFrame with the most recent indicator values
    """
    engine = create_engine()
    
    print(f"[DEBUG] Searching for {indicator_name} values on {timeframe} relative to {target_date}")
    
    # First, check if there are any values for this indicator/timeframe
    check_query = """
        SELECT COUNT(*) 
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
    """
    
    with engine.begin() as conn:
        total_count = conn.execute(
            text(check_query),
            {
                "indicator_name": indicator_name,
                "timeframe": timeframe
            }
        ).scalar()
        
        print(f"[DEBUG] Found {total_count} total records for {indicator_name} on {timeframe}")
        
        if total_count == 0:
            return pd.DataFrame()
    
    # Build the query to get values
    # First, find all dates with values
    date_query = """
        SELECT DISTINCT
            CAST(TimestampEnd AS DATE) as DateOnly,
            MIN(TimestampEnd) as FirstTimestamp
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        GROUP BY CAST(TimestampEnd AS DATE)
        ORDER BY DateOnly
    """
    
    # Then get all values from that date
    query = """
        SELECT 
            iv.BarId, iv.Timeframe, iv.IndicatorId, iv.Value, iv.AuxValue, 
            iv.TimestampStart, iv.TimestampEnd, iv.Qualifier, iv.ParametersJson
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND CAST(iv.TimestampEnd AS DATE) = :most_recent_date
        AND (:qualifier IS NULL OR iv.Qualifier = :qualifier)
        ORDER BY iv.Qualifier, iv.Value
    """
    
    with engine.begin() as conn:
        # Find all dates with values
        all_dates = conn.execute(
            text(date_query),
            {
                "indicator_name": indicator_name,
                "timeframe": timeframe
            }
        ).fetchall()
        
        if not all_dates:
            print(f"[DEBUG] No dates found with values")
            return pd.DataFrame()
        
        print(f"[DEBUG] All dates with values:")
        for row in all_dates:
            print(f"[DEBUG]   - {row[0]} (first timestamp: {row[1]})")
        
        # Convert target_date to naive datetime for comparison
        target_date_naive = target_date
        if hasattr(target_date, 'tzinfo') and target_date.tzinfo:
            target_date_naive = target_date.replace(tzinfo=None)
        
        # Convert all dates to Python dates for comparison
        python_dates = []
        for row in all_dates:
            date_only = row[0]
            if not isinstance(date_only, datetime):
                try:
                    date_only = pd.to_datetime(date_only).date()
                except:
                    print(f"[DEBUG] Failed to convert {date_only} to date")
                    continue
            elif hasattr(date_only, 'date'):
                date_only = date_only.date()
            
            python_dates.append((date_only, row[0]))  # (Python date, original date string)
        
        # Find the closest date
        target_date_only = target_date_naive.date()
        closest_date = None
        min_diff = float('inf')
        
        for python_date, original_date in python_dates:
            # Calculate days difference
            diff = abs((python_date - target_date_only).days)
            
            if closest_date is None or diff < min_diff:
                closest_date = original_date
                min_diff = diff
        
        print(f"[DEBUG] Closest date to {target_date_only} is {closest_date} (diff: {min_diff} days)")
        
        # Execute the main query to get all values from the closest date
        result = conn.execute(
            text(query),
            {
                "indicator_name": indicator_name,
                "timeframe": timeframe,
                "most_recent_date": closest_date,
                "qualifier": qualifier
            }
        )
        
        # Convert to DataFrame
        columns = [
            "bar_id", "timeframe", "indicator_id", "value", "aux_value", 
            "timestamp_start", "timestamp_end", "qualifier", "parameters_json"
        ]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
        print(f"[DEBUG] Found {len(df)} previous values to carry forward")
        if not df.empty:
            print(f"[DEBUG] Qualifiers found: {df['qualifier'].tolist()}")
    
    return df

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

            # Prepare parameters
            params = {
                "bar_id": bar_id,
                "timeframe": timeframe,
                "indicator_id": indicator_id,
                "value": float(val),
                "aux_value": int(row.get("aux_value", 0)),
                "timestamp_start": ts_start,
                "qualifier": row.get("qualifier"),
                "parameters_json": row.get("parameters_json")
            }
            
            # Handle timestamp_end (NULL if None)
            if ts_end is None:
                # Use a different SQL statement for NULL timestamp_end
                null_end_stmt = text("""
                    INSERT INTO indicator_values
                      (BarId, Timeframe, IndicatorId, Value, AuxValue, TimestampStart, TimestampEnd, Qualifier, ParametersJson)
                    VALUES
                      (:bar_id, :timeframe, :indicator_id, :value, :aux_value, :timestamp_start, NULL, :qualifier, :parameters_json)
                """)
                conn.execute(null_end_stmt, params)
            else:
                # Use the original statement with timestamp_end
                params["timestamp_end"] = ts_end
                conn.execute(insert_stmt, params)
            rows_inserted += 1

    print(f"[{thread_name}] {indicator_name} on {timeframe} | {day} | Inserted {rows_inserted} rows.")
