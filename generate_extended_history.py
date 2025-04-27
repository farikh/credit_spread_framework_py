"""
Generate an extended price history (6+ months) for SPX to better match TradingView's SR zone calculation.
This will create a more realistic dataset spanning multiple months for proper SR zone detection.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
import numpy as np
import random

def main():
    engine = get_engine()
    
    # Generate 6 months of daily data with realistic price action (Oct 2024 - Apr 2025)
    start_date = datetime(2024, 10, 1, tzinfo=timezone.utc)
    end_date = datetime(2025, 4, 15, tzinfo=timezone.utc)
    
    # Market parameters - customize based on expected SPX behavior
    initial_price = 5000
    volatility = 0.015  # 1.5% daily volatility
    drift = 0.0002      # slight upward trend
    
    # Generate random walk with drift
    days = (end_date - start_date).days
    daily_returns = np.random.normal(drift, volatility, days) + 1
    
    # Create price series with reasonable market structure (will include support/resistance zones)
    prices = [initial_price]
    for ret in daily_returns:
        # Add some mean reversion and support/resistance effects
        last_price = prices[-1]
        
        # Create resistance around round numbers
        resistance_level = round(last_price / 100) * 100 + 50
        support_level = round(last_price / 100) * 100 - 50
        
        # Stronger mean reversion near resistance/support
        if abs(last_price - resistance_level) < 20:
            ret = min(ret, 1.0)  # Resistance
        elif abs(last_price - support_level) < 20:
            ret = max(ret, 1.0)  # Support bounce
            
        # Additional volatility around key levels to create pivots
        if abs(last_price - resistance_level) < 5 or abs(last_price - support_level) < 5:
            ret *= random.uniform(0.95, 1.05)
            
        prices.append(last_price * ret)
    
    # Convert to OHLC data
    daily_bars = []
    current_date = start_date
    
    for i, close_price in enumerate(prices[1:]):  # Skip first price (initialization)
        # Only generate weekday bars (Monday-Friday)
        if current_date.weekday() < 5:  # 0-4 are weekdays
            # Create realistic intraday price action
            daily_range = close_price * volatility * random.uniform(0.7, 1.3)
            open_price = prices[i] * random.uniform(0.998, 1.002)
            high_price = max(open_price, close_price) + daily_range * random.uniform(0.3, 0.7)
            low_price = min(open_price, close_price) - daily_range * random.uniform(0.3, 0.7)
            
            # Add SPX market hours: 9:30 AM - 4:00 PM EST (UTC-4)
            market_close = current_date.replace(hour=20, minute=0, second=0)  # 4:00 PM EST = 20:00 UTC
            
            # Use appropriate volume levels
            volume = int(25000000 + 5000000 * np.random.randn())
            volume = max(volume, 15000000)  # Ensure minimum volume
            
            daily_bars.append({
                "bar_id": f"spx_{current_date.strftime('%Y%m%d')}_daily",
                "timestamp": market_close,
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "spy_volume": volume
            })
        
        current_date += timedelta(days=1)
    
    # Clear existing data for this date range
    with engine.begin() as conn:
        delete_query = """
            DELETE FROM dbo.spx_ohlcv_1d 
            WHERE timestamp >= :start_date AND timestamp <= :end_date
        """
        conn.execute(text(delete_query), {
            "start_date": start_date.strftime('%Y-%m-%d'), 
            "end_date": end_date.strftime('%Y-%m-%d')
        })
        
        print(f"Cleared existing 1d data from {start_date.date()} to {end_date.date()}")
        
        # Insert daily bars
        insert_query = """
            INSERT INTO dbo.spx_ohlcv_1d 
            (bar_id, timestamp, [open], [high], [low], [close], spy_volume)
            VALUES (:bar_id, :timestamp, :open, :high, :low, :close, :spy_volume)
        """
        
        rows_inserted = 0
        for bar in daily_bars:
            conn.execute(text(insert_query), bar)
            rows_inserted += 1
        
        print(f"Inserted {rows_inserted} daily bars")
    
    print("Test data insertion complete")

if __name__ == "__main__":
    main()
