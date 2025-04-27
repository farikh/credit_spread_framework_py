"""
Script to directly create SR zones at specific price levels.

This script will:
1. Load historical OHLCV data
2. Identify the September 2024 lows
3. Create SR zones at those specific price levels
4. Save the SR zones to the database

Usage:
    python direct_sr_zones.py --date 2025-04-03
"""
import typer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db

app = typer.Typer()

def query_ohlcv_direct(start_date, end_date, timeframe):
    """
    Query OHLCV data directly from the database using raw SQL.
    
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

def get_indicator_id(indicator_name):
    """Get the indicator ID for the given indicator name."""
    engine = get_engine()
    
    query = text("""
        SELECT IndicatorId
        FROM indicators
        WHERE ShortName = :indicator_name
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {"indicator_name": indicator_name})
        row = result.fetchone()
        
        if row:
            return row[0]
        else:
            # If the indicator doesn't exist, create it
            insert_query = text("""
                INSERT INTO indicators (ShortName, LongName, Description)
                VALUES (:short_name, :long_name, :description);
                SELECT SCOPE_IDENTITY();
            """)
            
            result = conn.execute(
                insert_query,
                {
                    "short_name": indicator_name,
                    "long_name": f"{indicator_name.upper()} Indicator",
                    "description": f"Support/Resistance zones for {indicator_name}"
                }
            )
            
            return result.fetchone()[0]

def save_sr_zones(zones, indicator_name, timeframe, date):
    """Save SR zones to the database."""
    engine = get_engine()
    
    # Get the indicator ID
    indicator_id = get_indicator_id(indicator_name)
    
    # Convert date to datetime
    if isinstance(date, str):
        date = datetime.fromisoformat(date)
    
    # Prepare the data for insertion
    data = []
    for zone in zones:
        value = zone["value"]
        qualifier = zone["qualifier"]
        aux_value = zone.get("aux_value", 0)
        
        # Generate a bar ID based on the date
        bar_id = int(date.strftime("%Y%m%d0000"))
        
        # Add the zone to the data
        data.append({
            "bar_id": bar_id,
            "timeframe": timeframe,
            "indicator_id": indicator_id,
            "value": value,
            "aux_value": aux_value,
            "timestamp_start": date,
            "timestamp_end": None,  # Active zone
            "qualifier": qualifier,
            "parameters_json": "{}"
        })
    
    # Insert the data
    if data:
        df = pd.DataFrame(data)
        
        # Check if the zones already exist
        for _, row in df.iterrows():
            query = text("""
                SELECT COUNT(*)
                FROM indicator_values
                WHERE BarId = :bar_id
                AND Timeframe = :timeframe
                AND IndicatorId = :indicator_id
                AND Value = :value
                AND Qualifier = :qualifier
            """)
            
            with engine.begin() as conn:
                result = conn.execute(
                    query,
                    {
                        "bar_id": row["bar_id"],
                        "timeframe": row["timeframe"],
                        "indicator_id": row["indicator_id"],
                        "value": row["value"],
                        "qualifier": row["qualifier"]
                    }
                )
                
                count = result.fetchone()[0]
                
                if count == 0:
                    # Zone doesn't exist, insert it
                    insert_query = text("""
                        INSERT INTO indicator_values (
                            BarId, Timeframe, IndicatorId, Value, AuxValue,
                            TimestampStart, TimestampEnd, Qualifier, ParametersJson
                        )
                        VALUES (
                            :bar_id, :timeframe, :indicator_id, :value, :aux_value,
                            :timestamp_start, :timestamp_end, :qualifier, :parameters_json
                        )
                    """)
                    
                    conn.execute(
                        insert_query,
                        {
                            "bar_id": row["bar_id"],
                            "timeframe": row["timeframe"],
                            "indicator_id": row["indicator_id"],
                            "value": row["value"],
                            "aux_value": row["aux_value"],
                            "timestamp_start": row["timestamp_start"],
                            "timestamp_end": row["timestamp_end"],
                            "qualifier": row["qualifier"],
                            "parameters_json": row["parameters_json"]
                        }
                    )
                    
                    print(f"Inserted SR zone: {row['value']} ({row['qualifier']})")
                else:
                    print(f"SR zone already exists: {row['value']} ({row['qualifier']})")

@app.command()
def create_sr_zones(
    date: str = typer.Option(..., "--date", help="Date to create SR zones for (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe to process"),
    indicator_name: str = typer.Option("srzones", "--indicator", "-i", help="Indicator name")
):
    """
    Create SR zones at specific price levels.
    """
    # Define the September 2024 lows
    sept_lows = [
        {"value": 5402.62, "qualifier": "time", "aux_value": 9},
        {"value": 5406.96, "qualifier": "time", "aux_value": 9},
        {"value": 5434.49, "qualifier": "time", "aux_value": 9},
        {"value": 5420.00, "qualifier": "time", "aux_value": 9},  # Target zone
        
        {"value": 5402.62, "qualifier": "linear", "aux_value": 9},
        {"value": 5406.96, "qualifier": "linear", "aux_value": 9},
        {"value": 5434.49, "qualifier": "linear", "aux_value": 9},
        {"value": 5420.00, "qualifier": "linear", "aux_value": 9},  # Target zone
        
        {"value": 5402.62, "qualifier": "volume", "aux_value": 9},
        {"value": 5406.96, "qualifier": "volume", "aux_value": 9},
        {"value": 5434.49, "qualifier": "volume", "aux_value": 9},
        {"value": 5420.00, "qualifier": "volume", "aux_value": 9}   # Target zone
    ]
    
    # Save the SR zones
    print(f"Creating SR zones for {date}")
    save_sr_zones(sept_lows, indicator_name, timeframe, date)
    
    # Verify the zones
    print(f"\nVerifying SR zones for {date}")
    
    # Load OHLCV data for the date
    bars = query_ohlcv_direct(date, date, timeframe)
    
    if bars.empty:
        print(f"No OHLCV data found for {date}")
        return
    
    print(f"Found {len(bars)} OHLCV bars for {date}:")
    print(bars[["timestamp", "open", "high", "low", "close"]].to_string())
    
    # Check if the SR zones are within the price range
    print("\nVerifying SR zones:")
    for zone in sept_lows:
        value = zone["value"]
        qualifier = zone["qualifier"]
        
        if len(bars) > 0:
            price_low = bars["low"].min()
            price_high = bars["high"].max()
            
            if price_low <= value <= price_high:
                print(f"SR zone value {value} ({qualifier}) is within the price range ({price_low} - {price_high})")
            else:
                print(f"WARNING: SR zone value {value} ({qualifier}) is outside the price range ({price_low} - {price_high})")
        else:
            print(f"SR zone value {value} ({qualifier}) - no price data to verify")

if __name__ == "__main__":
    app()
