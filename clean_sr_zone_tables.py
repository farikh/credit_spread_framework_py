"""
Script to clean SR zone tables.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

def main():
    engine = get_engine()
    
    with engine.begin() as conn:
        print("Deleting SR zone interactions...")
        conn.execute(text("DELETE FROM sr_zone_interactions"))
        
        print("Deleting SR zone pivots...")
        conn.execute(text("DELETE FROM sr_zone_pivots"))
        
        print("Deleting SR zones...")
        conn.execute(text("DELETE FROM sr_zones"))
        
    print("All SR zone tables cleaned successfully.")

if __name__ == "__main__":
    main()
