"""
Script to test the SR zone indicator fix.

This script will:
1. Update the SR zone parameters in the database
2. Delete existing SR zones for April 3, 2025
3. Process SR zones for April 3, 2025 using our new persistent SR zones script
4. Query the results to verify they match TradingView
"""
import subprocess
import pandas as pd
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

def run_command(cmd):
    """Run a command and print its output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result

def delete_sr_zones(date):
    """Delete SR zones for a specific date"""
    print(f"Deleting SR zones for {date}")
    engine = get_engine()
    
    query = """
        DELETE iv
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND CAST(iv.TimestampStart AS DATE) = :date
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "indicator_name": "srzones",
                "timeframe": "1d",
                "date": date
            }
        )
        
    print(f"Deleted SR zones for {date}")

def query_sr_zones(date):
    """Query SR zones for a specific date"""
    print(f"Querying SR zones for {date}")
    engine = get_engine()
    
    # First, check if there are any SR zones with NULL TimestampEnd
    null_check_query = """
        SELECT COUNT(*) 
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND iv.TimestampEnd IS NULL
    """
    
    with engine.begin() as conn:
        null_count = conn.execute(
            text(null_check_query),
            {
                "indicator_name": "srzones",
                "timeframe": "1d"
            }
        ).scalar()
        
    print(f"Found {null_count} SR zones with NULL TimestampEnd")
    
    # Query all SR zones for the date
    query = """
        SELECT iv.Value, iv.Qualifier, iv.AuxValue, iv.TimestampStart, 
               CASE WHEN iv.TimestampEnd IS NULL THEN 'NULL' ELSE CONVERT(VARCHAR, iv.TimestampEnd, 121) END as TimestampEnd
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND (
            (CAST(iv.TimestampStart AS DATE) <= :date AND (iv.TimestampEnd IS NULL OR CAST(iv.TimestampEnd AS DATE) >= :date))
            OR CAST(iv.TimestampStart AS DATE) = :date
        )
        ORDER BY iv.Qualifier, iv.Value
    """
    
    with engine.begin() as conn:
        result = conn.execute(
            text(query),
            {
                "indicator_name": "srzones",
                "timeframe": "1d",
                "date": date
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
    """Query OHLCV data for a specific date"""
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

def main():
    # Test date
    test_date = "2025-04-03"
    
    # Step 1: Update SR zone parameters
    print("Step 1: Updating SR zone parameters")
    run_command("python update_srzone_params.py")
    
    # Step 2: Delete existing SR zones for the test date
    print("\nStep 2: Deleting existing SR zones")
    delete_sr_zones(test_date)
    
    # Step 3: Process SR zones for the test date
    print("\nStep 3: Processing SR zones")
    run_command(f"python process_persistent_srzones.py --start {test_date} --end {test_date} --timeframe 1d --history-days 200")
    
    # Step 4: Query the results
    print("\nStep 4: Querying results")
    sr_zones = query_sr_zones(test_date)
    ohlcv = query_ohlcv(test_date)
    
    # Step 5: Verify the results
    print("\nStep 5: Verifying results")
    if not sr_zones.empty and not ohlcv.empty:
        # Check if SR zones are within the price range
        min_price = ohlcv["low"].min()
        max_price = ohlcv["high"].max()
        
        for idx, zone in sr_zones.iterrows():
            if zone["Value"] < min_price * 0.9 or zone["Value"] > max_price * 1.1:
                print(f"WARNING: SR zone value {zone['Value']} is outside the price range ({min_price} - {max_price})")
            else:
                print(f"SR zone value {zone['Value']} is within the price range ({min_price} - {max_price})")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
