"""
Pivot point detection for SRZone.

This module provides functions for detecting pivot highs and lows in price data,
which are essential for identifying support and resistance zones.
"""

import numpy as np
import pandas as pd


def detect_pivot_high(series, left, right):
    """
    Detect pivot highs in a price series.

    A pivot high is a point where the price is higher than all points
    within 'left' bars to the left and 'right' bars to the right.

    Parameters:
    -----------
    series : array-like
        Price series (typically high prices)
    left : int
        Number of bars to check on the left
    right : int
        Number of bars to check on the right

    Returns:
    --------
    list of bool
        Boolean array where True indicates a pivot high
    """
    # Convert to numpy array if it's not already
    if isinstance(series, (pd.Series, list)):
        series = np.array(series)

    pivots = []
    series_length = len(series)

    # We need at least left + right + 1 bars to detect a pivot
    if series_length < left + right + 1:
        return [False] * series_length

    # Check each potential pivot point
    for i in range(left, series_length - right):
        is_pivot = True

        # Check if current point is higher than all points to the left
        for j in range(1, left + 1):
            if series[i] <= series[i - j]:
                is_pivot = False
                break

        # If still a potential pivot, check points to the right
        if is_pivot:
            for j in range(1, right + 1):
                if series[i] <= series[i + j]:
                    is_pivot = False
                    break

        pivots.append(is_pivot)

    # Add False for the bars at the beginning and end where we couldn't check
    return [False] * left + pivots + [False] * right


def detect_pivot_low(series, left, right):
    """
    Detect pivot lows in a price series.

    A pivot low is a point where the price is lower than all points
    within 'left' bars to the left and 'right' bars to the right.

    Parameters:
    -----------
    series : array-like
        Price series (typically low prices)
    left : int
        Number of bars to check on the left
    right : int
        Number of bars to check on the right

    Returns:
    --------
    list of bool
        Boolean array where True indicates a pivot low
    """
    # Convert to numpy array if it's not already
    if isinstance(series, (pd.Series, list)):
        series = np.array(series)

    pivots = []
    series_length = len(series)

    # We need at least left + right + 1 bars to detect a pivot
    if series_length < left + right + 1:
        return [False] * series_length

    # Check each potential pivot point
    for i in range(left, series_length - right):
        is_pivot = True

        # Check if current point is lower than all points to the left
        for j in range(1, left + 1):
            if series[i] >= series[i - j]:
                is_pivot = False
                break

        # If still a potential pivot, check points to the right
        if is_pivot:
            for j in range(1, right + 1):
                if series[i] >= series[i + j]:
                    is_pivot = False
                    break

        pivots.append(is_pivot)

    # Add False for the bars at the beginning and end where we couldn't check
    return [False] * left + pivots + [False] * right


def detect_pivots(df, strength_params=None, weight_style='Linear'):
    """
    Detect pivot highs and lows in OHLCV data with multiple strength parameters.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    strength_params : list of dict, optional
        List of dictionaries with strength parameters:
        [
            {'length': 5, 'include': True},
            {'length': 10, 'include': True},
            ...
        ]
        If None, default parameters will be used.
    weight_style : str, optional
        Weighting style ('Linear', 'Time', or 'Volume')
        Default is 'Linear'

    Returns:
    --------
    dict
        Dictionary with pivot information:
        {
            'pivot_high_idx': list of indices where pivot highs were detected,
            'pivot_high_values': list of price values at pivot highs,
            'pivot_high_weights': list of weights for pivot highs,
            'pivot_low_idx': list of indices where pivot lows were detected,
            'pivot_low_values': list of price values at pivot lows,
            'pivot_low_weights': list of weights for pivot lows,
            'pivot_high_mask': boolean mask for all pivot highs,
            'pivot_low_mask': boolean mask for all pivot lows
        }
    """
    # Default strength parameters if none provided
    if strength_params is None:
        strength_params = [
            {'length': 5, 'include': True},
            {'length': 10, 'include': True},
            {'length': 20, 'include': True},
            {'length': 50, 'include': True}
        ]

    # Initialize result containers
    pivot_high_mask = np.zeros(len(df), dtype=bool)
    pivot_low_mask = np.zeros(len(df), dtype=bool)
    pivot_high_values = []
    pivot_low_values = []
    pivot_high_idx = []
    pivot_low_idx = []
    pivot_high_weights = []
    pivot_low_weights = []

    # Detect pivots for each strength parameter
    for param in strength_params:
        if not param['include']:
            continue

        length = param['length']

        # Detect pivot highs
        ph_mask = detect_pivot_high(df['high'].values, length, length)
        # Update the combined mask
        for i in range(len(ph_mask)):
            if ph_mask[i]:
                pivot_high_mask[i] = True
                pivot_high_values.append(df['high'].iloc[i])
                pivot_high_idx.append(i)

                # Calculate weight based on weighting style (matching TradingView Pine script)
                if weight_style == 'Time':
                    # Time-based weighting: bar_index - length
                    weight = i - length
                elif weight_style == 'Volume' and 'volume' in df.columns:
                    # Volume-based weighting: volume at the pivot bar
                    weight = df['volume'].iloc[i]
                elif weight_style == 'Volume' and 'spy_volume' in df.columns:
                    # Alternative volume field name
                    weight = df['spy_volume'].iloc[i]
                else:
                    # Linear weighting: all pivots have equal weight
                    weight = 1

                pivot_high_weights.append(weight)

        # Detect pivot lows
        pl_mask = detect_pivot_low(df['low'].values, length, length)
        # Update the combined mask
        for i in range(len(pl_mask)):
            if pl_mask[i]:
                pivot_low_mask[i] = True
                pivot_low_values.append(df['low'].iloc[i])
                pivot_low_idx.append(i)

                # Calculate weight based on weighting style (matching TradingView Pine script)
                if weight_style == 'Time':
                    # Time-based weighting: bar_index - length
                    weight = i - length
                elif weight_style == 'Volume' and 'volume' in df.columns:
                    # Volume-based weighting: volume at the pivot bar
                    weight = df['volume'].iloc[i]
                elif weight_style == 'Volume' and 'spy_volume' in df.columns:
                    # Alternative volume field name
                    weight = df['spy_volume'].iloc[i]
                else:
                    # Linear weighting: all pivots have equal weight
                    weight = 1

                pivot_low_weights.append(weight)

    # Normalize time weights to match TradingView's implementation
    if weight_style == 'Time' and (pivot_high_weights or pivot_low_weights):
        # Find the minimum weight across all pivots
        all_weights = pivot_high_weights + pivot_low_weights
        if all_weights:
            min_weight = min(all_weights)
            # Normalize weights: w = 1 + (w - min_weight)
            pivot_high_weights = [1 + (w - min_weight) for w in pivot_high_weights]
            pivot_low_weights = [1 + (w - min_weight) for w in pivot_low_weights]

    return {
        'pivot_high_idx': pivot_high_idx,
        'pivot_high_values': pivot_high_values,
        'pivot_high_weights': pivot_high_weights,
        'pivot_low_idx': pivot_low_idx,
        'pivot_low_values': pivot_low_values,
        'pivot_low_weights': pivot_low_weights,
        'pivot_high_mask': pivot_high_mask,
        'pivot_low_mask': pivot_low_mask
    }
