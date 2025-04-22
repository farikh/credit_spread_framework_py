import pandas as pd
import pandas_ta as ta
from credit_spread_framework.indicators.base import BaseIndicator

class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, bars: pd.DataFrame) -> pd.Series:
        """
        Calculate the RSI indicator on the given bars DataFrame.
        Ensures the result Series uses the 'timestamp' as its index.
        """
        rsi = ta.rsi(bars['close'], length=self.period)
        rsi.index = bars['timestamp']  # ✅ Ensure index is timestamp for correct downstream usage
        return rsi
