"""
Peak detection export utilities for SRZone.

This module provides functions for exporting peak detection results to CSV
for direct comparison with TradingView's debug table output.
"""

import os
import pandas as pd
import numpy as np


def get_peak_table(peak_indices, filtered_scores, min_range, bin_size):
    """
    Generate a table of peak information similar to TradingView's debug table.
    
    Parameters:
    -----------
    peak_indices : list
        Indices of detected peaks from peak_detection()
    filtered_scores : array-like
        Filtered scores array
    min_range : float
        Minimum range value
    bin_size : float
        Size of each bin
        
    Returns:
    --------
    pandas.DataFrame
        Table with columns: Peak #, Array Index, Score, Price
    """
    peaks = []
    
    for i, p_idx in enumerate(peak_indices):
        # Get the actual index in the filtered_scores array
        actual_idx = int(p_idx)
        
        # Get the score value at this peak
        peak_score = filtered_scores[actual_idx] if actual_idx < len(filtered_scores) else 0
        
        # Calculate bin boundaries
        bin_top = min_range + bin_size * (p_idx + 1)
        bin_bottom = min_range + bin_size * p_idx
        
        # Calculate price at this peak
        peak_price = (bin_top + bin_bottom) / 2
        
        peaks.append({
            'Peak #': i,
            'Array Index': p_idx,
            'Score': peak_score,
            'Price': peak_price
        })
    
    return pd.DataFrame(peaks)


def export_peak_detection_data(peak_indices, filtered_scores, min_range, bin_size, output_path):
    """
    Export peak detection results to CSV for validation against TradingView.
    
    Parameters:
    -----------
    peak_indices : list
        Indices of detected peaks from peak_detection()
    filtered_scores : array-like
        Filtered scores array
    min_range : float
        Minimum range value
    bin_size : float
        Size of each bin
    output_path : str
        Path to save the CSV file
        
    Returns:
    --------
    str
        Path to the saved CSV file
    """
    # Generate peak table
    peak_table = get_peak_table(peak_indices, filtered_scores, min_range, bin_size)
    
    # Normalize path and create directory if it doesn't exist
    output_path = os.path.normpath(output_path)
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Save to CSV
    peak_table.to_csv(output_path, index=False)
    
    return output_path
