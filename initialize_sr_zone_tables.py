"""
Script to initialize the SR zone tables.

This script will:
1. Run the migration script to create the SR zone tables
2. Register the enhanced SR zone indicator in the indicators table

Usage:
    python initialize_sr_zone_tables.py
"""
import typer
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()

def run_migration_script(script_path):
    """
    Run a SQL migration script.
    
    Args:
        script_path: Path to the SQL script
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(script_path):
        logger.error(f"Migration script not found: {script_path}")
        return False
        
    try:
        # Read the script
        with open(script_path, 'r') as f:
            script = f.read()
            
        # Execute the script
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text(script))
            
        logger.info(f"Successfully executed migration script: {script_path}")
        return True
    except Exception as e:
        logger.error(f"Error executing migration script: {e}")
        return False

def register_indicator(short_name, long_name, description):
    """
    Register an indicator in the indicators table.
    
    Args:
        short_name: Short name of the indicator
        long_name: Long name of the indicator
        description: Description of the indicator
        
    Returns:
        The ID of the indicator
    """
    engine = get_engine()
    
    # Check if the indicator already exists
    query = text("""
        SELECT IndicatorId
        FROM indicators
        WHERE ShortName = :short_name
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {"short_name": short_name})
        row = result.fetchone()
        
        if row:
            logger.info(f"Indicator {short_name} already exists with ID {row[0]}")
            return row[0]
            
        # Insert the indicator
        insert_query = text("""
            INSERT INTO indicators (ShortName, Name, ParametersJson, IsActive)
            VALUES (:short_name, :long_name, :description, 1);
            SELECT SCOPE_IDENTITY();
        """)
        
        result = conn.execute(
            insert_query,
            {
                "short_name": short_name,
                "long_name": long_name,
                "description": description
            }
        )
        
        indicator_id = result.scalar()
        logger.info(f"Registered indicator {short_name} with ID {indicator_id}")
        return indicator_id

@app.command()
def initialize():
    """
    Initialize the SR zone tables.
    """
    logger.info("Initializing SR zone tables...")
    
    # Run the migration script
    script_path = os.path.join(
        "credit_spread_framework", "data", "migrations", "0003_create_sr_zone_tables.sql"
    )
    if not run_migration_script(script_path):
        logger.error("Failed to create SR zone tables")
        return
        
    # Register the enhanced SR zone indicator
    register_indicator(
        short_name="enhanced_srzones",
        long_name="Enhanced SR Zones",
        description="Enhanced Support/Resistance zones with historical persistence and interaction tracking"
    )
    
    logger.info("SR zone tables initialized successfully")

if __name__ == "__main__":
    app()
