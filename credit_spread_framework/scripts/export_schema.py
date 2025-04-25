import sqlalchemy
from sqlalchemy import create_engine, text
import pandas as pd
import urllib

from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING

def export_schema(output_path="schema_export.md"):
    # Prepare the connection string
    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    # Queries to retrieve table and column information
    query_tables = """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """

    query_columns = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """

    # Execute the queries and fetch data into pandas DataFrames
    with engine.begin() as conn:
        tables = pd.read_sql(query_tables, conn)
        columns = pd.read_sql(query_columns, conn)

    # Write the schema to a Markdown file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Database Schema Export\n\n")
        for _, table_row in tables.iterrows():
            schema, table = table_row["TABLE_SCHEMA"], table_row["TABLE_NAME"]
            f.write(f"## `{schema}.{table}`\n\n")
            f.write("| Column Name     | Data Type    | Nullable |\n")
            f.write("|-----------------|--------------|----------|\n")
            table_columns = columns[
                (columns["TABLE_SCHEMA"] == schema) & (columns["TABLE_NAME"] == table)
            ]
            for _, col_row in table_columns.iterrows():
                col_name = col_row["COLUMN_NAME"]
                data_type = col_row["DATA_TYPE"]
                nullable = col_row["IS_NULLABLE"]
                f.write(f"| {col_name}         | {data_type}      | {nullable}    |\n")
            f.write("\n")

    print(f"[INFO] Schema exported successfully to: {output_path}")

if __name__ == "__main__":
    export_schema()
