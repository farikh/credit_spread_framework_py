# SR Zones Implementation

This document describes the implementation of Support/Resistance (SR) zones in the Credit Spread Trading Software.

## Overview

The SR zone indicator is designed to identify key price levels where the market has shown significant support or resistance. These levels are calculated using pivot points and can be weighted in different ways:

- **Time**: Newer pivots have more weight
- **Linear**: All pivots have equal weight
- **Volume**: Pivots with higher volume have more weight

The implementation is based on the TradingView "Dynamic Support/Resistance Zones" indicator by ChartPrime.

## Key Features

1. **Multiple SR Zones**: The indicator detects multiple SR zones (up to 3 per weighting method), not just the strongest one.
2. **Historical Persistence**: SR zones persist over time until they are invalidated by price action.
3. **Invalidation Logic**: SR zones are invalidated when:
   - Price breaks through the zone and moves a significant distance beyond it
   - The zone is too far from the current price range

## Usage

### Processing SR Zones

To process SR zones for a specific date range:

```bash
python process_persistent_srzones.py --start 2025-04-03 --end 2025-04-03 --timeframe 1d
```

Options:

- `--start`: Start date (YYYY-MM-DD)
- `--end`: End date (YYYY-MM-DD)
- `--timeframe`: Timeframe to process (default: 1d)
- `--qualifier`: Optional qualifier to filter by (time, linear, volume)
- `--history-days`: Number of days of historical data to load for pivot detection (default: 200)

### Querying SR Zones

To query SR zones for a specific date:

```bash
python query_srzones.py --date 2025-04-03
```

### Cleaning Up Duplicate SR Zones

If you have duplicate SR zones in the database, you can clean them up with:

```bash
python clean_duplicate_sr_zones.py
```

## Implementation Details

### SR Zone Calculation

The SR zone calculation involves the following steps:

1. **Pivot Detection**: Identify pivot highs and lows in the price data
2. **Histogram Creation**: Create a histogram of pivot levels, weighted by time, volume, or equally
3. **Peak Detection**: Find significant peaks in the histogram
4. **Zone Creation**: Create SR zones at the peak levels

### Database Storage

SR zones are stored in the `indicator_values` table with the following key fields:

- `Value`: The price level of the SR zone
- `Qualifier`: The weighting method (time, linear, volume)
- `TimestampStart`: When the SR zone was first identified
- `TimestampEnd`: When the SR zone was invalidated (NULL if still active)
- `AuxValue`: Additional information about the SR zone (e.g., strength)

## Troubleshooting

If you encounter issues with the SR zones:

1. **Missing SR Zones**: Make sure you have enough historical data (at least 200 days) for pivot detection
2. **Duplicate SR Zones**: Run `clean_duplicate_sr_zones.py` to remove duplicates
3. **Incorrect SR Zones**: Check the parameters in the database (IndicatorId 2)

## Parameters

The SR zone indicator uses the following parameters:

- `pivot_lookback`: Maximum number of pivots to consider (default: 50)
- `filter_len`: Smoothing filter size (default: 3)
- `precision`: Number of histogram bins (default: 75)
- `threshold_ratio`: Relative strength needed for a level to be considered SR (default: 0.25)
- `include_ph`: Include pivot highs (default: true)
- `include_pl`: Include pivot lows (default: true)
- `lengths`: Pivot detection window sizes (default: [5, 10, 20, 50])

These parameters can be updated using the `update_srzone_params.py` script.
