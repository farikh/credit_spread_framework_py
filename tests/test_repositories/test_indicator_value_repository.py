import pandas as pd
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db

def test_save_indicator_values_to_db_mock(monkeypatch):
    # Corrected Mock DB connection
    class DummyResult:
        def fetchone(self):
            return (1,)  # Simulates fetching IndicatorId

    class DummyConn:
        def execute(self, stmt, params=None):
            return DummyResult()  # Return object with fetchone()
        def begin(self):
            return self
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass

    dummy_data = pd.DataFrame({
        'timestamp_start': pd.date_range(start='2024-01-01', periods=5, freq='15min'),
        'rsi': [50, 55, None, 60, 65]  # Includes one NaN to test skipping
    })

    # Monkeypatch engine creation to use DummyConn instead of real DB
    monkeypatch.setattr(
        "credit_spread_framework.data.repositories.indicator_value_repository.create_engine",
        lambda _: DummyConn()
    )

    # Run the function (this should now pass without exceptions)
    save_indicator_values_to_db(dummy_data, 'RSI', '15m')
