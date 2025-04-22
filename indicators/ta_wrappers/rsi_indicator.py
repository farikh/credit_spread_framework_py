import pandas as pd
import pandas_ta as ta
from credit_spread_framework.indicators.base import BaseIndicator

class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        self.period = period

    def calculate(self, bars: pd.DataFrame) -> pd.Series:
        return ta.rsi(bars['close'], length=self.period)
