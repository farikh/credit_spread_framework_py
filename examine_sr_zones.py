"""
Script to examine SR zones for the 5726 level.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime

def main():
    engine = get_engine()
    
    # Query SR zones for the 5726 level
    level = 5726
    tolerance = 15
    
    query = text("""
        SELECT 
            zone_id, value, qualifier, timeframe, strength,
            first_detected, last_confirmed, is_active
        FROM sr_zones
        WHERE ABS(value - :level) <= :tolerance
        ORDER BY qualifier, first_detected
    """)
    
    with engine.begin() as conn:
        result = conn.execute(
            query,
            {
                "level": level,
                "tolerance": tolerance
            }
        )
        
        columns = [
            "zone_id", "value", "qualifier", "timeframe", "strength",
            "first_detected", "last_confirmed", "is_active"
        ]
        df = pd.DataFrame(result.fetchall(), columns=columns)
    
    if df.empty:
        print(f"No SR zones found for level {level} (tolerance: {tolerance}).")
        return
    
    print(f"Found {len(df)} SR zones for level {level} (tolerance: {tolerance}):")
    print(df)
    
    # Check for zones with last_confirmed before first_detected
    invalid_timeline = df["last_confirmed"] < df["first_detected"]
    if invalid_timeline.any():
        print("\nZones with last_confirmed before first_detected:")
        invalid_zones = df[invalid_timeline]
        print(invalid_zones)
        
        # Get the pivots for these zones
        for _, zone in invalid_zones.iterrows():
            zone_id = zone["zone_id"]
            print(f"\nPivots for zone {zone_id}:")
            
            pivot_query = text("""
                SELECT 
                    pivot_id, zone_id, pivot_value, pivot_timestamp, pivot_type, weight
                FROM sr_zone_pivots
                WHERE zone_id = :zone_id
                ORDER BY pivot_timestamp
            """)
            
            with engine.begin() as conn:
                pivot_result = conn.execute(
                    pivot_query,
                    {
                        "zone_id": zone_id
                    }
                )
                
                pivot_columns = [
                    "pivot_id", "zone_id", "pivot_value", "pivot_timestamp", "pivot_type", "weight"
                ]
                pivot_df = pd.DataFrame(pivot_result.fetchall(), columns=pivot_columns)
                
                if pivot_df.empty:
                    print("  No pivots found for this zone.")
                else:
                    print(pivot_df)
            
            # Get the interactions for this zone
            print(f"\nInteractions for zone {zone_id}:")
            
            interaction_query = text("""
                SELECT 
                    interaction_id, zone_id, bar_id, interaction_type, interaction_strength, timestamp, price
                FROM sr_zone_interactions
                WHERE zone_id = :zone_id
                ORDER BY timestamp
            """)
            
            with engine.begin() as conn:
                interaction_result = conn.execute(
                    interaction_query,
                    {
                        "zone_id": zone_id
                    }
                )
                
                interaction_columns = [
                    "interaction_id", "zone_id", "bar_id", "interaction_type", "interaction_strength", "timestamp", "price"
                ]
                interaction_df = pd.DataFrame(interaction_result.fetchall(), columns=interaction_columns)
                
                if interaction_df.empty:
                    print("  No interactions found for this zone.")
                else:
                    print(interaction_df)

if __name__ == "__main__":
    main()
