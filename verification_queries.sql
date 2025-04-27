-- Verification Queries for SR Zones and Resampled Bars
-- These queries can be used to verify that the fixes are working properly

-- 1. Verify SR Zones active on 2025-04-03
-- This query shows all active SR zones for 2025-04-03, regardless of when they were first detected
SELECT 
    qualifier,
    value,
    strength,
    first_detected,
    last_confirmed,
    DATEDIFF(day, first_detected, '2025-04-03') AS days_active
FROM 
    sr_zones
WHERE 
    is_active = 1
    AND first_detected <= '2025-04-03'
    AND (invalidated_at IS NULL OR invalidated_at > '2025-04-03')
ORDER BY 
    qualifier, value;

-- 2. Verify that all target zones are present
-- This query checks if all 7 target zones from TradingView are present
SELECT 
    target_value,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM sr_zones 
            WHERE ABS(value - target_value) < 15
        ) THEN 'Present'
        ELSE 'Missing'
    END AS status
FROM (
    VALUES 
        (6132), -- Major Resistance
        (5726), -- Resistance
        (5431), -- Resistance
        (5178), -- Support
        (4939), -- Support
        (4558), -- Support
        (4095)  -- Major Support
) AS target_zones(target_value);

-- 3. Verify timestamps in SR zones
-- This query checks if the timestamps are from OHLCV data instead of current time
SELECT 
    zone_id,
    value,
    first_detected,
    last_confirmed,
    DATEDIFF(day, first_detected, GETDATE()) AS days_since_detection
FROM 
    sr_zones
ORDER BY 
    first_detected DESC;

-- 4. Verify resampled bars for 2025-04-01 to 2025-04-03
-- This query shows the resampled bars for each timeframe

-- 4.1 Daily bars
SELECT * FROM spx_ohlcv_1d
WHERE timestamp BETWEEN '2025-04-01' AND '2025-04-03'
ORDER BY timestamp;

-- 4.2 Hourly bars
SELECT * FROM spx_ohlcv_1h
WHERE timestamp BETWEEN '2025-04-01' AND '2025-04-03'
ORDER BY timestamp;

-- 4.3 15-minute bars
SELECT * FROM spx_ohlcv_15m
WHERE timestamp BETWEEN '2025-04-01' AND '2025-04-03'
ORDER BY timestamp;

-- 4.4 3-minute bars
SELECT * FROM spx_ohlcv_3m
WHERE timestamp BETWEEN '2025-04-01' AND '2025-04-03'
ORDER BY timestamp;

-- 5. Verify consistency between timeframes
-- This query compares the daily OHLC values with the min/max values from lower timeframes

-- 5.1 Compare daily with hourly
SELECT 
    d.timestamp AS day_timestamp,
    d.open AS day_open,
    d.high AS day_high,
    d.low AS day_low,
    d.close AS day_close,
    MIN(h.timestamp) AS first_hour,
    MAX(h.timestamp) AS last_hour,
    MIN(h.low) AS min_hourly_low,
    MAX(h.high) AS max_hourly_high
FROM 
    spx_ohlcv_1d d
JOIN 
    spx_ohlcv_1h h ON CONVERT(date, d.timestamp) = CONVERT(date, h.timestamp)
WHERE 
    d.timestamp BETWEEN '2025-04-01' AND '2025-04-03'
GROUP BY 
    d.timestamp, d.open, d.high, d.low, d.close;

-- 5.2 Compare hourly with 15-minute
SELECT 
    h.timestamp AS hour_timestamp,
    h.open AS hour_open,
    h.high AS hour_high,
    h.low AS hour_low,
    h.close AS hour_close,
    MIN(m.timestamp) AS first_15min,
    MAX(m.timestamp) AS last_15min,
    MIN(m.low) AS min_15min_low,
    MAX(m.high) AS max_15min_high
FROM 
    spx_ohlcv_1h h
JOIN 
    spx_ohlcv_15m m ON 
        DATEPART(year, h.timestamp) = DATEPART(year, m.timestamp) AND
        DATEPART(month, h.timestamp) = DATEPART(month, m.timestamp) AND
        DATEPART(day, h.timestamp) = DATEPART(day, m.timestamp) AND
        DATEPART(hour, h.timestamp) = DATEPART(hour, m.timestamp)
WHERE 
    h.timestamp BETWEEN '2025-04-01' AND '2025-04-03'
GROUP BY 
    h.timestamp, h.open, h.high, h.low, h.close
ORDER BY 
    h.timestamp;

-- 6. Verify SR zone interactions
-- This query shows interactions between price and SR zones
SELECT 
    i.interaction_id,
    i.zone_id,
    z.value AS zone_value,
    z.qualifier,
    i.interaction_type,
    i.interaction_strength,
    i.timestamp,
    i.price
FROM 
    sr_zone_interactions i
JOIN 
    sr_zones z ON i.zone_id = z.zone_id
WHERE 
    i.timestamp >= '2025-04-01'
ORDER BY 
    i.timestamp DESC;

-- 7. Verify SR zone pivots
-- This query shows pivots contributing to SR zones
SELECT 
    p.pivot_id,
    p.zone_id,
    z.value AS zone_value,
    z.qualifier,
    p.pivot_value,
    p.pivot_type,
    p.pivot_timestamp,
    p.weight
FROM 
    sr_zone_pivots p
JOIN 
    sr_zones z ON p.zone_id = z.zone_id
WHERE 
    p.pivot_timestamp >= '2025-04-01'
ORDER BY 
    p.pivot_timestamp DESC;

-- 8. Verify last_confirmed updates
-- This query shows zones with interactions and how last_confirmed is updated
SELECT 
    z.zone_id,
    z.value,
    z.qualifier,
    z.first_detected,
    z.last_confirmed,
    MAX(i.timestamp) AS last_interaction_time,
    COUNT(i.interaction_id) AS interaction_count
FROM 
    sr_zones z
LEFT JOIN 
    sr_zone_interactions i ON z.zone_id = i.zone_id
WHERE 
    z.is_active = 1
GROUP BY 
    z.zone_id, z.value, z.qualifier, z.first_detected, z.last_confirmed
HAVING 
    COUNT(i.interaction_id) > 0
ORDER BY 
    MAX(i.timestamp) DESC;

-- 9. Verify consistency between last_confirmed and interactions
-- This query identifies any zones where last_confirmed doesn't match the latest interaction
SELECT 
    z.zone_id,
    z.value,
    z.qualifier,
    z.last_confirmed,
    MAX(i.timestamp) AS last_interaction_time,
    DATEDIFF(second, z.last_confirmed, MAX(i.timestamp)) AS time_difference_seconds
FROM 
    sr_zones z
JOIN 
    sr_zone_interactions i ON z.zone_id = i.zone_id
GROUP BY 
    z.zone_id, z.value, z.qualifier, z.last_confirmed
HAVING 
    z.last_confirmed <> MAX(i.timestamp)
ORDER BY 
    ABS(DATEDIFF(second, z.last_confirmed, MAX(i.timestamp))) DESC;
