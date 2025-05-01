"""
Data loading and preprocessing utilities for SRZone with improved SQL handling.

This module provides functions for loading and preprocessing OHLCV data
from various sources, including CSV files exported from TradingView and
SQL database tables.

This version includes improved SQL query handling that addresses:
1. UTC to EST time zone conversion for date ranges
2. Full 24-hour coverage when the same date is specified for start and end
3. More efficient query using UNION ALL
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

    # Load data from CSV
    df = pd.read_csv(file_path)

    # Check if the file is a TradingView export
    if 'time' in df.columns:
        # TradingView export format
        df['timestamp'] = pd.to_datetime(df['time'])
        df = df.set_index('timestamp')
        
        # Rename columns to match our standard format
        column_mapping = {
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'Volume': 'volume'  # TradingView uses 'Volume' with capital V
        }
        
        # Only include columns that exist in the DataFrame
        column_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Select only the columns we need
        columns_to_keep = ['open', 'high', 'low', 'close']
        if 'volume' in df.columns:
            columns_to_keep.append('volume')
        
        df = df[columns_to_keep]
    else:
        # Assume standard OHLCV format with timestamp column
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')

    # Ensure volume column exists (set to 1 if not present)
    if 'volume' not in df.columns:
        df['volume'] = 1

    return df


def resample_ohlcv(df, timeframe):
    """
    Resample OHLCV data to a different timeframe.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    timeframe : str
        Target timeframe for resampling (e.g., '1H', '4H', '1D')

    Returns:
    --------
    pandas.DataFrame
        Resampled DataFrame
    """
    # Map timeframe strings to pandas resample rule
    timeframe_map = {
        '1m': '1min',
        '3m': '3min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '1H',
        '2h': '2H',
        '4h': '4H',
        '1d': '1D'
    }

    # Get the resample rule
    if timeframe in timeframe_map:
        rule = timeframe_map[timeframe]
    else:
        # Try to use the timeframe directly
        rule = timeframe

    # Resample
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
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
        DataFrame with OHLCV data
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
        
        # Add parent directory to sys.path to allow importing from credit_spread_framework
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            if debug:
                print(f"Added parent directory to sys.path: {parent_dir}")
                print(f"sys.path: {sys.path}")
            
        # Import here to avoid circular imports
        try:
            # Import the database engine
            from credit_spread_framework.data.db_engine import get_engine
            
            # Import our improved load_bars function
            from srzone.load_bars_improved import load_bars_improved
            
            if debug:
                print("Successfully imported load_bars_improved")
        except ImportError as e:
            error_msg = f"Could not import required modules: {str(e)}"
            print(error_msg)
            raise ImportError(error_msg)
        
        # Get the database engine
        engine = get_engine()
            
        if debug:
            print(f"Calling load_bars_improved with timeframe={timeframe}, start={start_date}, end={end_date}")
            
        # Load data from SQL with improved query
        try:
            df = load_bars_improved(engine, timeframe, start=start_date, end=end_date, limit=max_bars, debug=debug)
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
    if debug:
        print("Loading data for analysis")
        print(f"Source type: {source_type}")
        print(f"File path: {file_path}")
        print(f"Timeframe: {timeframe}")
        print(f"Start date: {start_date}")
        print(f"End date: {end_date}")
        print(f"Max bars: {max_bars}")
    
    # Validate parameters
    if source_type.lower() == 'csv' and not file_path:
        raise ValueError("file_path is required when source_type is 'csv'")
    if source_type.lower() == 'sql' and not timeframe:
        raise ValueError("timeframe is required when source_type is 'sql'")
    
    # Load data
    df = load_data(
        source_type=source_type,
        timeframe=timeframe,
        file_path=file_path,
        start_date=start_date,
        end_date=end_date,
        max_bars=max_bars,
        debug=debug
    )
    
    return df
