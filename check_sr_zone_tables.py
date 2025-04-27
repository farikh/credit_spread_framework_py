"""
Script to check if the SR zone tables were created successfully.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

def main():
    engine = get_engine()
    with engine.begin() as conn:
        # Check if sr_zones table exists
        result = conn.execute(text("SELECT OBJECT_ID('dbo.sr_zones') AS table_id"))
        sr_zones_exists = result.scalar() is not None
        print(f"sr_zones table exists: {sr_zones_exists}")
        
        # Check if sr_zone_pivots table exists
        result = conn.execute(text("SELECT OBJECT_ID('dbo.sr_zone_pivots') AS table_id"))
        sr_zone_pivots_exists = result.scalar() is not None
        print(f"sr_zone_pivots table exists: {sr_zone_pivots_exists}")
        
        # Check if sr_zone_interactions table exists
        result = conn.execute(text("SELECT OBJECT_ID('dbo.sr_zone_interactions') AS table_id"))
        sr_zone_interactions_exists = result.scalar() is not None
        print(f"sr_zone_interactions table exists: {sr_zone_interactions_exists}")
        
        # If sr_zones table exists, check its structure
        if sr_zones_exists:
            result = conn.execute(text("SELECT TOP 0 * FROM sr_zones"))
            columns = result.keys()
            print(f"sr_zones columns: {columns}")

if __name__ == "__main__":
    main()
