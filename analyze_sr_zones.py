"""
Script to analyze SR zone detection with different parameters.

This script will:
1. Load historical OHLCV data
2. Run the SR zone detection with different parameter configurations
3. Compare the results to identify which configuration best captures specific zones
4. Visualize the results

Usage:
    python analyze_sr_zones.py --start 2024-09-01 --end 2024-09-30 --timeframe 1d
"""
import typer
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sqlalchemy import text
from credit_spread_framework.data.db_engine import get_engine
from credit_spread_framework.indicators.custom.sr_zone_indicator import SRZoneIndicator
from credit_spread_framework.data.repositories.ohlcv_repository import load_bars_from_db

app = typer.Typer()

def query_ohlcv_direct(start_date, end_date, timeframe):
    """
    Query OHLCV data directly from the database using raw SQL.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Timeframe (e.g., '1d', '1m')
        
    Returns:
        DataFrame with OHLCV data
    """
    engine = get_engine()
    
    # Determine the table name based on the timeframe
    table_name = f"spx_ohlcv_{timeframe}"
    
    # Build the query
    query = text(f"""
        SELECT TOP (1000) [bar_id]
            ,[timestamp]
            ,[ticker]
            ,[open]
            ,[high]
            ,[low]
            ,[close]
            ,[spy_volume]
        FROM [CreditSpreadsDB].[dbo].[{table_name}]
        WHERE timestamp >= '{start_date} 00:00:00.000' AND timestamp <= '{end_date} 23:59:59.999'
        ORDER BY timestamp
    """)
    
    # Execute the query
    with engine.begin() as conn:
        result = conn.execute(query)
        
        # Convert to DataFrame
        columns = ["bar_id", "timestamp", "ticker", "open", "high", "low", "close", "spy_volume"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
        
    return df

def run_sr_zone_detection(bars, params, qualifier=None):
    """
    Run SR zone detection with the specified parameters.
    
    Args:
        bars: DataFrame with OHLCV data
        params: Dict of parameters for SR zone detection
        qualifier: Optional qualifier to filter by (e.g., 'time', 'linear', 'volume')
        
    Returns:
        DataFrame with detected SR zones
    """
    indicator = SRZoneIndicator(parameters_json=params, qualifier=qualifier)
    return indicator.calculate(bars)

def analyze_parameter_impact(bars, target_zone, parameter_variations):
    """
    Analyze the impact of different parameters on SR zone detection.
    
    Args:
        bars: DataFrame with OHLCV data
        target_zone: The target zone to look for (e.g., 5420)
        parameter_variations: List of parameter configurations to test
        
    Returns:
        DataFrame with analysis results
    """
    results = []
    
    for params in parameter_variations:
        # Run SR zone detection with these parameters
        zones = run_sr_zone_detection(bars, params)
        
        # Check if the target zone is detected
        closest_zone = None
        min_distance = float('inf')
        
        for _, zone in zones.iterrows():
            distance = abs(zone['value'] - target_zone)
            if distance < min_distance:
                min_distance = distance
                closest_zone = zone['value']
        
        # Record the results
        results.append({
            'parameters': params,
            'closest_zone': closest_zone,
            'distance': min_distance,
            'detected': min_distance < 20,  # Within 20 points
            'num_zones': len(zones)
        })
    
    return pd.DataFrame(results)

def visualize_sr_zones(bars, zones, title):
    """
    Visualize the OHLCV data and detected SR zones.
    
    Args:
        bars: DataFrame with OHLCV data
        zones: DataFrame with detected SR zones
        title: Title for the plot
    """
    plt.figure(figsize=(12, 6))
    
    # Plot OHLCV data
    plt.plot(bars['timestamp'], bars['close'], label='Close')
    plt.plot(bars['timestamp'], bars['high'], 'g--', alpha=0.5, label='High')
    plt.plot(bars['timestamp'], bars['low'], 'r--', alpha=0.5, label='Low')
    
    # Plot SR zones
    for _, zone in zones.iterrows():
        plt.axhline(y=zone['value'], color='blue', linestyle='-', alpha=0.7)
        plt.text(bars['timestamp'].iloc[0], zone['value'], f"{zone['value']:.2f} ({zone['qualifier']})")
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f"{title.replace(' ', '_')}.png")
    plt.close()

@app.command()
def main(
    start: str = typer.Option(..., "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", "-e", help="End date (YYYY-MM-DD)"),
    timeframe: str = typer.Option("1d", "--timeframe", "-t", help="Timeframe (e.g., '1d', '1m')"),
    target_zone: float = typer.Option(5420, "--target", help="Target zone to look for"),
    history_days: int = typer.Option(200, "--history", "-h", help="Number of days of historical data to load")
):
    """
    Analyze SR zone detection with different parameters.
    """
    # Validate dates
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        return
    
    # Calculate history start date
    history_start = start_date - timedelta(days=history_days)
    history_start_str = history_start.strftime("%Y-%m-%d")
    
    print(f"Loading OHLCV data from {history_start_str} to {end}")
    
    # Load OHLCV data
    bars = query_ohlcv_direct(history_start_str, end, timeframe)
    
    if bars.empty:
        print(f"No OHLCV data found for {timeframe} from {history_start_str} to {end}")
        return
    
    print(f"Loaded {len(bars)} OHLCV bars")
    
    # Define parameter variations to test
    base_params = {
        "pivot_lookback": 50,
        "filter_len": 3,
        "precision": 75,
        "threshold_ratio": 0.25,
        "include_ph": True,
        "include_pl": True,
        "lengths": [5, 10, 20, 50]
    }
    
    parameter_variations = [
        # Base parameters (TradingView defaults)
        base_params,
        
        # Vary pivot_lookback
        {**base_params, "pivot_lookback": 100},
        {**base_params, "pivot_lookback": 200},
        
        # Vary filter_len
        {**base_params, "filter_len": 2},
        {**base_params, "filter_len": 4},
        
        # Vary precision
        {**base_params, "precision": 50},
        {**base_params, "precision": 100},
        {**base_params, "precision": 150},
        
        # Vary threshold_ratio
        {**base_params, "threshold_ratio": 0.15},
        {**base_params, "threshold_ratio": 0.35},
        
        # Vary lengths
        {**base_params, "lengths": [3, 7, 15, 30]},
        {**base_params, "lengths": [7, 14, 28, 56]},
        
        # Combined variations
        {**base_params, "pivot_lookback": 100, "precision": 100},
        {**base_params, "filter_len": 2, "threshold_ratio": 0.15},
        {**base_params, "precision": 150, "threshold_ratio": 0.15}
    ]
    
    print(f"Testing {len(parameter_variations)} parameter configurations")
    
    # Analyze parameter impact
    results = analyze_parameter_impact(bars, target_zone, parameter_variations)
    
    # Sort results by distance (closest first)
    results = results.sort_values('distance')
    
    # Display results
    print("\nParameter Analysis Results (sorted by closest to target zone):")
    for i, row in results.iterrows():
        params = row['parameters']
        print(f"\nConfiguration {i+1}:")
        print(f"  pivot_lookback: {params['pivot_lookback']}")
        print(f"  filter_len: {params['filter_len']}")
        print(f"  precision: {params['precision']}")
        print(f"  threshold_ratio: {params['threshold_ratio']}")
        print(f"  lengths: {params['lengths']}")
        print(f"  Closest zone: {row['closest_zone']:.2f}")
        print(f"  Distance from target ({target_zone}): {row['distance']:.2f}")
        print(f"  Detected: {row['detected']}")
        print(f"  Number of zones: {row['num_zones']}")
    
    # Get the best configuration
    best_config = results.iloc[0]['parameters']
    print("\nBest Configuration:")
    print(json.dumps(best_config, indent=2))
    
    # Run SR zone detection with the best configuration
    best_zones = run_sr_zone_detection(bars, best_config)
    
    print("\nDetected SR Zones with Best Configuration:")
    print(best_zones[['value', 'qualifier']].to_string())
    
    # Visualize the results
    visualize_sr_zones(bars, best_zones, f"SR Zones (Target: {target_zone})")
    
    # Also test each qualifier separately
    print("\nTesting each qualifier separately with best configuration:")
    for qualifier in ["time", "linear", "volume"]:
        qualifier_zones = run_sr_zone_detection(bars, best_config, qualifier)
        print(f"\n{qualifier.capitalize()} Qualifier:")
        print(qualifier_zones[['value', 'qualifier']].to_string())
        
        # Visualize
        visualize_sr_zones(bars, qualifier_zones, f"SR Zones - {qualifier.capitalize()} (Target: {target_zone})")

if __name__ == "__main__":
    app()
