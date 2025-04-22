from credit_spread_framework.indicators.ta_wrappers.rsi_indicator import RSIIndicator

def get_indicator_class(indicator_name: str):
    mapping = {
        "RSI": RSIIndicator,
        # Future indicators like "EMA": EMAIndicator can be added here
    }
    if indicator_name not in mapping:
        raise ValueError(f"Indicator {indicator_name} is not implemented.")
    return mapping[indicator_name]
