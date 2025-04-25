from dotenv import load_dotenv
import os
import logging

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

SQLSERVER_CONN_STRING = os.getenv("SQLSERVER_CONN_STRING")
if not SQLSERVER_CONN_STRING:
    raise ValueError("SQLSERVER_CONN_STRING is not set in the environment variables.")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

