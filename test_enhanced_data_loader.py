"""
Test script for the enhanced data loader.

This script tests the enhanced data loader with different date range scenarios:
1. Only start date specified
2. Only end date specified
3. Both start and end date specified
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the enhanced data loader
from credit_spread_framework.data.repositories.ohlcv_repository_enhanced import load_bars_from_db

def test_data_loader(timeframe='1d', limit=4000):
    """
    Test the enhanced data loader with different date range scenarios.
    
    Parameters:
    -----------
    timeframe : str, optional
        Timeframe for data (default: '1d')
    limit : int, optional
        Maximum number of bars to return (default: 4000)
    """
    print(f"Testing enhanced data loader for timeframe: {timeframe}, limit: {limit}")
    
    # Get current date
    today = datetime.now()
    
    # Test Case 1: Only end date specified
    print("\nTest Case 1: Only end date specified")
    end_date = today
    df1 = load_bars_from_db(timeframe, start=None, end=end_date, limit=limit)
    print(f"Retrieved {len(df1)} bars")
    if not df1.empty:
        print(f"Date range: {df1['timestamp'].min()} to {df1['timestamp'].max()}")
    
    # Test Case 2: Only start date specified
    print("\nTest Case 2: Only start date specified")
    start_date = today - timedelta(days=30)  # 30 days ago
    df2 = load_bars_from_db(timeframe, start=start_date, end=None, limit=limit)
    print(f"Retrieved {len(df2)} bars")
    if not df2.empty:
        print(f"Date range: {df2['timestamp'].min()} to {df2['timestamp'].max()}")
        print(f"Bars on or after start date: {len(df2[df2['timestamp'] >= start_date])}")
        print(f"Bars before start date: {len(df2[df2['timestamp'] < start_date])}")
    
    # Test Case 3: Both start and end date specified
    print("\nTest Case 3: Both start and end date specified")
    start_date = today - timedelta(days=30)  # 30 days ago
    end_date = today
    df3 = load_bars_from_db(timeframe, start=start_date, end=end_date, limit=limit)
    print(f"Retrieved {len(df3)} bars")
    if not df3.empty:
        print(f"Date range: {df3['timestamp'].min()} to {df3['timestamp'].max()}")
        print(f"Bars between start and end date: {len(df3[(df3['timestamp'] >= start_date) & (df3['timestamp'] <= end_date)])}")
        print(f"Bars before start date: {len(df3[df3['timestamp'] < start_date])}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the enhanced data loader')
    parser.add_argument('--timeframe', type=str, default='1d', choices=['1m', '3m', '15m', '1h', '1d'],
                        help='Timeframe for data (default: 1d)')
    parser.add_argument('--limit', type=int, default=4000,
                        help='Maximum number of bars to return (default: 4000)')
    
    args = parser.parse_args()
    
    test_data_loader(args.timeframe, args.limit)
