# SRZone Development Instructions

This document outlines the step-by-step process for developing the SRZone script independently from the overall credit spread framework. The goal is to create a standalone implementation that can be validated against the original TradingView Pine script.

## Project Structure

All development will be contained within the following directory structure:

```
Pine Conversion/
├── srzone/                  # Python package for SRZone implementation
│   ├── __init__.py
│   ├── pivot_detection.py   # Pivot high/low detection logic
│   ├── signal_processing.py # Signal processing utilities (sinc filter, peak detection)
│   ├── zone_generation.py   # Support/resistance zone generation
│   └── data_loader.py       # Data loading and preprocessing
├── validation/              # Validation data and results
│   ├── images/              # Screenshots from TradingView for comparison
│   └── csv/                 # CSV data for testing
└── tests/                   # Unit and integration tests
```

## Development Approach

We'll follow a modular approach, breaking down the SRZone implementation into distinct components:

1. **Data Loading**: Functions to load and preprocess OHLCV data
2. **Pivot Detection**: Algorithms to detect pivot highs and lows
3. **Signal Processing**: Implementation of the sinc filter and peak detection
4. **Zone Generation**: Logic to generate support and resistance zones

## Validation Strategy

As outlined in `Validation_Plan_Python_vs_Pine.md`, we'll validate our implementation by:

1. Using the same input data in both TradingView and our Python implementation
2. Comparing the outputs at each stage of the process:
   - Pivot points detected
   - Filtered score distributions
   - Peak detection results
   - Final zone placements

The enhanced debug version of the Pine script (`03-Dynamic_SR_With_Debug_Labels.pine`) will provide detailed information about the peak detection process, which is crucial for ensuring our Python implementation matches TradingView's behavior.

## Key Components

### Pivot High/Low Detection

As described in `Pivot_HighLow_Detection.md`, our implementation uses a custom approach to detect pivot points. The key parameters are:

- Multiple lookback periods (5, 10, 20, 50)
- Configurable inclusion of each pivot strength
- Support for both pivot highs and pivot lows

### Signal Processing

The signal processing module includes:

- **Sinc Filter**: For smoothing the distribution of pivot points
- **Peak Detection**: For identifying significant peaks in the filtered distribution

The peak detection algorithm is particularly important, as it directly determines where zones are placed. The TradingView debug script now includes a table view of all detected peaks, which will help us align our Python implementation.

### Zone Generation

The zone generation process:

1. Collects pivot points with their weights
2. Creates a distribution of scores across the price range
3. Applies the sinc filter for smoothing
4. Detects peaks in the smoothed distribution
5. Converts peaks to support/resistance zones

## Implementation Steps

1. **Set up the basic package structure**
2. **Implement the data loading module**
3. **Implement the pivot detection module**
4. **Implement the signal processing module**
5. **Implement the zone generation module**
6. **Create validation scripts to compare with TradingView**
7. **Refine the implementation based on validation results**

## TradingView to Python Function Mapping

Refer to `TradingView_to_Python_Function_Mapping.md` for detailed mappings between TradingView Pine script functions and their Python equivalents.

## Validation Data

The `/validation` folder contains:

- `SP_SPX, 3_3dc75.csv`: 3-minute SPX data for testing
- `2025_04_03_SPX_03minute_Linear.png`: Screenshot of TradingView showing expected output

## Notes on Peak Detection

The peak detection algorithm is the most critical component for ensuring our zones match TradingView's output. The key aspects to focus on:

1. How peaks are identified in the filtered score distribution
2. How plateaus (flat areas) are handled
3. The exact scaling and thresholding used

The debug table in the enhanced Pine script shows:

- Peak number
- Array index (position in the filtered scores array)
- Score value at that peak
- Price value (which becomes the zone price)

This information is crucial for validating our Python implementation.
