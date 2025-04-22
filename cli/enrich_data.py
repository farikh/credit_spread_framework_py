import typer
from datetime import datetime, timezone
from credit_spread_framework.indicators.factory import get_indicator_class
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db

app = typer.Typer()

@app.command()
def enrich_data(
    indicator: str = typer.Option(..., "--indicator", "-i", help="Indicator short name (e.g., RSI, EMA)"),
    timeframe: str = typer.Option(..., "--timeframe", "-t", help="Timeframe (e.g., 1m, 15m, 1h)"),
    start: str = typer.Option(..., "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="End date (YYYY-MM-DD)")
):
    """
    Enrich the indicator values table with calculated values for the given indicator and timeframe.
    """
    start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)

    print(f"Loading bars for timeframe: {timeframe} from {start_dt} to {end_dt}...")
    bars = load_bars_from_db(timeframe, start_dt, end_dt)

    print(f"Initializing indicator: {indicator}...")
    IndicatorClass = get_indicator_class(indicator)  # Lookup by SHORT NAME
    indicator_instance = IndicatorClass()

    print("Calculating indicator values...")
    values = indicator_instance.calculate(bars)

    print("Saving results to database...")
    save_indicator_values_to_db(values, indicator, timeframe)

    print("✅ Enrichment complete.")

if __name__ == "__main__":
    app()
