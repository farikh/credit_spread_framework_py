"""
SQL Database Example for SRZone

This script demonstrates how to use the SRZone package with SQL database as the data source.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the current directory to the path so we can import the srzone package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis


def run_sql_example(timeframe, start_date=None, end_date=None, output_dir=None, params=None, max_bars=4000, debug=False):
    """
    Run SRZone analysis using SQL database as the data source.

    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    start_date : str or datetime, optional
        Start date for data range
    end_date : str or datetime, optional
        End date for data range
    output_dir : str, optional
        Directory to save outputs
    params : dict, optional
        Configuration parameters
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)
    debug : bool, optional
        Whether to print debug information

    Returns:
    --------
    dict
        Analysis results
    """
    # Set default parameters if not provided
    if params is None:
        params = {
            'weight_style': 'Linear',
            'pivot_lookback': 50,
            'filter': 3,
            'precision': 75,
            'auto_precision': True,
            'include_ph': True,
            'include_pl': True,
            'scale': 30,
            'show_dist': True,
            'strength_params': [
                {'length': 5, 'include': True},
                {'length': 10, 'include': True},
                {'length': 20, 'include': True},
                {'length': 50, 'include': True}
            ]
        }
    
    # Set default end date to April 3, 2025 at 4:00 PM if not provided
    if end_date is None:
        end_date = datetime(2025, 4, 3, 16, 0, 0)
    
    # Set default start date if not provided
    if start_date is None:
        # Calculate a reasonable start date based on timeframe
        if timeframe == '1m':
            start_date = datetime(2025, 3, 27, 9, 30, 0)  # About 5 trading days before end_date
        elif timeframe == '3m':
            start_date = datetime(2025, 3, 27, 9, 30, 0)  # About 5 trading days before end_date
        elif timeframe == '15m':
            start_date = datetime(2025, 3, 27, 9, 30, 0)  # About 5 trading days before end_date
        elif timeframe == '1h':
            start_date = datetime(2025, 3, 20, 9, 30, 0)  # About 10 trading days before end_date
        elif timeframe == '1d':
            start_date = datetime(2025, 2, 1, 9, 30, 0)   # About 2 months before end_date
        else:
            start_date = datetime(2025, 3, 27, 9, 30, 0)  # Default to 5 trading days
    
    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.normpath(f'sql_srzone_{timeframe}_{timestamp}')
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading data from SQL database for timeframe: {timeframe}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    
    # Debug: Print SQL connection string if debug is enabled
    if debug:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        conn_str = os.getenv("SQLSERVER_CONN_STRING") or os.getenv("SQLSERVER_SQL_LOGIN_CONN_STRING")
        if conn_str:
            # Print a sanitized version of the connection string (hide password)
            sanitized_conn_str = conn_str
            if "Password=" in sanitized_conn_str:
                parts = sanitized_conn_str.split(";")
                for i, part in enumerate(parts):
                    if part.startswith("Password="):
                        parts[i] = "Password=********"
                sanitized_conn_str = ";".join(parts)
            print(f"Using SQL connection string: {sanitized_conn_str}")
        else:
            print("WARNING: No SQL connection string found in environment variables!")
    
    try:
        # Load and prepare data from SQL database
        df = prepare_data_for_analysis(
            source_type='sql',
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            max_bars=max_bars,
            debug=debug
        )
        
        # Debug: Print the first few rows of the dataframe
        if debug and not df.empty:
            print("\nFirst 5 rows of data:")
            print(df.head())
            print("\nLast 5 rows of data:")
            print(df.tail())
            print("\nDataFrame info:")
            print(df.info())
    except Exception as e:
        print(f"ERROR loading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    print(f"Loaded {len(df)} bars of data.")
    
    # Detect pivots
    print("Detecting pivot points...")
    pivot_results = detect_pivots(df, params.get('strength_params'))
    
    print(f"Detected {len(pivot_results['pivot_high_idx'])} pivot highs and {len(pivot_results['pivot_low_idx'])} pivot lows.")
    
    # Generate zones
    print("Generating support and resistance zones...")
    zone_results = generate_zones(
        df,
        pivot_results['pivot_high_values'],
        [1] * len(pivot_results['pivot_high_values']),  # Default weights
        pivot_results['pivot_low_values'],
        [1] * len(pivot_results['pivot_low_values']),  # Default weights
        params
    )
    
    print(f"Generated {len(zone_results['zones'])} zones.")
    
    # Create visualization
    print("Creating visualization...")
    output_image = os.path.join(output_dir, 'srzone_analysis.png')
    fig = plot_srzone_analysis(df, pivot_results, zone_results, params, output_image)
    
    print(f"Visualization saved to {output_image}")
    
    # Show the plot
    plt.show()
    
    return {
        'df': df,
        'pivot_results': pivot_results,
        'zone_results': zone_results,
        'output_image': output_image
    }


def run_validation_with_sql(timeframe, tradingview_image, start_date=None, end_date=None, output_dir=None, max_bars=4000, debug=False):
    """
    Run validation of the SRZone implementation against TradingView Pine script using SQL database.

    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    tradingview_image : str
        Path to the TradingView chart image
    start_date : str or datetime, optional
        Start date for data range
    end_date : str or datetime, optional
        End date for data range
    output_dir : str, optional
        Directory to save validation outputs
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)

    Returns:
    --------
    dict
        Validation results
    """
    # Import validation function
    from srzone.validation import validate_implementation
    
    # Normalize paths
    tradingview_image = os.path.normpath(tradingview_image)
    
    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.normpath(f'sql_validation_{timeframe}_{timestamp}')
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Running validation with SQL database for timeframe: {timeframe}")
    print(f"Start date: {start_date}")
    print(f"End date: {end_date}")
    print(f"TradingView image: {tradingview_image}")
    print(f"Output directory: {output_dir}")
    
    # Run validation
    validation_results = validate_implementation(
        data_file=None,
        tradingview_export=None,
        tradingview_image=tradingview_image,
        output_dir=output_dir,
        source_type='sql',
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        max_bars=max_bars
    )
    
    print(f"Validation complete. Results saved to {output_dir}")
    
    # Print information about peak detection data
    if 'peak_csv_path' in validation_results:
        print(f"\nPeak detection data exported to: {validation_results['peak_csv_path']}")
    
    # Print information about comparison image
    if 'comparison_image_path' in validation_results and validation_results['comparison_image_path']:
        print(f"Comparison image saved to: {validation_results['comparison_image_path']}")
    
    return validation_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run SRZone analysis with SQL database')
    parser.add_argument('--timeframe', choices=['1m', '3m', '15m', '1h', '1d'], required=True,
                        help='Timeframe for data')
    parser.add_argument('--start', type=str, default=None,
                        help='Start date (format: YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default=None,
                        help='End date (format: YYYY-MM-DD)')
    parser.add_argument('--validate', action='store_true',
                        help='Run validation against TradingView image')
    parser.add_argument('--image', type=str, default=None,
                        help='Path to TradingView image for validation')
    parser.add_argument('--max-bars', type=int, default=4000,
                        help='Maximum number of bars to return (default: 4000)')
    parser.add_argument('--debug', action='store_true',
                        help='Print debug information')
    
    args = parser.parse_args()
    
    # Parse dates if provided
    start_date = None
    if args.start:
        try:
            start_date = datetime.strptime(args.start, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid start date format: {args.start}. Using default.")
    
    end_date = None
    if args.end:
        try:
            end_date = datetime.strptime(args.end, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid end date format: {args.end}. Using default.")
    
    # Run validation or regular analysis
    if args.validate:
        if not args.image:
            print("Error: --image is required when using --validate")
            sys.exit(1)
        
        run_validation_with_sql(
            timeframe=args.timeframe,
            tradingview_image=args.image,
            start_date=start_date,
            end_date=end_date,
            max_bars=args.max_bars,
            debug=args.debug
        )
    else:
        run_sql_example(
            timeframe=args.timeframe,
            start_date=start_date,
            end_date=end_date,
            max_bars=args.max_bars,
            debug=args.debug
        )
