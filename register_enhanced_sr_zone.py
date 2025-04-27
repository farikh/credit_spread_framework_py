"""
Script to register the enhanced SR zone indicator in the indicators table.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    engine = get_engine()
    
    # Check if the indicator already exists
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :short_name"),
            {"short_name": "enhanced_srzones"}
        )
        row = result.fetchone()
        
        if row:
            logger.info(f"Indicator enhanced_srzones already exists with ID {row[0]}")
            return
            
        # Insert the indicator
        conn.execute(
            text("""
                INSERT INTO indicators (ShortName, Name, ParametersJson, IsActive)
                VALUES (:short_name, :name, :parameters_json, 1)
            """),
            {
                "short_name": "enhanced_srzones",
                "name": "Enhanced SR Zones",
                "parameters_json": '{"pivot_lookback": 50, "filter_len": 3, "precision": 75, "threshold_ratio": 0.25, "include_ph": true, "include_pl": true, "lengths": [5, 10, 20, 50], "zone_tolerance": 15}'
            }
        )
        
        # Verify the indicator was inserted
        result = conn.execute(
            text("SELECT IndicatorId FROM indicators WHERE ShortName = :short_name"),
            {"short_name": "enhanced_srzones"}
        )
        row = result.fetchone()
        
        if row:
            logger.info(f"Successfully registered enhanced_srzones with ID {row[0]}")
        else:
            logger.error("Failed to register enhanced_srzones")

if __name__ == "__main__":
    main()
