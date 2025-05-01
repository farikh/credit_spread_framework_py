"""
Test script for comparing different weighting methods in SRZone.

This script demonstrates how to use the srzone package with different weighting methods
(Linear, Time, Volume) and compare the results.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Add the current directory to the path so we can import the srzone package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis


def test_weighting_methods(data_file=None, output_dir=None, source_type='csv',
                          timeframe=None, start_date=None, end_date=None, max_bars=4000,
                          skip_visualization=True, debug=False):
    """
    Test different weighting methods for SRZone analysis.

    Parameters:
    -----------
    data_file : str, optional
        Path to the OHLCV data file (required if source_type is 'csv')
    output_dir : str, optional
        Directory to save outputs
    source_type : str, optional
        Type of data source ('csv' or 'sql'), default is 'csv'
    timeframe : str, optional
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
        Required for SQL, optional for CSV (for resampling)
    start_date : str or datetime, optional
        Start date for data range (SQL only)
    end_date : str or datetime, optional
        End date for data range (SQL only)
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)

    Returns:
    --------
    dict
        Analysis results for each weighting method
    """
    # Validate parameters
    if source_type.lower() == 'csv' and not data_file:
        raise ValueError("data_file is required when source_type is 'csv'")
    if source_type.lower() == 'sql' and not timeframe:
        raise ValueError("timeframe is required when source_type is 'sql'")

    # Normalize data file path if provided
    if data_file:
        data_file = os.path.normpath(data_file)

    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Get the script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Create output directory in the script directory
        output_dir = os.path.join(script_dir, f'weighting_test_{timestamp}')

    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Load and prepare data
    if source_type.lower() == 'csv':
        print(f"Loading data from CSV file: {data_file}...")
    else:
        print(f"Loading data from SQL database for timeframe: {timeframe}...")
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")

    print(f"Debug mode: {debug}")
    print(f"Max bars: {max_bars}")

    try:
        df = prepare_data_for_analysis(
            file_path=data_file,
            timeframe=timeframe,
            source_type=source_type,
            start_date=start_date,
            end_date=end_date,
            max_bars=max_bars,
            debug=debug
        )
        print(f"Data loaded successfully with {len(df)} rows")
    except Exception as e:
        print(f"ERROR loading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    print(f"Loaded {len(df)} bars of data.")

    # Define weighting methods to test
    weighting_methods = ['Linear', 'Time', 'Volume']

    # Base parameters
    base_params = {
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

    # Store results for each weighting method
    results = {}

    # Test each weighting method
    for weight_style in weighting_methods:
        print(f"\n=== Testing {weight_style} Weighting ===")

        # Create a copy of base parameters with the current weighting method
        params = base_params.copy()
        params['weight_style'] = weight_style

        # Detect pivots with the current weighting method
        print(f"Detecting pivot points with {weight_style} weighting...")
        pivot_results = detect_pivots(df, params['strength_params'], weight_style)

        print(f"Detected {len(pivot_results['pivot_high_idx'])} pivot highs and {len(pivot_results['pivot_low_idx'])} pivot lows.")

        # Generate zones
        print(f"Generating support and resistance zones with {weight_style} weighting...")
        zone_results = generate_zones(
            df,
            pivot_results['pivot_high_values'],
            pivot_results['pivot_high_weights'],
            pivot_results['pivot_low_values'],
            pivot_results['pivot_low_weights'],
            params
        )

        print(f"Generated {len(zone_results['zones'])} zones.")

        # Create visualization if not skipped
        output_image = None
        if not skip_visualization:
            print(f"Creating visualization for {weight_style} weighting...")
            output_image = os.path.join(output_dir, f'srzone_{weight_style.lower()}_weighting.png')
            fig = plot_srzone_analysis(df, pivot_results, zone_results, params, output_image)
            print(f"Visualization saved to {output_image}")
            # Close the figure to free memory
            plt.close(fig)

        # Store results
        results[weight_style] = {
            'pivot_results': pivot_results,
            'zone_results': zone_results,
            'output_image': output_image
        }

    # Skip visualization comparison
    print("\n=== Weighting Method Comparison Summary ===")

    # Print a summary of the results for each weighting method
    for weight_style in weighting_methods:
        zone_count = len(results[weight_style]['zone_results']['zones'])
        pivot_high_count = len(results[weight_style]['pivot_results']['pivot_high_idx'])
        pivot_low_count = len(results[weight_style]['pivot_results']['pivot_low_idx'])

        print(f"\n{weight_style} Weighting:")
        print(f"  - Pivot Highs: {pivot_high_count}")
        print(f"  - Pivot Lows: {pivot_low_count}")
        print(f"  - Total Zones: {zone_count}")

        # Print top 5 zones by score
        if zone_count > 0:
            print(f"  - Top 5 zones by score:")
            sorted_zones = sorted(results[weight_style]['zone_results']['zones'],
                                 key=lambda x: x['score'], reverse=True)
            for i, zone in enumerate(sorted_zones[:5]):
                print(f"    {i+1}. Price: {zone['price']:.2f}, Score: {zone['score']:.2f}, Type: {zone['type']}")

    # Save results to JSON file
    try:
        import json

        # Create a serializable version of the results
        serializable_results = {}
        for weight_style in weighting_methods:
            # Extract the zones which are already serializable
            zones = results[weight_style]['zone_results']['zones']

            # Create a summary of pivot points (not including the full data which may not be serializable)
            pivot_summary = {
                'pivot_high_count': len(results[weight_style]['pivot_results']['pivot_high_idx']),
                'pivot_low_count': len(results[weight_style]['pivot_results']['pivot_low_idx']),
                'pivot_high_values': results[weight_style]['pivot_results']['pivot_high_values'],
                'pivot_low_values': results[weight_style]['pivot_results']['pivot_low_values']
            }

            # Store the serializable data
            serializable_results[weight_style] = {
                'zones': zones,
                'pivot_summary': pivot_summary,
                'output_image': results[weight_style].get('output_image')
            }

        # Save to JSON file
        results_file = os.path.join(output_dir, 'weighting_results.json')
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\nResults saved to {results_file}")

        # Also save a summary text file
        summary_file = os.path.join(output_dir, 'summary.txt')
        with open(summary_file, 'w') as f:
            f.write("=== Weighting Method Comparison Summary ===\n\n")

            for weight_style in weighting_methods:
                zone_count = len(results[weight_style]['zone_results']['zones'])
                pivot_high_count = len(results[weight_style]['pivot_results']['pivot_high_idx'])
                pivot_low_count = len(results[weight_style]['pivot_results']['pivot_low_idx'])

                f.write(f"{weight_style} Weighting:\n")
                f.write(f"  - Pivot Highs: {pivot_high_count}\n")
                f.write(f"  - Pivot Lows: {pivot_low_count}\n")
                f.write(f"  - Total Zones: {zone_count}\n")

                # Write top 5 zones by score
                if zone_count > 0:
                    f.write(f"  - Top 5 zones by score:\n")
                    sorted_zones = sorted(results[weight_style]['zone_results']['zones'],
                                         key=lambda x: x['score'], reverse=True)
                    for i, zone in enumerate(sorted_zones[:5]):
                        f.write(f"    {i+1}. Price: {zone['price']:.2f}, Score: {zone['score']:.2f}, Type: {zone['type']}\n")

                f.write("\n")

        print(f"Summary saved to {summary_file}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")
        import traceback
        traceback.print_exc()

    return results


if __name__ == "__main__":
    import argparse

    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_data_dir = os.path.join(script_dir, 'validation', 'data')

    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Test SRZone weighting methods')
    parser.add_argument('--file', type=str, help='Path to the CSV file')
    parser.add_argument('--dir', type=str, default=default_data_dir,
                        help=f'Directory containing CSV files (default: {default_data_dir})')
    parser.add_argument('--timeframe', type=str, choices=['1m', '3m', '15m', '1h', '1d'],
                        help='Timeframe for SQL data source')
    parser.add_argument('--source', type=str, default='csv', choices=['csv', 'sql'],
                        help='Data source type (default: csv)')
    parser.add_argument('--start', type=str, help='Start date for SQL data (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date for SQL data (YYYY-MM-DD)')
    parser.add_argument('--visualize', action='store_true',
                        help='Generate visualizations (default: False)')
    parser.add_argument('--output', type=str,
                        help='Output directory for results (default: weighting_test_TIMESTAMP in script directory)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode for more detailed output')

    args = parser.parse_args()

    # Determine the data file to use
    data_file = None
    if args.file:
        data_file = os.path.normpath(args.file)
    else:
        # Use the first CSV file in the specified directory
        data_dir = os.path.normpath(args.dir)
        if os.path.exists(data_dir) and os.path.isdir(data_dir):
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if csv_files:
                data_file = os.path.join(data_dir, csv_files[0])
                print(f"Using CSV file: {data_file}")

    # Run the test
    if args.source == 'csv' and data_file and os.path.exists(data_file):
        results = test_weighting_methods(
            data_file=data_file,
            output_dir=args.output,
            source_type=args.source,
            skip_visualization=not args.visualize
        )
    elif args.source == 'sql' and args.timeframe:
        results = test_weighting_methods(
            output_dir=args.output,
            source_type=args.source,
            timeframe=args.timeframe,
            start_date=args.start,
            end_date=args.end,
            skip_visualization=not args.visualize,
            debug=args.debug  # Use the debug flag from command line
        )
    else:
        if args.source == 'csv':
            print("Error: CSV file not found or not specified.")
            print(f"Please provide a valid CSV file with --file or ensure CSV files exist in {args.dir}")
        else:
            print("Error: For SQL source, timeframe must be specified with --timeframe")

        # Print usage examples
        print("\nUsage examples:")
        print("  python test_weighting_methods.py")
        print("  python test_weighting_methods.py --file \"validation/data/SP_SPX, 3_3dc75.csv\"")
        print("  python test_weighting_methods.py --source sql --timeframe 1d --start 2025-04-01 --end 2025-04-03")
        print("  python test_weighting_methods.py --visualize --output \"output_dir\"")
