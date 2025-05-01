"""
Simple script to test database connection.
"""
import os
import urllib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get connection string from environment
    conn_str = os.getenv("SQLSERVER_CONN_STRING")
    if not conn_str:
        print("No SQL connection string found! Check your .env file.")
        return
    
    print(f"Connection string: {conn_str}")
    
    try:
        # Create engine
        conn_str_encoded = urllib.parse.quote_plus(conn_str)
        engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={conn_str_encoded}",
            echo=False,
            connect_args={"autocommit": True}
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT GETDATE() as current_time"))
            row = result.fetchone()
            print(f"Connected to database! Server time: {row.current_time}")
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_NAME LIKE 'spx_ohlcv_%'
            """))
            
            tables = [row[0] for row in result]
            print(f"Found tables: {tables}")
            
            # Check data in each table
            for table in tables:
                result = conn.execute(text(f"""
                    SELECT 
                        MIN(CAST(timestamp AS DATE)) as min_date,
                        MAX(CAST(timestamp AS DATE)) as max_date,
                        COUNT(*) as total_rows
                    FROM dbo.{table}
                """))
                
                row = result.fetchone()
                if row and row.min_date and row.max_date:
                    print(f"{table}: {row.min_date} to {row.max_date} ({row.total_rows} rows)")
                else:
                    print(f"{table}: No data found")
    
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")

if __name__ == "__main__":
    main()
