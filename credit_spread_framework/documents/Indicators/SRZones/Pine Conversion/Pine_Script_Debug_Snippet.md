
# 🟢 Pine Script Debug Snippet: Output Active Zones on a Specific Date

```pinescript
// === Debug Settings ===
target_year  = 2025
target_month = 4
target_day   = 3

// Define your zone data here (replace these with your actual zone values/arrays)
zone_top    = 5300.0  // Example: replace with your array.get or calculation
zone_bottom = 5280.0  // Example: replace with your array.get or calculation
zone_score  = 5       // Example: replace with your scoring logic

// === Trigger Only for the Target Date ===
is_target_date = (year == target_year and month == target_month and dayofmonth == target_day)

// === Output Labels for Debugging Zones ===
if is_target_date and barstate.isconfirmed
    label.new(bar_index, high,
      text = 'Zone Top: ' + str.tostring(zone_top) +
             '\nZone Bottom: ' + str.tostring(zone_bottom) +
             '\nScore: ' + str.tostring(zone_score),
      color = color.yellow,
      style = label.style_label_down,
      size = size.small)
```

---

## 🟠 How to Use:
- Replace:
  - `zone_top`, `zone_bottom`, `zone_score`
- With your actual **zone array lookups** or calculated values.
- Drop this near the **end of your zone detection logic** so the zones are already populated.
- This outputs a **yellow label** for each bar on your chosen day, showing:
  - Zone Top  
  - Zone Bottom  
  - Score  

---

## 🔍 Example for Multiple Zones (If You Store Zones in Arrays):
```pinescript
if is_target_date and barstate.isconfirmed and array.size(zone_tops) > 0
    for i = 0 to array.size(zone_tops) - 1
        this_top = array.get(zone_tops, i)
        this_bottom = array.get(zone_bottoms, i)
        this_score = array.get(zone_scores, i)
        label.new(bar_index, high,
          text = 'Zone[' + str.tostring(i) + '] Top: ' + str.tostring(this_top) +
                 '\nBottom: ' + str.tostring(this_bottom) +
                 '\nScore: ' + str.tostring(this_score),
          color = color.yellow,
          style = label.style_label_down,
          size = size.small)
```

---

## 🚩 Extra Add-On: Show OHLC + Timestamp for the Same Bar:
```pinescript
if is_target_date and barstate.isconfirmed
    label.new(bar_index, low,
      text = 'Time: ' + str.tostring(time, format = format.date_time) +
             '\nOpen: ' + str.tostring(open) +
             '\nHigh: ' + str.tostring(high) +
             '\nLow: ' + str.tostring(low) +
             '\nClose: ' + str.tostring(close),
      color = color.orange,
      style = label.style_label_up,
      size = size.small)
```

---

## ⚡ Validation Workflow Suggestion with This Debug:
1. Run your Pine script on **4/3/2025**.
2. Visually inspect labels for **zone ranges and scores**.
3. Manually record them or take screenshots.
4. Compare with your **Python-generated zones** at the same bar timestamps.
