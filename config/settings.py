from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")

SQLSERVER_CONN_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LAPTOP-DKR7BL4Q\\SQLEXPRESS;"
    "DATABASE=CreditSpreadsDB;"
    "Trusted_Connection=yes;"
)
