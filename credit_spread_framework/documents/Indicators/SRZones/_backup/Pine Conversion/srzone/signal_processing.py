"""
Signal processing utilities for SRZone.

This module provides functions for signal processing, including the sinc filter
for smoothing pivot distributions and other mathematical operations needed for
support and resistance zone detection.
"""

import numpy as np
import pandas as pd


def sinc(x, bandwidth):
    """
    Calculate the sinc function value.

    Parameters:
    -----------
    x : float or numpy.ndarray
        Input value(s)
    bandwidth : float
        Bandwidth parameter

    Returns:
    --------
    float or numpy.ndarray
        Sinc function value(s)
    """
    # Handle the case where x is 0 to avoid division by zero
    if np.isscalar(x):
        if x == 0:
            return 1.0
        else:
            return np.sin(np.pi * x / bandwidth) / (np.pi * x / bandwidth)
    else:
        # For array input, handle zeros separately
        result = np.zeros_like(x, dtype=float)
        nonzero = x != 0
        result[~nonzero] = 1.0
        result[nonzero] = np.sin(np.pi * x[nonzero] / bandwidth) / (np.pi * x[nonzero] / bandwidth)
        return result


def sinc_filter(values, length):
    """
    Apply sinc filter to smooth values.

    Parameters:
    -----------
    values : array-like
        Input values to smooth
    length : float
        Filter length parameter

    Returns:
    --------
    numpy.ndarray
        Smoothed values
    """
    # Convert to numpy array if it's not already
    if isinstance(values, (pd.Series, list)):
        values = np.array(values)
    
    # If length is 0 or negative, or values is empty, return the original values
    if length <= 0 or len(values) == 0:
        return values
    
    src_size = len(values)
    result = np.zeros(src_size)
    
    for i in range(src_size):
        # Calculate weights for each point
        diff = i - np.arange(src_size)
        weights = sinc(diff, length + 1)
        
        # Apply weights
        weighted_sum = np.sum(values * weights)
        weight_sum = np.sum(weights)
        
        # Calculate smoothed value
        current_price = weighted_sum / weight_sum
        
        # Ensure non-negative values (if needed)
        result[i] = max(0, current_price)
    
    return result


def peak_detection(values, scale, real_minimum, enable=True):
    """
    Detect peaks in a distribution of values.

    Parameters:
    -----------
    values : array-like
        Input values to analyze
    scale : int
        Scale parameter for discretizing the values
    real_minimum : float
        Minimum value to consider
    enable : bool, optional
        Whether to enable peak detection (default: True)

    Returns:
    --------
    list
        Indices of detected peaks
    """
    # Convert to numpy array if it's not already
    if isinstance(values, (pd.Series, list)):
        values = np.array(values)
    
    peak_idx = []
    
    # If not enabled or values is empty, return empty list
    if not enable or len(values) == 0:
        return peak_idx
    
    # Calculate the maximum value for scaling
    max_val = values.max() - real_minimum
    
    i = -1
    while i < len(values) - 1:
        i += 1
        
        # Scale the current value to the range [1, scale]
        center = int((values[i] - real_minimum) / max_val * (scale - 1) + 1)
        
        # Get scaled values for previous and next points
        previous = 0 if i == 0 else int((values[i - 1] - real_minimum) / max_val * (scale - 1) + 1)
        next_val = 0 if i == len(values) - 1 else int((values[i + 1] - real_minimum) / max_val * (scale - 1) + 1)
        
        # Check if current value is higher than previous
        if center > previous:
            j = i + 1
            
            # If current value equals next value, find where the plateau ends
            if center == next_val:
                while j <= len(values) - 1:
                    j += 1
                    if j >= len(values):
                        break
                    
                    vary_previous = int((values[j - 1] - real_minimum) / max_val * (scale - 1) + 1)
                    very_next = 0 if j >= len(values) else int((values[j] - real_minimum) / max_val * (scale - 1) + 1)
                    
                    # If we found the end of the plateau
                    if very_next != vary_previous:
                        # If the plateau ends with a drop, it's a peak
                        if center > very_next:
                            p_idx = int((i + j) / 2.0)
                            # Adjust for even/odd plateau length
                            peak_idx.append(p_idx if (j - i) > 2 and (j - i) % 2 != 0 else p_idx - 0.5)
                            i = j
                        else:
                            i = j - 1
                        break
            
            # If current value is higher than next value, it's a peak
            if center > next_val:
                peak_idx.append(i)
    
    return peak_idx


def calculate_weighted_average(values, min_range, bin_size, weights=None):
    """
    Calculate weighted average of values.

    Parameters:
    -----------
    values : array-like
        Input values (typically scores)
    min_range : float
        Minimum range value
    bin_size : float
        Size of each bin
    weights : array-like, optional
        Weights for each value (default: None, equal weights)

    Returns:
    --------
    float
        Weighted average
    """
    # Convert to numpy arrays if they're not already
    if isinstance(values, (pd.Series, list)):
        values = np.array(values)
    
    if weights is not None and isinstance(weights, (pd.Series, list)):
        weights = np.array(weights)
    
    # If values is empty, return NaN
    if len(values) == 0 or values.max() <= 0:
        return np.nan
    
    weight_sum = 0.0
    value_sum = 0.0
    
    for i in range(len(values)):
        score = values[i]
        if score == 0:
            continue
        
        # Calculate the bin boundaries
        bin_top = min_range + bin_size * (i + 1)
        bin_bottom = min_range + bin_size * i
        
        # Calculate the price (middle of the bin)
        price = (bin_top + bin_bottom) / 2
        
        # Get the weight (default to score if no weights provided)
        weight = weights[i] if weights is not None else score
        
        weight_sum += weight
        value_sum += price * weight
    
    # Calculate weighted average
    if weight_sum > 0:
        return value_sum / weight_sum
    else:
        return np.nan
