import pandas as pd
from credit_spread_framework.indicators.ta_wrappers.rsi_indicator import RSIIndicator

def test_rsi_calculation_basic():
    # Sample data for testing
    data = {
        'timestamp': pd.date_range(start='2024-01-01', periods=20, freq='15min'),
        'close': [i for i in range(20)]
    }
    bars = pd.DataFrame(data)

    rsi_indicator = RSIIndicator(period=14)
    result = rsi_indicator.calculate(bars)

    # Basic assertions
    assert 'rsi' in result.columns, "RSI column missing in output"
    assert 'timestamp_start' in result.columns, "timestamp_start column missing"
    assert result.shape[0] == 20, "Incorrect number of rows"
    # Ensure NaNs only in initial lookback
    assert result['rsi'].iloc[14:].notna().all(), "RSI should not be NaN after lookback period"
