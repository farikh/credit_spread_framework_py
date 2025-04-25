# Database Schema Export

## `dbo.__EFMigrationsHistory`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| MigrationId         | nvarchar      | NO    |
| ProductVersion         | nvarchar      | NO    |

## `dbo.indicator_values`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| IndicatorValueId         | int      | NO    |
| BarId         | nvarchar      | NO    |
| Timeframe         | nvarchar      | NO    |
| IndicatorId         | int      | NO    |
| Value         | float      | YES    |
| TimestampStart         | datetime2      | NO    |
| TimestampEnd         | datetime2      | YES    |

## `dbo.indicators`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| IndicatorId         | int      | NO    |
| Name         | nvarchar      | NO    |
| ShortName         | nvarchar      | NO    |
| Lookback         | int      | NO    |
| ParametersJson         | nvarchar      | YES    |
| IsActive         | bit      | NO    |

## `dbo.spx_ohlcv_15m`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| bar_id         | varchar      | NO    |
| timestamp         | datetime2      | NO    |
| ticker         | nvarchar      | YES    |
| open         | float      | YES    |
| high         | float      | YES    |
| low         | float      | YES    |
| close         | float      | YES    |
| spy_volume         | float      | YES    |

## `dbo.spx_ohlcv_1d`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| bar_id         | varchar      | NO    |
| timestamp         | datetime2      | NO    |
| ticker         | nvarchar      | YES    |
| open         | float      | YES    |
| high         | float      | YES    |
| low         | float      | YES    |
| close         | float      | YES    |
| spy_volume         | float      | YES    |

## `dbo.spx_ohlcv_1h`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| bar_id         | varchar      | NO    |
| timestamp         | datetime2      | NO    |
| ticker         | nvarchar      | YES    |
| open         | float      | YES    |
| high         | float      | YES    |
| low         | float      | YES    |
| close         | float      | YES    |
| spy_volume         | float      | YES    |

## `dbo.spx_ohlcv_1m`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| bar_id         | varchar      | NO    |
| timestamp         | datetime2      | NO    |
| ticker         | nvarchar      | YES    |
| open         | float      | YES    |
| high         | float      | YES    |
| low         | float      | YES    |
| close         | float      | YES    |
| spy_volume         | float      | YES    |

## `dbo.spx_ohlcv_3m`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| bar_id         | varchar      | NO    |
| timestamp         | datetime2      | NO    |
| ticker         | nvarchar      | YES    |
| open         | float      | YES    |
| high         | float      | YES    |
| low         | float      | YES    |
| close         | float      | YES    |
| spy_volume         | float      | YES    |

## `dbo.sysdiagrams`

| Column Name     | Data Type    | Nullable |
|-----------------|--------------|----------|
| name         | nvarchar      | NO    |
| principal_id         | int      | NO    |
| diagram_id         | int      | NO    |
| version         | int      | YES    |
| definition         | varbinary      | YES    |

