"""
Script to clean up duplicate SR zones.

This script will:
1. Find duplicate SR zones (same value, qualifier, and timestamp_start)
2. Keep only one instance of each unique SR zone
3. Delete the duplicates
"""
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine

def main():
    """Clean up duplicate SR zones"""
    print("Cleaning up duplicate SR zones...")
    engine = get_engine()
    
    # Find duplicate SR zones
    find_duplicates_query = """
        WITH duplicates AS (
            SELECT 
                iv.Value, iv.Qualifier, iv.TimestampStart,
                COUNT(*) as count,
                MIN(iv.IndicatorValueId) as keep_id
            FROM indicator_values iv
            JOIN indicators i ON iv.IndicatorId = i.IndicatorId
            WHERE i.ShortName = 'srzones'
            AND iv.Timeframe = '1d'
            AND iv.TimestampEnd IS NULL
            GROUP BY iv.Value, iv.Qualifier, iv.TimestampStart
            HAVING COUNT(*) > 1
        )
        SELECT 
            d.Value, d.Qualifier, d.TimestampStart, d.count, d.keep_id,
            iv.IndicatorValueId
        FROM duplicates d
        JOIN indicator_values iv ON 
            iv.Value = d.Value AND 
            iv.Qualifier = d.Qualifier AND 
            iv.TimestampStart = d.TimestampStart
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
        AND iv.TimestampEnd IS NULL
        AND iv.IndicatorValueId <> d.keep_id
        ORDER BY d.Value, d.Qualifier, d.TimestampStart
    """
    
    # Delete duplicate SR zones
    delete_duplicates_query = """
        WITH duplicates AS (
            SELECT 
                iv.Value, iv.Qualifier, iv.TimestampStart,
                COUNT(*) as count,
                MIN(iv.IndicatorValueId) as keep_id
            FROM indicator_values iv
            JOIN indicators i ON iv.IndicatorId = i.IndicatorId
            WHERE i.ShortName = 'srzones'
            AND iv.Timeframe = '1d'
            AND iv.TimestampEnd IS NULL
            GROUP BY iv.Value, iv.Qualifier, iv.TimestampStart
            HAVING COUNT(*) > 1
        )
        DELETE iv
        FROM indicator_values iv
        JOIN duplicates d ON 
            iv.Value = d.Value AND 
            iv.Qualifier = d.Qualifier AND 
            iv.TimestampStart = d.TimestampStart
        WHERE iv.IndicatorValueId <> d.keep_id
    """
    
    with engine.begin() as conn:
        # Find duplicates
        result = conn.execute(text(find_duplicates_query))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"Found {len(duplicates)} duplicate SR zones:")
            for row in duplicates:
                print(f"  Value: {row[0]}, Qualifier: {row[1]}, TimestampStart: {row[2]}, Count: {row[3]}, Keep ID: {row[4]}, Delete ID: {row[5]}")
            
            # Delete duplicates
            result = conn.execute(text(delete_duplicates_query))
            print(f"Deleted {result.rowcount} duplicate SR zones")
        else:
            print("No duplicate SR zones found")
    
    # Verify the cleanup
    verify_query = """
        SELECT 
            iv.Value, iv.Qualifier, iv.TimestampStart,
            COUNT(*) as count
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
        AND iv.TimestampEnd IS NULL
        GROUP BY iv.Value, iv.Qualifier, iv.TimestampStart
        HAVING COUNT(*) > 1
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(verify_query))
        remaining_duplicates = result.fetchall()
        
        if remaining_duplicates:
            print(f"WARNING: Still found {len(remaining_duplicates)} duplicate SR zones:")
            for row in remaining_duplicates:
                print(f"  Value: {row[0]}, Qualifier: {row[1]}, TimestampStart: {row[2]}, Count: {row[3]}")
        else:
            print("No duplicate SR zones remaining")
    
    # Count total SR zones
    count_query = """
        SELECT COUNT(*)
        FROM indicator_values iv
        JOIN indicators i ON iv.IndicatorId = i.IndicatorId
        WHERE i.ShortName = 'srzones'
        AND iv.Timeframe = '1d'
        AND iv.TimestampEnd IS NULL
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(count_query))
        total_count = result.scalar()
        print(f"Total SR zones: {total_count}")
    
    print("Done")

if __name__ == "__main__":
    main()
