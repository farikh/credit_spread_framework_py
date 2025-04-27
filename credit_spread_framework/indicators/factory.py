"""
Indicator factory module.

This module provides functions for registering and retrieving indicator classes.
"""
import importlib
import json
import logging
from typing import Tuple, Dict, Any, Type

from credit_spread_framework.indicators.base import BaseIndicator
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Registry of indicator classes
_indicator_registry = {}

def register_indicator_class(indicator_name: str, indicator_class: Type[BaseIndicator]) -> None:
    """
    Register an indicator class with the factory.
    
    Args:
        indicator_name: The name of the indicator
        indicator_class: The indicator class
    """
    global _indicator_registry
    _indicator_registry[indicator_name] = indicator_class
    logger.debug(f"Registered indicator class: {indicator_name}")

def get_indicator_class(indicator_name: str) -> Tuple[Type[BaseIndicator], Dict[str, Any]]:
    """
    Get an indicator class by name.
    
    This function first checks the registry for the indicator class. If not found,
    it attempts to dynamically import the class based on naming conventions.
    
    Args:
        indicator_name: The name of the indicator
        
    Returns:
        A tuple of (IndicatorClass, metadata)
    """
    global _indicator_registry
    
    # Check if we have metadata for this indicator
    metadata = _get_indicator_metadata(indicator_name)
    
    # Check if the class is already registered
    if indicator_name in _indicator_registry:
        return _indicator_registry[indicator_name], metadata
    
    # Try to dynamically import the class
    try:
        # For custom indicators
        if indicator_name == "srzones":
            module_name = "credit_spread_framework.indicators.custom.sr_zone_indicator"
            class_name = "SRZoneIndicator"
        elif indicator_name == "enhanced_srzones":
            module_name = "credit_spread_framework.indicators.custom.enhanced_sr_zone_indicator"
            class_name = "EnhancedSRZoneIndicator"
        # For TA-Lib wrappers
        elif indicator_name == "rsi":
            module_name = "credit_spread_framework.indicators.ta_wrappers.rsi_indicator"
            class_name = "RSIIndicator"
        else:
            # Default naming convention
            module_name = f"credit_spread_framework.indicators.custom.{indicator_name}_indicator"
            class_name = f"{indicator_name.capitalize()}Indicator"
        
        module = importlib.import_module(module_name)
        indicator_class = getattr(module, class_name)
        
        # Register the class for future use
        register_indicator_class(indicator_name, indicator_class)
        
        return indicator_class, metadata
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import indicator class for {indicator_name}: {e}")
        raise ValueError(f"Indicator {indicator_name} not found")

def _get_indicator_metadata(indicator_name: str) -> Dict[str, Any]:
    """
    Get metadata for an indicator from the database.
    
    Args:
        indicator_name: The name of the indicator
        
    Returns:
        A dictionary of metadata
    """
    engine = get_engine()
    
    query = text("""
        SELECT IndicatorId, ShortName, LongName, Description, ParametersJson
        FROM indicators
        WHERE ShortName = :name AND IsActive = 1
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {"name": indicator_name})
        row = result.fetchone()
        
        if row:
            metadata = {
                "IndicatorId": row.IndicatorId,
                "ShortName": row.ShortName,
                "LongName": row.LongName,
                "Description": row.Description
            }
            
            # Parse parameters JSON if available
            if row.ParametersJson:
                try:
                    params = json.loads(row.ParametersJson)
                    metadata["ParametersJson"] = params
                except json.JSONDecodeError:
                    metadata["ParametersJson"] = {}
            else:
                metadata["ParametersJson"] = {}
                
            return metadata
        else:
            return {}
