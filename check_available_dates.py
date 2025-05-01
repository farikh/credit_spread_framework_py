"""
Script to check what dates are available in the database.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

def main():
    engine = get_engine()
    
    timeframes = ['1m', '3m', '15m', '1h', '1d']
    
    for timeframe in timeframes:
        table_name = f"spx_ohlcv_{timeframe}"
        
        # Check if table exists
        check_query = text(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{table_name}'
        """)
        
        with engine.begin() as conn:
            table_exists = conn.execute(check_query).scalar()
            
            if not table_exists:
                print(f"Table {table_name} does not exist")
                continue
            
            # Get date range
            date_query = text(f"""
                SELECT 
                    MIN(CAST(timestamp AS DATE)) as min_date,
                    MAX(CAST(timestamp AS DATE)) as max_date,
                    COUNT(DISTINCT CAST(timestamp AS DATE)) as date_count,
                    COUNT(*) as row_count
                FROM dbo.{table_name}
            """)
            
            result = conn.execute(date_query).fetchone()
            
            if result and result.min_date and result.max_date:
                print(f"{table_name}: {result.min_date} to {result.max_date} ({result.date_count} dates, {result.row_count} rows)")
                
                # Get a list of dates with data
                dates_query = text(f"""
                    SELECT DISTINCT TOP 10 CAST(timestamp AS DATE) as date
                    FROM dbo.{table_name}
                    ORDER BY date DESC
                """)
                
                dates = [row[0] for row in conn.execute(dates_query)]
                print(f"  Recent dates: {', '.join(str(d) for d in dates)}")
                
                # Get row counts for specific dates
                for date in dates[:3]:  # Check first 3 dates
                    count_query = text(f"""
                        SELECT COUNT(*) 
                        FROM dbo.{table_name}
                        WHERE CAST(timestamp AS DATE) = :date
                    """)
                    
                    count = conn.execute(count_query, {"date": date}).scalar()
                    print(f"  {date}: {count} rows")
            else:
                print(f"{table_name}: No data found")

if __name__ == "__main__":
    main()
