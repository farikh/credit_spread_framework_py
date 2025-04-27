"""
Script to delete SR zones for a specific date.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd

def main():
    engine = get_engine()
    
    # Delete SR zones for April 3, 2025
    query = text("""
        DELETE iv
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = :indicator_name
        AND iv.Timeframe = :timeframe
        AND CAST(iv.TimestampEnd AS DATE) = :date
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {
            "indicator_name": "srzones",
            "timeframe": "1d",
            "date": "2025-04-03"
        })
        
        print(f"Deleted SR zones for April 3, 2025")

if __name__ == "__main__":
    main()
