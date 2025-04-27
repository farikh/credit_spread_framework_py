"""
Script to check OHLCV data for a specific date range.

Usage:
    python improved_check_ohlcv.py --start 2024-09-05 --end 2024-09-12 --timeframe 1d
"""
import typer
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

app = typer.Typer()

def query_ohlcv_data(start_date, end_date, timeframe):
    """
    Query OHLCV data for a specific date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Timeframe (e.g., '1d', '1m')
        
    Returns:
        DataFrame with OHLCV data
    """
    engine = get_engine()
    
    # Determine the table name based on the timeframe
    table_name = f"spx_ohlcv_{timeframe}"
    
    # Build the query
    query = text(f"""
        SELECT [bar_id], [timestamp], [ticker], [open], [high], [low], [close], [spy_volume]
        FROM dbo.{table_name}
        WHERE timestamp >= :start_date AND timestamp <= :end_date
        ORDER BY timestamp
    """)
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(
            query,
            {
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall())
        
    return df

def query_ohlcv_direct(start_date, end_date, timeframe):
    """
    Query OHLCV data directly from the database using raw SQL.
    This is a backup method in case the standard query doesn't work.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Timeframe (e.g., '1d', '1m')
        
    Returns:
        DataFrame with OHLCV data
    """
    engine = get_engine()
    
    # Determine the table name based on the timeframe
    table_name = f"spx_ohlcv_{timeframe}"
    
    # Build the query
    query = text(f"""
        SELECT TOP (1000) [bar_id]
            ,[timestamp]
            ,[ticker]
            ,[open]
            ,[high]
            ,[low]
            ,[close]
            ,[spy_volume]
        FROM [CreditSpreadsDB].[dbo].[{table_name}]
        WHERE timestamp >= '{start_date} 00:00:00.000' AND timestamp <= '{end_date} 23:59:59.999'
        ORDER BY timestamp
    """)
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(query)
        
        # Convert to DataFrame
        columns = ["bar_id", "timestamp", "ticker", "open", "high", "low", "close", "spy_volume"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    return df

@app.command()
def main(
    start: str = typer.Option(..., "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", "-e", help="End date (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe (e.g., '1d', '1m')")
):
    """
    Check OHLCV data for a specific date range.
    """
    # Validate dates
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return
    
    # Validate timeframe
    valid_timeframes = ["1d", "1m", "5m", "15m", "30m", "1h", "4h"]
    if timeframe not in valid_timeframes:
        print(f"Invalid timeframe. Please use one of: {', '.join(valid_timeframes)}")
        return
    
    print(f"Querying OHLCV data for {timeframe} from {start} to {end}")
    
    # Try the standard query first
    df = query_ohlcv_data(start, end, timeframe)
    
    # If the standard query fails, try the direct query
    if df.empty:
        print("Standard query returned no results. Trying direct SQL query...")
        df = query_ohlcv_direct(start, end, timeframe)
    
    # Display the results
    if df.empty:
        print(f"No OHLCV data found for {timeframe} from {start} to {end}")
    else:
        print(f"Found {len(df)} OHLCV bars for {timeframe} from {start} to {end}:")
        print(df.to_string())
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"Price Range: {df['low'].min()} to {df['high'].max()}")
        print(f"Average Volume: {df['spy_volume'].mean()}")
        
        # Highlight potential support/resistance levels
        print("\nPotential Support/Resistance Levels:")
        print(f"Lowest Low: {df['low'].min()} on {df.loc[df['low'].idxmin(), 'timestamp']}")
        print(f"Highest High: {df['high'].max()} on {df.loc[df['high'].idxmax(), 'timestamp']}")
        
        # Find clusters of lows (potential support)
        lows = df['low'].sort_values()
        low_clusters = []
        for i in range(len(lows) - 1):
            if abs(lows.iloc[i] - lows.iloc[i+1]) < 10:  # Within 10 points
                cluster = [lows.iloc[i], lows.iloc[i+1]]
                low_clusters.append(sum(cluster) / len(cluster))
        
        if low_clusters:
            print(f"Low Clusters (potential support): {', '.join([f'{c:.2f}' for c in low_clusters])}")
        
        # Find clusters of highs (potential resistance)
        highs = df['high'].sort_values()
        high_clusters = []
        for i in range(len(highs) - 1):
            if abs(highs.iloc[i] - highs.iloc[i+1]) < 10:  # Within 10 points
                cluster = [highs.iloc[i], highs.iloc[i+1]]
                high_clusters.append(sum(cluster) / len(cluster))
        
        if high_clusters:
            print(f"High Clusters (potential resistance): {', '.join([f'{c:.2f}' for c in high_clusters])}")

if __name__ == "__main__":
    app()
