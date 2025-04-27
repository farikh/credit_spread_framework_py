"""
Script to check SR zones for a specific date.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd

def main():
    engine = get_engine()
    
    # Query SR zones for April 4, 2025
    query = text("""
        SELECT iv.Value, iv.Qualifier, iv.TimestampStart, iv.TimestampEnd
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND CAST(iv.TimestampEnd AS DATE) = :date
        ORDER BY iv.Qualifier, iv.Value
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {
            "indicator_name": "srzones",
            "timeframe": "1d",
            "date": "2025-04-04"
        })
        
        # Convert to DataFrame
        df = pd.DataFrame(result.fetchall(), columns=["Value", "Qualifier", "TimestampStart", "TimestampEnd"])
        
        if df.empty:
            print("No SR zones found for April 4, 2025")
        else:
            print(f"Found {len(df)} SR zones for April 4, 2025:")
            print(df.to_string())

if __name__ == "__main__":
    main()
