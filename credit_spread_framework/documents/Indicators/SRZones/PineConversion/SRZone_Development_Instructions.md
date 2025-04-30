# SRZone Script Development Instructions

## 1. Overview and Purpose

The SRZone script is designed to identify and visualize support and resistance zones on price charts. This document outlines the process for developing the SRZone script as a standalone component, separate from the overall credit spread framework. This approach allows for focused development, testing, and validation of the SRZone functionality before integration.

### Key Requirements:

- **Algorithmic Generation**: All pivots and zones MUST be generated algorithmically. No hardcoding of pivot points or zone levels is permitted.
- **Standalone Operation**: The script should function independently without dependencies on the broader credit spread framework.
- **Validation Capability**: The implementation must support thorough validation against the original TradingView Pine script.

## 2. Development Approach

The development will follow a step-by-step process, implementing each component in a modular fashion to allow for incremental testing and validation.

### Development Steps:

1. **Data Handling**

   - Implement functions to load and preprocess OHLCV data
   - Support for different timeframes and data sources

2. **Pivot Detection**

   - Implement the pivot high/low detection algorithms
   - Ensure accurate identification of local maxima and minima

3. **Signal Processing**

   - Implement the sinc filter for smoothing
   - Develop array handling utilities

4. **Zone Generation**

   - Implement support/resistance zone calculation logic
   - Score calculation for zones based on pivot strength

5. **Visualization**

   - Create plotting functions for zones and pivots
   - Implement comparison visualization for validation

6. **Validation**
   - Develop validation tools to compare with TradingView output
   - Document validation results

### Implementation Guidelines:

- Each component should be implemented as a separate module or function
- Use clear, descriptive variable and function names
- Include comprehensive docstrings and comments
- Implement proper error handling and edge cases
- Ensure all calculations are performed algorithmically with no hardcoded values

## 3. File Structure

```
credit_spread_framework/documents/Indicators/SRZones/PineConversion/
├── SRZone_Development_Instructions.md (this file)
├── Code_Overview.md
├── TradingView_to_Python_Function_Mapping.md
├── Pivot_HighLow_Detection.md
├── Validation_Plan_Python_vs_Pine.md
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

## 4. Implementation Details

### 4.1 Data Handling

- Implement functions to read CSV data from TradingView exports
- Support pandas DataFrame operations for data manipulation
- Include resampling capabilities for different timeframes

```python
# Example structure (not complete implementation)
def load_ohlcv_data(file_path):
    """
    Load OHLCV data from CSV file.

    Parameters:
    -----------
    file_path : str
        Path to the CSV file containing OHLCV data

    Returns:
    --------
    pandas.DataFrame
        DataFrame with datetime index and OHLCV columns
    """
    # Implementation here
```

### 4.2 Pivot Detection

Based on the Pivot_HighLow_Detection.md document, implement the pivot detection logic:

```python
def detect_pivot_high(series, left, right):
    """
    Detect pivot highs in a price series.

    A pivot high is a point where the price is higher than all points
    within 'left' bars to the left and 'right' bars to the right.

    Parameters:
    -----------
    series : array-like
        Price series (typically high prices)
    left : int
        Number of bars to check on the left
    right : int
        Number of bars to check on the right

    Returns:
    --------
    list of bool
        Boolean array where True indicates a pivot high
    """
    # Implementation based on Pivot_HighLow_Detection.md
```

### 4.3 Signal Processing

Implement the sinc filter and other signal processing functions:

```python
def sinc(x, bandwidth):
    """
    Calculate the sinc function value.

    Parameters:
    -----------
    x : float
        Input value
    bandwidth : float
        Bandwidth parameter

    Returns:
    --------
    float
        Sinc function value
    """
    # Implementation based on Pine script

def sinc_filter(values, length):
    """
    Apply sinc filter to smooth values.

    Parameters:
    -----------
    values : array-like
        Input values to smooth
    length : float
        Filter length parameter

    Returns:
    --------
    array-like
        Smoothed values
    """
    # Implementation based on Pine script
```

### 4.4 Zone Generation

Implement the support and resistance zone generation logic:

```python
def generate_zones(pivots_high, pivots_low, prices, parameters):
    """
    Generate support and resistance zones based on pivot points.

    Parameters:
    -----------
    pivots_high : array-like
        Boolean array indicating pivot highs
    pivots_low : array-like
        Boolean array indicating pivot lows
    prices : pandas.DataFrame
        OHLCV price data
    parameters : dict
        Configuration parameters

    Returns:
    --------
    dict
        Dictionary containing support and resistance zones
    """
    # Implementation based on Pine script
```

### 4.5 Visualization

Implement visualization functions for zones and pivots:

```python
def plot_zones(prices, zones, pivots_high, pivots_low, filename=None):
    """
    Plot price chart with support/resistance zones and pivots.

    Parameters:
    -----------
    prices : pandas.DataFrame
        OHLCV price data
    zones : dict
        Support and resistance zones
    pivots_high : array-like
        Boolean array indicating pivot highs
    pivots_low : array-like
        Boolean array indicating pivot lows
    filename : str, optional
        If provided, save the plot to this file

    Returns:
    --------
    matplotlib.figure.Figure
        The generated figure
    """
    # Implementation using matplotlib or plotly
```

## 5. Validation Methodology

Follow the approach outlined in Validation_Plan_Python_vs_Pine.md:

### 5.1 Data Preparation

- Use the same historical data for both TradingView and Python implementation
- Export TradingView results for comparison

### 5.2 Visual Validation

- Generate charts with both implementations
- Compare zone placements, pivot points, and other visual elements

### 5.3 Numerical Validation

- Compare pivot detection results bar by bar
- Compare zone levels and scores
- Document any discrepancies

### 5.4 Validation Reporting

Create a validation report that includes:

- Screenshots of both implementations
- Tables comparing numerical results
- Analysis of any differences
- Recommendations for adjustments

## 6. References

### 6.1 Documentation

- [Code_Overview.md](Code_Overview.md): Overview of the Pine script implementation
- [TradingView_to_Python_Function_Mapping.md](TradingView_to_Python_Function_Mapping.md): Mapping between TradingView and Python functions
- [Pivot_HighLow_Detection.md](Pivot_HighLow_Detection.md): Details on pivot detection implementation
- [Validation_Plan_Python_vs_Pine.md](Validation_Plan_Python_vs_Pine.md): Plan for validating the Python implementation

### 6.2 Pine Script Reference

- [03-Dynamic_SR_Annotated_With_Comments.pine](03-Dynamic_SR_Annotated_With_Comments.pine): Original Pine script with comments

### 6.3 Validation Data

- Sample data in the validation folder
- TradingView screenshots for comparison

## 7. Development Timeline

1. **Data Handling & Pivot Detection**: Implement the core functionality for loading data and detecting pivots
2. **Signal Processing & Zone Generation**: Implement the signal processing and zone generation logic
3. **Visualization**: Create visualization tools for the zones and pivots
4. **Validation**: Perform thorough validation against TradingView results
5. **Documentation**: Complete documentation of the implementation and validation results

## 8. Conclusion

This document provides a comprehensive guide for developing the SRZone script as a standalone component. By following this step-by-step approach and adhering to the requirement of algorithmic generation (no hardcoding), the implementation will be robust, maintainable, and accurately reflect the behavior of the original TradingView Pine script.
