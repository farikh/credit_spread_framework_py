# SRZone Package

This package provides a Python implementation of the TradingView Pine script for Support and Resistance Zones detection. It includes tools for detecting pivot points, generating support and resistance zones, and validating the implementation against TradingView.

## Features

- **Pivot Detection**: Detect pivot highs and lows in price data
- **Zone Generation**: Generate support and resistance zones based on pivot points
- **Validation**: Validate the Python implementation against TradingView Pine script
- **Peak Detection Comparison**: Compare peak detection results between Python and TradingView
- **Visualization**: Create visualizations of support and resistance zones
- **SQL Database Integration**: Load data directly from SQL database instead of CSV files

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage with CSV Files

```python
from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis

# Load and prepare data from CSV file
df = prepare_data_for_analysis(file_path="path/to/data.csv", source_type="csv")

# Detect pivots
pivot_results = detect_pivots(df)

# Generate zones
zone_results = generate_zones(
    df,
    pivot_results['pivot_high_values'],
    [1] * len(pivot_results['pivot_high_values']),  # Default weights
    pivot_results['pivot_low_values'],
    [1] * len(pivot_results['pivot_low_values']),  # Default weights
    params
)

# Create visualization
plot_srzone_analysis(df, pivot_results, zone_results, params, "output.png")
```

### Basic Usage with SQL Database

```python
from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis

# Load and prepare data from SQL database
df = prepare_data_for_analysis(
    source_type="sql",
    timeframe="1h",  # Must be one of: '1m', '3m', '15m', '1h', '1d'
    start_date="2025-03-01",  # Optional
    end_date="2025-04-03",    # Optional
    max_bars=4000             # Optional, default is 4000
)

# Detect pivots
pivot_results = detect_pivots(df)

# Generate zones
zone_results = generate_zones(
    df,
    pivot_results['pivot_high_values'],
    [1] * len(pivot_results['pivot_high_values']),  # Default weights
    pivot_results['pivot_low_values'],
    [1] * len(pivot_results['pivot_low_values']),  # Default weights
    params
)

# Create visualization
plot_srzone_analysis(df, pivot_results, zone_results, params, "output.png")
```

### Validation Against TradingView with CSV Files

```python
from srzone.validation import validate_implementation

# Run validation with CSV file
validation_results = validate_implementation(
    data_file="path/to/data.csv",
    tradingview_export="path/to/tradingview_export.csv",  # Optional
    tradingview_image="path/to/tradingview_image.png",    # Optional
    output_dir="validation_output",
    source_type="csv"
)

# Access validation results
print(validation_results['comparison_results']['summary'])
```

### Validation Against TradingView with SQL Database

```python
from srzone.validation import validate_implementation

# Run validation with SQL database
validation_results = validate_implementation(
    tradingview_image="path/to/tradingview_image.png",  # Optional
    output_dir="validation_output",
    source_type="sql",
    timeframe="1h",  # Must be one of: '1m', '3m', '15m', '1h', '1d'
    start_date="2025-03-01",  # Optional
    end_date="2025-04-03",    # Optional
    max_bars=4000             # Optional, default is 4000
)

# Access validation results
print(validation_results['comparison_results']['summary'])
```

### Peak Detection Comparison

The package includes tools for comparing peak detection results between the Python implementation and TradingView Pine script. This is useful for debugging and ensuring that the Python implementation matches TradingView's behavior.

#### Exporting Peak Detection Data from TradingView

1. In TradingView, use the enhanced debug script (`03-Dynamic_SR_With_Debug_Labels.pine`) which includes a table view of peak detection data
2. Take a screenshot or manually copy the table data to a CSV file with columns: `Peak #`, `Array Index`, `Score`, `Price`

#### Comparing Peak Detection Data

```python
from srzone.peak_comparison import run_peak_comparison

# Run peak comparison
comparison_results = run_peak_comparison(
    "path/to/python_peaks.csv",
    "path/to/tradingview_peaks.csv",
    output_dir="peak_comparison_output"
)

# Access comparison results
print(comparison_results['comparison_results']['summary'])
```

## Package Structure

- **data_loader.py**: Functions for loading and preparing OHLCV data from CSV files or SQL database
- **pivot_detection.py**: Functions for detecting pivot highs and lows
- **signal_processing.py**: Signal processing utilities (sinc filter, peak detection)
- **zone_generation.py**: Functions for generating support and resistance zones
- **validation.py**: Functions for validating the implementation against TradingView
- **peak_detection_export.py**: Functions for exporting peak detection data
- **peak_comparison.py**: Functions for comparing peak detection results
- **visualization.py**: Functions for creating visualizations

## Peak Detection Comparison

The peak detection algorithm is a critical component of the SRZone implementation. It determines where support and resistance zones are placed based on the distribution of pivot points. The TradingView Pine script and Python implementation should produce similar results, but there may be slight differences due to implementation details.

The `peak_detection_export.py` module provides functions for exporting peak detection data to a CSV file, which can be compared with TradingView's peak detection data. The `peak_comparison.py` module provides functions for comparing the two datasets and visualizing the differences.

### Peak Detection Data Format

The peak detection data is exported as a CSV file with the following columns:

- **Peak #**: Index of the peak
- **Array Index**: Position in the filtered scores array
- **Score**: Value at that position
- **Price**: Calculated price level for that peak

### Comparison Metrics

The peak comparison module calculates the following metrics:

- **Matching peaks**: Number of peaks that match between Python and TradingView
- **Python-only peaks**: Number of peaks detected by Python but not by TradingView
- **TradingView-only peaks**: Number of peaks detected by TradingView but not by Python
- **Match percentage**: Percentage of matching peaks

### Visualization

The peak comparison module creates a visualization comparing the peak detection results:

- Top plot: Python peak detection
- Bottom plot: TradingView peak detection

This visualization helps identify differences between the two implementations and can be used to debug and improve the Python implementation.

## Example Scripts

- **srzone_example.py**: Complete example of how to use the package with CSV files
- **sql_example.py**: Complete example of how to use the package with SQL database
- **validate_all_timeframes.py**: Example of how to run validation for all timeframes

## SQL Database Integration

The package now supports loading data directly from the credit spread framework's SQL database instead of using CSV files. This allows you to use the SRZone package with real-time data from the database.

For detailed information about the SQL database integration, see the [SQL_INTEGRATION.md](../SQL_INTEGRATION.md) file.

### SQL Database Tables

The SQL database integration uses the following tables:

- `spx_ohlcv_1m`: 1-minute OHLCV data
- `spx_ohlcv_3m`: 3-minute OHLCV data
- `spx_ohlcv_15m`: 15-minute OHLCV data
- `spx_ohlcv_1h`: 1-hour OHLCV data
- `spx_ohlcv_1d`: 1-day OHLCV data

### SQL Database Parameters

When using the SQL database as a data source, you can specify the following parameters:

- `source_type`: Must be `'sql'` to use the SQL database
- `timeframe`: The timeframe for the data (e.g., `'1m'`, `'3m'`, `'15m'`, `'1h'`, `'1d'`)
- `start_date`: The start date for the data range (optional)
- `end_date`: The end date for the data range (optional)
- `max_bars`: The maximum number of bars to return (default: 4000)
