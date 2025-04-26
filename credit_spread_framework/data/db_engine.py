from sqlalchemy import create_engine
import os
import urllib
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """
    Create a SQLAlchemy engine based on environment variable.
    Supports SQLite for testing (URLs starting with sqlite://) and
    SQL Server via pyodbc for production.
    """
    conn_str = os.getenv("SQLSERVER_CONN_STRING") or os.getenv("SQLSERVER_SQL_LOGIN_CONN_STRING")
    if not conn_str:
        raise RuntimeError("No SQL connection string found! Check your .env file.")
    if conn_str.startswith("sqlite://"):
        return create_engine(conn_str, echo=False)
    # For SQL Server, use pyodbc connection string
    conn_str_encoded = urllib.parse.quote_plus(conn_str)
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={conn_str_encoded}",
        echo=False,
        fast_executemany=True,
        connect_args={"autocommit": True}
    )
