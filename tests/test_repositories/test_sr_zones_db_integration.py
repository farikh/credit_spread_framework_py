import pandas as pd
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, DateTime
import credit_spread_framework.config.settings as settings
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator

def test_sr_zone_integration_db(tmp_path, monkeypatch):
    """
    Integration test for SRZoneIndicator DB insertion using a temporary SQLite database.
    Creates indicator_metadata and indicator_values tables, inserts metadata, runs calculation,
    and verifies that save_indicator_values_to_db inserts the expected rows.
    """
    # Configure a temporary SQLite database file
    db_path = tmp_path / "test_sr_zones.db"
    sqlite_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("SQLSERVER_CONN_STRING", sqlite_url)

    # Create engine and tables
    engine = get_engine()
    metadata = MetaData()
    indicator_metadata = Table(
        "indicator_metadata", metadata,
        Column("IndicatorId", Integer, primary_key=True, autoincrement=True),
        Column("Name", String, nullable=False),
        Column("Timeframe", String, nullable=False)
    )
    indicator_values = Table(
        "indicator_values", metadata,
        Column("BarId", String, primary_key=True),
        Column("Timeframe", String, nullable=False),
        Column("IndicatorId", Integer, nullable=False),
        Column("Value", Float, nullable=False),
        Column("TimestampStart", DateTime, nullable=False)
    )
    metadata.create_all(engine)

    # Insert metadata row for SR_ZONES
    with engine.begin() as conn:
        conn.execute(
            indicator_metadata.insert(),
            {"Name": "SR_ZONES", "Timeframe": "15m"}
        )

    # Instantiate indicator and calculate dummy zones
    indicator = SRZoneIndicator(qualifier="time")
    values = indicator.calculate(pd.DataFrame())

    # Ensure dummy data available
    assert not values.empty
    assert {"value", "timestamp_start", "qualifier", "parameters_json"}.issubset(values.columns)

    # Save to DB
    save_indicator_values_to_db(values, "SR_ZONES", "15m")

    # Verify inserted rows count matches dummy output
    with engine.connect() as conn:
        result = conn.execute(sa.select(indicator_values))
        rows = result.fetchall()
    assert len(rows) == values.shape[0]
