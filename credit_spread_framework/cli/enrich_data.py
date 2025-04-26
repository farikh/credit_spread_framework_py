import typer
from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from credit_spread_framework.indicators.factory import get_indicator_class
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db
from credit_spread_framework.data.repositories.indicator_repository import get_all_indicators

app = typer.Typer()

TIMEFRAMES = ['1m', '3m', '15m', '1h', '1d']

def run_enrich_for_indicator(indicator: str, timeframe: str,
                             start: str, end: str, qualifier: str):
    # Compute EST session window (09:30–16:00) converted to UTC
    est = ZoneInfo("America/New_York")
    if start:
        d0 = date.fromisoformat(start)
        local_start = datetime(d0.year, d0.month, d0.day, 9, 30, tzinfo=est)
        start_dt = local_start.astimezone(timezone.utc)
    else:
        start_dt = None
    if end:
        d1 = date.fromisoformat(end)
        local_end = datetime(d1.year, d1.month, d1.day, 16, 0, tzinfo=est)
        end_dt = local_end.astimezone(timezone.utc)
    else:
        end_dt = None

    print(f"[INFO] Enriching {indicator} on {timeframe} from {start_dt} to {end_dt} (UTC)")

    bars = load_bars_from_db(timeframe, start_dt, end_dt)
    IndicatorClass, metadata = get_indicator_class(indicator)

    raw_params = metadata.get("ParametersJson")
    if not isinstance(raw_params, dict):
        raw_params = {}
    indicator_instance = IndicatorClass(parameters_json=raw_params,
                                        qualifier=qualifier)

    values = indicator_instance.calculate(bars)
    print(f"[DEBUG] {indicator} {timeframe} generated {values.shape[0]} records")
    print(values.head())

    save_indicator_values_to_db(values, indicator, timeframe,
                                metadata, start_dt, end_dt)

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
                                  help="Qualifier (time, linear, volume)")
):
    indicators = indicator or get_all_indicators()
    timeframes = timeframe or TIMEFRAMES

    print(f"[INFO] Indicators: {indicators}")
    print(f"[INFO] Timeframes: {timeframes}")
    print(f"[INFO] Threads: {threads}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(run_enrich_for_indicator, ind, tf,
                            start, end, qualifier)
            for ind in indicators
            for tf in timeframes
        ]
        for future in futures:
            future.result()

if __name__ == "__main__":
    app()
