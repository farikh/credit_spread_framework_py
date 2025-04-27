"""
Repository for SR Zone Interaction data access.

This module provides methods for creating, updating, and querying SR zone interactions.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SRZoneInteractionRepository:
    """Repository for SR Zone Interaction data access."""
    
    @staticmethod
    def add_interaction(zone_id, bar_id, timeframe, interaction_type, interaction_strength, timestamp, price):
        """
        Add an interaction between price and an SR zone.
        
        Args:
            zone_id: The ID of the zone this interaction is associated with
            bar_id: The ID of the OHLCV bar where the interaction occurred
            timeframe: The timeframe of the interaction
            interaction_type: The type of interaction ('touch', 'crossover_up', 'crossover_down', 'bounce')
            interaction_strength: The strength of the interaction
            timestamp: The timestamp when the interaction occurred
            price: The price at which the interaction occurred
            
        Returns:
            The ID of the newly created interaction
        """
        engine = get_engine()
        
        query = text("""
            INSERT INTO sr_zone_interactions (
                zone_id, bar_id, timeframe, interaction_type, 
                interaction_strength, timestamp, price
            )
            VALUES (
                :zone_id, :bar_id, :timeframe, :interaction_type, 
                :interaction_strength, :timestamp, :price
            )
        """)
        
        with engine.begin() as conn:
            conn.execute(
                query,
                {
                    "zone_id": zone_id,
                    "bar_id": bar_id,
                    "timeframe": timeframe,
                    "interaction_type": interaction_type,
                    "interaction_strength": interaction_strength,
                    "timestamp": timestamp,
                    "price": price
                }
            )
            
            # Get the ID of the newly created interaction
            get_id_query = text("""
                SELECT interaction_id 
                FROM sr_zone_interactions 
                WHERE zone_id = :zone_id 
                AND bar_id = :bar_id 
                AND timestamp = :timestamp
                AND interaction_type = :interaction_type
            """)
            
            result = conn.execute(
                get_id_query,
                {
                    "zone_id": zone_id,
                    "bar_id": bar_id,
                    "timestamp": timestamp,
                    "interaction_type": interaction_type
                }
            )
            
            interaction_id = result.scalar()
            logger.debug(f"Added interaction {interaction_id} of type {interaction_type} for zone {zone_id}")
            return interaction_id
    
    @staticmethod
    def get_interactions_for_zone(zone_id, start_date=None, end_date=None, interaction_type=None):
        """
        Get interactions for a specific SR zone.
        
        Args:
            zone_id: The ID of the zone to get interactions for
            start_date: Optional start date for the query
            end_date: Optional end date for the query
            interaction_type: Optional interaction type to filter by
            
        Returns:
            DataFrame with interaction data
        """
        engine = get_engine()
        
        query_parts = [
            """
            SELECT 
                i.interaction_id, i.zone_id, i.bar_id, i.timeframe, 
                i.interaction_type, i.interaction_strength, i.timestamp, i.price,
                z.value as zone_value, z.qualifier, z.strength
            FROM sr_zone_interactions i
            JOIN sr_zones z ON i.zone_id = z.zone_id
            WHERE i.zone_id = :zone_id
            """
        ]
        
        params = {
            "zone_id": zone_id
        }
        
        if start_date:
            query_parts.append("AND i.timestamp >= :start_date")
            params["start_date"] = start_date
            
        if end_date:
            query_parts.append("AND i.timestamp <= :end_date")
            params["end_date"] = end_date
            
        if interaction_type:
            query_parts.append("AND i.interaction_type = :interaction_type")
            params["interaction_type"] = interaction_type
            
        query_parts.append("ORDER BY i.timestamp DESC")
        
        query = text(" ".join(query_parts))
        
        with engine.begin() as conn:
            result = conn.execute(query, params)
            
            columns = [
                "interaction_id", "zone_id", "bar_id", "timeframe", 
                "interaction_type", "interaction_strength", "timestamp", "price",
                "zone_value", "qualifier", "strength"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} interactions for zone {zone_id}" + 
                        (f" of type {interaction_type}" if interaction_type else ""))
            return df
    
    @staticmethod
    def get_recent_interactions(timeframe, start_date, end_date=None, interaction_type=None):
        """
        Get recent interactions for a specific timeframe and date range.
        
        Args:
            timeframe: The timeframe to query
            start_date: The start date for the query
            end_date: Optional end date (defaults to current date)
            interaction_type: Optional interaction type to filter by
            
        Returns:
            DataFrame with interaction data
        """
        engine = get_engine()
        
        if end_date is None:
            end_date = datetime.now()
        
        query = text("""
            SELECT 
                i.interaction_id, i.zone_id, i.bar_id, i.timeframe, 
                i.interaction_type, i.interaction_strength, i.timestamp, i.price,
                z.value as zone_value, z.qualifier, z.strength
            FROM sr_zone_interactions i
            JOIN sr_zones z ON i.zone_id = z.zone_id
            WHERE i.timeframe = :timeframe
            AND i.timestamp BETWEEN :start_date AND :end_date
            AND (:interaction_type IS NULL OR i.interaction_type = :interaction_type)
            ORDER BY i.timestamp DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "timeframe": timeframe,
                    "start_date": start_date,
                    "end_date": end_date,
                    "interaction_type": interaction_type
                }
            )
            
            columns = [
                "interaction_id", "zone_id", "bar_id", "timeframe", 
                "interaction_type", "interaction_strength", "timestamp", "price",
                "zone_value", "qualifier", "strength"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} recent interactions for {timeframe}" + 
                        (f" of type {interaction_type}" if interaction_type else ""))
            return df
    
    @staticmethod
    def get_interactions_by_bar(bar_id, timeframe):
        """
        Get interactions for a specific OHLCV bar.
        
        Args:
            bar_id: The ID of the bar to get interactions for
            timeframe: The timeframe of the bar
            
        Returns:
            DataFrame with interaction data
        """
        engine = get_engine()
        
        query = text("""
            SELECT 
                i.interaction_id, i.zone_id, i.bar_id, i.timeframe, 
                i.interaction_type, i.interaction_strength, i.timestamp, i.price,
                z.value as zone_value, z.qualifier, z.strength
            FROM sr_zone_interactions i
            JOIN sr_zones z ON i.zone_id = z.zone_id
            WHERE i.bar_id = :bar_id
            AND i.timeframe = :timeframe
            ORDER BY i.interaction_strength DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "bar_id": bar_id,
                    "timeframe": timeframe
                }
            )
            
            columns = [
                "interaction_id", "zone_id", "bar_id", "timeframe", 
                "interaction_type", "interaction_strength", "timestamp", "price",
                "zone_value", "qualifier", "strength"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} interactions for bar {bar_id} on {timeframe}")
            return df
    
    @staticmethod
    def get_strongest_interactions(timeframe, limit=10, interaction_type=None):
        """
        Get the strongest interactions for a specific timeframe.
        
        Args:
            timeframe: The timeframe to query
            limit: The maximum number of interactions to return
            interaction_type: Optional interaction type to filter by
            
        Returns:
            DataFrame with interaction data
        """
        engine = get_engine()
        
        query = text("""
            SELECT TOP (:limit)
                i.interaction_id, i.zone_id, i.bar_id, i.timeframe, 
                i.interaction_type, i.interaction_strength, i.timestamp, i.price,
                z.value as zone_value, z.qualifier, z.strength
            FROM sr_zone_interactions i
            JOIN sr_zones z ON i.zone_id = z.zone_id
            WHERE i.timeframe = :timeframe
            AND (:interaction_type IS NULL OR i.interaction_type = :interaction_type)
            ORDER BY i.interaction_strength DESC
        """)
        
        with engine.begin() as conn:
            result = conn.execute(
                query,
                {
                    "timeframe": timeframe,
                    "limit": limit,
                    "interaction_type": interaction_type
                }
            )
            
            columns = [
                "interaction_id", "zone_id", "bar_id", "timeframe", 
                "interaction_type", "interaction_strength", "timestamp", "price",
                "zone_value", "qualifier", "strength"
            ]
            df = pd.DataFrame(result.fetchall(), columns=columns)
            
            logger.debug(f"Found {len(df)} strongest interactions for {timeframe}" + 
                        (f" of type {interaction_type}" if interaction_type else ""))
            return df
    
    @staticmethod
    def delete_interactions_for_zone(zone_id):
        """
        Delete all interactions associated with an SR zone.
        
        Args:
            zone_id: The ID of the zone to delete interactions for
            
        Returns:
            The number of interactions deleted
        """
        engine = get_engine()
        
        query = text("""
            DELETE FROM sr_zone_interactions
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
            logger.debug(f"Deleted {rows_affected} interactions for zone {zone_id}")
            return rows_affected
