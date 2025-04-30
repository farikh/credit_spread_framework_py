"""
Validation utilities for SRZone.

This module provides functions for validating the Python implementation of SRZone
against the TradingView Pine script implementation.
"""

import pandas as pd
import numpy as np
import os
import json
import csv
from .data_loader import load_ohlcv_data, prepare_data_for_analysis
from .pivot_detection import detect_pivots
from .zone_generation import generate_zones
from .visualization import create_validation_comparison


def export_pivot_data(df, pivot_results, output_path):
    """
    Export pivot detection results to CSV for validation.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data
    pivot_results : dict
        Results from detect_pivots
    output_path : str
        Path to save the CSV file

    Returns:
    --------
    str
        Path to the saved CSV file
    """
    # Create DataFrame with pivot data
    pivot_data = pd.DataFrame({
        'timestamp': df.index,
        'open': df['open'],
        'high': df['high'],
        'low': df['low'],
        'close': df['close'],
        'is_pivot_high': pivot_results['pivot_high_mask'],
        'is_pivot_low': pivot_results['pivot_low_mask']
    })
    
    # Create directory if it doesn't exist
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save to CSV
    pivot_data.to_csv(output_path, index=False)
    
    return output_path


def export_zone_data(zone_results, output_path):
    """
    Export zone detection results to CSV for validation.

    Parameters:
    -----------
    zone_results : dict
        Results from generate_zones
    output_path : str
        Path to save the CSV file

    Returns:
    --------
    str
        Path to the saved CSV file
    """
    # If no zones, create empty DataFrame
    if not zone_results or not zone_results['zones']:
        zone_data = pd.DataFrame(columns=['price', 'top', 'bottom', 'type', 'score'])
    else:
        # Create DataFrame with zone data
        zone_data = pd.DataFrame(zone_results['zones'])
    
    # Create directory if it doesn't exist
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save to CSV
    zone_data.to_csv(output_path, index=False)
    
    return output_path


def import_tradingview_zones(file_path):
    """
    Import zone data from TradingView export for comparison.

    Parameters:
    -----------
    file_path : str
        Path to the TradingView export file (CSV or JSON)

    Returns:
    --------
    list of dict
        List of zone dictionaries
    """
    # Check file extension
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == '.json':
        # Load JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract zones from JSON
        zones = []
        if 'zones' in data:
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
        raise ValueError(f"Unsupported file format: {ext}")


def compare_zones(python_zones, tradingview_zones, tolerance=0.01):
    """
    Compare zones between Python and TradingView implementations.

    Parameters:
    -----------
    python_zones : list of dict
        Zones from Python implementation
    tradingview_zones : list of dict
        Zones from TradingView implementation
    tolerance : float, optional
        Tolerance for price comparison (default: 0.01)

    Returns:
    --------
    dict
        Comparison results:
        {
            'matching_zones': list of tuples (python_zone, tv_zone),
            'python_only_zones': list of python_zones not in TradingView,
            'tv_only_zones': list of TradingView zones not in Python,
            'match_percentage': percentage of matching zones,
            'summary': text summary of comparison
        }
    """
    matching_zones = []
    python_only_zones = []
    tv_only_zones = list(tradingview_zones)  # Copy to remove matches
    
    # For each Python zone, find matching TradingView zone
    for py_zone in python_zones:
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
    total_zones = len(python_zones) + len(tv_only_zones)
    match_percentage = len(matching_zones) / total_zones * 100 if total_zones > 0 else 0
    
    # Create summary
    summary = f"Comparison Results:\n"
    summary += f"- Matching zones: {len(matching_zones)}\n"
    summary += f"- Python-only zones: {len(python_only_zones)}\n"
    summary += f"- TradingView-only zones: {len(tv_only_zones)}\n"
    summary += f"- Match percentage: {match_percentage:.2f}%\n"
    
    return {
        'matching_zones': matching_zones,
        'python_only_zones': python_only_zones,
        'tv_only_zones': tv_only_zones,
        'match_percentage': match_percentage,
        'summary': summary
    }


def validate_implementation(data_file, tradingview_export=None, tradingview_image=None, params=None, output_dir=None):
    """
    Validate the Python implementation against TradingView Pine script.

    Parameters:
    -----------
    data_file : str
        Path to the OHLCV data file
    tradingview_export : str, optional
        Path to the TradingView zone export file
    tradingview_image : str, optional
        Path to the TradingView chart image
    params : dict, optional
        Configuration parameters
    output_dir : str, optional
        Directory to save validation outputs

    Returns:
    --------
    dict
        Validation results
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
            'strength_params': [
                {'length': 5, 'include': True},
                {'length': 10, 'include': True},
                {'length': 20, 'include': True},
                {'length': 50, 'include': True}
            ]
        }
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(data_file), 'validation_output')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load and prepare data
    df = prepare_data_for_analysis(data_file, params.get('timeframe'))
    
    # Detect pivots
    pivot_results = detect_pivots(df, params.get('strength_params'))
    
    # Generate zones
    zone_results = generate_zones(
        df,
        pivot_results['pivot_high_values'],
        [1] * len(pivot_results['pivot_high_values']),  # Default weights
        pivot_results['pivot_low_values'],
        [1] * len(pivot_results['pivot_low_values']),  # Default weights
        params
    )
    
    # Export pivot data
    pivot_csv_path = os.path.join(output_dir, 'python_pivots.csv')
    export_pivot_data(df, pivot_results, pivot_csv_path)
    
    # Export zone data
    zone_csv_path = os.path.join(output_dir, 'python_zones.csv')
    export_zone_data(zone_results, zone_csv_path)
    
    # Compare with TradingView if export is provided
    comparison_results = None
    if tradingview_export and os.path.exists(tradingview_export):
        tv_zones = import_tradingview_zones(tradingview_export)
        comparison_results = compare_zones(zone_results['zones'], tv_zones)
        
        # Save comparison results
        comparison_path = os.path.join(output_dir, 'zone_comparison.txt')
        with open(comparison_path, 'w') as f:
            f.write(comparison_results['summary'])
    
    # Create visual comparison if image is provided
    comparison_image_path = None
    if tradingview_image and os.path.exists(tradingview_image):
        comparison_image_path = os.path.join(output_dir, 'visual_comparison.png')
        create_validation_comparison(
            tradingview_image,
            df,
            pivot_results,
            zone_results,
            params,
            comparison_image_path
        )
    
    # Return validation results
    return {
        'pivot_results': pivot_results,
        'zone_results': zone_results,
        'pivot_csv_path': pivot_csv_path,
        'zone_csv_path': zone_csv_path,
        'comparison_results': comparison_results,
        'comparison_image_path': comparison_image_path
    }


def run_batch_validation(data_dir, tradingview_dir, params=None, output_dir=None):
    """
    Run batch validation on multiple data files.

    Parameters:
    -----------
    data_dir : str
        Directory containing OHLCV data files
    tradingview_dir : str
        Directory containing TradingView exports and images
    params : dict, optional
        Configuration parameters
    output_dir : str, optional
        Directory to save validation outputs

    Returns:
    --------
    dict
        Batch validation results
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(data_dir, 'batch_validation')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find all CSV files in data directory
    data_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    # Run validation for each data file
    results = {}
    for data_file in data_files:
        # Get base name without extension
        base_name = os.path.splitext(data_file)[0]
        
        # Look for matching TradingView export and image
        tv_export = None
        tv_image = None
        
        # Check for export file
        for ext in ['.csv', '.json']:
            export_path = os.path.join(tradingview_dir, f"{base_name}_zones{ext}")
            if os.path.exists(export_path):
                tv_export = export_path
                break
        
        # Check for image file
        for ext in ['.png', '.jpg', '.jpeg']:
            image_path = os.path.join(tradingview_dir, f"{base_name}{ext}")
            if os.path.exists(image_path):
                tv_image = image_path
                break
        
        # Create output subdirectory for this validation
        file_output_dir = os.path.join(output_dir, base_name)
        
        # Run validation
        result = validate_implementation(
            os.path.join(data_dir, data_file),
            tv_export,
            tv_image,
            params,
            file_output_dir
        )
        
        # Store result
        results[base_name] = result
    
    # Create summary report
    summary_path = os.path.join(output_dir, 'batch_summary.txt')
    with open(summary_path, 'w') as f:
        f.write("Batch Validation Summary\n")
        f.write("=======================\n\n")
        
        for name, result in results.items():
            f.write(f"File: {name}\n")
            if result['comparison_results']:
                f.write(f"Match percentage: {result['comparison_results']['match_percentage']:.2f}%\n")
            else:
                f.write("No comparison available\n")
            f.write(f"Zones detected: {len(result['zone_results']['zones'])}\n")
            f.write("\n")
    
    return {
        'results': results,
        'summary_path': summary_path
    }
