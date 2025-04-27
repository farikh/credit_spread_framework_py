"""
Script to verify SR zone timestamps against OHLCV data.

This script will:
1. Load SR zones from the database
2. Load OHLCV data for the same period
3. Verify that the first_detected and last_confirmed timestamps correspond to actual OHLCV data
"""
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timedelta

def main():
    engine = get_engine()
    
    # Query all SR zones
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT 
                zone_id, value, qualifier, timeframe, strength,
                first_detected, last_confirmed, is_active
            FROM sr_zones
            ORDER BY qualifier, value
        """))
        
        columns = [
            "zone_id", "value", "qualifier", "timeframe", "strength",
            "first_detected", "last_confirmed", "is_active"
        ]
        zones_df = pd.DataFrame(result.fetchall(), columns=columns)
    
    if zones_df.empty:
        print("No SR zones found in the database.")
        return
    
    print(f"Found {len(zones_df)} SR zones in the database.")
    
    # Get the earliest first_detected and latest last_confirmed
    earliest_date = zones_df["first_detected"].min()
    latest_date = zones_df["last_confirmed"].max()
    
    print(f"Date range: {earliest_date} to {latest_date}")
    
    # Load OHLCV data for this period
    timeframe = zones_df["timeframe"].iloc[0]  # Assume all zones have the same timeframe
    bars = load_bars_from_db(timeframe, earliest_date - timedelta(days=7), latest_date + timedelta(days=7))
    
    if bars.empty:
        print(f"No OHLCV data found for {timeframe} from {earliest_date} to {latest_date}")
        return
    
    print(f"Loaded {len(bars)} OHLCV bars from {bars['timestamp'].min()} to {bars['timestamp'].max()}")
    
    # Convert timestamps to dates for easier comparison
    bars["date"] = bars["timestamp"].dt.date
    zones_df["first_detected_date"] = zones_df["first_detected"].dt.date
    zones_df["last_confirmed_date"] = zones_df["last_confirmed"].dt.date
    
    # Get unique dates in OHLCV data
    ohlcv_dates = set(bars["date"])
    
    # Check if first_detected dates are in OHLCV data
    first_detected_in_ohlcv = zones_df["first_detected_date"].apply(lambda x: x in ohlcv_dates)
    print(f"\nFirst detected dates in OHLCV data: {first_detected_in_ohlcv.sum()} / {len(zones_df)}")
    
    if not first_detected_in_ohlcv.all():
        print("\nZones with first_detected not in OHLCV data:")
        invalid_zones = zones_df[~first_detected_in_ohlcv]
        print(invalid_zones[["zone_id", "value", "qualifier", "first_detected", "last_confirmed"]])
    
    # Check if last_confirmed dates are in OHLCV data
    last_confirmed_in_ohlcv = zones_df["last_confirmed_date"].apply(lambda x: x in ohlcv_dates)
    print(f"\nLast confirmed dates in OHLCV data: {last_confirmed_in_ohlcv.sum()} / {len(zones_df)}")
    
    if not last_confirmed_in_ohlcv.all():
        print("\nZones with last_confirmed not in OHLCV data:")
        invalid_zones = zones_df[~last_confirmed_in_ohlcv]
        print(invalid_zones[["zone_id", "value", "qualifier", "first_detected", "last_confirmed"]])
    
    # Check for zones with last_confirmed before first_detected
    invalid_timeline = zones_df["last_confirmed"] < zones_df["first_detected"]
    print(f"\nZones with last_confirmed before first_detected: {invalid_timeline.sum()} / {len(zones_df)}")
    
    if invalid_timeline.any():
        print("\nZones with invalid timeline:")
        invalid_zones = zones_df[invalid_timeline]
        print(invalid_zones[["zone_id", "value", "qualifier", "first_detected", "last_confirmed"]])
    
    # Check for zones with first_detected in the future
    future_first_detected = zones_df["first_detected"] > datetime.now()
    print(f"\nZones with first_detected in the future: {future_first_detected.sum()} / {len(zones_df)}")
    
    if future_first_detected.any():
        print("\nZones with future first_detected:")
        invalid_zones = zones_df[future_first_detected]
        print(invalid_zones[["zone_id", "value", "qualifier", "first_detected", "last_confirmed"]])
    
    # Check for zones with last_confirmed in the future
    future_last_confirmed = zones_df["last_confirmed"] > datetime.now()
    print(f"\nZones with last_confirmed in the future: {future_last_confirmed.sum()} / {len(zones_df)}")
    
    if future_last_confirmed.any():
        print("\nZones with future last_confirmed:")
        invalid_zones = zones_df[future_last_confirmed]
        print(invalid_zones[["zone_id", "value", "qualifier", "first_detected", "last_confirmed"]])
    
    # Check for zones with first_detected = last_confirmed
    same_dates = zones_df["first_detected"] == zones_df["last_confirmed"]
    print(f"\nZones with first_detected = last_confirmed: {same_dates.sum()} / {len(zones_df)}")
    
    # Group zones by first_detected date
    print("\nZones by first_detected date:")
    date_counts = zones_df.groupby("first_detected_date").size()
    for date, count in date_counts.items():
        print(f"  {date}: {count} zones")
    
    # Group zones by last_confirmed date
    print("\nZones by last_confirmed date:")
    date_counts = zones_df.groupby("last_confirmed_date").size()
    for date, count in date_counts.items():
        print(f"  {date}: {count} zones")
    
    print("\nVerification complete.")

if __name__ == "__main__":
    main()
