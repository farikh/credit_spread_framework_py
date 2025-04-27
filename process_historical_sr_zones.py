"""
Script to process historical data and establish initial SR zones.

This script will:
1. Load historical OHLCV data for a specified date range
2. Process the data using the enhanced SR zone indicator
3. Create initial SR zones in the database

Usage:
    python process_historical_sr_zones.py --start 2024-01-01 --end 2024-09-30 --timeframe 1d
"""
import typer
from datetime import datetime, timedelta
import pandas as pd
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.indicators.custom.enhanced_sr_zone_indicator import EnhancedSRZoneIndicator
from credit_spread_framework.indicators.factory import register_indicator_class
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()

def register_enhanced_sr_zone_indicator():
    """
    Register the enhanced SR zone indicator with the indicator factory.
    """
    register_indicator_class("enhanced_srzones", EnhancedSRZoneIndicator)
    logger.info("Registered enhanced SR zone indicator")

@app.command()
def process_historical(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe to process"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    batch_days: int = typer.Option(30, "--batch-days", "-b", help="Number of days to process in each batch")
):
    """
    Process historical data and establish initial SR zones.
    """
    # Register the enhanced SR zone indicator
    register_enhanced_sr_zone_indicator()
    
    # Parse dates
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)
    
    logger.info(f"Processing historical data from {start_date} to {end_date}")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"Qualifier: {qualifier or 'all'}")
    logger.info(f"Batch days: {batch_days}")
    
    # Create the indicator instance
    parameters = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 75,
        "threshold_ratio": 0.25,
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50],
        "zone_tolerance": 15
    }
    indicator = EnhancedSRZoneIndicator(parameters_json=parameters, qualifier=qualifier)
    
    # Process in batches
    current_date = start_date
    while current_date <= end_date:
        batch_end = min(current_date + timedelta(days=batch_days), end_date)
        
        logger.info(f"Processing batch: {current_date} to {batch_end}")
        
        # Load OHLCV data for this batch
        bars = load_bars_from_db(timeframe, current_date, batch_end)
        
        if bars.empty:
            logger.warning(f"No data found for {current_date} to {batch_end}")
            current_date = batch_end + timedelta(days=1)
            continue
            
        logger.info(f"Loaded {len(bars)} bars")
        
        # Process the data
        zones = indicator.calculate(bars)
        
        logger.info(f"Created {len(zones)} zones")
        
        # Move to the next batch
        current_date = batch_end + timedelta(days=1)
    
    logger.info("Historical processing complete")

@app.command()
def process_specific_dates(
    dates: list[str] = typer.Option(..., "--date", "-d", help="Specific dates to process (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe to process"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    lookback_days: int = typer.Option(180, "--lookback", "-l", help="Number of days to look back for context")
):
    """
    Process specific dates to establish SR zones.
    """
    # Register the enhanced SR zone indicator
    register_enhanced_sr_zone_indicator()
    
    logger.info(f"Processing specific dates: {dates}")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"Qualifier: {qualifier or 'all'}")
    logger.info(f"Lookback days: {lookback_days}")
    
    # Create the indicator instance
    parameters = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 75,
        "threshold_ratio": 0.25,
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50],
        "zone_tolerance": 15
    }
    indicator = EnhancedSRZoneIndicator(parameters_json=parameters, qualifier=qualifier)
    
    # Process each date
    for date_str in dates:
        target_date = datetime.fromisoformat(date_str)
        start_date = target_date - timedelta(days=lookback_days)
        
        logger.info(f"Processing date: {target_date} (with lookback to {start_date})")
        
        # Load OHLCV data for this date with lookback
        bars = load_bars_from_db(timeframe, start_date, target_date)
        
        if bars.empty:
            logger.warning(f"No data found for {start_date} to {target_date}")
            continue
            
        logger.info(f"Loaded {len(bars)} bars")
        
        # Process the data
        zones = indicator.calculate(bars)
        
        logger.info(f"Created {len(zones)} zones for {target_date}")

@app.command()
def process_target_zones(
    target_zones: list[float] = typer.Option(..., "--zone", "-z", help="Target zone values to establish"),
    date: str = typer.Option(..., "--date", "-d", help="Date to establish zones for (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe to process"),
    lookback_days: int = typer.Option(180, "--lookback", "-l", help="Number of days to look back for context")
):
    """
    Process data to establish specific target zones.
    """
    # Register the enhanced SR zone indicator
    register_enhanced_sr_zone_indicator()
    
    logger.info(f"Processing target zones: {target_zones}")
    logger.info(f"Date: {date}")
    logger.info(f"Timeframe: {timeframe}")
    logger.info(f"Lookback days: {lookback_days}")
    
    # Parse date
    target_date = datetime.fromisoformat(date)
    start_date = target_date - timedelta(days=lookback_days)
    
    # Load OHLCV data
    bars = load_bars_from_db(timeframe, start_date, target_date)
    
    if bars.empty:
        logger.warning(f"No data found for {start_date} to {target_date}")
        return
        
    logger.info(f"Loaded {len(bars)} bars")
    
    # Create the indicator instance with focus on target zones
    parameters = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 150,  # Higher precision for better targeting
        "threshold_ratio": 0.15,  # Lower threshold to detect more peaks
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50],
        "zone_tolerance": 10,  # Tighter tolerance for target zones
        "focus_zones": target_zones  # Focus on these specific zones
    }
    
    # Process for each qualifier
    for qualifier in ["time", "linear", "volume"]:
        logger.info(f"Processing qualifier: {qualifier}")
        
        indicator = EnhancedSRZoneIndicator(parameters_json=parameters, qualifier=qualifier)
        zones = indicator.calculate(bars)
        
        logger.info(f"Created {len(zones)} zones for {qualifier}")
        
        # Check if target zones were established
        for target in target_zones:
            found = False
            closest_value = None
            closest_distance = float('inf')
            
            for _, zone in zones.iterrows():
                distance = abs(zone["value"] - target)
                if distance <= 15:  # Within 15 points
                    found = True
                    logger.info(f"Target zone {target} established at {zone['value']} ({distance:.2f} points away)")
                    break
                    
                if distance < closest_distance:
                    closest_distance = distance
                    closest_value = zone["value"]
            
            if not found:
                logger.warning(f"Target zone {target} not established. Closest zone: {closest_value} ({closest_distance:.2f} points away)")

if __name__ == "__main__":
    app()
