"""
Test script to verify the carry-forward functionality for SR zones.
"""
import sys
from datetime import datetime
from credit_spread_framework.cli.enrich_data import run_enrich_for_indicator

def main():
    # Process SR zones for April 3, 2025
    indicator = "srzones"
    start_date = "2025-04-03"
    end_date = "2025-04-03"
    
    # Test with all timeframes
    timeframes = ['1m', '3m', '15m', '1h', '1d']
    
    for timeframe in timeframes:
        print(f"\n\nTesting carry-forward for {indicator} on {timeframe} for {start_date}")
        run_enrich_for_indicator(
            indicator=indicator,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            qualifier=None,  # Process all qualifiers
            batch_days=1,
            carry_forward=True
        )
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main()
