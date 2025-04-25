
from credit_spread_framework.indicators.base import BaseIndicator
import pandas as pd
from datetime import datetime, timezone

class SRZoneIndicator(BaseIndicator):
    def __init__(self, parameters_json=None, qualifier=None):
        self.available_methods = ["time", "linear", "volume"]
        if qualifier:
            if qualifier not in self.available_methods:
                raise ValueError(f"[ERROR] Qualifier '{qualifier}' is not supported by SR_ZONES.")
            self.methods_to_run = [qualifier]
        else:
            self.methods_to_run = self.available_methods

    def calculate(self, bars: pd.DataFrame) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        all_results = []
        for method in self.methods_to_run:
            zones = pd.DataFrame({
                "timestamp_start": [now, now],
                "zone_level": [4300, 4400],
                "touch_count": [5, 3]
            })
            zones["qualifier"] = method
            zones["parameters_json"] = zones.apply(lambda row: f'{{"touch_count": {row["touch_count"]}}}', axis=1)
            all_results.append(zones.rename(columns={"zone_level": "value", "timestamp_start": "timestamp_start"}))
        return pd.concat(all_results, ignore_index=True)
