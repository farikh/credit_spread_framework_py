"""
Script to process enhanced SR zones for a specific date range.

This script will:
1. Process SR zones for all timeframes for the specified date range using the enhanced SR zone indicator
2. Create or update zones in the dedicated SR zone tables
3. Track interactions between price and existing zones

Usage:
    python process_enhanced_sr_zones.py --start 2025-04-03 --end 2025-04-03
    python process_enhanced_sr_zones.py --start 2025-04-01 --end 2025-04-10 --timeframe 1d
    python process_enhanced_sr_zones.py --start 2025-04-01 --end 2025-04-10 --qualifier time
"""
import typer
from datetime import datetime, timedelta
from credit_spread_framework.indicators.custom.enhanced_sr_zone_indicator import EnhancedSRZoneIndicator
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.sr_zone_repository import SRZoneRepository
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def process_sr_zones(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    timeframe: list[str] = typer.Option(None, "--timeframe", "-t", help="Timeframes to process (default: all)"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    batch_days: int = typer.Option(1, "--batch-days", "-b", help="Number of days to process in each batch"),
    threads: int = typer.Option(4, "--threads", help="Parallel threads")
):
    """
    Process enhanced SR zones for the specified date range.
    """
    indicator_name = "enhanced_srzones"
    timeframes = timeframe or ['1m', '3m', '15m', '1h', '1d']
    
    logger.info(f"Processing {indicator_name} for {start} to {end}")
    logger.info(f"Timeframes: {timeframes}")
    logger.info(f"Qualifier: {qualifier or 'all'}")
    logger.info(f"Batch days: {batch_days}")
    logger.info(f"Threads: {threads}")
    
    # Parse dates
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)
    
    # Create indicator parameters
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
    
    # Process each timeframe
    for tf in timeframes:
        logger.info(f"\nProcessing {indicator_name} on {tf} for {start} to {end}")
        
        # Process in batches
        current_date = start_date
        while current_date <= end_date:
            batch_end = min(current_date + timedelta(days=batch_days), end_date)
            
            logger.info(f"Processing batch: {current_date} to {batch_end}")
            
            # Load OHLCV data for this batch
            bars = load_bars_from_db(tf, current_date, batch_end)
            
            if bars.empty:
                logger.warning(f"No data found for {current_date} to {batch_end}")
                current_date = batch_end + timedelta(days=1)
                continue
                
            logger.info(f"Loaded {len(bars)} bars")
            
            # Create indicator instance
            indicator = EnhancedSRZoneIndicator(parameters_json=parameters, qualifier=qualifier)
            
            # Process the data
            zones = indicator.calculate(bars)
            
            logger.info(f"Processed {len(zones)} zones for {tf}")
            
            # Move to the next batch
            current_date = batch_end + timedelta(days=1)
    
    logger.info("\nProcessing completed.")

@app.command()
def list_active_zones(
    timeframe: str = typer.Option(..., "--timeframe", "-t", help="Timeframe to query"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    date: str = typer.Option(None, "--date", "-d", help="Date to check (default: current date)")
):
    """
    List active SR zones for a specific timeframe and date.
    """
    # Parse date
    if date:
        check_date = datetime.fromisoformat(date)
    else:
        check_date = datetime.now()
        
    logger.info(f"Listing active zones for {timeframe}" + 
               (f" and qualifier {qualifier}" if qualifier else "") + 
               f" as of {check_date}")
    
    # Get active zones
    zone_repo = SRZoneRepository()
    zones = zone_repo.get_active_zones(
        timeframe=timeframe,
        qualifier=qualifier,
        date=check_date
    )
    
    if zones.empty:
        logger.info("No active zones found")
        return
        
    # Display zones
    logger.info(f"Found {len(zones)} active zones:")
    for _, zone in zones.iterrows():
        logger.info(f"Zone {zone['zone_id']}: {zone['value']} (strength: {zone['strength']}, qualifier: {zone['qualifier']})")
        logger.info(f"  First detected: {zone['first_detected']}")
        logger.info(f"  Last confirmed: {zone['last_confirmed']}")
        logger.info("")

@app.command()
def list_zone_interactions(
    zone_id: int = typer.Option(..., "--zone-id", "-z", help="Zone ID to query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of interactions to show")
):
    """
    List interactions for a specific SR zone.
    """
    from credit_spread_framework.data.repositories.sr_zone_interaction_repository import SRZoneInteractionRepository
    
    logger.info(f"Listing interactions for zone {zone_id}")
    
    # Get zone details
    zone_repo = SRZoneRepository()
    zone = zone_repo.get_zone_by_id(zone_id)
    
    if not zone:
        logger.error(f"Zone {zone_id} not found")
        return
        
    logger.info(f"Zone {zone_id}: {zone['value']} (strength: {zone['strength']}, qualifier: {zone['qualifier']})")
    logger.info(f"Timeframe: {zone['timeframe']}")
    logger.info(f"Status: {'Active' if zone['is_active'] else 'Invalidated'}")
    
    # Get interactions
    interaction_repo = SRZoneInteractionRepository()
    interactions = interaction_repo.get_interactions_for_zone(zone_id)
    
    if interactions.empty:
        logger.info("No interactions found")
        return
        
    # Display interactions (limited)
    interactions = interactions.head(limit)
    logger.info(f"Found {len(interactions)} interactions (showing {limit}):")
    for _, interaction in interactions.iterrows():
        logger.info(f"Interaction {interaction['interaction_id']}: {interaction['interaction_type']}")
        logger.info(f"  Timestamp: {interaction['timestamp']}")
        logger.info(f"  Price: {interaction['price']}")
        logger.info(f"  Strength: {interaction['interaction_strength']}")
        logger.info("")

@app.command()
def invalidate_zone(
    zone_id: int = typer.Option(..., "--zone-id", "-z", help="Zone ID to invalidate"),
    reason: str = typer.Option(None, "--reason", "-r", help="Reason for invalidation")
):
    """
    Invalidate a specific SR zone.
    """
    logger.info(f"Invalidating zone {zone_id}" + (f" - Reason: {reason}" if reason else ""))
    
    # Get zone details
    zone_repo = SRZoneRepository()
    zone = zone_repo.get_zone_by_id(zone_id)
    
    if not zone:
        logger.error(f"Zone {zone_id} not found")
        return
        
    if not zone['is_active']:
        logger.warning(f"Zone {zone_id} is already invalidated")
        return
        
    # Invalidate the zone
    success = zone_repo.invalidate_zone(zone_id, reason)
    
    if success:
        logger.info(f"Successfully invalidated zone {zone_id}")
    else:
        logger.error(f"Failed to invalidate zone {zone_id}")

if __name__ == "__main__":
    app()
