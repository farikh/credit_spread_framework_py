"""
Script to manually insert test OHLCV data for April 3, 2025 to test SR zone calculation.
This will allow us to verify that the indicator produces zones when data is available.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
from datetime import datetime, timezone

def main():
    engine = get_engine()
    
    # Data for April 3, 2025 - using values close to what's in the screenshot
    # Inserting multiple bars to simulate a full day of trading
    bars = [
        {
            "bar_id": "spx_20250403_0930",  # Market open
            "timestamp": datetime(2025, 4, 3, 13, 30, 0, tzinfo=timezone.utc),  # 9:30 AM EST = 13:30 UTC
            "open": 5450.0,
            "high": 5475.0,
            "low": 5425.0,
            "close": 5445.0,
            "spy_volume": 12500000
        },
        {
            "bar_id": "spx_20250403_1200",  # Mid-day
            "timestamp": datetime(2025, 4, 3, 16, 0, 0, tzinfo=timezone.utc),  # 12:00 PM EST = 16:00 UTC
            "open": 5445.0,
            "high": 5480.0,
            "low": 5430.0,
            "close": 5460.0,
            "spy_volume": 18000000
        },
        {
            "bar_id": "spx_20250403_1600",  # Market close
            "timestamp": datetime(2025, 4, 3, 20, 0, 0, tzinfo=timezone.utc),  # 4:00 PM EST = 20:00 UTC
            "open": 5460.0,
            "high": 5490.0,
            "low": 5455.0,
            "close": 5470.0,
            "spy_volume": 25000000
        }
    ]
    
    # Clear existing data for this date to avoid duplicate insertion
    with engine.begin() as conn:
        delete_query = """
            DELETE FROM dbo.spx_ohlcv_1d 
            WHERE CAST(timestamp AS DATE) = CAST(:date AS DATE)
        """
        conn.execute(text(delete_query), {"date": "2025-04-03"})
        print("Cleared any existing data for April 3, 2025")
        
        # Insert new test data
        insert_query = """
            INSERT INTO dbo.spx_ohlcv_1d 
            (bar_id, timestamp, [open], [high], [low], [close], spy_volume)
            VALUES (:bar_id, :timestamp, :open, :high, :low, :close, :spy_volume)
        """
        
        for bar in bars:
            conn.execute(text(insert_query), bar)
        
        print(f"Inserted {len(bars)} test bars for April 3, 2025")
    
    print("Test data insertion complete")

if __name__ == "__main__":
    main()
