"""
SRZone Validation Script

This script validates the Python implementation of SRZones against the TradingView Pine script implementation.
It loads data from CSV files, processes it using the SRZone implementation, and compares the results with
expected outputs from TradingView.

Usage:
    python validate_srzone_implementation.py --timeframe 1d --source csv --file "SP_SPX, 1d_Linear.csv"
    python validate_srzone_implementation.py --timeframe 15m --source csv --file "SP_SPX, 15m__Linear.csv"
    python validate_srzone_implementation.py --timeframe 1m --source sql --start 2025-04-01 --end 2025-04-03
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import json
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

# Add the current directory to the path so we can import the srzone package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the SRZone modules
from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis

# Default parameters for SRZone
DEFAULT_PARAMS = {
    'strength_params': [
        {'length': 5, 'include': True},
        {'length': 10, 'include': True},
        {'length': 20, 'include': True}
    ],
    'weight_style': 'Linear',  # 'Linear', 'Time', or 'Volume'
    'zone_width': 0.5,         # Zone width percentage
    'zone_strength': 2,        # Minimum strength for a zone
    'max_zones': 10,           # Maximum number of zones to display
    'extend_right': 20         # Number of bars to extend zones to the right
}

def setup_output_directory(timeframe, source_type):
    """
    Create an output directory for validation results.
    
    Parameters:
    -----------
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    source_type : str
        Type of data source ('csv' or 'sql')
        
    Returns:
    --------
    str
        Path to the output directory
    """
    # Create a timestamp for the output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the output directory
    output_dir = os.path.join(current_dir, "validation", "output", f"validation_{timeframe}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def export_pivot_data(df, pivot_results, output_dir):
    """
    Export pivot detection data to CSV.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    pivot_results : dict
        Dictionary with pivot detection results
    output_dir : str
        Path to the output directory
        
    Returns:
    --------
    str
        Path to the exported CSV file
    """
    # Create a DataFrame with pivot data
    pivot_data = []
    
    for i in range(len(df)):
        row = {
            'timestamp': df.index[i] if isinstance(df.index[i], str) else df.index[i].strftime('%Y-%m-%d %H:%M:%S'),
            'bar_index': i,
            'high': df['high'].iloc[i],
            'low': df['low'].iloc[i],
            'is_pivot_high': i in pivot_results['pivot_high_idx'],
            'is_pivot_low': i in pivot_results['pivot_low_idx']
        }
        pivot_data.append(row)
    
    # Create a DataFrame and export to CSV
    pivot_df = pd.DataFrame(pivot_data)
    output_file = os.path.join(output_dir, 'python_pivots.csv')
    pivot_df.to_csv(output_file, index=False)
    
    return output_file

def export_zone_data(zones, output_dir):
    """
    Export zone data to CSV.
    
    Parameters:
    -----------
    zones : list of dict
        List of zone dictionaries from generate_zones
    output_dir : str
        Path to the output directory
        
    Returns:
    --------
    str
        Path to the exported CSV file
    """
    # Create a DataFrame with zone data
    zone_df = pd.DataFrame(zones)
    output_file = os.path.join(output_dir, 'python_zones.csv')
    zone_df.to_csv(output_file, index=False)
    
    return output_file

def load_tradingview_data(file_path):
    """
    Load TradingView data from CSV or JSON file.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV or JSON file
        
    Returns:
    --------
    list of dict
        List of zone dictionaries
    """
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    # Get file extension
    ext = os.path.splitext(file_path)[1]
    
    if ext.lower() == '.json':
        # Load JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract zones from JSON
        zones = []
        if isinstance(data, dict) and 'zones' in data:
            zones = data['zones']
        elif isinstance(data, list):
            zones = data
        
        return zones
    
    elif ext.lower() == '.csv':
        # Load CSV file
        zones = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string values to appropriate types
                zone = {
                    'price': float(row.get('price', 0)),
                    'top': float(row.get('top', 0)),
                    'bottom': float(row.get('bottom', 0)),
                    'type': row.get('type', ''),
                    'score': float(row.get('score', 0))
                }
                zones.append(zone)
        
        return zones
    
    else:
        print(f"Unsupported file format: {ext}")
        return []

def compare_zones(python_zones, tradingview_zones, tolerance=0.01):
    """
    Compare Python zones with TradingView zones.
    
    Parameters:
    -----------
    python_zones : list of dict
        List of zone dictionaries from Python implementation
    tradingview_zones : list of dict
        List of zone dictionaries from TradingView
    tolerance : float, optional
        Tolerance for price comparison (default: 0.01)
        
    Returns:
    --------
    dict
        Dictionary with comparison results
    """
    # Copy zones to avoid modifying the originals
    py_zones = python_zones.copy()
    tv_zones = tradingview_zones.copy()
    
    # Initialize results
    matching_zones = []
    python_only_zones = []
    tv_only_zones = tv_zones.copy()
    
    # For each Python zone, find matching TradingView zone
    for py_zone in py_zones:
        match_found = False
        
        for i, tv_zone in enumerate(tv_only_zones):
            # Check if zones match within tolerance
            price_match = abs(py_zone['price'] - tv_zone['price']) <= tolerance
            type_match = py_zone['type'] == tv_zone['type']
            
            if price_match and type_match:
                matching_zones.append((py_zone, tv_zone))
                tv_only_zones.pop(i)
                match_found = True
                break
        
        if not match_found:
            python_only_zones.append(py_zone)
    
    # Calculate match percentage
    total_zones = len(python_zones) + len(tradingview_zones) - len(matching_zones)
    match_percentage = len(matching_zones) / total_zones * 100 if total_zones > 0 else 0
    
    return {
        'matching_zones': matching_zones,
        'python_only_zones': python_only_zones,
        'tv_only_zones': tv_only_zones,
        'match_percentage': match_percentage
    }

def generate_comparison_report(comparison_results, output_dir):
    """
    Generate a comparison report.
    
    Parameters:
    -----------
    comparison_results : dict
        Dictionary with comparison results
    output_dir : str
        Path to the output directory
        
    Returns:
    --------
    str
        Path to the report file
    """
    # Create report file
    report_file = os.path.join(output_dir, 'comparison_report.md')
    
    with open(report_file, 'w') as f:
        f.write('# SRZone Comparison Report\n\n')
        
        # Write match percentage
        f.write(f'## Match Percentage: {comparison_results["match_percentage"]:.2f}%\n\n')
        
        # Write matching zones
        f.write('## Matching Zones\n\n')
        f.write('| Python Price | Python Type | TradingView Price | TradingView Type |\n')
        f.write('|-------------|------------|-----------------|----------------|\n')
        
        for py_zone, tv_zone in comparison_results['matching_zones']:
            f.write(f"| {py_zone['price']:.2f} | {py_zone['type']} | {tv_zone['price']:.2f} | {tv_zone['type']} |\n")
        
        # Write Python-only zones
        f.write('\n## Python-only Zones\n\n')
        f.write('| Price | Type | Score |\n')
        f.write('|-------|------|-------|\n')
        
        for zone in comparison_results['python_only_zones']:
            f.write(f"| {zone['price']:.2f} | {zone['type']} | {zone['score']:.2f} |\n")
        
        # Write TradingView-only zones
        f.write('\n## TradingView-only Zones\n\n')
        f.write('| Price | Type | Score |\n')
        f.write('|-------|------|-------|\n')
        
        for zone in comparison_results['tv_only_zones']:
            f.write(f"| {zone['price']:.2f} | {zone['type']} | {zone['score']:.2f} |\n")
    
    return report_file

def run_validation(args):
    """
    Run validation of the SRZone implementation.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Command-line arguments
    """
    # Set up output directory
    output_dir = setup_output_directory(args.timeframe, args.source)
    print(f"Output directory: {output_dir}")
    
    # Load data
    print(f"Loading data from {args.source}...")
    
    if args.source == 'csv':
        # Check if file exists
        data_dir = os.path.join(current_dir, "validation", "data")
        file_path = os.path.join(data_dir, args.file)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        # Load data
        df = prepare_data_for_analysis(
            file_path=file_path,
            timeframe=args.timeframe,
            source_type='csv',
            debug=args.debug
        )
    else:
        # Load data from SQL
        df = prepare_data_for_analysis(
            source_type='sql',
            timeframe=args.timeframe,
            start_date=args.start,
            end_date=args.end,
            max_bars=args.max_bars,
            debug=args.debug
        )
    
    # Check if data is loaded
    if df is None or df.empty:
        print("No data loaded.")
        return
    
    print(f"Loaded {len(df)} bars.")
    
    # Save loaded data to CSV
    data_file = os.path.join(output_dir, 'input_data.csv')
    df.to_csv(data_file)
    print(f"Saved input data to {data_file}")
    
    # Set up parameters
    params = DEFAULT_PARAMS.copy()
    params['weight_style'] = args.weight_style
    
    # Detect pivots
    print("Detecting pivots...")
    pivot_results = detect_pivots(df, params.get('strength_params'), weight_style=params['weight_style'])
    
    # Export pivot data
    pivot_file = export_pivot_data(df, pivot_results, output_dir)
    print(f"Exported pivot data to {pivot_file}")
    
    # Generate zones
    print("Generating zones...")
    zone_results = generate_zones(
        df,
        pivot_results['pivot_high_values'],
        pivot_results['pivot_high_weights'],
        pivot_results['pivot_low_values'],
        pivot_results['pivot_low_weights'],
        params
    )
    
    # Export zone data
    zone_file = export_zone_data(zone_results['zones'], output_dir)
    print(f"Exported zone data to {zone_file}")
    
    # Create visualization
    print("Creating visualization...")
    output_image = os.path.join(output_dir, 'srzone_analysis.png')
    fig = plot_srzone_analysis(df, pivot_results, zone_results, params, output_image)
    print(f"Saved visualization to {output_image}")
    
    # Compare with TradingView data if available
    if args.tv_data:
        print(f"Comparing with TradingView data from {args.tv_data}...")
        tv_zones = load_tradingview_data(args.tv_data)
        
        if tv_zones:
            comparison_results = compare_zones(zone_results['zones'], tv_zones)
            report_file = generate_comparison_report(comparison_results, output_dir)
            print(f"Generated comparison report: {report_file}")
            print(f"Match percentage: {comparison_results['match_percentage']:.2f}%")
        else:
            print("No TradingView data loaded.")
    
    print("\nValidation completed successfully.")
    print(f"All output files are in: {output_dir}")

def main():
    """
    Main function to parse command-line arguments and run validation.
    """
    parser = argparse.ArgumentParser(description='Validate SRZone implementation against TradingView Pine script.')
    
    # Data source parameters
    parser.add_argument('--source', choices=['csv', 'sql'], default='csv',
                        help='Data source type (csv or sql)')
    parser.add_argument('--file', type=str, help='CSV file name (for csv source)')
    parser.add_argument('--timeframe', type=str, required=True,
                        help='Timeframe for data (e.g., 1m, 3m, 15m, 1h, 1d)')
    parser.add_argument('--start', type=str, help='Start date for SQL data (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date for SQL data (YYYY-MM-DD)')
    parser.add_argument('--max-bars', type=int, default=4000,
                        help='Maximum number of bars to load (default: 4000)')
    
    # TradingView comparison parameters
    parser.add_argument('--tv-data', type=str,
                        help='Path to TradingView zone data (CSV or JSON)')
    
    # Algorithm parameters
    parser.add_argument('--weight-style', choices=['Linear', 'Time', 'Volume'],
                        default='Linear', help='Weighting style for pivots')
    
    # Debug parameters
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug output')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.source == 'csv' and not args.file:
        parser.error("--file is required when source is 'csv'")
    
    if args.source == 'sql' and not (args.start or args.end):
        parser.error("Either --start or --end (or both) is required when source is 'sql'")
    
    # Run validation
    run_validation(args)

if __name__ == '__main__':
    main()
