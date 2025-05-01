"""
Simple test script for the updated data_loader.py in the PineConversion folder.

This script directly imports the prepare_data_for_analysis function from the
updated data_loader.py and tests it with different parameters.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the PineConversion folder to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
pine_conversion_dir = os.path.join(current_dir, "credit_spread_framework", "documents", "Indicators", "SRZones", "PineConversion")
if pine_conversion_dir not in sys.path:
    sys.path.append(pine_conversion_dir)

# Import the prepare_data_for_analysis function from the updated data_loader.py
from srzone.data_loader import prepare_data_for_analysis

def test_data_loader(timeframe, start_date=None, end_date=None):
    """
    Test the updated data_loader.py with the specified parameters.
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start_date : str, optional
        Start date for data range
    end_date : str, optional
        End date for data range
    """
    print(f"\n=== Testing Updated Data Loader ===")
    print(f"Timeframe: {timeframe}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    try:
        # Load data using the updated data_loader.py
        df = prepare_data_for_analysis(
            source_type='sql',
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            debug=True
        )
        
        # Print summary of the data
        print(f"\nData Summary:")
        print(f"  - Total rows: {len(df)}")
        if not df.empty:
            print(f"  - Date range: {df.index.min()} to {df.index.max()}")
            print(f"  - Columns: {df.columns.tolist()}")
            
            # Print first and last few rows
            print(f"\nFirst 5 rows:")
            print(df.head().to_string())
            print(f"\nLast 5 rows:")
            print(df.tail().to_string())
        else:
            print("No data found for the specified parameters.")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with 15m timeframe
    test_data_loader('15m', '2025-04-03', '2025-04-03')
    
    # Test with 1d timeframe
    test_data_loader('1d', '2025-04-03', '2025-04-03')
