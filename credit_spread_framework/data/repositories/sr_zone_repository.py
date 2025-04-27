"""
Repository for SR Zone data access.

This module provides methods for creating, updating, and querying SR zones.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SRZoneRepository:
    """Repository for SR Zone data access."""
    
    @staticmethod
    def create_zone(value, qualifier, timeframe, strength, parameters_json=None, first_detected=None, last_confirmed=None):
        """
        Create a new SR zone.
        
        Args:
            value: The price level of the zone
            qualifier: The qualifier (time, linear, volume)
            timeframe: The timeframe (1m, 3m, 15m, 1h, 1d)
            strength: The initial strength of the zone
            parameters_json: Optional parameters used to create the zone
            first_detected: Timestamp when the zone was first detected (defaults to current time)
            last_confirmed: Timestamp when the zone was last confirmed (defaults to first_detected)
            
        Returns:
            The ID of the newly created zone
        """
        engine = get_engine()
        
        # Use current time if timestamps not provided
        if first_detected is None:
            first_detected = datetime.now()
        if last_confirmed is None:
            last_confirmed = first_detected
        
        # Check if a similar zone already exists
        query = text("""
            SELECT zone_id, value, strength, is_active
            FROM sr_zones
            WHERE qualifier = :qualifier
            AND timeframe = :timeframe
            AND ABS(value - :value) < 15  -- Within 15 points
            AND is_active = 1
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "qualifier": qualifier,
                    "timeframe": timeframe,
                    "value": value
                }
            )
            
            existing_zone = result.fetchone()
            
            if existing_zone:
                # Update the existing zone instead of creating a new one
                zone_id = existing_zone.zone_id
                existing_value = existing_zone.value
                existing_strength = existing_zone.strength
                
                # Calculate weighted average for the zone value
                total_strength = existing_strength + strength
                # Avoid division by zero and NaN values
                if total_strength > 0:
                    new_value = (existing_value * existing_strength + value * strength) / total_strength
                else:
                    new_value = value  # Use the new value if total strength is zero
                
                update_query = text("""
                    UPDATE sr_zones
                    SET value = :value,
                        strength = :strength,
                        last_confirmed = :last_confirmed
                    WHERE zone_id = :zone_id
                """)
                
                conn.execute(
                    update_query,
                    {
                        "value": new_value,
                        "strength": total_strength,
                        "last_confirmed": last_confirmed,
                        "zone_id": zone_id
                    }
                )
                
                logger.info(f"Updated existing zone {zone_id} from {existing_value} to {new_value} with strength {total_strength}")
                return zone_id
            
            # No existing zone found, create a new one
            insert_query = text("""
                INSERT INTO sr_zones (
                    value, qualifier, timeframe, strength,
                    first_detected, last_confirmed, is_active, parameters_json
                )
                VALUES (
                    :value, :qualifier, :timeframe, :strength,
                    :first_detected, :last_confirmed, 1, :parameters_json
                )
            """)
            
            conn.execute(
                insert_query,
                {
                    "value": value,
                    "qualifier": qualifier,
                    "timeframe": timeframe,
                    "strength": strength,
                    "first_detected": first_detected,
                    "last_confirmed": last_confirmed,
                    "parameters_json": parameters_json
                }
            )
            
            # Get the ID of the newly created zone
            get_id_query = text("""
                SELECT zone_id 
                FROM sr_zones 
                WHERE value = :value 
                AND qualifier = :qualifier 
                AND timeframe = :timeframe
                AND first_detected = :first_detected
            """)
            
            result = conn.execute(
                get_id_query,
                {
                    "value": value,
                    "qualifier": qualifier,
                    "timeframe": timeframe,
                    "first_detected": first_detected
                }
            )
            
            zone_id = result.scalar()
            logger.info(f"Created new zone {zone_id} at {value} with strength {strength}")
            return zone_id
    
    @staticmethod
    def update_zone_strength(zone_id, strength_delta, last_confirmed=None):
        """
        Update the strength of an SR zone.
        
        Args:
            zone_id: The ID of the zone to update
            strength_delta: The amount to adjust the strength by (positive or negative)
            last_confirmed: Timestamp when the zone was last confirmed (defaults to current time)
            
        Returns:
            The updated strength value
        """
        engine = get_engine()
        
        # Use current time if timestamp not provided
        if last_confirmed is None:
            last_confirmed = datetime.now()
        
        update_query = text("""
            UPDATE sr_zones
            SET strength = strength + :strength_delta,
                last_confirmed = :last_confirmed
            WHERE zone_id = :zone_id
        """)
        
        with engine.begin() as conn:
            conn.execute(
                update_query,
                {
                    "zone_id": zone_id,
                    "strength_delta": strength_delta,
                    "last_confirmed": last_confirmed
                }
            )
            
            # Get the updated strength
            get_strength_query = text("""
                SELECT strength
                FROM sr_zones
                WHERE zone_id = :zone_id
            """)
            
            result = conn.execute(
                get_strength_query,
                {
                    "zone_id": zone_id
                }
            )
            
            updated_strength = result.scalar()
            logger.debug(f"Updated zone {zone_id} strength by {strength_delta} to {updated_strength}")
            return updated_strength
    
    @staticmethod
    def invalidate_zone(zone_id, reason=None, invalidated_at=None):
        """
        Invalidate an SR zone.
        
        Args:
            zone_id: The ID of the zone to invalidate
            reason: Optional reason for invalidation
            invalidated_at: Timestamp when the zone was invalidated (defaults to current time)
            
        Returns:
            True if the zone was invalidated, False otherwise
        """
        engine = get_engine()
        
        # Use current time if timestamp not provided
        if invalidated_at is None:
            invalidated_at = datetime.now()
        
        query = text("""
            UPDATE sr_zones
            SET is_active = 0,
                invalidated_at = :invalidated_at
            WHERE zone_id = :zone_id
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "zone_id": zone_id,
                    "invalidated_at": invalidated_at
                }
            )
            
            rows_affected = result.rowcount
            if rows_affected > 0:
                logger.info(f"Invalidated zone {zone_id} at {invalidated_at}" + (f" - Reason: {reason}" if reason else ""))
                return True
            else:
                logger.warning(f"Failed to invalidate zone {zone_id} - zone not found")
                return False
    
    @staticmethod
    def get_active_zones(timeframe, qualifier=None, date=None):
        """
        Get active SR zones for a specific timeframe and date.
        
        Args:
            timeframe: The timeframe to query
            qualifier: Optional qualifier to filter by
            date: Optional date to check (defaults to current date)
            
        Returns:
            DataFrame with active zones
        """
        engine = get_engine()
        
        if date is None:
            date = datetime.now()
        
        query = text("""
            SELECT 
                zone_id, value, qualifier, timeframe, strength,
                first_detected, last_confirmed, parameters_json
            FROM sr_zones
            WHERE timeframe = :timeframe
            AND is_active = 1
            AND first_detected <= :date
            AND (:qualifier IS NULL OR qualifier = :qualifier)
            ORDER BY qualifier, value
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "timeframe": timeframe,
                    "date": date,
                    "qualifier": qualifier
                }
            )
            
            columns = [
                "zone_id", "value", "qualifier", "timeframe", "strength",
                "first_detected", "last_confirmed", "parameters_json"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} active zones for {timeframe}" + 
                        (f" and qualifier {qualifier}" if qualifier else ""))
            return df
    
    @staticmethod
    def get_zone_by_id(zone_id):
        """
        Get an SR zone by ID.
        
        Args:
            zone_id: The ID of the zone to retrieve
            
        Returns:
            Dictionary with zone data or None if not found
        """
        engine = get_engine()
        
        query = text("""
            SELECT 
                zone_id, value, qualifier, timeframe, strength,
                first_detected, last_confirmed, invalidated_at, is_active, parameters_json
            FROM sr_zones
            WHERE zone_id = :zone_id
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "zone_id": zone_id
                }
            )
            
            row = result.fetchone()
            if row:
                return {
                    "zone_id": row.zone_id,
                    "value": row.value,
                    "qualifier": row.qualifier,
                    "timeframe": row.timeframe,
                    "strength": row.strength,
                    "first_detected": row.first_detected,
                    "last_confirmed": row.last_confirmed,
                    "invalidated_at": row.invalidated_at,
                    "is_active": bool(row.is_active),
                    "parameters_json": row.parameters_json
                }
            else:
                return None
    
    @staticmethod
    def find_zones_near_price(price, timeframe, tolerance=15, qualifier=None):
        """
        Find active zones near a specific price.
        
        Args:
            price: The price to search near
            timeframe: The timeframe to query
            tolerance: The maximum distance from the price (default: 15 points)
            qualifier: Optional qualifier to filter by
            
        Returns:
            DataFrame with matching zones
        """
        engine = get_engine()
        
        query = text("""
            SELECT 
                zone_id, value, qualifier, timeframe, strength,
                first_detected, last_confirmed, parameters_json,
                ABS(value - :price) as distance
            FROM sr_zones
            WHERE timeframe = :timeframe
            AND is_active = 1
            AND ABS(value - :price) <= :tolerance
            AND (:qualifier IS NULL OR qualifier = :qualifier)
            ORDER BY distance, strength DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "price": price,
                    "timeframe": timeframe,
                    "tolerance": tolerance,
                    "qualifier": qualifier
                }
            )
            
            columns = [
                "zone_id", "value", "qualifier", "timeframe", "strength",
                "first_detected", "last_confirmed", "parameters_json", "distance"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} zones near price {price} for {timeframe}" + 
                        (f" and qualifier {qualifier}" if qualifier else ""))
            return df
