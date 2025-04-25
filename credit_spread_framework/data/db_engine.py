from sqlalchemy import create_engine
import os
import urllib
from dotenv import load_dotenv

load_dotenv()

# Try Windows Auth first
conn_str = os.getenv("SQLSERVER_CONN_STRING")

# If not available (like inside Docker), fallback to SQL login
if not conn_str:
    conn_str = os.getenv("SQLSERVER_SQL_LOGIN_CONN_STRING")

if not conn_str:
    raise RuntimeError("No SQL connection string found! Check your .env file.")

conn_str_encoded = urllib.parse.quote_plus(conn_str)

def get_engine():
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={conn_str_encoded}",
        echo=False,
        fast_executemany=True,
        connect_args={"autocommit": True}
    )
