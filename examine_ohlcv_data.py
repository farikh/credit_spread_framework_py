"""
Script to examine OHLCV data for specific dates.
"""
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
import pandas as pd
from datetime import datetime, timedelta

def main():
    # Load OHLCV data for the period around 2025-03-26 and 2025-03-27
    start_date = datetime(2025, 3, 25)
    end_date = datetime(2025, 3, 28)
    timeframe = "1d"
    
    print(f"Loading OHLCV data for {timeframe} from {start_date} to {end_date}")
    bars = load_bars_from_db(timeframe, start_date, end_date)
    
    if bars.empty:
        print("No data found for the specified period.")
        return
    
    print(f"Loaded {len(bars)} bars:")
    print(bars[["timestamp", "open_price", "high", "low", "close_price"]])
    
    # Check if 2025-03-26 and 2025-03-27 are in the data
    dates = bars["timestamp"].dt.date.tolist()
    print("\nDates in the data:", dates)
    
    date_2025_03_26 = datetime(2025, 3, 26).date()
    date_2025_03_27 = datetime(2025, 3, 27).date()
    
    print(f"Checking if {date_2025_03_26} is in {dates}: {date_2025_03_26 in dates}")
    print(f"Checking if {date_2025_03_27} is in {dates}: {date_2025_03_27 in dates}")
    
    # Check each date individually
    print("\nChecking each date individually:")
    for idx, bar_date in enumerate(dates):
        print(f"  Bar {idx}: {bar_date}, equals 2025-03-26: {bar_date == date_2025_03_26}")
        print(f"  Bar {idx}: {bar_date}, equals 2025-03-27: {bar_date == date_2025_03_27}")
    
    # Check for the 5726 level
    level = 5726
    tolerance = 15
    
    print(f"\nChecking for bars near level {level} (tolerance: {tolerance}):")
    for _, bar in bars.iterrows():
        if (bar["low"] - tolerance <= level <= bar["high"] + tolerance):
            print(f"  {bar['timestamp']}: {bar['open_price']} {bar['high']} {bar['low']} {bar['close_price']}")
    
    # Load all daily data
    print("\nLoading all daily data to check for gaps:")
    all_bars = load_bars_from_db("1d", None, None)
    
    if all_bars.empty:
        print("No daily data found.")
        return
    
    # Check for gaps in the data
    all_bars = all_bars.sort_values("timestamp")
    all_bars["next_day"] = all_bars["timestamp"].shift(-1)
    all_bars["days_gap"] = (all_bars["next_day"] - all_bars["timestamp"]).dt.days
    
    gaps = all_bars[all_bars["days_gap"] > 1]
    if not gaps.empty:
        print("\nFound gaps in the daily data:")
        for _, gap in gaps.iterrows():
            print(f"  Gap between {gap['timestamp']} and {gap['next_day']} ({gap['days_gap']} days)")
    else:
        print("\nNo gaps found in the daily data.")

if __name__ == "__main__":
    main()
