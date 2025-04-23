from dotenv import load_dotenv
load_dotenv()

import os
import urllib
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

conn_str = urllib.parse.quote_plus(os.getenv("SQLSERVER_CONN_STRING"))

def get_engine():
    return create_engine(
        f"mssql+pyodbc:///?odbc_connect={conn_str}",
        echo=False,  # This shows all SQL commands sent
        fast_executemany=True,
        connect_args={"autocommit": True}
    )

