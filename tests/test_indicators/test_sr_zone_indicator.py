import pandas as pd
import pytest
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator

def make_sample_bars(n=60):
    # Create simple bars with constant high/low/close and volume
    times = pd.date_range(start='2025-01-01', periods=n, freq='T')
    return pd.DataFrame({
        'timestamp': times,
        'high': [100 + i % 5 for i in range(n)],
        'low': [95 + i % 5 for i in range(n)],
        'close_price': [98 + i % 5 for i in range(n)],
        'spy_volume': [1000 + 10*i for i in range(n)]
    })

def test_calculate_returns_expected_columns_and_qualifier():
    bars = make_sample_bars()
    # Use small pivot_lookback so time zones are detected
    params = {'pivot_lookback': 1, 'zone_tolerance': 0}
    indicator = SRZoneIndicator(parameters_json=params, qualifier='time')
    result = indicator.calculate(bars)
    # Expected output columns
    expected = {'timestamp_start', 'timestamp_end', 'value', 'aux_value', 'qualifier', 'parameters_json'}
    assert expected.issubset(set(result.columns))
    # All qualifiers should match 'time'
    assert set(result['qualifier'].unique()) == {'time'}

def test_calculate_all_methods_and_json_snapshot():
    bars = make_sample_bars()
    params = {'pivot_lookback': 1, 'zone_tolerance': 0}
    indicator = SRZoneIndicator(parameters_json=params)
    result = indicator.calculate(bars)
    # Should include all three methods
    qualifiers = set(result['qualifier'].unique())
    assert qualifiers == {'time', 'linear', 'volume'}
    # JSON string in parameters_json should include pivot_lookback
    for pj in result['parameters_json']:
        assert '"pivot_lookback"' in pj or "'pivot_lookback'" in pj

def test_empty_bars_returns_empty_df():
    indicator = SRZoneIndicator(qualifier='time')
    empty = pd.DataFrame(columns=['timestamp','high','low','close_price','spy_volume'])
    result = indicator.calculate(empty)
    # No zones should be returned
    assert result.empty
