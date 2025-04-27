"""
Script to insert test OHLCV data for multiple days across timeframes to properly test SR zones.
This creates a realistic dataset across 3 days (April 3-5, 2025) for all timeframes.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
from datetime import datetime, timezone, timedelta

def main():
    engine = get_engine()
    
    # Date range to insert data for (April 3-5, 2025)
    base_date = datetime(2025, 4, 3, tzinfo=timezone.utc)
    days = 3
    
    # Generate test data for 1d timeframe (daily bars)
    daily_bars = []
    for day_offset in range(days):
        current_date = base_date + timedelta(days=day_offset)
        
        # Daily bar data (9:30 AM to 4:00 PM EST / 13:30 to 20:00 UTC)
        # Using fluctuating prices around realistic SPX levels
        price_base = 5450 + (day_offset * 20) # price trends upward over days
        
        daily_bars.append({
            "bar_id": f"spx_{current_date.strftime('%Y%m%d')}_daily",
            "timestamp": current_date.replace(hour=20, minute=0, second=0), # 4:00 PM EST
            "open": price_base - 5,
            "high": price_base + 25 + (day_offset * 5),
            "low": price_base - 15 - (day_offset * 2),
            "close": price_base + 10 + (day_offset * 8),
            "spy_volume": 25000000 + (day_offset * 2000000)
        })
    
    # Clear existing data for these dates to avoid duplicates
    with engine.begin() as conn:
        date_str = base_date.strftime('%Y-%m-%d')
        end_date = (base_date + timedelta(days=days-1)).strftime('%Y-%m-%d')
        
        delete_query = """
            DELETE FROM dbo.spx_ohlcv_1d 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """
        conn.execute(text(delete_query), {
            "start_date": date_str, 
            "end_date": end_date + " 23:59:59"
        })
        print(f"Cleared existing 1d data from {date_str} to {end_date}")
        
        # Insert daily bars
        insert_query = """
            INSERT INTO dbo.spx_ohlcv_1d 
            (bar_id, timestamp, [open], [high], [low], [close], spy_volume)
            VALUES (:bar_id, :timestamp, :open, :high, :low, :close, :spy_volume)
        """
        
        for bar in daily_bars:
            conn.execute(text(insert_query), bar)
        
        print(f"Inserted {len(daily_bars)} daily bars")
        
        # Also add hourly data for the first day
        hourly_bars = []
        for hour in range(7):  # 9:30 AM to 4:00 PM
            timestamp = base_date.replace(hour=13+hour, minute=30 if hour==0 else 0)
            
            # Prices fluctuate throughout the day
            price_offset = 10 * (hour % 3 - 1)  # oscillate between -10, 0, and +10
            
            hourly_bars.append({
                "bar_id": f"spx_{base_date.strftime('%Y%m%d')}_{timestamp.strftime('%H%M')}",
                "timestamp": timestamp,
                "open": 5450 + price_offset - 5,
                "high": 5450 + price_offset + 15,
                "low": 5450 + price_offset - 10,
                "close": 5450 + price_offset + 7,
                "spy_volume": 3500000 + (hour * 500000)
            })
        
        # Clear hourly data
        conn.execute(text("DELETE FROM dbo.spx_ohlcv_1h WHERE timestamp >= :start_date AND timestamp <= :end_date"), 
                    {"start_date": date_str, "end_date": date_str + " 23:59:59"})
        
        # Insert hourly bars
        for bar in hourly_bars:
            conn.execute(text("""
                INSERT INTO dbo.spx_ohlcv_1h 
                (bar_id, timestamp, [open], [high], [low], [close], spy_volume)
                VALUES (:bar_id, :timestamp, :open, :high, :low, :close, :spy_volume)
            """), bar)
        
        print(f"Inserted {len(hourly_bars)} hourly bars for {date_str}")
    
    print("Test data insertion complete")

if __name__ == "__main__":
    main()
