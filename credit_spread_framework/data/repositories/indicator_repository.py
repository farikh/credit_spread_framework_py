from credit_spread_framework.data.db_engine import get_engine
# File: credit_spread_framework/data/repositories/indicator_repository.py

import sqlalchemy as sa
import urllib

def get_all_indicators():

    with engine.begin() as conn:
        result = conn.execute(text("SELECT ShortName FROM indicators"))
        indicators = [row[0] for row in result]
    
    return indicators
