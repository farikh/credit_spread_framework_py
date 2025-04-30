"""
Data loading and preprocessing utilities for SRZone.

This module provides functions for loading and preprocessing OHLCV data
from various sources, including CSV files exported from TradingView and
SQL database tables.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys


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


def load_data(source_type, timeframe=None, file_path=None, start_date=None, end_date=None, max_bars=4000, debug=False):
    """
    Load OHLCV data from specified source (CSV or SQL database) with a limit on the number of bars.
    
    Parameters:
    -----------
    source_type : str
        Type of data source ('csv' or 'sql')
    timeframe : str
        Timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
    file_path : str, optional
        Path to CSV file (required if source_type is 'csv')
    start_date : str or datetime, optional
        Start date for data range (SQL only)
    end_date : str or datetime, optional
        End date for data range (SQL only)
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)
    debug : bool, optional
        Whether to print debug information
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standardized OHLCV data
    """
    if debug:
        print(f"Loading data from {source_type} source")
        print(f"Timeframe: {timeframe}")
        print(f"File path: {file_path}")
        print(f"Start date: {start_date}")
        print(f"End date: {end_date}")
        print(f"Max bars: {max_bars}")

    if source_type.lower() == 'csv':
        if not file_path:
            raise ValueError("file_path is required for CSV data source")
        
        # Load all data from CSV
        df = load_ohlcv_data(file_path)
        
        if debug:
            print(f"Loaded {len(df)} rows from CSV file")
        
        # Limit to the most recent max_bars
        if len(df) > max_bars:
            df = df.iloc[-max_bars:]
            if debug:
                print(f"Limited to {len(df)} rows (max_bars={max_bars})")
            
        # Resample if timeframe is specified
        if timeframe:
            df = resample_ohlcv(df, timeframe)
            if debug:
                print(f"Resampled to {timeframe} timeframe, resulting in {len(df)} rows")
    
    elif source_type.lower() == 'sql':
        if not timeframe:
            raise ValueError("timeframe is required for SQL data source")
            
        # Add the parent directory to the path to import from credit_spread_framework
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            
        if debug:
            print(f"Added parent directory to sys.path: {parent_dir}")
            print(f"sys.path: {sys.path}")
            
        # Import here to avoid circular imports
        try:
            from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
            if debug:
                print("Successfully imported load_bars_from_db")
        except ImportError as e:
            error_msg = f"Could not import load_bars_from_db: {str(e)}"
            print(error_msg)
            raise ImportError(error_msg)
        
        # If end_date is not specified, use current date
        if end_date is None:
            end_date = datetime.now()
            
        if debug:
            print(f"Calling load_bars_from_db with timeframe={timeframe}, start={start_date}, end={end_date}")
            
        # Load data from SQL with limit directly in the query
        try:
            df = load_bars_from_db(timeframe, start=start_date, end=end_date, limit=max_bars)
            if debug:
                print(f"Loaded {len(df)} rows from SQL database with limit={max_bars}")
                if not df.empty:
                    print(f"Columns: {df.columns.tolist()}")
                    print(f"First row: {df.iloc[0].to_dict()}")
                    print(f"Last row: {df.iloc[-1].to_dict()}")
        except Exception as e:
            error_msg = f"Error loading data from SQL database: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            raise Exception(error_msg)
        
        # Standardize column names to match CSV format
        column_mapping = {
            'open_price': 'open',
            'close_price': 'close',
            'spy_volume': 'volume'
        }
        df = df.rename(columns=column_mapping)
        if debug:
            print(f"Renamed columns: {column_mapping}")
            print(f"Columns after renaming: {df.columns.tolist()}")
        
        # Set timestamp as index
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
            if debug:
                print("Set timestamp as index")
    
    else:
        raise ValueError(f"Invalid source_type: {source_type}. Must be 'csv' or 'sql'")
    
    return df


def prepare_data_for_analysis(file_path=None, timeframe=None, source_type='csv', start_date=None, end_date=None, max_bars=4000, debug=False):
    """
    Load and prepare data for SRZone analysis from either CSV or SQL database.
    
    Parameters:
    -----------
    file_path : str, optional
        Path to the CSV file containing OHLCV data (required if source_type is 'csv')
    timeframe : str, optional
        Target timeframe for data (e.g., '1m', '3m', '15m', '1h', '1d')
        Required for SQL, optional for CSV (for resampling)
    source_type : str, optional
        Type of data source ('csv' or 'sql'), default is 'csv'
    start_date : str or datetime, optional
        Start date for data range (SQL only)
    end_date : str or datetime, optional
        End date for data range (SQL only)
    max_bars : int, optional
        Maximum number of bars to return (default: 4000, matching Pine script)
    debug : bool, optional
        Whether to print debug information
        
    Returns:
    --------
    pandas.DataFrame
        Prepared DataFrame with OHLCV data
    """
    return load_data(source_type, timeframe, file_path, start_date, end_date, max_bars, debug)
