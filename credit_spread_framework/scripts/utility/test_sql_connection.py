import urllib
from sqlalchemy import create_engine, text

# Paste this or load it from config.settings if you prefer
conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=LAPTOP-DKR7BL4Q\\SQLEXPRESS;DATABASE=CreditSpreadsDB;Trusted_Connection=yes;"
encoded = urllib.parse.quote_plus(conn_str)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={encoded}",
    echo=True,
    connect_args={"autocommit": True}
)

with engine.connect() as conn:
    result = conn.execute(text("SELECT GETDATE()"))
    print("✅ Connected! Server time:", result.scalar())
