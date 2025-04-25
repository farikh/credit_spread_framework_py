
import typer
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from credit_spread_framework.indicators.factory import get_indicator_class
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db
from credit_spread_framework.data.repositories.indicator_value_repository import save_indicator_values_to_db
from credit_spread_framework.data.repositories.indicator_repository import get_all_indicators

app = typer.Typer()

TIMEFRAMES = ['1m', '3m', '15m', '1h', '1d']

def run_enrich_for_indicator(indicator: str, timeframe: str, start: str, end: str, qualifier: str):
    print(f"[INFO] Running enrichment for {indicator} on {timeframe} with qualifier '{qualifier}'...")
    start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc) if start else None
    end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc) if end else None

    bars = load_bars_from_db(timeframe, start_dt, end_dt)
    IndicatorClass, metadata = get_indicator_class(indicator)
    indicator_instance = IndicatorClass(
        parameters_json=metadata.get("ParametersJson") or {}, 
        qualifier=qualifier
    )
    values = indicator_instance.calculate(bars)
    save_indicator_values_to_db(values, indicator, timeframe, metadata)

@app.command()
def enrich_data(
    indicator: list[str] = typer.Option(None, "--indicator", "-i", help="Indicators to compute (e.g. RSI EMA ADX)"),
    timeframe: list[str] = typer.Option(None, "--timeframe", "-t", help="Timeframes (e.g. 1m 15m 1h)"),
    start: str = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    threads: int = typer.Option(4, "--threads", help="Number of threads to use"),
    qualifier: str = typer.Option(None, "--qualifier", "-q", help="Qualifier (e.g. 'time', 'linear', 'volume')")
):
    indicators = indicator or get_all_indicators()
    timeframes = timeframe or TIMEFRAMES

    print(f"[INFO] Indicators: {indicators}")
    print(f"[INFO] Timeframes: {timeframes}")
    print(f"[INFO] Threads: {threads}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(run_enrich_for_indicator, ind, tf, start, end, qualifier)
            for ind in indicators
            for tf in timeframes
        ]
        for future in futures:
            future.result()

if __name__ == "__main__":
    app()
