-- Migration: add AuxValue column to indicator_values table
ALTER TABLE indicator_values
ADD AuxValue INT NULL;
