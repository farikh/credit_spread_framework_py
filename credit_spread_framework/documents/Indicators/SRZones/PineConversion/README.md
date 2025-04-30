# SRZone - Support and Resistance Zone Detection

This package provides a Python implementation of the TradingView Pine Script for detecting and visualizing support and resistance zones based on pivot points in price data.

## Overview

The SRZone package is a standalone implementation of the support and resistance zone detection algorithm originally written in TradingView Pine Script. It identifies pivot points in price data and uses them to generate support and resistance zones, which can be visualized on price charts.

Key features:

- Pivot high and low detection with configurable strength parameters
- Support and resistance zone generation with customizable settings
- Signal processing with sinc filter for smoothing
- Visualization of zones and pivots on price charts
- Validation tools for comparing with TradingView Pine Script results

## Directory Structure

```
PineConversion/
├── README.md (this file)
├── SRZone_Development_Instructions.md
├── Code_Overview.md
├── TradingView_to_Python_Function_Mapping.md
├── Pivot_HighLow_Detection.md
├── Validation_Plan_Python_vs_Pine.md
├── srzone_example.py
├── srzone/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── pivot_detection.py
│   ├── signal_processing.py
│   ├── zone_generation.py
│   ├── visualization.py
│   └── validation.py
└── validation/
    ├── images/
    │   └── (validation screenshots and comparison charts)
    └── data/
        └── (CSV files and validation output data)
```

## Installation

The package is designed to be used directly from the repository. No installation is required.

## Dependencies

- pandas
- numpy
- matplotlib

## Usage

### Basic Usage

```python
import pandas as pd
from srzone.data_loader import prepare_data_for_analysis
from srzone.pivot_detection import detect_pivots
from srzone.zone_generation import generate_zones
from srzone.visualization import plot_srzone_analysis

# Load and prepare data
df = prepare_data_for_analysis('path/to/ohlcv_data.csv')

# Detect pivots
pivot_results = detect_pivots(df)

# Generate zones
zone_results = generate_zones(
    df,
    pivot_results['pivot_high_values'],
    [1] * len(pivot_results['pivot_high_values']),  # Default weights
    pivot_results['pivot_low_values'],
    [1] * len(pivot_results['pivot_low_values']),  # Default weights
    {
        'weight_style': 'Linear',
        'pivot_lookback': 50,
        'filter': 3,
        'precision': 75,
        'auto_precision': True,
        'include_ph': True,
        'include_pl': True,
        'scale': 30
    }
)

# Visualize results
plot_srzone_analysis(df, pivot_results, zone_results, {}, 'srzone_output.png')
```

### Example Script

For a complete example, see `srzone_example.py`:

```python
python srzone_example.py
```

This script demonstrates how to use the srzone package to detect support and resistance zones in price data and visualize the results.

## Configuration Parameters

The SRZone algorithm can be configured with various parameters:

- `weight_style`: Weighting style for pivots ('Linear', 'Time', or 'Volume')
- `pivot_lookback`: Number of pivots to consider
- `filter`: Smoothing filter length
- `precision`: Number of bins for zone detection
- `auto_precision`: Whether to auto-calculate precision
- `include_ph`: Whether to include pivot highs
- `include_pl`: Whether to include pivot lows
- `scale`: Scale for visualization
- `strength_params`: List of dictionaries with pivot strength parameters

Example configuration:

```python
params = {
    'weight_style': 'Linear',
    'pivot_lookback': 50,
    'filter': 3,
    'precision': 75,
    'auto_precision': True,
    'include_ph': True,
    'include_pl': True,
    'scale': 30,
    'strength_params': [
        {'length': 5, 'include': True},
        {'length': 10, 'include': True},
        {'length': 20, 'include': True},
        {'length': 50, 'include': True}
    ]
}
```

## Validation

The package includes tools for validating the Python implementation against the TradingView Pine Script implementation:

```python
from srzone.validation import validate_implementation

validation_results = validate_implementation(
    'path/to/ohlcv_data.csv',
    'path/to/tradingview_export.csv',
    'path/to/tradingview_image.png'
)
```

## Documentation

For more detailed information, refer to the following documentation files:

- `SRZone_Development_Instructions.md`: Step-by-step instructions for developing the SRZone script
- `Code_Overview.md`: Overview of the original Pine script implementation
- `TradingView_to_Python_Function_Mapping.md`: Mapping between TradingView and Python functions
- `Pivot_HighLow_Detection.md`: Details on pivot detection implementation
- `Validation_Plan_Python_vs_Pine.md`: Plan for validating the Python implementation

## License

This project is licensed under the same terms as the original Pine Script.

## Acknowledgements

This implementation is based on the TradingView Pine Script "Dynamic Support/Resistance Zones" by ChartPrime.
