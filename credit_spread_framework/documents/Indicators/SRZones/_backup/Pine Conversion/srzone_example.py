"""
SRZone Example Script

This script demonstrates how to use the srzone package to detect support and resistance zones
in price data and visualize the results.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis
from srzone.validation import validate_implementation


def run_srzone_example(data_file, output_dir=None, params=None):
    """
    Run SRZone analysis on the provided data file.

    Parameters:
    -----------
    data_file : str
        Path to the OHLCV data file
    output_dir : str, optional
        Directory to save outputs
    params : dict, optional
        Configuration parameters

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
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(data_file), 'srzone_output')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Loading data from {data_file}...")
    
    # Load and prepare data
    df = prepare_data_for_analysis(data_file, params.get('timeframe'))
    
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


def run_validation_example(data_file, tradingview_export=None, tradingview_image=None, output_dir=None):
    """
    Run validation of the SRZone implementation against TradingView Pine script.

    Parameters:
    -----------
    data_file : str
        Path to the OHLCV data file
    tradingview_export : str, optional
        Path to the TradingView zone export file
    tradingview_image : str, optional
        Path to the TradingView chart image
    output_dir : str, optional
        Directory to save validation outputs

    Returns:
    --------
    dict
        Validation results
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(data_file), 'validation_output')
    
    print(f"Running validation with data from {data_file}...")
    
    # Run validation
    validation_results = validate_implementation(
        data_file,
        tradingview_export,
        tradingview_image,
        output_dir=output_dir
    )
    
    print(f"Validation complete. Results saved to {output_dir}")
    
    # If comparison was performed, print summary
    if validation_results['comparison_results']:
        print("\nComparison Results:")
        print(validation_results['comparison_results']['summary'])
    
    return validation_results


if __name__ == "__main__":
    # Example usage
    # Replace with actual path to your data file
    sample_data_file = "credit_spread_framework/documents/Indicators/SRZones/Pine Conversion/validation/SP_SPX, 3_3dc75.csv"
    
    # Check if the file exists
    if os.path.exists(sample_data_file):
        # Run SRZone analysis
        results = run_srzone_example(sample_data_file)
        
        # Optionally run validation if TradingView data is available
        tradingview_image = "credit_spread_framework/documents/Indicators/SRZones/Pine Conversion/validation/2025_04_03_SPX_03minute_Linear.png"
        if os.path.exists(tradingview_image):
            validation_results = run_validation_example(sample_data_file, tradingview_image=tradingview_image)
    else:
        print(f"Sample data file not found: {sample_data_file}")
        print("Please update the file path to point to a valid OHLCV CSV file.")
