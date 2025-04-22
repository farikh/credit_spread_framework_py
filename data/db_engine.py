import urllib
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from config.settings import SQLSERVER_CONN_STRING

conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={conn_str}",
    echo=True,  # 👈 this shows all SQL commands sent
    fast_executemany=True,
    connect_args={"autocommit": True}
)

