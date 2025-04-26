import pandas as pd
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db

def test_save_sr_zone_values_to_db_mock(monkeypatch):
    """
    Validate that SRZoneIndicator outputs can be saved to the database
    via save_indicator_values_to_db without errors. A dummy connection
    is provided to simulate INSERTs and metadata lookup.
    """
    # Dummy result for fetching IndicatorId
    class DummyResult:
        def fetchone(self):
            return (1,)  # Simulates fetching IndicatorId = 1

    # Dummy connection to capture INSERT calls
    class DummyConn:
        def __init__(self):
            self.insert_calls = 0

        def execute(self, stmt, params=None):
            text = str(stmt).strip().upper()
            if text.startswith("SELECT INDICATORID"):
                return DummyResult()
            # Count each INSERT execution
            if text.startswith("INSERT INTO INDICATOR_VALUES"):
                self.insert_calls += 1
                return None
            return None

        def begin(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    # Monkeypatch engine creation to use DummyConn
    monkeypatch.setattr(
        "credit_spread_framework.data.repositories.indicator_value_repository.create_engine",
        lambda _: DummyConn()
    )

    # Instantiate the indicator and generate dummy values
    indicator = SRZoneIndicator(qualifier="time")
    values = indicator.calculate(pd.DataFrame())

    # Sanity check on returned DataFrame
    assert "value" in values.columns
    assert "timestamp_start" in values.columns

    # Call the save function; should not raise
    save_indicator_values_to_db(values, "SR_ZONES", "15m")

    # Verify that INSERT was called for each row in values
    # Two zones per method; qualifier="time" -> 2 rows
    assert values.shape[0] == 2
    # Fetch the dummy connection instance to inspect insert_calls
    dummy_conn = (  
        # recreate to inspect count: our lambda returns a new DummyConn,
        # so we capture it here instead of relying on save function's instance
        None
    )
    # To properly verify, patch create_engine to return a single shared DummyConn
    shared_conn = DummyConn()
    monkeypatch.setattr(
        "credit_spread_framework.data.repositories.indicator_value_repository.create_engine",
        lambda _: shared_conn
    )
    # Re-run save to count inserts
    save_indicator_values_to_db(values, "SR_ZONES", "15m")
    assert shared_conn.insert_calls == values.shape[0]
