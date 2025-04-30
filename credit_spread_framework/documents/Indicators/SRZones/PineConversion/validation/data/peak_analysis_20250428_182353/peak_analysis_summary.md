# Peak Detection Analysis Summary

## Peak Counts by Timeframe

| Timeframe | Number of Peaks |
|-----------|----------------|
| 1m | 6 |
| 3m | 5 |
| 15m | 2 |
| 1h | 3 |
| 1d | 3 |
| output | 5 |

## Score Statistics by Timeframe

| Timeframe | Min Score | Max Score | Mean Score | Median Score | Std Dev |
|-----------|-----------|-----------|------------|--------------|--------|
| 1m | 0.25 | 3.94 | 1.80 | 1.24 | 1.55 |
| 3m | 1.65 | 5.46 | 3.32 | 2.79 | 1.81 |
| 15m | 3.50 | 4.05 | 3.77 | 3.77 | 0.39 |
| 1h | 3.87 | 5.25 | 4.34 | 3.88 | 0.79 |
| 1d | 2.40 | 3.76 | 3.17 | 3.36 | 0.70 |
| output | 1.65 | 5.46 | 3.32 | 2.79 | 1.81 |

## Price Ranges by Timeframe

| Timeframe | Min Price | Max Price | Price Range |
|-----------|-----------|-----------|-------------|
| 1m | 5444.55 | 5666.60 | 222.04 |
| 3m | 5418.92 | 5692.96 | 274.04 |
| 15m | 5663.19 | 5780.07 | 116.89 |
| 1h | 5503.70 | 6132.46 | 628.76 |
| 1d | 5184.88 | 6119.12 | 934.24 |
| output | 5418.92 | 5692.96 | 274.04 |

## Analysis Observations

1. The number of peaks detected varies by timeframe, with 1m having the most peaks (6) and 15m having the fewest (2).
2. The score distribution shows how the algorithm assigns importance to different price levels across timeframes.
3. The price distribution shows the range of prices where support and resistance zones are detected.

## Conclusion

The peak detection algorithm behaves consistently across different timeframes, adapting to the price patterns and volatility characteristics of each timeframe. The number of peaks and their distribution vary by timeframe, which is expected as different timeframes capture different market dynamics.
