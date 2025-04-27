"""
Repository for SR Zone Pivot data access.

This module provides methods for creating, updating, and querying SR zone pivots.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SRZonePivotRepository:
    """Repository for SR Zone Pivot data access."""
    
    @staticmethod
    def add_pivot(zone_id, pivot_value, pivot_timestamp, pivot_type, weight, timeframe):
        """
        Add a pivot point associated with an SR zone.
        
        Args:
            zone_id: The ID of the zone this pivot is associated with
            pivot_value: The price level of the pivot
            pivot_timestamp: The timestamp when the pivot occurred
            pivot_type: The type of pivot ('high' or 'low')
            weight: The weight of the pivot
            timeframe: The timeframe of the pivot
            
        Returns:
            The ID of the newly created pivot
        """
        engine = get_engine()
        
        query = text("""
            INSERT INTO sr_zone_pivots (
                zone_id, pivot_value, pivot_timestamp, pivot_type, weight, timeframe
            )
            VALUES (
                :zone_id, :pivot_value, :pivot_timestamp, :pivot_type, :weight, :timeframe
            )
        """)
        
        with engine.begin() as conn:
            conn.execute(
                query,
                {
                    "zone_id": zone_id,
                    "pivot_value": pivot_value,
                    "pivot_timestamp": pivot_timestamp,
                    "pivot_type": pivot_type,
                    "weight": weight,
                    "timeframe": timeframe
                }
            )
            
            # Get the ID of the newly created pivot
            get_id_query = text("""
                SELECT pivot_id 
                FROM sr_zone_pivots 
                WHERE zone_id = :zone_id 
                AND pivot_value = :pivot_value 
                AND pivot_timestamp = :pivot_timestamp
                AND pivot_type = :pivot_type
            """)
            
            result = conn.execute(
                get_id_query,
                {
                    "zone_id": zone_id,
                    "pivot_value": pivot_value,
                    "pivot_timestamp": pivot_timestamp,
                    "pivot_type": pivot_type
                }
            )
            
            pivot_id = result.scalar()
            logger.debug(f"Added pivot {pivot_id} at {pivot_value} for zone {zone_id}")
            return pivot_id
    
    @staticmethod
    def get_pivots_for_zone(zone_id):
        """
        Get all pivots associated with an SR zone.
        
        Args:
            zone_id: The ID of the zone to get pivots for
            
        Returns:
            DataFrame with pivot data
        """
        engine = get_engine()
        
        query = text("""
            SELECT 
                pivot_id, zone_id, pivot_value, pivot_timestamp, pivot_type, weight, timeframe
            FROM sr_zone_pivots
            WHERE zone_id = :zone_id
            ORDER BY pivot_timestamp DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "zone_id": zone_id
                }
            )
            
            columns = [
                "pivot_id", "zone_id", "pivot_value", "pivot_timestamp", 
                "pivot_type", "weight", "timeframe"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} pivots for zone {zone_id}")
            return df
    
    @staticmethod
    def get_recent_pivots(timeframe, start_date, end_date=None, pivot_type=None):
        """
        Get recent pivots for a specific timeframe and date range.
        
        Args:
            timeframe: The timeframe to query
            start_date: The start date for the query
            end_date: Optional end date (defaults to current date)
            pivot_type: Optional pivot type to filter by ('high' or 'low')
            
        Returns:
            DataFrame with pivot data
        """
        engine = get_engine()
        
        if end_date is None:
            end_date = datetime.now()
        
        query = text("""
            SELECT 
                p.pivot_id, p.zone_id, p.pivot_value, p.pivot_timestamp, 
                p.pivot_type, p.weight, p.timeframe,
                z.value as zone_value, z.qualifier, z.strength
            FROM sr_zone_pivots p
            JOIN sr_zones z ON p.zone_id = z.zone_id
            WHERE p.timeframe = :timeframe
            AND p.pivot_timestamp BETWEEN :start_date AND :end_date
            AND (:pivot_type IS NULL OR p.pivot_type = :pivot_type)
            ORDER BY p.pivot_timestamp DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "timeframe": timeframe,
                    "start_date": start_date,
                    "end_date": end_date,
                    "pivot_type": pivot_type
                }
            )
            
            columns = [
                "pivot_id", "zone_id", "pivot_value", "pivot_timestamp", 
                "pivot_type", "weight", "timeframe", "zone_value", 
                "qualifier", "strength"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} recent pivots for {timeframe}" + 
                        (f" and type {pivot_type}" if pivot_type else ""))
            return df
    
    @staticmethod
    def get_pivots_near_price(price, timeframe, tolerance=15, pivot_type=None):
        """
        Get pivots near a specific price.
        
        Args:
            price: The price to search near
            timeframe: The timeframe to query
            tolerance: The maximum distance from the price (default: 15 points)
            pivot_type: Optional pivot type to filter by ('high' or 'low')
            
        Returns:
            DataFrame with pivot data
        """
        engine = get_engine()
        
        query = text("""
            SELECT 
                p.pivot_id, p.zone_id, p.pivot_value, p.pivot_timestamp, 
                p.pivot_type, p.weight, p.timeframe,
                z.value as zone_value, z.qualifier, z.strength,
                ABS(p.pivot_value - :price) as distance
            FROM sr_zone_pivots p
            JOIN sr_zones z ON p.zone_id = z.zone_id
            WHERE p.timeframe = :timeframe
            AND ABS(p.pivot_value - :price) <= :tolerance
            AND (:pivot_type IS NULL OR p.pivot_type = :pivot_type)
            ORDER BY distance, p.pivot_timestamp DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "price": price,
                    "timeframe": timeframe,
                    "tolerance": tolerance,
                    "pivot_type": pivot_type
                }
            )
            
            columns = [
                "pivot_id", "zone_id", "pivot_value", "pivot_timestamp", 
                "pivot_type", "weight", "timeframe", "zone_value", 
                "qualifier", "strength", "distance"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} pivots near price {price} for {timeframe}" + 
                        (f" and type {pivot_type}" if pivot_type else ""))
            return df
    
    @staticmethod
    def delete_pivots_for_zone(zone_id):
        """
        Delete all pivots associated with an SR zone.
        
        Args:
            zone_id: The ID of the zone to delete pivots for
            
        Returns:
            The number of pivots deleted
        """
        engine = get_engine()
        
        query = text("""
            DELETE FROM sr_zone_pivots
            WHERE zone_id = :zone_id
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "zone_id": zone_id
                }
            )
            
            rows_affected = result.rowcount
            logger.debug(f"Deleted {rows_affected} pivots for zone {zone_id}")
            return rows_affected
