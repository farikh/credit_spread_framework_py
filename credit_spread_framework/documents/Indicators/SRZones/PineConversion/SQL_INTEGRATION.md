# SQL Database Integration for SRZone

This document explains how to use the SQL database integration with the SRZone package. The integration allows you to fetch OHLCV data directly from the credit spread framework's SQL database instead of using CSV files.

## Overview

The SRZone package now supports two data sources:

1. **CSV Files**: The original data source, using CSV files exported from TradingView.
2. **SQL Database**: The new data source, using the credit spread framework's SQL database.

The SQL integration ensures that the SRZone algorithm produces the same results regardless of the data source, as long as the data is the same. This is achieved by:

1. Limiting the number of bars to 4000 (matching the Pine script's `max_bars_back` parameter)
2. Using the same pivot detection and zone generation algorithms
3. Standardizing column names and data formats

## Usage

### Basic Usage

To use the SQL database as a data source, you need to specify the `source_type` parameter as `'sql'` and provide the `timeframe` parameter:

```python
from srzone.data_loader import prepare_data_for_analysis

# Load data from SQL database
df = prepare_data_for_analysis(
    source_type='sql',
    timeframe='1h',  # Must be one of: '1m', '3m', '15m', '1h', '1d'
    start_date='2025-03-01',  # Optional
    end_date='2025-04-03',    # Optional
    max_bars=4000             # Optional, default is 4000
)

# Use the data for SRZone analysis
# ...
```

### Example Script

The `sql_example.py` script demonstrates how to use the SQL database integration:

```bash
# Run SRZone analysis with SQL database for 1-hour timeframe
python sql_example.py --timeframe 1h

# Run SRZone analysis with SQL database for 1-hour timeframe with specific date range
python sql_example.py --timeframe 1h --start 2025-03-01 --end 2025-04-03

# Run validation against TradingView image
python sql_example.py --timeframe 1h --validate --image validation/images/2025_04_03_SPX_01hour_Linear.png
```

### Validation

You can run validation for all timeframes using the SQL database as the data source:

```bash
# Run validation for all timeframes using SQL database
python validate_all_timeframes.py --source sql

# Run validation for all timeframes using SQL database with specific date
python validate_all_timeframes.py --source sql --date 2025-04-03
```

## Parameters

### Data Loading Parameters

When using the SQL database as a data source, you can specify the following parameters:

- `source_type`: Must be `'sql'` to use the SQL database.
- `timeframe`: The timeframe for the data. Must be one of: `'1m'`, `'3m'`, `'15m'`, `'1h'`, `'1d'`.
- `start_date`: The start date for the data range. Optional.
- `end_date`: The end date for the data range. Optional.
- `max_bars`: The maximum number of bars to return. Default is 4000, matching the Pine script's `max_bars_back` parameter.

### SQL Database Tables

The SQL database integration uses the following tables:

- `spx_ohlcv_1m`: 1-minute OHLCV data
- `spx_ohlcv_3m`: 3-minute OHLCV data
- `spx_ohlcv_15m`: 15-minute OHLCV data
- `spx_ohlcv_1h`: 1-hour OHLCV data
- `spx_ohlcv_1d`: 1-day OHLCV data

## Technical Details

### Data Standardization

The SQL database integration standardizes the column names to match the CSV format:

- `open_price` → `open`
- `close_price` → `close`
- `spy_volume` → `volume`

### Bar Limit

The SQL database integration limits the number of bars to 4000 by default, matching the Pine script's `max_bars_back` parameter. This ensures that the SRZone algorithm produces the same results regardless of the data source.

If you need to use a different number of bars, you can specify the `max_bars` parameter:

```python
df = prepare_data_for_analysis(
    source_type='sql',
    timeframe='1h',
    max_bars=2000  # Use 2000 bars instead of the default 4000
)
```

### Date Range

If you don't specify a date range, the SQL database integration will use the current date as the end date and calculate a reasonable start date based on the timeframe:

- `1m`, `3m`, `15m`: 5 trading days before the end date
- `1h`: 10 trading days before the end date
- `1d`: 60 days (about 2 months) before the end date

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues, check the following:

1. Make sure the `.env` file contains the correct SQL Server connection string.
2. Make sure the SQL Server is running and accessible.
3. Make sure you have the necessary permissions to access the database.

### Data Quality Issues

If you encounter data quality issues, check the following:

1. Make sure the SQL database contains data for the specified timeframe and date range.
2. Make sure the data is properly formatted (OHLCV data with timestamp).
3. Try using a different date range or timeframe.

## Conclusion

The SQL database integration provides a convenient way to use the SRZone package with the credit spread framework's SQL database. It ensures that the SRZone algorithm produces the same results regardless of the data source, as long as the data is the same.
