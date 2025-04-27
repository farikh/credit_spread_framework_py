"""
Script to process SR zones for an extended period using all available data.
This approach more closely matches TradingView's implementation by:
1. Processing a longer timeframe all at once
2. Using all historical data for detecting zones
3. Adjusting parameters for better zone detection

Usage:
    python process_extended_period.py
"""
from datetime import datetime, timezone, timedelta
import json
import pandas as pd
import numpy as np
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db

def main():
    # Configuration
    timeframe = "1d"
    start_date = datetime(2025, 4, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 4, 10, tzinfo=timezone.utc)
    qualifier = "time"
    
    print(f"Loading all {timeframe} bars from database...")
    
    # Important: Load much more historical data to get better SR zones
    # Use the full available data, not just the start-end window
    # This closer matches TradingView's approach of using all visible bars
    historical_start = datetime(2024, 10, 1, tzinfo=timezone.utc)  # Go back 6 months
    all_bars = load_bars_from_db(timeframe, historical_start, end_date)
    
    if all_bars.empty:
        print(f"No {timeframe} bars found in the specified range.")
        return
    
    print(f"Loaded {len(all_bars)} bars from {all_bars['timestamp'].min()} to {all_bars['timestamp'].max()}")
    
    # Create optimized parameters for better TradingView matching
    params = {
        "pivot_lookback": 200,      # Increased pivot lookback for more historical context
        "filter_len": 5,            # Increased filter length for smoother histogram
        "precision": 200,           # Increased precision for finer-grained detection
        "threshold_ratio": 0.20,    # Lowered threshold to detect more zones
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50]  # Standard TradingView pivot lengths
    }
    
    # Process full dataset at once to detect all SR zones (more like TradingView)
    print(f"Calculating SR zones with {qualifier} weighting...")
    
    indicator = SRZoneIndicator(parameters_json=params, qualifier=qualifier)
    result_df = indicator.calculate(all_bars)
    
    if result_df.empty:
        print("No SR zones detected!")
        return
    
    print(f"Detected {len(result_df)} SR zones")
    
    # Filter zones for target date range and save to database
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    rows_saved = 0
    
    for current_date in date_range:
        day_start = current_date.replace(hour=0, minute=0, second=0)
        day_end = current_date.replace(hour=23, minute=59, second=59)
        
        # Adjust timestamps for market hours (9:30 AM - 4:00 PM EST)
        market_start = day_start.replace(hour=13, minute=30)  # 9:30 AM EST = 13:30 UTC
        market_end = day_start.replace(hour=20, minute=0)     # 4:00 PM EST = 20:00 UTC
        
        # Create copy with adjusted timestamps for this day
        day_df = result_df.copy()
        day_df['timestamp_start'] = market_start
        day_df['timestamp_end'] = market_end
        
        # Save this day's SR zones
        day_str = current_date.strftime('%Y-%m-%d')
        print(f"Saving {len(day_df)} zones for {day_str}...")
        
        save_indicator_values_to_db(
            day_df, 
            "srzones", 
            timeframe,
            json.dumps(params), 
            market_start, 
            market_end
        )
        
        rows_saved += len(day_df)
    
    print(f"\nProcessing complete: Saved {rows_saved} SR zone records for {len(date_range)} days")
    print(f"Zone values: {sorted(result_df['value'].unique())}")

if __name__ == "__main__":
    main()
