from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    @abstractmethod
    def calculate(self, bars: pd.DataFrame) -> pd.Series:
        pass
