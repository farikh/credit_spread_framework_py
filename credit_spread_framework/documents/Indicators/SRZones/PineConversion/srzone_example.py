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
from srzone.peak_comparison import run_peak_comparison


def run_srzone_example(data_file=None, output_dir=None, params=None, source_type='csv', 
                      timeframe=None, start_date=None, end_date=None, max_bars=4000):
    """
    Run SRZone analysis on data from specified source.

    Parameters:
    -----------
    data_file : str, optional
        Path to the OHLCV data file (required if source_type is 'csv')
    output_dir : str, optional
        Directory to save outputs
    params : dict, optional
        Configuration parameters
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
        if data_file:
            output_dir = os.path.join(os.path.dirname(data_file), f'srzone_output_{timestamp}')
        else:
            # For SQL source, create output in current directory
            output_dir = os.path.normpath(f'srzone_output_{timestamp}')
    
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
    
    df = prepare_data_for_analysis(
        file_path=data_file,
        timeframe=timeframe or params.get('timeframe'),
        source_type=source_type,
        start_date=start_date,
        end_date=end_date,
        max_bars=max_bars
    )
    
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


def run_validation_example(data_file=None, tradingview_export=None, tradingview_image=None, output_dir=None,
                          source_type='csv', timeframe=None, start_date=None, end_date=None, max_bars=4000):
    """
    Run validation of the SRZone implementation against TradingView Pine script.

    Parameters:
    -----------
    data_file : str, optional
        Path to the OHLCV data file (required if source_type is 'csv')
    tradingview_export : str, optional
        Path to the TradingView zone export file
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
    if tradingview_export:
        tradingview_export = os.path.normpath(tradingview_export)
    if tradingview_image:
        tradingview_image = os.path.normpath(tradingview_image)
    
    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if data_file:
            output_dir = os.path.join(os.path.dirname(data_file), f'validation_output_{timestamp}')
        else:
            # For SQL source, create output in current directory
            output_dir = os.path.normpath(f'validation_output_{timestamp}')
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Print data source information
    if source_type.lower() == 'csv':
        print(f"Running validation with data from CSV file: {data_file}...")
    else:
        print(f"Running validation with data from SQL database for timeframe: {timeframe}...")
        if start_date:
            print(f"Start date: {start_date}")
        if end_date:
            print(f"End date: {end_date}")
    
    # Run validation
    validation_results = validate_implementation(
        data_file,
        tradingview_export,
        tradingview_image,
        output_dir=output_dir,
        source_type=source_type,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        max_bars=max_bars
    )
    
    print(f"Validation complete. Results saved to {output_dir}")
    
    # If comparison was performed, print summary
    if validation_results['comparison_results']:
        print("\nComparison Results:")
        print(validation_results['comparison_results']['summary'])
    
    # Print information about peak detection data
    if 'peak_csv_path' in validation_results:
        print(f"\nPeak detection data exported to: {validation_results['peak_csv_path']}")
        print("This CSV file contains the same information as the TradingView debug table:")
        print("- Peak #: Index of the peak")
        print("- Array Index: Position in the filtered scores array")
        print("- Score: Value at that position")
        print("- Price: Calculated price level for that peak")
        print("\nYou can use this data to directly compare with TradingView's peak detection.")
    
    return validation_results


def run_peak_comparison_example(python_peaks_path, tradingview_peaks_path, output_dir=None):
    """
    Run a comparison between Python and TradingView peak detection.
    
    This function demonstrates how to compare the peak detection results
    between the Python implementation and TradingView Pine script.
    
    Parameters:
    -----------
    python_peaks_path : str
        Path to the Python peak detection CSV file
    tradingview_peaks_path : str
        Path to the TradingView peak detection CSV file
    output_dir : str, optional
        Directory to save comparison outputs
        
    Returns:
    --------
    dict
        Comparison results
    """
    # Normalize paths
    python_peaks_path = os.path.normpath(python_peaks_path)
    tradingview_peaks_path = os.path.normpath(tradingview_peaks_path)
    
    # Set default output directory if not provided
    if output_dir is None:
        # Add timestamp to output directory to ensure it's unique
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(python_peaks_path), f'peak_comparison_{timestamp}')
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Comparing peak detection data...")
    print(f"Python peaks: {python_peaks_path}")
    print(f"TradingView peaks: {tradingview_peaks_path}")
    
    # Run peak comparison
    comparison_results = run_peak_comparison(
        python_peaks_path,
        tradingview_peaks_path,
        output_dir
    )
    
    print(f"Peak comparison complete. Results saved to {output_dir}")
    print("\nPeak Comparison Results:")
    print(comparison_results['comparison_results']['summary'])
    print(f"\nVisualization saved to: {comparison_results['visualization_path']}")
    
    # Show the plot
    plt.figure(figsize=(12, 10))
    img = plt.imread(comparison_results['visualization_path'])
    plt.imshow(img)
    plt.axis('off')
    plt.show()
    
    return comparison_results


if __name__ == "__main__":
    # Example usage
    # Replace with actual path to your data file
    sample_data_file = os.path.normpath("validation/data/SP_SPX, 3_3dc75.csv")
    
    # Check if the file exists
    if os.path.exists(sample_data_file):
        # Create validation directory if it doesn't exist
        validation_dir = os.path.dirname(sample_data_file)
        if not os.path.exists(validation_dir):
            os.makedirs(validation_dir, exist_ok=True)
            
        # Run SRZone analysis
        results = run_srzone_example(sample_data_file)
        
        # Optionally run validation if TradingView data is available
        tradingview_image = os.path.normpath("validation/images/2025_04_03_SPX_03minute_Linear.png")
        
        # Create images directory if it doesn't exist
        images_dir = os.path.dirname(tradingview_image)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir, exist_ok=True)
            
        if os.path.exists(tradingview_image):
            validation_results = run_validation_example(sample_data_file, tradingview_image=tradingview_image)
            
            # If you have TradingView peak data, you can compare it with Python peak data
            python_peaks_path = validation_results.get('peak_csv_path')
            tradingview_peaks_path = os.path.normpath("validation/data/tradingview_peaks.csv")
            
            if os.path.exists(python_peaks_path) and os.path.exists(tradingview_peaks_path):
                # Use timestamp for peak comparison directory
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                peak_comparison_dir = os.path.normpath(os.path.join(os.path.dirname(python_peaks_path), f'peak_comparison_{timestamp}'))
                if not os.path.exists(peak_comparison_dir):
                    os.makedirs(peak_comparison_dir, exist_ok=True)
                    
                peak_comparison_results = run_peak_comparison_example(
                    python_peaks_path,
                    tradingview_peaks_path,
                    peak_comparison_dir
                )
    else:
        print(f"Sample data file not found: {sample_data_file}")
        print("Please update the file path to point to a valid OHLCV CSV file.")
