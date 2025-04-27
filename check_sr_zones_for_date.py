"""
Script to check SR zones for a specific date.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime

def main():
    engine = get_engine()
    
    # Query all SR zones
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT 
                zone_id, value, qualifier, timeframe, strength,
                first_detected, last_confirmed, is_active
            FROM sr_zones
            ORDER BY qualifier, value
        """))
        
        columns = [
            "zone_id", "value", "qualifier", "timeframe", "strength",
            "first_detected", "last_confirmed", "is_active"
        ]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
        print(f"Found {len(df)} SR zones in total")
        print(df)
        
        # Count zones by qualifier
        print("\nZones by qualifier:")
        print(df.groupby("qualifier").size())
        
        # Count zones by timeframe
        print("\nZones by timeframe:")
        print(df.groupby("timeframe").size())
        
        # Get the strongest zones
        print("\nTop 5 strongest zones:")
        print(df.sort_values("strength", ascending=False).head(5))

