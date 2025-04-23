import sqlalchemy as sa
import urllib
from sqlalchemy import create_engine, text
from credit_spread_framework.config.settings import SQLSERVER_CONN_STRING

# Import your actual indicator classes here
from credit_spread_framework.indicators.ta_wrappers.rsi_indicator import RSIIndicator
# from credit_spread_framework.indicators.ta_wrappers.ema_indicator import EMAIndicator
# Add more imports as needed

# Registry: ShortName -> Class
CLASS_REGISTRY = {
    "RSI": RSIIndicator,
    # "EMA": EMAIndicator,
    # "ADX": ADXIndicator,
}

def get_all_indicators_from_db():
    conn_str = urllib.parse.quote_plus(SQLSERVER_CONN_STRING)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    with engine.begin() as conn:
        result = conn.execute(text("SELECT ShortName FROM indicators"))
        return [row[0] for row in result]

def get_indicator_class(short_name: str):
    if short_name not in CLASS_REGISTRY:
        raise ValueError(f"Indicator '{short_name}' not registered in factory CLASS_REGISTRY.")
    return CLASS_REGISTRY[short_name]

def list_supported_indicators():
    """Validate DB-defined indicators against available classes."""
    db_indicators = get_all_indicators_from_db()
    valid_indicators = [name for name in db_indicators if name in CLASS_REGISTRY]

    missing_classes = set(db_indicators) - set(CLASS_REGISTRY.keys())
    if missing_classes:
        print(f"[WARNING] These indicators exist in DB but are not registered in CLASS_REGISTRY: {missing_classes}")

    return valid_indicators
