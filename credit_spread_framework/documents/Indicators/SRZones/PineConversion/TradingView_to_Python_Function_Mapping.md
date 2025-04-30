# 🛠️ TradingView to Python Function Mapping (with Equivalents)

## 1️⃣ Pivot Detection

| TradingView Function              | Purpose                   | Python Equivalent                                                           |
| --------------------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `ta.pivothigh(high, left, right)` | Detect local pivot highs. | Rolling window max + comparison logic using `pandas.Series.rolling().max()` |
| `ta.pivotlow(low, left, right)`   | Detect local pivot lows.  | Rolling window min + comparison logic using `pandas.Series.rolling().min()` |

### Example in Python (Pivot High):

```python
import pandas as pd

def detect_pivot_high(series, left, right):
    rolling_high = series.rolling(window=left + right + 1, center=True).max()
    return (series == rolling_high)
```

---

## 2️⃣ Math Operations

| TradingView Function | Purpose            | Python Equivalent   |
| -------------------- | ------------------ | ------------------- |
| `math.pow(x, y)`     | Power calculation. | `numpy.power(x, y)` |
| `math.sin(x)`        | Sine function.     | `numpy.sin(x)`      |
| `math.pi`            | π constant.        | `numpy.pi`          |

✅ Direct match with NumPy.

---

## 3️⃣ Signal Smoothing (Sinc Filter)

| TradingView Logic            | Purpose                          | Python Equivalent                             |
| ---------------------------- | -------------------------------- | --------------------------------------------- |
| `sinc()` and `sinc_filter()` | Signal smoothing/filter weights. | `numpy.sinc()` or manual sinc implementation. |

### Python Example:

```python
import numpy as np

def sinc_filter(values, length):
    result = np.zeros_like(values)
    for i in range(len(values)):
        weights = np.sinc((i - np.arange(len(values))) / (length + 1))
        weighted_sum = np.sum(values * weights)
        result[i] = weighted_sum / np.sum(weights)
    return result
```

---

## 4️⃣ Array Handling

| TradingView Array Functions      | Purpose           | Python Equivalent                  |
| -------------------------------- | ----------------- | ---------------------------------- |
| `array.new<float>(size)`         | Create array.     | `numpy.zeros(size)` or Python list |
| `array.size()`                   | Get array length. | `len(array)`                       |
| `array.get(array, index)`        | Access element.   | `array[index]`                     |
| `array.set(array, index, value)` | Set element.      | `array[index] = value`             |
| `array.clear()`                  | Clear array.      | `array.clear()` or `array = []`    |

✅ Python lists or NumPy arrays fully cover this.

---

## 5️⃣ User Inputs (Configurable Parameters)

| TradingView Input | Purpose            | Python Equivalent                                                   |
| ----------------- | ------------------ | ------------------------------------------------------------------- |
| `input.int()`     | Integer parameter. | Function arguments, config dictionary, or CLI arguments (argparse). |
| `input.bool()`    | Boolean flag.      | Same as above.                                                      |
| `input.color()`   | Color selection.   | RGB/HEX values as arguments or config.                              |

---

## 6️⃣ Drawing / Visualization

| TradingView Function                              | Purpose              | Python Equivalent                                                   |
| ------------------------------------------------- | -------------------- | ------------------------------------------------------------------- |
| `line.new()`                                      | Draw line.           | `matplotlib.pyplot.plot()` or `axhline()` / `axvline()`             |
| `box.new()`                                       | Draw rectangle/zone. | `matplotlib.patches.Rectangle()`                                    |
| `label.new()`                                     | Add text label.      | `plt.text()`                                                        |
| `line.delete()`, `box.delete()`, `label.delete()` | Remove visuals.      | Not needed in static plots; dynamic update logic in Plotly / Bokeh. |

### Example (Support/Resistance Zone Box in Matplotlib):

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots()
ax.add_patch(patches.Rectangle((x1, y1), width=(x2 - x1), height=(y2 - y1), color='green', alpha=0.3))
plt.show()
```

---

## 7️⃣ Color Adjustments / Transparency

| TradingView Function             | Purpose              | Python Equivalent                                           |
| -------------------------------- | -------------------- | ----------------------------------------------------------- |
| `color.new(color, transparency)` | Adjust transparency. | `alpha` argument in plotting functions (e.g., `alpha=0.3`). |

---

## 8️⃣ Bar Control / Timing Logic

| TradingView Logic | Purpose            | Python Equivalent            |
| ----------------- | ------------------ | ---------------------------- |
| `barstate.islast` | Check if last bar. | `if index == len(data) - 1:` |
| `na`              | Null/missing data. | `numpy.nan` or `pandas.NA`   |

---

## ✅ Summary of Mapping Coverage

| Category               | TradingView               | Python                          | Notes                                         |
| ---------------------- | ------------------------- | ------------------------------- | --------------------------------------------- |
| Pivot Detection        | `ta.pivothigh/low`        | `rolling().max()/min()`         | Requires manual pivot condition checking.     |
| Math / Smoothing       | `math.pow`, `sinc_filter` | `numpy` functions               | Sinc smoothing directly portable.             |
| Array Handling         | `array.*`                 | `list` / `numpy.array`          | Full equivalence.                             |
| User Inputs            | `input.*`                 | Args / Config / CLI             | Full equivalence.                             |
| Drawing                | `line.new`, `box.new`     | `matplotlib`, `plotly`, `bokeh` | Slight learning curve for interactive charts. |
| Colors / Transparency  | `color.new()`             | `alpha`, RGB / HEX              | Fully supported.                              |
| Cleanup / Control Flow | `barstate.islast`         | Index-based control flow        | Direct replacement.                           |
