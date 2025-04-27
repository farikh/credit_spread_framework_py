"""
Script to check the structure of the indicators table.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

def main():
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("SELECT TOP 1 * FROM indicators"))
        columns = result.keys()
        print("Indicators table columns:", columns)

if __name__ == "__main__":
    main()
