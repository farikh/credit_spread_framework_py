"""
Script to check resampled OHLCV data for consistency.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime

def main():
    engine = get_engine()
    
    # Define date range
    start_date = "2025-04-01"
    end_date = "2025-04-03"
    
    # Check each timeframe
    timeframes = ["1d", "1h", "15m", "3m"]
    
    for timeframe in timeframes:
        table_name = f"spx_ohlcv_{timeframe}"
        
        # Query data
        query = text(f"""
            SELECT * FROM {table_name}
            WHERE timestamp BETWEEN :start AND :end
            ORDER BY timestamp
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "start": start_date,
                    "end": end_date
                }
            )
            
            columns = [col[0] for col in result.cursor.description]
            df = pd.DataFrame(result.fetchall(), columns=columns)
        
        if df.empty:
            print(f"No data found for {timeframe} between {start_date} and {end_date}")
            continue
            
        print(f"\n{'-'*80}")
        print(f"Timeframe: {timeframe}")
        print(f"Found {len(df)} bars")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        # Print first and last few rows
        print("\nFirst 3 rows:")
        print(df.head(3)[["timestamp", "open", "high", "low", "close", "spy_volume"]])
        
        print("\nLast 3 rows:")
        print(df.tail(3)[["timestamp", "open", "high", "low", "close", "spy_volume"]])
        
        # Check for consistency
        if timeframe == "1d":
            # For daily bars, check if open matches first hour's open and close matches last hour's close
            hour_table = "spx_ohlcv_1h"
            
            for _, day_bar in df.iterrows():
                day_date = day_bar["timestamp"].strftime("%Y-%m-%d")
                
                # Get hourly bars for this day
                hour_query = text(f"""
                    SELECT * FROM {hour_table}
                    WHERE CONVERT(date, timestamp) = :day_date
                    ORDER BY timestamp
                """)
                
                with engine.begin() as conn:
                    hour_result = conn.execute(
                        hour_query,
                        {
                            "day_date": day_date
                        }
                    )
                    
                    hour_columns = [col[0] for col in hour_result.cursor.description]
                    hour_df = pd.DataFrame(hour_result.fetchall(), columns=hour_columns)
                
                if hour_df.empty:
                    print(f"No hourly data found for {day_date}")
                    continue
                    
                # Check consistency
                first_hour = hour_df.iloc[0]
                last_hour = hour_df.iloc[-1]
                
                print(f"\nConsistency check for {day_date}:")
                print(f"Daily open: {day_bar['open']}, First hour open: {first_hour['open']}")
                print(f"Daily close: {day_bar['close']}, Last hour close: {last_hour['close']}")
                print(f"Daily high: {day_bar['high']}, Max hourly high: {hour_df['high'].max()}")
                print(f"Daily low: {day_bar['low']}, Min hourly low: {hour_df['low'].min()}")
                
                # Check if daily high/low match max/min of hourly high/low
                high_match = abs(day_bar['high'] - hour_df['high'].max()) < 0.01
                low_match = abs(day_bar['low'] - hour_df['low'].min()) < 0.01
                
                if high_match and low_match:
                    print("✅ High/low consistency check passed")
                else:
                    print("❌ High/low consistency check failed")

if __name__ == "__main__":
    main()
