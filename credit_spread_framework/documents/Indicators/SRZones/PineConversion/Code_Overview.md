# 🧭 1. Pivot Detection (Highs & Lows)

## Function | Purpose | Example Usage

| Function                          | Purpose                                                                                 | Example Usage                                         |
| --------------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `ta.pivothigh(high, left, right)` | Finds local pivot highs where the high is greater than left and right surrounding bars. | `pivot_high = ta.pivothigh(high, strength, strength)` |
| `ta.pivotlow(low, left, right)`   | Finds local pivot lows where the low is lower than left and right surrounding bars.     | `pivot_low = ta.pivotlow(low, strength, strength)`    |

**Note:** This is central to how the zones are detected. These functions return the pivot value only at the pivot bar; otherwise, they return `na`.

---

# 🔢 2. Math and Smoothing Logic

| Function         | Purpose                              | Example Usage                       |
| ---------------- | ------------------------------------ | ----------------------------------- |
| `math.pow(x, y)` | Calculates `x` to the power of `y`.  | `sq(source) => math.pow(source, 2)` |
| `math.sin(x)`    | Sine function (used in sinc filter). | Part of sinc calculation.           |
| `math.pi`        | π constant.                          | Used in the sinc denominator.       |

---

# 🗃️ 3. Array Operations

| Function                         | Purpose                          | Example Usage                                 |
| -------------------------------- | -------------------------------- | --------------------------------------------- |
| `array.new<float>(size)`         | Creates a new float array.       | `estimate_array = array.new<float>(src_size)` |
| `array.size(array)`              | Gets the array length.           | `src_size = array.size(source)`               |
| `array.get(array, index)`        | Retrieves a value by index.      | `array.get(source, j)`                        |
| `array.set(array, index, value)` | Sets a value at the given index. | `array.set(estimate_array, i, result)`        |
| `array.clear(array)`             | Clears the array contents.       | `array.clear(srLines)`                        |

---

# 🎛️ 4. Input Handling (User Configuration)

| Function        | Purpose         | Example Usage                                                            |
| --------------- | --------------- | ------------------------------------------------------------------------ |
| `input.int()`   | Integer input.  | `strength = input.int(title="Pivot Strength", defval=3)`                 |
| `input.bool()`  | Boolean toggle. | `show_support = input.bool(title="Show Support Zones", defval=true)`     |
| `input.color()` | Color picker.   | `support_color = input.color(title="Support Color", defval=color.green)` |

---

# 🎨 5. Chart Object Drawing (Lines, Boxes, Labels)

| Function         | Purpose                 | Example Usage                                           |
| ---------------- | ----------------------- | ------------------------------------------------------- |
| `line.new()`     | Creates a new line.     | `line.new(x1, y1, x2, y2)`                              |
| `box.new()`      | Creates a new box.      | `box.new(left, bottom, right, top, border_color=color)` |
| `label.new()`    | Places a text label.    | Optional (not always used).                             |
| `line.delete()`  | Deletes a line object.  | `line.delete(array.get(srLines, i))`                    |
| `box.delete()`   | Deletes a box object.   | Same as above for boxes.                                |
| `label.delete()` | Deletes a label object. | Optional (same pattern if labels are used).             |

---

# 🌊 6. Color Adjustments

| Function                         | Purpose                     | Example Usage                  |
| -------------------------------- | --------------------------- | ------------------------------ |
| `color.new(color, transparency)` | Adjusts color transparency. | `color.new(support_color, 90)` |

---

# ⏱️ 7. Bar State / Control Flow

| Function          | Purpose                                                     | Example Usage                          |
| ----------------- | ----------------------------------------------------------- | -------------------------------------- |
| `barstate.islast` | True at the last bar of the chart (used for cleanup logic). | `if barstate.islast`                   |
| `na`              | Represents Not Available / Null value.                      | Used for logic like: `pivot_high = na` |

---

# 🚀 Summary of Dependency on Native TradingView Functions

| Category                | Critical to Logic?           | Replaceable Outside TradingView?                         |
| ----------------------- | ---------------------------- | -------------------------------------------------------- |
| Pivot Detection         | YES                          | Requires reimplementation outside TradingView.           |
| Math Functions          | YES (basic math)             | Easily replaceable in other languages.                   |
| Arrays                  | YES                          | Reimplement with NumPy or Python lists.                  |
| Inputs / User Controls  | Optional outside TradingView | Replace with function arguments or config.               |
| Drawing / Visualization | YES (for chart output)       | Needs replacement with Matplotlib / Plotly / Bokeh, etc. |
| Cleanup / Limits        | YES (TradingView-specific)   | Unnecessary outside TradingView.                         |
