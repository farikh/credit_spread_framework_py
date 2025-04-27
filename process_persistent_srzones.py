"""
Script to process SR zones with historical persistence.

This script will:
1. Process new SR zones for a given date
2. Retrieve existing active SR zones
3. Combine them, giving priority to newer zones
4. Check for invalidation of existing zones
5. Save the updated zones to the database

Usage:
    python process_persistent_srzones.py --start 2025-04-03 --end 2025-04-03 --timeframe 1d
"""
import typer
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.indicators.factory import get_indicator_class
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db
from concurrent.futures import ThreadPoolExecutor

app = typer.Typer()

def get_active_sr_zones(indicator_name, timeframe, end_date=None):
    """
    Retrieve all active SR zones (where TimestampEnd is NULL or after the specified date).
    
    Args:
        indicator_name: The short name of the indicator (e.g., 'srzones')
        timeframe: The timeframe (e.g., '1d')
        end_date: Optional date to filter zones that are active on or after this date
        
    Returns:
        DataFrame with active SR zones
    """
    engine = get_engine()
    
    query = """
        SELECT 
            iv.BarId, iv.Timeframe, iv.IndicatorId, iv.Value, iv.AuxValue, 
            iv.TimestampStart, iv.TimestampEnd, iv.Qualifier, iv.ParametersJson
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND (iv.TimestampEnd IS NULL OR iv.TimestampEnd >= :end_date)
        ORDER BY iv.Qualifier, iv.Value
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "indicator_name": indicator_name,
                "timeframe": timeframe,
                "end_date": end_date or datetime.now()
            }
        )
        
        # Convert to DataFrame
        columns = [
            "bar_id", "timeframe", "indicator_id", "value", "aux_value", 
            "timestamp_start", "timestamp_end", "qualifier", "parameters_json"
        ]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    print(f"Found {len(df)} active SR zones for {indicator_name} on {timeframe}")
    return df

def check_zone_invalidation(zone_value, bars, atr_multiple=2.0, max_distance_percent=20.0):
    """
    Check if an SR zone has been invalidated by price action.
    
    A zone is considered invalidated if:
    1. Price has crossed the zone and moved a significant distance beyond it
    2. The zone is too far from the current price range (outside max_distance_percent)
    
    Args:
        zone_value: The price level of the SR zone
        bars: DataFrame of OHLCV bars to check against
        atr_multiple: How many ATRs price must move beyond the zone to invalidate it
        max_distance_percent: Maximum distance from current price range as a percentage
        
    Returns:
        Boolean indicating if the zone is invalidated, and the invalidation date if applicable
    """
    if bars.empty:
        return False, None
    
    # Check if the DataFrame has the required columns
    required_columns = ['high', 'low']
    for col in required_columns:
        if col not in bars.columns:
            print(f"WARNING: Column '{col}' not found in bars DataFrame. Available columns: {bars.columns.tolist()}")
            return False, None
    
    # Map column names to handle different naming conventions
    close_col = 'close' if 'close' in bars.columns else 'close_price'
    
    # Calculate ATR
    high_low = bars['high'] - bars['low']
    high_close = np.abs(bars['high'] - bars[close_col].shift())
    low_close = np.abs(bars['low'] - bars[close_col].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().fillna(tr.mean())
    
    # Get the most recent bar
    latest_bar = bars.iloc[-1]
    latest_timestamp = latest_bar['timestamp']
    
    # Check if the zone is too far from the current price range
    current_price = latest_bar[close_col]
    max_distance = current_price * (max_distance_percent / 100.0)
    
    if abs(zone_value - current_price) > max_distance:
        print(f"SR zone at {zone_value} is too far from current price {current_price} (max distance: {max_distance})")
        return True, latest_timestamp
    
    # Check for invalidation by price action
    for idx, row in bars.iterrows():
        # Skip if ATR is not available
        if idx < 14:
            continue
            
        current_atr = atr.iloc[idx]
        invalidation_threshold = current_atr * atr_multiple
        
        # Check if price has crossed and moved beyond the zone
        if row['low'] > zone_value and row['low'] - zone_value > invalidation_threshold:
            # Zone was support, now broken to the upside
            return True, row['timestamp']
        elif row['high'] < zone_value and zone_value - row['high'] > invalidation_threshold:
            # Zone was resistance, now broken to the downside
            return True, row['timestamp']
    
    return False, None

def process_sr_zones(indicator_name, timeframe, start_date, end_date, qualifier=None, history_days=200):
    """
    Process SR zones with historical persistence.
    
    Args:
        indicator_name: The short name of the indicator (e.g., 'srzones')
        timeframe: The timeframe (e.g., '1d')
        start_date: Start date for processing
        end_date: End date for processing
        qualifier: Optional qualifier to filter by (e.g., 'time', 'linear', 'volume')
        history_days: Number of days of historical data to load for pivot detection
    """
    print(f"Processing {indicator_name} on {timeframe} from {start_date} to {end_date}")
    
    # Convert dates to datetime objects
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    # Calculate history start date
    history_start_dt = start_dt - timedelta(days=history_days)
    
    # Load OHLCV data with extended history for pivot detection
    print(f"Loading historical data from {history_start_dt} to {end_dt}")
    bars = load_bars_from_db(timeframe, history_start_dt, end_dt)
    if bars.empty:
        print(f"No bars found for {timeframe} from {history_start_dt} to {end_dt}")
        return
    
    # Filter to the requested date range for processing
    process_bars = bars[(bars["timestamp"] >= start_dt) & (bars["timestamp"] <= end_dt)]
    if process_bars.empty:
        print(f"No bars found for {timeframe} from {start_dt} to {end_dt}")
        return
    
    # Get indicator class and metadata
    IndicatorClass, metadata = get_indicator_class(indicator_name)
    raw_params = metadata.get("ParametersJson", {})
    
    # Calculate new SR zones
    indicator_instance = IndicatorClass(parameters_json=raw_params, qualifier=qualifier)
    new_zones = indicator_instance.calculate(bars)
    
    if new_zones.empty:
        print(f"No new SR zones generated for {timeframe} from {start_dt} to {end_dt}")
        return
    
    print(f"Generated {len(new_zones)} new SR zones")
    
    # Get existing active SR zones
    active_zones = get_active_sr_zones(indicator_name, timeframe)
    
    # Combine new and existing zones
    combined_zones = pd.concat([new_zones, active_zones])
    
    # Check for invalidation of existing zones
    invalidated_zones = []
    for idx, zone in active_zones.iterrows():
        is_invalidated, invalidation_date = check_zone_invalidation(zone['value'], bars)
        if is_invalidated:
            print(f"SR zone at {zone['value']} has been invalidated on {invalidation_date}")
            # Update the TimestampEnd to mark when it was invalidated
            invalidated_zones.append({
                "bar_id": zone['bar_id'],
                "timeframe": zone['timeframe'],
                "indicator_id": zone['indicator_id'],
                "value": zone['value'],
                "aux_value": zone['aux_value'],
                "timestamp_start": zone['timestamp_start'],
                "timestamp_end": invalidation_date,
                "qualifier": zone['qualifier'],
                "parameters_json": zone['parameters_json']
            })
    
    # Save invalidated zones
    if invalidated_zones:
        invalidated_df = pd.DataFrame(invalidated_zones)
        save_indicator_values_to_db(invalidated_df, indicator_name, timeframe, metadata, start_dt, end_dt)
    
    # Prepare new zones for saving
    # Set TimestampEnd to NULL for active zones
    # Create a copy of the DataFrame to avoid modifying the original
    new_zones_copy = new_zones.copy()
    for i, row in new_zones_copy.iterrows():
        new_zones_copy.at[i, 'timestamp_end'] = None
        
    # Print the first few rows to verify TimestampEnd is None
    print("First few rows of new_zones_copy:")
    print(new_zones_copy.head().to_string())
    
    # Save new zones
    save_indicator_values_to_db(new_zones_copy, indicator_name, timeframe, metadata, start_dt, end_dt)
    
    print(f"Processed {len(new_zones)} new zones and invalidated {len(invalidated_zones)} existing zones")

@app.command()
def process_persistent_srzones(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe to process"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    history_days: int = typer.Option(200, "--history-days", "-h", help="Number of days of historical data to load for pivot detection"),
    threads: int = typer.Option(4, "--threads", help="Parallel threads")
):
    """
    Process SR zones with historical persistence.
    """
    indicator = "srzones"
    
    print(f"Processing {indicator} for {start} to {end}")
    print(f"Timeframe: {timeframe}")
    print(f"Qualifier: {qualifier or 'all'}")
    print(f"History days: {history_days}")
    print(f"Threads: {threads}")
    print()
    
    process_sr_zones(indicator, timeframe, start, end, qualifier, history_days)
    
    print("\nProcessing completed.")

if __name__ == "__main__":
    app()
