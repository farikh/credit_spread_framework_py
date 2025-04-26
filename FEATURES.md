# Feature Documentation

This document collects completed features, their parameters, and usage examples. Add a new section here whenever a feature is implemented.

---

## SRZoneIndicator (Support/Resistance Zones)

**Location**  
`credit_spread_framework/indicators/custom/sr_zone_indicator.py`

**Description**  
Detects dynamic support/resistance zones over price bars, using three weighting methods:

- **time**: clusters pivot highs/lows by rolling‐window extrema and counts touches.
- **linear**: scans pairwise bar‐close linear fits to identify levels with repeated touches.
- **volume**: builds volume profile bins and marks levels with significant trading volume.

Zones are output with:

- `timestamp_start` – when zone becomes active
- `timestamp_end` – when zone expires
- `value` – price level of the zone
- `aux_value` – touch count (generic second value)
- `qualifier` – one of `time`, `linear`, or `volume`
- `parameters_json` – JSON snapshot of input settings

**Default Parameters** (if not overridden via CLI):

```json
{
  "pivot_lookback": 50,
  "filter": 3,
  "precision": 75,
  "auto_precision": true,
  "scale": 30
}
```

**Command-Line Usage Examples**

1. Generate only “time” zones on 15-minute bars for Jan 1–2, 2024:

   ```bash
   python -m credit_spread_framework.cli.enrich_data \
     --indicator SR_ZONES \
     --timeframe 15m \
     --start 2024-01-01 \
     --end   2024-01-02 \
     --qualifier time
   ```

2. Generate “linear” zones on hourly bars with a custom lookback:

   ```bash
   python -m credit_spread_framework.cli.enrich_data \
     -i SR_ZONES \
     -t 1h \
     -q linear \
     --parameters-json '{"pivot_lookback": 30, "precision": 50}'
   ```

3. Generate all three methods on daily bars (no date filter):
   ```bash
   python -m credit_spread_framework.cli.enrich_data \
     --indicator SR_ZONES \
     --timeframe 1d
   ```
