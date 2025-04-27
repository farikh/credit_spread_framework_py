"""
Script to test the enhanced SR zone indicator.

This script will:
1. Load historical OHLCV data from September 2024
2. Run the enhanced SR zone indicator with a focus on the 5420 support zone
3. Compare the results with the original SR zone indicator
4. Display the detected zones

Usage:
    python test_enhanced_sr_zones.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator
from credit_spread_framework.indicators.custom.enhanced_sr_zone_indicator import EnhancedSRZoneIndicator

def query_ohlcv_direct(start_date, end_date, timeframe):
    """
    Query OHLCV data directly from the database using raw SQL.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Timeframe (e.g., '1d', '1m')
        
    Returns:
        DataFrame with OHLCV data
    """
    engine = get_engine()
    
    # Determine the table name based on the timeframe
    table_name = f"spx_ohlcv_{timeframe}"
    
    # Build the query
    query = text(f"""
        SELECT TOP (1000) [bar_id]
            ,[timestamp]
            ,[ticker]
            ,[open]
            ,[high]
            ,[low]
            ,[close]
            ,[spy_volume]
        FROM [CreditSpreadsDB].[dbo].[{table_name}]
        WHERE timestamp >= '{start_date} 00:00:00.000' AND timestamp <= '{end_date} 23:59:59.999'
        ORDER BY timestamp
    """)
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(query)
        
        # Convert to DataFrame
        columns = ["bar_id", "timestamp", "ticker", "open", "high", "low", "close", "spy_volume"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    return df

def main():
    # Test parameters
    start_date = "2024-09-01"
    end_date = "2024-09-30"
    history_start_date = "2024-03-01"  # 6 months of history
    timeframe = "1d"
    target_zone = 5420
    
    # Load OHLCV data
    print(f"Loading OHLCV data from {history_start_date} to {end_date}")
    bars = query_ohlcv_direct(history_start_date, end_date, timeframe)
    
    if bars.empty:
        print(f"No OHLCV data found for {timeframe} from {history_start_date} to {end_date}")
        return
    
    print(f"Loaded {len(bars)} OHLCV bars")
    
    # Print the September lows
    sept_bars = bars[(bars["timestamp"] >= "2024-09-01") & (bars["timestamp"] <= "2024-09-30")]
    print("\nSeptember 2024 Lows:")
    for _, row in sept_bars.iterrows():
        print(f"{row['timestamp'].strftime('%Y-%m-%d')}: Low = {row['low']}")
    
    # Run original SR zone indicator
    print("\nRunning original SR zone indicator...")
    original_params = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 75,
        "threshold_ratio": 0.25,
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50]
    }
    original_indicator = SRZoneIndicator(parameters_json=original_params)
    original_zones = original_indicator.calculate(bars)
    
    # Run enhanced SR zone indicator
    print("\nRunning enhanced SR zone indicator...")
    enhanced_params = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 150,  # Higher precision for better granularity
        "threshold_ratio": 0.15,  # Lower threshold to detect more peaks
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50],
        "focus_zones": [target_zone, 5402.62, 5406.96, 5434.49],  # Target zone + September lows
        "focus_range": 20,  # Smaller range for more precise targeting
        "time_decay": 15  # Faster decay to prioritize recent pivots
    }
    enhanced_indicator = EnhancedSRZoneIndicator(parameters_json=enhanced_params)
    enhanced_zones = enhanced_indicator.calculate(bars)
    
    # Compare results
    print("\nOriginal SR Zone Indicator Results:")
    print(original_zones[["value", "qualifier"]].to_string())
    
    print("\nEnhanced SR Zone Indicator Results:")
    print(enhanced_zones[["value", "qualifier"]].to_string())
    
    # Check for zones near the target
    target_range = 20  # Within 20 points of the target
    
    original_near_target = original_zones[abs(original_zones["value"] - target_zone) <= target_range]
    enhanced_near_target = enhanced_zones[abs(enhanced_zones["value"] - target_zone) <= target_range]
    
    print(f"\nOriginal zones near target ({target_zone}):")
    if original_near_target.empty:
        print("  None found")
    else:
        print(original_near_target[["value", "qualifier"]].to_string())
    
    print(f"\nEnhanced zones near target ({target_zone}):")
    if enhanced_near_target.empty:
        print("  None found")
    else:
        print(enhanced_near_target[["value", "qualifier"]].to_string())
    
    # Calculate improvement
    if not original_near_target.empty:
        original_closest = abs(original_near_target["value"] - target_zone).min()
    else:
        original_closest = abs(original_zones["value"] - target_zone).min()
    
    if not enhanced_near_target.empty:
        enhanced_closest = abs(enhanced_near_target["value"] - target_zone).min()
    else:
        enhanced_closest = abs(enhanced_zones["value"] - target_zone).min()
    
    improvement = original_closest - enhanced_closest
    
    print(f"\nClosest original zone: {original_closest:.2f} points from target")
    print(f"Closest enhanced zone: {enhanced_closest:.2f} points from target")
    print(f"Improvement: {improvement:.2f} points closer to target")
    
    # Check if we detected the September lows
    sept_lows = [5402.62, 5434.49, 5406.96]
    print("\nChecking if indicators detected the September lows:")
    for low in sept_lows:
        original_near_low = original_zones[abs(original_zones["value"] - low) <= 10]
        enhanced_near_low = enhanced_zones[abs(enhanced_zones["value"] - low) <= 10]
        
        print(f"\nLow: {low}")
        print(f"  Original: {'Detected' if not original_near_low.empty else 'Not detected'}")
        print(f"  Enhanced: {'Detected' if not enhanced_near_low.empty else 'Not detected'}")

if __name__ == "__main__":
    main()
