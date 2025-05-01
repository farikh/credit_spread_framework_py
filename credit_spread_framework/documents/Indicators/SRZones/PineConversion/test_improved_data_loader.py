"""
Test script for the improved data loader.

This script tests the improved data loader with different date range scenarios
and demonstrates how it addresses the issues with the original implementation.

Usage:
    python test_improved_data_loader.py --timeframe 15m --start 2025-04-03 --end 2025-04-03
    python test_improved_data_loader.py --timeframe 1d --start 2025-04-03 --end 2025-04-03
"""

import os
import sys
import argparse
from datetime import datetime

# Add the current directory to the path so we can import the srzone package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the improved data loader
from srzone.data_loader_improved import prepare_data_for_analysis


def test_improved_data_loader(timeframe, start_date=None, end_date=None, output_dir=None, debug=True):
    """
    Test the improved data loader with the specified parameters.
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start_date : str, optional
        Start date for data range
    end_date : str, optional
        End date for data range
    output_dir : str, optional
        Directory to save outputs
    debug : bool, optional
        Whether to print debug information
    """
    print(f"\n=== Testing Improved Data Loader ===")
    print(f"Timeframe: {timeframe}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    try:
        # Load data using the improved data loader
        df = prepare_data_for_analysis(
            source_type='sql',
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            debug=debug
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
            
            # Save to CSV if output directory is specified
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # Create a filename based on the parameters
                start_str = start_date.replace('-', '') if start_date else 'none'
                end_str = end_date.replace('-', '') if end_date else 'none'
                filename = f"sql_data_{timeframe}_{start_str}_{end_str}.csv"
                filepath = os.path.join(output_dir, filename)
                
                # Save to CSV
                df.to_csv(filepath)
                print(f"\nData saved to {filepath}")
        else:
            print("No data found for the specified parameters.")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Test improved data loader')
    parser.add_argument('--timeframe', type=str, required=True,
                        choices=['1m', '3m', '15m', '1h', '1d'],
                        help='Timeframe for data')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, help='Output directory for results')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Run the test
    test_improved_data_loader(
        timeframe=args.timeframe,
        start_date=args.start,
        end_date=args.end,
        output_dir=args.output,
        debug=args.debug
    )
