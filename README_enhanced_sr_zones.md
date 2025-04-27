# Enhanced SR Zone Implementation

This document describes the enhanced SR Zone implementation, which provides better historical persistence and more closely matches TradingView's behavior for detecting support and resistance zones.

## Overview

The original SR Zone implementation had several limitations:

1. Zones were recalculated for each date without historical context
2. Zones didn't persist over time
3. There was no tracking of interactions between price and zones
4. The algorithm didn't match TradingView's behavior closely enough

The enhanced implementation addresses these issues by:

1. Using dedicated tables for SR zones, pivots, and interactions
2. Implementing proper zone lifetime management
3. Tracking interactions between price and zones
4. Refining the algorithm to better match TradingView's behavior

## Database Schema

The implementation uses three dedicated tables:

### sr_zones

Stores the SR zones themselves:

- `zone_id`: Unique identifier for the zone
- `value`: The price level of the zone
- `qualifier`: The qualifier (time, linear, volume)
- `timeframe`: The timeframe (1m, 3m, 15m, 1h, 1d)
- `strength`: The strength of the zone
- `first_detected`: When the zone was first detected
- `last_confirmed`: When the zone was last confirmed
- `invalidated_at`: When the zone was invalidated (NULL if active)
- `is_active`: Whether the zone is active
- `parameters_json`: Parameters used to create the zone

### sr_zone_pivots

Stores the pivot points that contribute to each zone:

- `pivot_id`: Unique identifier for the pivot
- `zone_id`: The zone this pivot is associated with
- `pivot_value`: The price level of the pivot
- `pivot_timestamp`: When the pivot occurred
- `pivot_type`: The type of pivot (high or low)
- `weight`: The weight of the pivot
- `timeframe`: The timeframe of the pivot

### sr_zone_interactions

Tracks interactions between price and zones:

- `interaction_id`: Unique identifier for the interaction
- `zone_id`: The zone this interaction is associated with
- `bar_id`: The OHLCV bar where the interaction occurred
- `timeframe`: The timeframe of the interaction
- `interaction_type`: The type of interaction (touch, crossover_up, crossover_down, bounce)
- `interaction_strength`: The strength of the interaction
- `timestamp`: When the interaction occurred
- `price`: The price at which the interaction occurred

## Setup Instructions

### 1. Initialize the SR Zone Tables

Run the initialization script to create the SR zone tables and register the enhanced SR zone indicator:

```bash
python initialize_sr_zone_tables.py
```

### 2. Process Historical Data

Process historical data to establish initial SR zones:

```bash
python process_historical_sr_zones.py --start 2024-01-01 --end 2024-09-30 --timeframe 1d
```

For specific dates:

```bash
python process_historical_sr_zones.py process-specific-dates --date 2025-04-03 --timeframe 1d --lookback 180
```

For specific target zones:

```bash
python process_historical_sr_zones.py process-target-zones --zone 6132 --zone 5726 --zone 5431 --zone 5178 --zone 4939 --zone 4558 --zone 4095 --date 2025-04-03 --timeframe 1d
```

### 3. Process New Data

Process new data to update SR zones and track interactions:

```bash
python process_enhanced_sr_zones.py process-sr-zones --start 2025-04-03 --end 2025-04-03
```

For a specific timeframe:

```bash
python process_enhanced_sr_zones.py process-sr-zones --start 2025-04-03 --end 2025-04-03 --timeframe 1d
```

For a specific qualifier:

```bash
python process_enhanced_sr_zones.py process-sr-zones --start 2025-04-03 --end 2025-04-03 --qualifier time
```

### 4. Query SR Zones

List active SR zones:

```bash
python process_enhanced_sr_zones.py list-active-zones --timeframe 1d --date 2025-04-03
```

List interactions for a specific zone:

```bash
python process_enhanced_sr_zones.py list-zone-interactions --zone-id 1
```

Invalidate a zone:

```bash
python process_enhanced_sr_zones.py invalidate-zone --zone-id 1 --reason "No longer relevant"
```

## Implementation Details

### Enhanced SR Zone Indicator

The `EnhancedSRZoneIndicator` class implements the improved algorithm:

1. **Pivot Detection**: Detects pivot points from OHLCV data
2. **Zone Creation**: Creates or updates SR zones based on these pivots
3. **Interaction Detection**: Detects interactions between price and existing zones
4. **Zone Management**: Updates zone strength based on interactions

### Zone Lifetime Management

Zones are created with `is_active = 1` and `invalidated_at = NULL`. They remain active until explicitly invalidated, which happens when:

1. Price decisively crosses and stays beyond the zone
2. The zone's strength falls below a threshold
3. A stronger zone forms very close to it

### Interaction Types

The system tracks several types of interactions:

- **Touch**: Price comes close to the zone without crossing
- **Crossover Up**: Price crosses up through the zone
- **Crossover Down**: Price crosses down through the zone
- **Bounce Up**: Price reverses upward after touching the zone
- **Bounce Down**: Price reverses downward after touching the zone

Each interaction affects the zone's strength, with bounces having a positive impact and crossovers having a negative impact.

## Comparison with TradingView

The enhanced implementation more closely matches TradingView's behavior:

1. **Historical Persistence**: Zones persist over time, just like in TradingView
2. **Zone Detection**: The algorithm uses similar techniques for detecting zones
3. **Zone Strength**: Zones have strength values that evolve based on interactions
4. **Zone Invalidation**: Zones are invalidated based on price action

The implementation aims to produce zones within 10-15 points of TradingView's zones, which is sufficient for trading purposes.

## Troubleshooting

If you encounter issues:

1. **No zones detected**: Try processing with a longer lookback period
2. **Too many zones**: Adjust the threshold_ratio parameter
3. **Zones not matching TradingView**: Adjust the precision and zone_tolerance parameters
4. **Database errors**: Check the SQL Server connection and ensure the tables exist

For more detailed logging, set the logging level to DEBUG in the scripts.
