
# 1️⃣ Pivot Detection

## TradingView Function | Purpose | Python Equivalent

| TradingView Function               | Purpose                       | Python Equivalent                                |
|--------------------------------------|--------------------------------|--------------------------------------------------|
| `ta.pivothigh(high, left, right)`    | Detect local pivot highs.      | Manual pivot logic using centered comparison within a window. |
| `ta.pivotlow(low, left, right)`      | Detect local pivot lows.       | Manual pivot logic using centered comparison within a window. |

---

## ✅ Correct Python Example (Pivot High and Low Detection):

```python
import pandas as pd

def detect_pivot_high(series, left, right):
    pivots = []
    series_length = len(series)
    for i in range(left, series_length - right):
        is_pivot = True
        for j in range(1, left + 1):
            if series[i] <= series[i - j]:
                is_pivot = False
                break
        for j in range(1, right + 1):
            if series[i] <= series[i + j]:
                is_pivot = False
                break
        pivots.append(is_pivot)
    return [False]*left + pivots + [False]*right

def detect_pivot_low(series, left, right):
    pivots = []
    series_length = len(series)
    for i in range(left, series_length - right):
        is_pivot = True
        for j in range(1, left + 1):
            if series[i] >= series[i - j]:
                is_pivot = False
                break
        for j in range(1, right + 1):
            if series[i] >= series[i + j]:
                is_pivot = False
                break
        pivots.append(is_pivot)
    return [False]*left + pivots + [False]*right
```

This approach accurately replicates the TradingView `ta.pivothigh` and `ta.pivotlow` behavior, ensuring the center bar is strictly greater than (or less than) all neighbors to the left and right.

---

# 2️⃣ Math Operations

## TradingView Function | Purpose | Python Equivalent

| TradingView Function    | Purpose             | Python Equivalent    |
|-------------------------|---------------------|----------------------|
| `math.pow(x, y)`        | Power calculation   | `numpy.power(x, y)`  |
| `math.sin(x)`           | Sine function       | `numpy.sin(x)`       |
| `math.pi`               | π constant          | `numpy.pi`           |
