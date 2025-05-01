import os
import sys
from sqlalchemy import text
from datetime import datetime

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ''))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the database engine
from credit_spread_framework.data.db_engine import get_engine

def check_available_data():
    """Check what data is available in the database tables."""
    engine = get_engine()
    
    # List of tables to check
    tables = [
        "spx_ohlcv_1m",
        "spx_ohlcv_3m",
        "spx_ohlcv_15m",
        "spx_ohlcv_1h",
        "spx_ohlcv_1d"
    ]
    
    print("Checking available data in the database...")
    
    for table in tables:
        try:
            # Query to get the min and max dates
            query = f"""
                SELECT 
                    MIN(timestamp) as min_date,
                    MAX(timestamp) as max_date,
                    COUNT(*) as row_count
                FROM dbo.{table}
            """
            
            with engine.begin() as conn:
                result = conn.execute(text(query))
                row = result.fetchone()
                
                if row:
                    min_date, max_date, row_count = row
                    print(f"Table: {table}")
                    print(f"  - Date range: {min_date} to {max_date}")
                    print(f"  - Total rows: {row_count}")
                    
                    # Get a sample of recent data
                    if row_count > 0:
                        sample_query = f"""
                            SELECT TOP 5
                                timestamp,
                                [open] AS open_price,
                                [high],
                                [low],
                                [close] AS close_price,
                                spy_volume
                            FROM dbo.{table}
                            ORDER BY timestamp DESC
                        """
                        
                        sample_result = conn.execute(text(sample_query))
                        sample_rows = sample_result.fetchall()
                        
                        print("  - Recent data samples:")
                        for sample in sample_rows:
                            print(f"    {sample}")
                else:
                    print(f"Table: {table} - No data found")
        except Exception as e:
            print(f"Error checking table {table}: {str(e)}")
    
    print("\nDone checking database.")

if __name__ == "__main__":
    check_available_data()
