"""
Data loading and preprocessing utilities for SRZone.

This module provides functions for loading and preprocessing OHLCV data
from various sources, including CSV files exported from TradingView.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os


def load_ohlcv_data(file_path):
    """
    Load OHLCV data from CSV file.

    Parameters:
    -----------
    file_path : str
        Path to the CSV file containing OHLCV data

    Returns:
    --------
    pandas.DataFrame
        DataFrame with datetime index and OHLCV columns
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read CSV file
    df = pd.read_csv(file_path)

    # TradingView CSV format typically has these columns
    # Determine the format based on column names
    if 'time' in df.columns:
        # TradingView format
        time_col = 'time'
    elif 'Date' in df.columns:
        # Common format
        time_col = 'Date'
    else:
        # Try to find a datetime column
        datetime_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if datetime_cols:
            time_col = datetime_cols[0]
        else:
            raise ValueError("Could not identify datetime column in CSV file")

    # Convert time column to datetime
    df[time_col] = pd.to_datetime(df[time_col])

    # Set time column as index
    df = df.set_index(time_col)

    # Standardize column names
    column_mapping = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'volume': 'volume',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
    }

    # Rename columns if they exist
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    # Ensure OHLCV columns exist
    required_columns = ['open', 'high', 'low', 'close']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Sort by index
    df = df.sort_index()

    return df


def resample_ohlcv(df, timeframe):
    """
    Resample OHLCV data to a different timeframe.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    timeframe : str
        Target timeframe (e.g., '1H', '4H', '1D')

    Returns:
    --------
    pandas.DataFrame
        Resampled DataFrame
    """
    # Ensure df has datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be DatetimeIndex")

    # Resample
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum' if 'volume' in df.columns else None
    })

    # Drop rows with NaN values
    resampled = resampled.dropna()

    return resampled


def prepare_data_for_analysis(file_path, timeframe=None):
    """
    Load and prepare data for SRZone analysis.

    Parameters:
    -----------
    file_path : str
        Path to the CSV file containing OHLCV data
    timeframe : str, optional
        Target timeframe for resampling (e.g., '1H', '4H', '1D')
        If None, no resampling is performed

    Returns:
    --------
    pandas.DataFrame
        Prepared DataFrame with OHLCV data
    """
    # Load data
    df = load_ohlcv_data(file_path)

    # Resample if timeframe is specified
    if timeframe is not None:
        df = resample_ohlcv(df, timeframe)

    return df
