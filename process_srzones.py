"""
Script to process SR zones for a specific date range, with carry-forward functionality.

This script will:
1. Process SR zones for all timeframes for the specified date range
2. If no bars are found for a timeframe, it will carry forward the most recent SR zones
3. If bars are found but no SR zones are generated, it will also carry forward the most recent SR zones

Usage:
    python -m process_srzones --start 2025-04-03 --end 2025-04-03
    python -m process_srzones --start 2025-04-01 --end 2025-04-10 --timeframe 1d
    python -m process_srzones --start 2025-04-01 --end 2025-04-10 --qualifier time

Note: This script has been modified to fix an issue with the date handling for daily data.
The original script was using the EST session window (09:30-16:00) converted to UTC,
which was causing the script to use data from the wrong date. This has been fixed in
the enrich_data.py file, but we need to make sure we're using the correct date here.
"""
import typer
from datetime import datetime
from credit_spread_framework.cli.enrich_data import run_enrich_for_indicator

app = typer.Typer()

@app.command()
def process_srzones(
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)"),
    timeframe: list[str] = typer.Option(None, "--timeframe", "-t", help="Timeframes to process (default: all)"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (time, linear, volume)"),
    batch_days: int = typer.Option(1, "--batch-days", "-b", help="Number of days to process in each batch"),
    carry_forward: bool = typer.Option(True, "--carry-forward/--no-carry-forward", help="Carry forward previous values when no new data is available"),
    threads: int = typer.Option(4, "--threads", help="Parallel threads")
):
    """
    Process SR zones for the specified date range, with carry-forward functionality.
    """
    indicator = "srzones"
    timeframes = timeframe or ['1m', '3m', '15m', '1h', '1d']
    
    print(f"Processing {indicator} for {start} to {end}")
    print(f"Timeframes: {timeframes}")
    print(f"Qualifier: {qualifier or 'all'}")
    print(f"Carry forward: {carry_forward}")
    print(f"Batch days: {batch_days}")
    print(f"Threads: {threads}")
    print()
    
    for tf in timeframes:
        print(f"\nProcessing {indicator} on {tf} for {start} to {end}")
        run_enrich_for_indicator(
            indicator=indicator,
            timeframe=tf,
            start=start,
            end=end,
            qualifier=qualifier,
            batch_days=batch_days,
            carry_forward=carry_forward
        )
    
    print("\nProcessing completed.")

if __name__ == "__main__":
    app()
