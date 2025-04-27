"""
Script to update the SR zone indicator parameters in the database to match TradingView settings.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import json

def main():
    # TradingView parameters
    params = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 75,
        "threshold_ratio": 0.25,
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50]
    }
    
    # Convert to JSON string
    params_json = json.dumps(params)
    
    # Update the SR zone indicator parameters in the database
    engine = get_engine()
    with engine.begin() as conn:
        # First, check if the indicator exists
        result = conn.execute(
            text("SELECT IndicatorId, ParametersJson FROM indicators WHERE ShortName = :name"),
            {"name": "srzones"}
        ).fetchone()
        
        if result:
            indicator_id, current_params = result
            print(f"Found SR zone indicator with ID {indicator_id}")
            print(f"Current parameters: {current_params}")
            
            # Update the parameters
            conn.execute(
                text("UPDATE indicators SET ParametersJson = :params WHERE IndicatorId = :id"),
                {"params": params_json, "id": indicator_id}
            )
            print(f"Updated parameters to: {params_json}")
        else:
            print("SR zone indicator not found in the database")

if __name__ == "__main__":
    main()
