"""
Peak detection comparison utilities for SRZone.

This module provides functions for comparing peak detection results between
the Python implementation and TradingView Pine script.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def import_tradingview_peaks(file_path):
    """
    Import peak detection data from TradingView export.
    
    Parameters:
    -----------
    file_path : str
        Path to the TradingView peak export file (CSV)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with peak detection data
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read CSV file
    try:
        # Try to read with standard column names
        peaks = pd.read_csv(file_path)
        
        # Rename columns if they don't match our expected format
        column_mapping = {
            'Peak #': 'Peak #',
            'Peak': 'Peak #',
            'Array Index': 'Array Index',
            'Index': 'Array Index',
            'Score': 'Score',
            'Price': 'Price'
        }
        
        # Rename columns if needed
        for old_name, new_name in column_mapping.items():
            if old_name in peaks.columns and old_name != new_name:
                peaks.rename(columns={old_name: new_name}, inplace=True)
        
        return peaks
    
    except Exception as e:
        raise ValueError(f"Error reading TradingView peak data: {str(e)}")


def compare_peaks(python_peaks, tradingview_peaks, tolerance=0.01):
    """
    Compare peak detection results between Python and TradingView.
    
    Parameters:
    -----------
    python_peaks : pandas.DataFrame
        Peak detection data from Python implementation
    tradingview_peaks : pandas.DataFrame
        Peak detection data from TradingView
    tolerance : float, optional
        Tolerance for price comparison (default: 0.01)
        
    Returns:
    --------
    dict
        Comparison results:
        {
            'matching_peaks': list of tuples (python_peak, tv_peak),
            'python_only_peaks': list of python_peaks not in TradingView,
            'tv_only_peaks': list of TradingView peaks not in Python,
            'match_percentage': percentage of matching peaks,
            'summary': text summary of comparison
        }
    """
    matching_peaks = []
    python_only_peaks = []
    tv_only_peaks = tradingview_peaks.copy()  # Copy to remove matches
    
    # For each Python peak, find matching TradingView peak
    for _, py_peak in python_peaks.iterrows():
        match_found = False
        
        for i, (idx, tv_peak) in enumerate(tv_only_peaks.iterrows()):
            # Check if peaks match within tolerance
            price_match = abs(py_peak['Price'] - tv_peak['Price']) <= tolerance
            index_match = abs(py_peak['Array Index'] - tv_peak['Array Index']) <= 0.5
            
            if price_match or index_match:
                matching_peaks.append((py_peak, tv_peak))
                tv_only_peaks = tv_only_peaks.drop(idx)
                match_found = True
                break
        
        if not match_found:
            python_only_peaks.append(py_peak)
    
    # Calculate match percentage
    total_peaks = len(python_peaks) + len(tv_only_peaks)
    match_percentage = len(matching_peaks) / total_peaks * 100 if total_peaks > 0 else 0
    
    # Create summary
    summary = f"Peak Comparison Results:\n"
    summary += f"- Matching peaks: {len(matching_peaks)}\n"
    summary += f"- Python-only peaks: {len(python_only_peaks)}\n"
    summary += f"- TradingView-only peaks: {len(tv_only_peaks)}\n"
    summary += f"- Match percentage: {match_percentage:.2f}%\n"
    
    return {
        'matching_peaks': matching_peaks,
        'python_only_peaks': python_only_peaks,
        'tv_only_peaks': tv_only_peaks,
        'match_percentage': match_percentage,
        'summary': summary
    }


def plot_peak_comparison(python_peaks, tradingview_peaks, output_path=None):
    """
    Create a visualization comparing peak detection between Python and TradingView.
    
    Parameters:
    -----------
    python_peaks : pandas.DataFrame
        Peak detection data from Python implementation
    tradingview_peaks : pandas.DataFrame
        Peak detection data from TradingView
    output_path : str, optional
        Path to save the visualization
        
    Returns:
    --------
    matplotlib.figure.Figure
        Figure object
    """
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Plot Python peaks
    ax1.scatter(python_peaks['Array Index'], python_peaks['Price'], 
                color='blue', label='Python Peaks', s=50, alpha=0.7)
    ax1.set_title('Python Peak Detection')
    ax1.set_ylabel('Price')
    ax1.grid(True)
    ax1.legend()
    
    # Plot TradingView peaks
    ax2.scatter(tradingview_peaks['Array Index'], tradingview_peaks['Price'], 
                color='red', label='TradingView Peaks', s=50, alpha=0.7)
    ax2.set_title('TradingView Peak Detection')
    ax2.set_xlabel('Array Index')
    ax2.set_ylabel('Price')
    ax2.grid(True)
    ax2.legend()
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if output path is provided
    if output_path:
        # Normalize path and create directory if it doesn't exist
        output_path = os.path.normpath(output_path)
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        plt.savefig(output_path)
    
    return fig


def run_peak_comparison(python_peaks_path, tradingview_peaks_path, output_dir=None):
    """
    Run a comparison between Python and TradingView peak detection.
    
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
        output_dir = os.path.dirname(python_peaks_path)
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Load peak data
    python_peaks = pd.read_csv(python_peaks_path)
    tradingview_peaks = import_tradingview_peaks(tradingview_peaks_path)
    
    # Compare peaks
    comparison_results = compare_peaks(python_peaks, tradingview_peaks)
    
    # Save comparison results
    comparison_path = os.path.join(output_dir, 'peak_comparison.txt')
    with open(comparison_path, 'w') as f:
        f.write(comparison_results['summary'])
    
    # Create visualization
    visualization_path = os.path.join(output_dir, 'peak_comparison.png')
    plot_peak_comparison(python_peaks, tradingview_peaks, visualization_path)
    
    return {
        'python_peaks': python_peaks,
        'tradingview_peaks': tradingview_peaks,
        'comparison_results': comparison_results,
        'comparison_path': comparison_path,
        'visualization_path': visualization_path
    }
