"""
Validation script for all timeframes.

This script runs validation for all available timeframes and generates
exports for comparison with TradingView images.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Add the current directory to the path so we can import the srzone package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis, create_validation_comparison
from srzone.validation import validate_implementation
from srzone.peak_detection_export import export_peak_detection_data
from srzone.peak_comparison import run_peak_comparison


def validate_timeframe(data_file=None, tradingview_image=None, output_dir=None, source_type='csv',
                      timeframe=None, start_date=None, end_date=None, max_bars=4000):
    """
    Run validation for a specific timeframe.

    Parameters:
    -----------
    data_file : str, optional
        Path to the OHLCV data file (required if source_type is 'csv')
    tradingview_image : str, optional
        Path to the TradingView chart image
    output_dir : str, optional
        Directory to save validation outputs
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
        Validation results
    """
    # Validate parameters
    if source_type.lower() == 'csv' and not data_file:
        raise ValueError("data_file is required when source_type is 'csv'")
    if source_type.lower() == 'sql' and not timeframe:
        raise ValueError("timeframe is required when source_type is 'sql'")
    
    # Normalize paths
    if data_file:
        data_file = os.path.normpath(data_file)
    if tradingview_image:
        tradingview_image = os.path.normpath(tradingview_image)
    
    # Extract timeframe from filename or use provided timeframe
    if source_type.lower() == 'csv':
        extracted_timeframe = os.path.basename(data_file).split('_')[1].replace('.csv', '')
    else:
        extracted_timeframe = timeframe
    
    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if data_file:
            output_dir = os.path.join(os.path.dirname(data_file), f'validation_{extracted_timeframe}_{timestamp}')
        else:
            # For SQL source, create output in current directory
            output_dir = os.path.normpath(f'validation_{extracted_timeframe}_{timestamp}')
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*80}")
    print(f"Running validation for timeframe: {extracted_timeframe}")
    if source_type.lower() == 'csv':
        print(f"Data file: {data_file}")
    else:
        print(f"Data source: SQL database")
        print(f"Timeframe: {timeframe}")
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")
    print(f"TradingView image: {tradingview_image}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}\n")
    
    # Run validation
    validation_results = validate_implementation(
        data_file=data_file,
        tradingview_export=None,  # No TradingView export file
        tradingview_image=tradingview_image,
        output_dir=output_dir,
        source_type=source_type,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        max_bars=max_bars
    )
    
    print(f"Validation complete for {extracted_timeframe}. Results saved to {output_dir}")
    
    # Print information about peak detection data
    if 'peak_csv_path' in validation_results:
        print(f"\nPeak detection data exported to: {validation_results['peak_csv_path']}")
    
    # Print information about comparison image
    if 'comparison_image_path' in validation_results and validation_results['comparison_image_path']:
        print(f"Comparison image saved to: {validation_results['comparison_image_path']}")
    
    return validation_results


def main(source_type='csv', target_date=None, max_bars=4000):
    """
    Main function to run validation for all timeframes.
    
    Parameters:
    -----------
    source_type : str, optional
        Type of data source ('csv' or 'sql'), default is 'csv'
    target_date : str or datetime, optional
        Target date for validation (SQL only)
        If None, the current date is used
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)
    """
    # Base directories
    data_dir = os.path.normpath("validation/data")
    images_dir = os.path.normpath("validation/images")
    
    # Ensure images directory exists
    if not os.path.exists(images_dir):
        print(f"Images directory not found: {images_dir}")
        return
    
    # Define timeframes and corresponding files
    timeframes = {
        "1m": {
            "timeframe": "1m",
            "data": os.path.join(data_dir, "SP_SPX, 1m__Linear.csv"),
            "image": os.path.join(images_dir, "2025_04_03_SPX_01minute_Linear.png")
        },
        "3m": {
            "timeframe": "3m",
            "data": os.path.join(data_dir, "SP_SPX, 3m__Linear.csv"),
            "image": os.path.join(images_dir, "2025_04_03_SPX_03minute_Linear.png")
        },
        "15m": {
            "timeframe": "15m",
            "data": os.path.join(data_dir, "SP_SPX, 15m__Linear.csv"),
            "image": os.path.join(images_dir, "2025_04_03_SPX_15minute_Linear.png")
        },
        "1h": {
            "timeframe": "1h",
            "data": os.path.join(data_dir, "SP_SPX, 60m__Linear.csv"),
            "image": os.path.join(images_dir, "2025_04_03_SPX_01hour_Linear.png")
        },
        "1d": {
            "timeframe": "1d",
            "data": os.path.join(data_dir, "SP_SPX, 1d_Linear.csv"),
            "image": os.path.join(images_dir, "2025_04_03_SPX_01day_Linear.png")
        }
    }
    
    # Create timestamp for output directories
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Set end date for SQL queries
    if target_date is None:
        # Use April 3, 2025 as the default target date to match the validation images
        end_date = datetime(2025, 4, 3, 16, 0, 0)  # 4:00 PM on April 3, 2025
    else:
        end_date = target_date
    
    # Calculate start date based on max_bars and timeframe
    # This is a rough estimate to ensure we have enough data
    start_dates = {
        "1m": datetime(2025, 3, 27, 9, 30, 0),  # About 5 trading days before end_date
        "3m": datetime(2025, 3, 27, 9, 30, 0),  # About 5 trading days before end_date
        "15m": datetime(2025, 3, 27, 9, 30, 0),  # About 5 trading days before end_date
        "1h": datetime(2025, 3, 20, 9, 30, 0),   # About 10 trading days before end_date
        "1d": datetime(2025, 2, 1, 9, 30, 0),    # About 2 months before end_date
    }
    
    # Run validation for each timeframe
    results = {}
    for timeframe_key, config in timeframes.items():
        timeframe = config["timeframe"]
        image_path = config["image"]
        
        if source_type.lower() == 'csv':
            # CSV source
            data_path = config["data"]
            if os.path.exists(data_path) and os.path.exists(image_path):
                output_dir = os.path.join(data_dir, f"validation_{timeframe_key}_{timestamp}")
                results[timeframe_key] = validate_timeframe(
                    data_file=data_path,
                    tradingview_image=image_path,
                    output_dir=output_dir,
                    source_type='csv'
                )
            else:
                print(f"Skipping {timeframe_key} - files not found")
                if not os.path.exists(data_path):
                    print(f"  Missing data file: {data_path}")
                if not os.path.exists(image_path):
                    print(f"  Missing image file: {image_path}")
        else:
            # SQL source
            if os.path.exists(image_path):
                output_dir = os.path.join(data_dir, f"validation_{timeframe_key}_{timestamp}")
                results[timeframe_key] = validate_timeframe(
                    tradingview_image=image_path,
                    output_dir=output_dir,
                    source_type='sql',
                    timeframe=timeframe,
                    start_date=start_dates.get(timeframe_key),
                    end_date=end_date,
                    max_bars=max_bars
                )
            else:
                print(f"Skipping {timeframe_key} - image file not found")
                print(f"  Missing image file: {image_path}")
    
    # Print summary
    print("\n\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    for timeframe, result in results.items():
        print(f"\nTimeframe: {timeframe}")
        print(f"  Zones detected: {len(result['zone_results']['zones'])}")
        print(f"  Comparison image: {os.path.basename(result['comparison_image_path']) if 'comparison_image_path' in result and result['comparison_image_path'] else 'None'}")
        print(f"  Peak detection data: {os.path.basename(result['peak_csv_path']) if 'peak_csv_path' in result else 'None'}")
    
    print("\nValidation complete for all timeframes.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate SRZone implementation across all timeframes')
    parser.add_argument('--source', choices=['csv', 'sql'], default='csv',
                        help='Data source type (csv or sql)')
    parser.add_argument('--date', type=str, default=None,
                        help='Target date for validation (SQL only, format: YYYY-MM-DD)')
    parser.add_argument('--max-bars', type=int, default=4000,
                        help='Maximum number of bars to return (default: 4000)')
    
    args = parser.parse_args()
    
    # Parse target date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"Invalid date format: {args.date}. Using default.")
    
    main(source_type=args.source, target_date=target_date, max_bars=args.max_bars)
