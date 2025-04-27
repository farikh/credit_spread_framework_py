"""
Script to fix the TimestampEnd for SR zones.

This script will update all SR zones to have NULL TimestampEnd.
"""
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

def main():
    """Fix the TimestampEnd for SR zones"""
    print("Fixing TimestampEnd for SR zones...")
    engine = get_engine()
    
    # Update all SR zones to have NULL TimestampEnd
    query = """
        UPDATE iv
        SET TimestampEnd = NULL
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(query))
        print(f"Updated {result.rowcount} rows")
    
    # Verify the update
    verify_query = """
        SELECT COUNT(*) 
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
        AND iv.TimestampEnd IS NULL
    """
    
    with engine.begin() as conn:
        null_count = conn.execute(text(verify_query)).scalar()
        print(f"Found {null_count} SR zones with NULL TimestampEnd")
    
    print("Done")

if __name__ == "__main__":
    main()
