# File: credit_spread_framework/data/repositories/indicator_repository.py

import sqlalchemy as sa
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING
import urllib
from sqlalchemy import create_engine, text

def get_all_indicators():
    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    with engine.begin() as conn:
        result = conn.execute(text("SELECT ShortName FROM indicators"))
        indicators = [row[0] for row in result]
    
    return indicators
