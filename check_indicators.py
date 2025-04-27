"""
Script to check the indicators in the database.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

def main():
    engine = get_engine()
    
    # Query to get all indicators
    query = """
        SELECT IndicatorId, ShortName, ClassPath, IsActive
        FROM indicators
        ORDER BY IndicatorId
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        print("Indicators in the database:")
        print("---------------------------")
        for row in rows:
            indicator_id, short_name, class_path, is_active = row
            print(f"ID: {indicator_id}, ShortName: '{short_name}', Active: {is_active}")
            print(f"  ClassPath: {class_path}")
            print()
    
    # Query to check if there are any values for indicator ID 2
    query = """
        SELECT COUNT(*) as count, Timeframe
        FROM indicator_values
        WHERE IndicatorId = 2
        GROUP BY Timeframe
        ORDER BY Timeframe
    """
    
    with engine.begin() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        print("Values for Indicator ID 2:")
        print("-------------------------")
        if not rows:
            print("No values found for Indicator ID 2")
        else:
            for row in rows:
                count, timeframe = row
                print(f"Timeframe: {timeframe}, Count: {count}")

if __name__ == "__main__":
    main()
