import pandas as pd
import pandas_ta as ta
from credit_spread_framework.indicators.base import BaseIndicator

class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, bars: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the RSI indicator on actual bar data.
        Returns a DataFrame containing timestamp and the RSI value.
        """
        bars = bars.copy()
        bars['rsi'] = ta.rsi(bars['close_price'], length=self.period)
        bars['timestamp_start'] = bars['timestamp']  # Assign 'timestamp_start' directly from 'timestamp'
        return bars[['timestamp_start', 'rsi']]

__all__ = ["RSIIndicator"]
RSIIndicator = RSIIndicator