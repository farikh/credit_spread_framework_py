import typer
from datetime import datetime, date, time, timezone, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from credit_spread_framework.indicators.factory import get_indicator_class
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.indicator_value_repository import (
    save_indicator_values_to_db,
    get_most_recent_indicator_values
)
from credit_spread_framework.data.repositories.indicator_repository import get_all_indicators

app = typer.Typer()

TIMEFRAMES = ['1m', '3m', '15m', '1h', '1d']

def carry_forward_indicator_values(indicator: str, timeframe: str, 
                                  start_dt: datetime, end_dt: datetime, 
                                  qualifier: str = None):
    """
    Retrieve the most recent indicator values relative to the start date and
    carry them forward to the specified date range.
    
    Returns a DataFrame with the carried-forward values, or an empty DataFrame if none found.
    """
    print(f"[DEBUG] Attempting to carry forward {indicator} values for {timeframe} relative to {start_dt}")
    
    # Get the most recent values relative to the start date
    recent_values = get_most_recent_indicator_values(
        indicator_name=indicator,
        timeframe=timeframe,
        target_date=start_dt,
        qualifier=qualifier,
        closest_date=True  # Find the closest date, even if it's after the target date
    )
    
    if recent_values.empty:
        print(f"[INFO] No previous values found for {indicator} on {timeframe} before {start_dt}")
        return pd.DataFrame()
    
    print(f"[DEBUG] Original values before updating timestamps:")
    for i, row in recent_values.iterrows():
        print(f"[DEBUG] Value: {row.get('value')}, Qualifier: {row.get('qualifier')}, " +
              f"Original timestamps: {row.get('timestamp_start')} to {row.get('timestamp_end')}")
    
    # Update timestamps to the requested date range
    for i, row in recent_values.iterrows():
        # Convert timestamps to naive datetime objects to avoid dtype warnings
        start_naive = start_dt
        end_naive = end_dt
        
        if hasattr(start_dt, 'tzinfo') and start_dt.tzinfo:
            start_naive = start_dt.replace(tzinfo=None)
        
        if hasattr(end_dt, 'tzinfo') and end_dt.tzinfo:
            end_naive = end_dt.replace(tzinfo=None)
        
        recent_values.at[i, 'timestamp_start'] = start_naive
        recent_values.at[i, 'timestamp_end'] = end_naive
    
    print(f"[DEBUG] Updated values after changing timestamps:")
    for i, row in recent_values.iterrows():
        print(f"[DEBUG] Value: {row.get('value')}, Qualifier: {row.get('qualifier')}, " +
              f"New timestamps: {row.get('timestamp_start')} to {row.get('timestamp_end')}")
    
    print(f"[INFO] Carrying forward {len(recent_values)} previous values for {indicator} on {timeframe}")
    return recent_values

def run_enrich_for_indicator(indicator: str, timeframe: str,
                             start: str, end: str, qualifier: str,
                             batch_days: int = 1, carry_forward: bool = True):
    # For daily data, use the entire day (00:00-23:59)
    # For intraday data, use the EST session window (09:30–16:00) converted to UTC
    est = ZoneInfo("America/New_York")
    if start:
        d0 = date.fromisoformat(start)
        if timeframe == "1d":
            # For daily data, use the entire day
            # Use a naive datetime to avoid timezone issues
            start_dt = datetime(d0.year, d0.month, d0.day, 0, 0)
        else:
            # For intraday data, use the trading session
            local_start = datetime(d0.year, d0.month, d0.day, 9, 30, tzinfo=est)
            start_dt = local_start.astimezone(timezone.utc)
    else:
        start_dt = None
    if end:
        d1 = date.fromisoformat(end)
        if timeframe == "1d":
            # For daily data, use the entire day
            # Use a naive datetime to avoid timezone issues
            end_dt = datetime(d1.year, d1.month, d1.day, 23, 59, 59)
        else:
            # For intraday data, use the trading session
            local_end = datetime(d1.year, d1.month, d1.day, 16, 0, tzinfo=est)
            end_dt = local_end.astimezone(timezone.utc)
    else:
        end_dt = None

    print(f"[INFO] Enriching {indicator} on {timeframe} from {start_dt} to {end_dt} (UTC)")

    # Load all bars for the entire period
    bars = load_bars_from_db(timeframe, start_dt, end_dt)
    
    # If no bars found and carry_forward is enabled, try to carry forward previous values
    if bars.empty:
        print(f"[WARNING] No bars found for {indicator} on {timeframe} from {start_dt} to {end_dt}")
        if carry_forward:
            # Carry forward previous values
            carried_values = carry_forward_indicator_values(
                indicator=indicator,
                timeframe=timeframe,
                start_dt=start_dt,
                end_dt=end_dt,
                qualifier=qualifier
            )
            
            if not carried_values.empty:
                # Save the carried-forward values
                metadata = None  # We don't have metadata here, but it's optional
                save_indicator_values_to_db(carried_values, indicator, timeframe,
                                           metadata, start_dt, end_dt)
        return

    IndicatorClass, metadata = get_indicator_class(indicator)
    raw_params = metadata.get("ParametersJson")
    if not isinstance(raw_params, dict):
        raw_params = {}

    # Process in batches by day
    if batch_days <= 0:
        batch_days = 1  # Ensure positive batch size

    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(bars['timestamp']):
        bars['timestamp'] = pd.to_datetime(bars['timestamp'])

    # Group by date
    bars['date'] = bars['timestamp'].dt.date
    unique_dates = sorted(bars['date'].unique())
    
    # Process in batches of batch_days
    total_batches = (len(unique_dates) + batch_days - 1) // batch_days
    for batch_idx in range(total_batches):
        batch_start_idx = batch_idx * batch_days
        batch_end_idx = min(batch_start_idx + batch_days, len(unique_dates))
        batch_dates = unique_dates[batch_start_idx:batch_end_idx]
        
        # Get bars for this batch of dates
        batch_bars = bars[bars['date'].isin(batch_dates)]
        
        if batch_bars.empty:
            continue
            
        # Calculate indicator values for this batch
        indicator_instance = IndicatorClass(parameters_json=raw_params,
                                            qualifier=qualifier)
        batch_values = indicator_instance.calculate(batch_bars)
        
        if batch_values.empty:
            print(f"[WARNING] No values generated for {indicator} on {timeframe} for dates {batch_dates[0]} to {batch_dates[-1]}")
            
            if carry_forward:
                # Determine batch start and end times for database operations
                batch_start = datetime.combine(batch_dates[0], time.min, tzinfo=timezone.utc)
                batch_end = datetime.combine(batch_dates[-1], time.max, tzinfo=timezone.utc)
                
                # Try to carry forward previous values
                carried_values = carry_forward_indicator_values(
                    indicator=indicator,
                    timeframe=timeframe,
                    start_dt=batch_start,
                    end_dt=batch_end,
                    qualifier=qualifier
                )
                
                if not carried_values.empty:
                    # Save the carried-forward values
                    save_indicator_values_to_db(carried_values, indicator, timeframe,
                                              metadata, batch_start, batch_end)
            
            continue
            
        print(f"[DEBUG] {indicator} {timeframe} generated {batch_values.shape[0]} records for dates {batch_dates[0]} to {batch_dates[-1]}")
        
        # Determine batch start and end times for database operations
        batch_start = datetime.combine(batch_dates[0], time.min, tzinfo=timezone.utc)
        batch_end = datetime.combine(batch_dates[-1], time.max, tzinfo=timezone.utc)
        
        # Save this batch to the database
        save_indicator_values_to_db(batch_values, indicator, timeframe,
                                    metadata, batch_start, batch_end)

@app.command()
def enrich_data(
    indicator: list[str] = typer.Option(None, "--indicator", "-i",
                                        help="Indicators to compute"),
    timeframe: list[str] = typer.Option(None, "--timeframe", "-t",
                                        help="Timeframes to compute"),
    start: str = typer.Option(None, "--start",
                              help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(None, "--end",
                            help="End date (YYYY-MM-DD)"),
    threads: int = typer.Option(4, "--threads",
                                help="Parallel threads"),
    qualifier: str = typer.Option(None, "--qualifier", "-q",
                                  help="Qualifier (time, linear, volume)"),
    batch_days: int = typer.Option(1, "--batch-days", "-b",
                                  help="Number of days to process in each batch"),
    carry_forward: bool = typer.Option(True, "--carry-forward/--no-carry-forward",
                                      help="Carry forward previous values when no new data is available")
):
    indicators = indicator or get_all_indicators()
    timeframes = timeframe or TIMEFRAMES

    print(f"[INFO] Indicators: {indicators}")
    print(f"[INFO] Timeframes: {timeframes}")
    print(f"[INFO] Threads: {threads}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(run_enrich_for_indicator, ind, tf,
                            start, end, qualifier, batch_days, carry_forward)
            for ind in indicators
            for tf in timeframes
        ]
        for future in futures:
            future.result()

if __name__ == "__main__":
    app()
