"""
Support and resistance zone generation for SRZone.

This module provides functions for generating support and resistance zones
based on pivot points and their distributions.
"""

import numpy as np
import pandas as pd
from .signal_processing import sinc_filter, peak_detection, calculate_weighted_average


def add_to_score(scores, source, weight, weight_style, min_range, bin_size, precision):
    """
    Add pivot points to score distribution.

    Parameters:
    -----------
    scores : numpy.ndarray
        Array of scores to update
    source : array-like
        Source values (pivot points)
    weight : array-like
        Weight values for each pivot
    weight_style : str
        Weighting style ('Linear', 'Time', or 'Volume')
    min_range : float
        Minimum range value
    bin_size : float
        Size of each bin
    precision : int
        Number of bins

    Returns:
    --------
    numpy.ndarray
        Updated scores array
    """
    # Convert to numpy arrays if they're not already
    if isinstance(source, (pd.Series, list)):
        source = np.array(source)

    if isinstance(weight, (pd.Series, list)):
        weight = np.array(weight)

    # If source is empty, return the original scores
    if len(source) == 0:
        return scores

    # Process each pivot point
    for i in range(len(source)):
        # Get the value and weight
        value = source[i]
        w = weight[i]

        # Apply weighting style - use the weights directly as they are already calculated correctly
        # in the pivot_detection.py module
        if weight_style == "Time" or weight_style == "Volume":
            # Use the pre-calculated weight directly
            W = w
        else:  # "Linear" or default
            # Equal weighting
            W = 1

        # Calculate the bin index
        idx = min(int((value - min_range) / bin_size), precision - 1)

        # Update the score
        if 0 <= idx < len(scores):
            scores[idx] += W

    return scores


def generate_zones(df, pivot_high_values, pivot_high_weights, pivot_low_values, pivot_low_weights, params):
    """
    Generate support and resistance zones based on pivot points.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    pivot_high_values : array-like
        Values of pivot highs
    pivot_high_weights : array-like
        Weights for pivot highs (e.g., time or volume)
    pivot_low_values : array-like
        Values of pivot lows
    pivot_low_weights : array-like
        Weights for pivot lows (e.g., time or volume)
    params : dict
        Configuration parameters:
        {
            'weight_style': str,  # 'Linear', 'Time', or 'Volume'
            'pivot_lookback': int,  # Number of pivots to consider
            'filter': float,  # Smoothing filter length
            'precision': int,  # Number of bins
            'auto_precision': bool,  # Whether to auto-calculate precision
            'include_ph': bool,  # Whether to include pivot highs
            'include_pl': bool,  # Whether to include pivot lows
            'scale': int,  # Scale for visualization
        }

    Returns:
    --------
    dict
        Dictionary containing zone information:
        {
            'zones': list of dicts with zone information,
            'scores': numpy.ndarray of raw scores,
            'filtered_scores': numpy.ndarray of filtered scores,
            'min_range': float,
            'max_range': float,
            'bin_size': float,
        }
    """
    # Extract parameters
    weight_style = params.get('weight_style', 'Linear')
    pivot_lookback = params.get('pivot_lookback', 50)
    filter_length = params.get('filter', 3)
    precision = params.get('precision', 75)
    auto_precision = params.get('auto_precision', True)
    include_ph = params.get('include_ph', True)
    include_pl = params.get('include_pl', True)
    scale = params.get('scale', 30)

    # Limit the number of pivots to consider
    if len(pivot_high_values) > pivot_lookback:
        pivot_high_values = pivot_high_values[-pivot_lookback:]
        pivot_high_weights = pivot_high_weights[-pivot_lookback:]

    if len(pivot_low_values) > pivot_lookback:
        pivot_low_values = pivot_low_values[-pivot_lookback:]
        pivot_low_weights = pivot_low_weights[-pivot_lookback:]

    # Calculate range
    max_range = max(
        max(pivot_high_values) if include_ph and len(pivot_high_values) > 0 else 0,
        max(pivot_low_values) if include_pl and len(pivot_low_values) > 0 else 0
    )

    min_range = min(
        min(pivot_high_values) if include_ph and len(pivot_high_values) > 0 else float('inf'),
        min(pivot_low_values) if include_pl and len(pivot_low_values) > 0 else float('inf')
    )

    # If no valid range, return empty result
    if max_range <= 0 or min_range == float('inf') or max_range <= min_range:
        return {
            'zones': [],
            'scores': np.array([]),
            'filtered_scores': np.array([]),
            'min_range': 0,
            'max_range': 0,
            'bin_size': 0,
        }

    # Calculate average true range (ATR) for auto precision
    atr = np.mean(df['high'] - df['low']) if len(df) > 0 else 10

    # Determine precision (number of bins)
    if auto_precision:
        precision = min(100, max(10, int((max_range - min_range) / atr)))

    # Calculate bin size
    bin_size = (max_range - min_range) / precision

    # Initialize scores array
    scores = np.zeros(precision)

    # Add pivot highs to scores
    if include_ph and len(pivot_high_values) > 0:
        scores = add_to_score(scores, pivot_high_values, pivot_high_weights, weight_style, min_range, bin_size, precision)

    # Add pivot lows to scores
    if include_pl and len(pivot_low_values) > 0:
        scores = add_to_score(scores, pivot_low_values, pivot_low_weights, weight_style, min_range, bin_size, precision)

    # Apply sinc filter for smoothing
    filtered_scores = sinc_filter(scores, filter_length)

    # Find the minimum non-zero score
    real_minimum = 0
    for i in range(len(filtered_scores)):
        if filtered_scores[i] > 0:
            real_minimum = filtered_scores[i]
            break

    # Detect peaks in the filtered scores
    peak_indices = peak_detection(filtered_scores, scale, real_minimum, True)

    # Generate zones from peaks
    zones = []
    for idx in peak_indices:
        # Calculate zone boundaries
        bin_top = min_range + bin_size * (idx + 1)
        bin_bottom = min_range + bin_size * idx

        # Calculate zone center
        zone_price = (bin_top + bin_bottom) / 2

        # Determine zone type (support or resistance)
        is_support = df['close'].iloc[-1] > zone_price if len(df) > 0 else False
        zone_type = 'support' if is_support else 'resistance'

        # Calculate zone score
        zone_score = filtered_scores[int(idx)] if int(idx) < len(filtered_scores) else 0

        # Add zone to list
        zones.append({
            'price': zone_price,
            'top': bin_top,
            'bottom': bin_bottom,
            'type': zone_type,
            'score': zone_score,
        })

    return {
        'zones': zones,
        'scores': scores,
        'filtered_scores': filtered_scores,
        'min_range': min_range,
        'max_range': max_range,
        'bin_size': bin_size,
        'peak_indices': peak_indices,
    }


def calculate_zone_average(zones, df, params):
    """
    Calculate weighted average of zone prices.

    Parameters:
    -----------
    zones : dict
        Zone information from generate_zones
    df : pandas.DataFrame
        DataFrame with OHLCV data
    params : dict
        Configuration parameters

    Returns:
    --------
    float
        Weighted average of zone prices
    """
    # Extract parameters
    enable_ma = params.get('enable_ma', False)

    # If not enabled or no zones, return NaN
    if not enable_ma or not zones or len(zones['filtered_scores']) == 0:
        return np.nan

    # Calculate weighted average
    ma = calculate_weighted_average(
        zones['filtered_scores'],
        zones['min_range'],
        zones['bin_size']
    )

    return ma
