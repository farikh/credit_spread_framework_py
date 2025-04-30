"""
Visualization utilities for SRZone.

This module provides functions for visualizing support and resistance zones,
pivot points, and other elements of the SRZone analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
import os


def plot_ohlc(ax, df, width=0.6, colorup='green', colordown='red', alpha=0.8):
    """
    Plot OHLC candlestick chart.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    df : pandas.DataFrame
        DataFrame with OHLC data
    width : float, optional
        Width of candlesticks (default: 0.6)
    colorup : str, optional
        Color for up candles (default: 'green')
    colordown : str, optional
        Color for down candles (default: 'red')
    alpha : float, optional
        Alpha transparency (default: 0.8)

    Returns:
    --------
    matplotlib.axes.Axes
        Updated axes
    """
    # Convert index to matplotlib dates if it's a datetime index
    if isinstance(df.index, pd.DatetimeIndex):
        dates = mdates.date2num(df.index.to_pydatetime())
    else:
        dates = np.arange(len(df))
    
    # Draw OHLC bars
    for i in range(len(df)):
        # Get OHLC values
        open_price = df['open'].iloc[i]
        high_price = df['high'].iloc[i]
        low_price = df['low'].iloc[i]
        close_price = df['close'].iloc[i]
        
        # Determine candle color
        color = colorup if close_price >= open_price else colordown
        
        # Plot candle body
        body_height = close_price - open_price
        rect = patches.Rectangle(
            (dates[i] - width/2, min(open_price, close_price)),
            width, abs(body_height),
            facecolor=color, edgecolor='black', alpha=alpha
        )
        ax.add_patch(rect)
        
        # Plot wicks
        ax.plot(
            [dates[i], dates[i]],
            [low_price, min(open_price, close_price)],
            color='black', alpha=alpha
        )
        ax.plot(
            [dates[i], dates[i]],
            [max(open_price, close_price), high_price],
            color='black', alpha=alpha
        )
    
    # Set x-axis formatter
    if isinstance(df.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()
    
    return ax


def plot_pivots(ax, df, pivot_high_mask, pivot_low_mask, high_color='red', low_color='green', marker_size=50):
    """
    Plot pivot high and low points.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    df : pandas.DataFrame
        DataFrame with OHLC data
    pivot_high_mask : array-like
        Boolean mask for pivot highs
    pivot_low_mask : array-like
        Boolean mask for pivot lows
    high_color : str, optional
        Color for pivot highs (default: 'red')
    low_color : str, optional
        Color for pivot lows (default: 'green')
    marker_size : int, optional
        Size of markers (default: 50)

    Returns:
    --------
    matplotlib.axes.Axes
        Updated axes
    """
    # Convert index to matplotlib dates if it's a datetime index
    if isinstance(df.index, pd.DatetimeIndex):
        dates = mdates.date2num(df.index.to_pydatetime())
    else:
        dates = np.arange(len(df))
    
    # Plot pivot highs
    pivot_high_indices = np.where(pivot_high_mask)[0]
    if len(pivot_high_indices) > 0:
        ax.scatter(
            dates[pivot_high_indices],
            df['high'].iloc[pivot_high_indices],
            color=high_color, marker='^', s=marker_size, zorder=5
        )
    
    # Plot pivot lows
    pivot_low_indices = np.where(pivot_low_mask)[0]
    if len(pivot_low_indices) > 0:
        ax.scatter(
            dates[pivot_low_indices],
            df['low'].iloc[pivot_low_indices],
            color=low_color, marker='v', s=marker_size, zorder=5
        )
    
    return ax


def plot_zones(ax, zones, df, support_color='green', resistance_color='red', alpha=0.3, extend_right=20):
    """
    Plot support and resistance zones.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    zones : list of dict
        List of zone dictionaries from generate_zones
    df : pandas.DataFrame
        DataFrame with OHLC data
    support_color : str, optional
        Color for support zones (default: 'green')
    resistance_color : str, optional
        Color for resistance zones (default: 'red')
    alpha : float, optional
        Alpha transparency (default: 0.3)
    extend_right : int, optional
        Number of bars to extend zones to the right (default: 20)

    Returns:
    --------
    matplotlib.axes.Axes
        Updated axes
    """
    # If no zones, return unchanged axes
    if not zones:
        return ax
    
    # Convert index to matplotlib dates if it's a datetime index
    if isinstance(df.index, pd.DatetimeIndex):
        dates = mdates.date2num(df.index.to_pydatetime())
    else:
        dates = np.arange(len(df))
    
    # Calculate x-coordinates for zones
    x_start = dates[0]
    x_end = dates[-1] + extend_right * (dates[1] - dates[0]) if len(dates) > 1 else dates[-1] + 1
    
    # Plot each zone
    for zone in zones:
        # Get zone properties
        zone_type = zone['type']
        top = zone['top']
        bottom = zone['bottom']
        
        # Determine color based on zone type
        color = support_color if zone_type == 'support' else resistance_color
        
        # Create rectangle patch
        rect = patches.Rectangle(
            (x_start, bottom),
            x_end - x_start, top - bottom,
            facecolor=color, edgecolor=color, alpha=alpha, zorder=1
        )
        ax.add_patch(rect)
        
        # Add zone price label
        ax.text(
            x_end, (top + bottom) / 2,
            f"{zone['price']:.2f}",
            color='black', fontsize=8, ha='left', va='center',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
        )
    
    return ax


def plot_distribution(ax, filtered_scores, min_range, bin_size, high_color='cyan', low_color='magenta', scale=30):
    """
    Plot score distribution.

    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        Axes to plot on
    filtered_scores : array-like
        Filtered scores from generate_zones
    min_range : float
        Minimum range value
    bin_size : float
        Size of each bin
    high_color : str, optional
        Color for high scores (default: 'cyan')
    low_color : str, optional
        Color for low scores (default: 'magenta')
    scale : int, optional
        Scale for visualization (default: 30)

    Returns:
    --------
    matplotlib.axes.Axes
        Updated axes
    """
    # If no scores, return unchanged axes
    if len(filtered_scores) == 0:
        return ax
    
    # Find the minimum non-zero score
    real_minimum = 0
    for i in range(len(filtered_scores)):
        if filtered_scores[i] > 0:
            real_minimum = filtered_scores[i]
            break
    
    # Create colormap
    cmap = LinearSegmentedColormap.from_list('custom_cmap', [low_color, high_color])
    
    # Calculate max score for normalization
    max_score = filtered_scores.max() - real_minimum
    
    # Plot distribution
    for i in range(len(filtered_scores)):
        score = filtered_scores[i]
        if score <= 0:
            continue
        
        # Calculate normalized score
        norm_score = int((score - real_minimum) / max_score * (scale - 1) + 1)
        
        # Calculate bin boundaries
        bin_top = min_range + bin_size * (i + 1)
        bin_bottom = min_range + bin_size * i
        
        # Calculate color based on score
        color = cmap(norm_score / scale)
        
        # Plot horizontal bar
        ax.barh(
            (bin_top + bin_bottom) / 2,
            norm_score,
            height=bin_size,
            color=color,
            alpha=0.7,
            left=ax.get_xlim()[1] - scale
        )
    
    return ax


def plot_srzone_analysis(df, pivot_results, zone_results, params, filename=None, figsize=(12, 8)):
    """
    Create a complete SRZone analysis plot.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLC data
    pivot_results : dict
        Results from detect_pivots
    zone_results : dict
        Results from generate_zones
    params : dict
        Configuration parameters
    filename : str, optional
        If provided, save the plot to this file
    figsize : tuple, optional
        Figure size (default: (12, 8))

    Returns:
    --------
    matplotlib.figure.Figure
        The generated figure
    """
    # Create figure and axes
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot OHLC data
    plot_ohlc(ax, df)
    
    # Plot pivot points
    plot_pivots(
        ax, df,
        pivot_results['pivot_high_mask'],
        pivot_results['pivot_low_mask']
    )
    
    # Plot zones
    plot_zones(ax, zone_results['zones'], df)
    
    # Plot distribution if enabled
    if params.get('show_dist', True):
        plot_distribution(
            ax,
            zone_results['filtered_scores'],
            zone_results['min_range'],
            zone_results['bin_size'],
            scale=params.get('scale', 30)
        )
    
    # Set title and labels
    symbol = df.index.name if df.index.name else 'Price'
    timeframe = params.get('timeframe', '')
    title = f"Support & Resistance Zones - {symbol} {timeframe}"
    ax.set_title(title)
    ax.set_ylabel('Price')
    
    # Add grid
    ax.grid(alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure if filename is provided
    if filename:
        # Create directory if it doesn't exist
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Save figure
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig


def create_validation_comparison(pine_image_path, df, pivot_results, zone_results, params, output_path):
    """
    Create a validation comparison between Pine and Python implementations.

    Parameters:
    -----------
    pine_image_path : str
        Path to the Pine script chart image
    df : pandas.DataFrame
        DataFrame with OHLC data
    pivot_results : dict
        Results from detect_pivots
    zone_results : dict
        Results from generate_zones
    params : dict
        Configuration parameters
    output_path : str
        Path to save the comparison image

    Returns:
    --------
    str
        Path to the saved comparison image
    """
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Load and display Pine chart
    if os.path.exists(pine_image_path):
        pine_img = plt.imread(pine_image_path)
        ax1.imshow(pine_img)
        ax1.axis('off')
        ax1.set_title('TradingView Pine Script')
    else:
        ax1.text(0.5, 0.5, 'Pine chart image not found', ha='center', va='center')
        ax1.axis('off')
    
    # Create Python implementation chart
    plot_ohlc(ax2, df)
    plot_pivots(ax2, df, pivot_results['pivot_high_mask'], pivot_results['pivot_low_mask'])
    plot_zones(ax2, zone_results['zones'], df)
    
    # Set title and labels
    symbol = df.index.name if df.index.name else 'Price'
    timeframe = params.get('timeframe', '')
    ax2.set_title(f"Python Implementation - {symbol} {timeframe}")
    ax2.set_ylabel('Price')
    ax2.grid(alpha=0.3)
    
    # Add main title
    fig.suptitle('Validation: Pine Script vs. Python Implementation', fontsize=16)
    
    # Adjust layout
    plt.tight_layout()
    fig.subplots_adjust(top=0.9)
    
    # Create directory if it doesn't exist
    directory = os.path.dirname(output_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Save comparison
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return output_path
