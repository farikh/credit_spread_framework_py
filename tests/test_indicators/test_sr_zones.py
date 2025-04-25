
import pandas as pd
import pytest
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator

SAMPLE_BARS = pd.DataFrame({
    'timestamp': pd.date_range(start='2024-01-01', periods=5, freq='15min'),
    'open': [4300, 4310, 4320, 4330, 4340],
    'high': [4310, 4320, 4330, 4340, 4350],
    'low': [4290, 4300, 4310, 4320, 4330],
    'close_price': [4305, 4315, 4325, 4335, 4345]
})

def test_srzone_runs_with_valid_qualifier():
    indicator = SRZoneIndicator(qualifier="time")
    result = indicator.calculate(SAMPLE_BARS)
    assert "value" in result.columns
    assert "qualifier" in result.columns
    assert (result["qualifier"] == "time").all()

def test_srzone_runs_with_no_qualifier_defaults_to_all():
    indicator = SRZoneIndicator()
    result = indicator.calculate(SAMPLE_BARS)
    qualifiers_found = set(result["qualifier"].unique())
    assert qualifiers_found == {"time", "linear", "volume"}

def test_srzone_raises_on_invalid_qualifier():
    with pytest.raises(ValueError, match="Qualifier 'invalid' is not supported by SR_ZONES"):
        SRZoneIndicator(qualifier="invalid")
