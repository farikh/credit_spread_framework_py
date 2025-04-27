-- Migration script to create SR Zone tables
-- This creates dedicated tables for SR zones, pivots, and interactions

-- Create SR Zones table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sr_zones]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sr_zones] (
        [zone_id] INT IDENTITY(1,1) PRIMARY KEY,
        [value] FLOAT NOT NULL,
        [qualifier] VARCHAR(50) NOT NULL,  -- 'time', 'linear', 'volume'
        [timeframe] VARCHAR(10) NOT NULL,  -- '1m', '3m', '15m', '1h', '1d'
        [strength] INT NOT NULL,
        [first_detected] DATETIME NOT NULL,
        [last_confirmed] DATETIME NOT NULL,
        [invalidated_at] DATETIME NULL,
        [is_active] BIT NOT NULL DEFAULT 1,
        [parameters_json] NVARCHAR(MAX) NULL,
        CONSTRAINT UQ_sr_zones UNIQUE ([value], [qualifier], [timeframe])
    );
    
    PRINT 'Created table sr_zones';
END
ELSE
BEGIN
    PRINT 'Table sr_zones already exists';
END

-- Create SR Zone Pivots table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sr_zone_pivots]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sr_zone_pivots] (
        [pivot_id] INT IDENTITY(1,1) PRIMARY KEY,
        [zone_id] INT FOREIGN KEY REFERENCES [dbo].[sr_zones]([zone_id]),
        [pivot_value] FLOAT NOT NULL,
        [pivot_timestamp] DATETIME NOT NULL,
        [pivot_type] VARCHAR(10) NOT NULL,  -- 'high' or 'low'
        [weight] FLOAT NOT NULL,
        [timeframe] VARCHAR(10) NOT NULL
    );
    
    CREATE INDEX [IX_sr_zone_pivots_zone_id] ON [dbo].[sr_zone_pivots]([zone_id]);
    CREATE INDEX [IX_sr_zone_pivots_timestamp] ON [dbo].[sr_zone_pivots]([pivot_timestamp]);
    
    PRINT 'Created table sr_zone_pivots';
END
ELSE
BEGIN
    PRINT 'Table sr_zone_pivots already exists';
END

-- Create SR Zone Interactions table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sr_zone_interactions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sr_zone_interactions] (
        [interaction_id] INT IDENTITY(1,1) PRIMARY KEY,
        [zone_id] INT FOREIGN KEY REFERENCES [dbo].[sr_zones]([zone_id]),
        [bar_id] VARCHAR(50) NOT NULL,  -- Links to OHLCV bar
        [timeframe] VARCHAR(10) NOT NULL,
        [interaction_type] VARCHAR(20) NOT NULL,  -- 'touch', 'crossover_up', 'crossover_down', 'bounce'
        [interaction_strength] FLOAT NOT NULL,
        [timestamp] DATETIME NOT NULL,
        [price] FLOAT NOT NULL
    );
    
    CREATE INDEX [IX_sr_zone_interactions_zone_id] ON [dbo].[sr_zone_interactions]([zone_id]);
    CREATE INDEX [IX_sr_zone_interactions_timestamp] ON [dbo].[sr_zone_interactions]([timestamp]);
    CREATE INDEX [IX_sr_zone_interactions_type] ON [dbo].[sr_zone_interactions]([interaction_type]);
    
    PRINT 'Created table sr_zone_interactions';
END
ELSE
BEGIN
    PRINT 'Table sr_zone_interactions already exists';
END
