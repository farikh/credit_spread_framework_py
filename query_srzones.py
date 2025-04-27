"""
Script to query SR zones for a specific date.

This script will:
1. Query SR zones for a specific date
2. Display the results in a formatted table
3. Optionally filter by qualifier (time, linear, volume)

Usage:
    python query_srzones.py --date 2025-04-03 [--qualifier time]
"""
import typer
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

app = typer.Typer()

def query_sr_zones(date, qualifier=None):
    """
    Query SR zones for a specific date.
    
    Args:
        date: The date to query (YYYY-MM-DD)
        qualifier: Optional qualifier to filter by (time, linear, volume)
        
    Returns:
        DataFrame with SR zones
    """
    print(f"Querying SR zones for {date}")
    engine = get_engine()
    
    # Query SR zones
    query = """
        SELECT 
            iv.Value, iv.Qualifier, iv.AuxValue, 
            iv.TimestampStart, iv.TimestampEnd
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
        AND (
            (CAST(iv.TimestampStart AS DATE) <= :date AND (iv.TimestampEnd IS NULL OR CAST(iv.TimestampEnd AS DATE) >= :date))
        )
        AND (:qualifier IS NULL OR iv.Qualifier = :qualifier)
        ORDER BY iv.Qualifier, iv.Value
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "date": date,
                "qualifier": qualifier
            }
        )
        
        # Convert to DataFrame
        columns = ["Value", "Qualifier", "AuxValue", "TimestampStart", "TimestampEnd"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    if df.empty:
        print(f"No SR zones found for {date}")
    else:
        print(f"Found {len(df)} SR zones for {date}:")
        print(df.to_string())
    
    return df

def query_ohlcv(date):
    """
    Query OHLCV data for a specific date.
    
    Args:
        date: The date to query (YYYY-MM-DD)
        
    Returns:
        DataFrame with OHLCV data
    """
    print(f"Querying OHLCV data for {date}")
    engine = get_engine()
    
    query = """
        SELECT [open], [high], [low], [close], spy_volume, timestamp
        FROM dbo.spx_ohlcv_1d
        WHERE CAST(timestamp AS DATE) = :date
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "date": date
            }
        )
        
        # Convert to DataFrame
        columns = ["open", "high", "low", "close", "spy_volume", "timestamp"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    if df.empty:
        print(f"No OHLCV data found for {date}")
    else:
        print(f"Found {len(df)} OHLCV bars for {date}:")
        print(df.to_string())
    
    return df

def verify_sr_zones(sr_zones, ohlcv):
    """
    Verify if SR zones are within the price range.
    
    Args:
        sr_zones: DataFrame with SR zones
        ohlcv: DataFrame with OHLCV data
    """
    if sr_zones.empty or ohlcv.empty:
        return
    
    print("\nVerifying SR zones:")
    
    # Check if SR zones are within the price range
    min_price = ohlcv["low"].min()
    max_price = ohlcv["high"].max()
    
    for idx, zone in sr_zones.iterrows():
        if zone["Value"] < min_price * 0.9 or zone["Value"] > max_price * 1.1:
            print(f"WARNING: SR zone value {zone['Value']} is outside the price range ({min_price} - {max_price})")
        else:
            print(f"SR zone value {zone['Value']} is within the price range ({min_price} - {max_price})")

@app.command()
def main(
    date: str = typer.Option(..., "--date", "-d", help="Date to query (YYYY-MM-DD)"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier to filter by (time, linear, volume)")
):
    """
    Query SR zones for a specific date.
    """
    # Parse date
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format: {date}. Please use YYYY-MM-DD.")
        return
    
    # Query SR zones
    sr_zones = query_sr_zones(date, qualifier)
    
    # Query OHLCV data
    ohlcv = query_ohlcv(date)
    
    # Verify SR zones
    verify_sr_zones(sr_zones, ohlcv)

if __name__ == "__main__":
    app()
