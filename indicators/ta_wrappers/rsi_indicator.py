
import pandas as pd
import pandas_ta as ta
from credit_spread_framework.indicators.base import BaseIndicator

class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14, parameters_json=None, qualifier=None):
        if qualifier:
            raise ValueError(f"[ERROR] 'qualifier' is not supported for RSI.")
        self.period = period

    def calculate(self, bars: pd.DataFrame) -> pd.DataFrame:
        bars = bars.copy()
        bars['value'] = ta.rsi(bars['close_price'], length=self.period)
        bars['timestamp_start'] = bars['timestamp']
        return bars[['timestamp_start', 'value']]

__all__ = ["RSIIndicator"]
RSIIndicator = RSIIndicator
