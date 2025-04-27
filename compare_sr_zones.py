"""
Script to compare SR zones calculated by our algorithm with the levels in the JSON files.
"""
from credit_spread_framework.data.db_engine import get_engine
from sqlalchemy import text
import pandas as pd
import json
import os

def load_json_levels(file_path):
    """
    Load SR zone levels from a JSON file.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    levels = []
    
    # Handle different JSON structures
    if 'support_resistance_levels' in data:
        sr_levels = data['support_resistance_levels']
        
        if 'zones' in sr_levels:
            # Format used in 1m and 3m files
            for zone in sr_levels['zones']:
                levels.append({
                    'level': zone['level'],
                    'type': zone['type']
                })
        else:
            # Format used in daily, 1h, and 15m files
            if 'resistance' in sr_levels:
                for zone in sr_levels['resistance']:
                    levels.append({
                        'level': zone['level'],
                        'type': 'Resistance'
                    })
            
            if 'support' in sr_levels:
                for zone in sr_levels['support']:
                    levels.append({
                        'level': zone['level'],
                        'type': 'Support'
                    })
    
    return levels

def get_db_levels(timeframe):
    """
    Get SR zone levels from the database for a specific timeframe.
    """
    engine = get_engine()
    
    query = text("""
        SELECT 
            value, 
            CASE 
                WHEN value > 5400 THEN 'Resistance'
                ELSE 'Support'
            END AS type,
            qualifier,
            strength
        FROM sr_zones
        WHERE timeframe = :timeframe
        AND is_active = 1
        ORDER BY value
    """)
    
    with engine.begin() as conn:
        result = conn.execute(
            query,
            {
                "timeframe": timeframe
            }
        )
        
        columns = ["value", "type", "qualifier", "strength"]
        df = pd.DataFrame(result.fetchall(), columns=columns)
    
    return df

def compare_levels(json_levels, db_levels, tolerance=25):
    """
    Compare SR zone levels from JSON and database.
    """
    matches = []
    unmatched_json = []
    unmatched_db = []
    
    # Convert JSON levels to a list of values
    json_values = [level['level'] for level in json_levels]
    
    # Check each JSON level against DB levels
    for json_level in json_levels:
        level_value = json_level['level']
        level_type = json_level['type']
        
        # Find closest DB level
        if not db_levels.empty:
            db_levels['distance'] = abs(db_levels['value'] - level_value)
            closest = db_levels.loc[db_levels['distance'].idxmin()]
            
            if closest['distance'] <= tolerance:
                matches.append({
                    'json_level': level_value,
                    'json_type': level_type,
                    'db_level': closest['value'],
                    'db_type': closest['type'],
                    'qualifier': closest['qualifier'],
                    'strength': closest['strength'],
                    'distance': closest['distance']
                })
            else:
                unmatched_json.append({
                    'level': level_value,
                    'type': level_type
                })
        else:
            unmatched_json.append({
                'level': level_value,
                'type': level_type
            })
    
    # Check for DB levels not matched to any JSON level
    for _, db_level in db_levels.iterrows():
        if not any(abs(db_level['value'] - json_level['level']) <= tolerance for json_level in json_levels):
            unmatched_db.append({
                'value': db_level['value'],
                'type': db_level['type'],
                'qualifier': db_level['qualifier'],
                'strength': db_level['strength']
            })
    
    return matches, unmatched_json, unmatched_db

def main():
    # Define timeframes and corresponding JSON files
    timeframes = {
        "1d": "credit_spread_framework/documents/Indicators/SRZones/spx_daily_srzones_chart_description_2025_04_03.json",
        "1h": "credit_spread_framework/documents/Indicators/SRZones/spx_1hr_srzones_chart_description_2025_04_03.json",
        "15m": "credit_spread_framework/documents/Indicators/SRZones/spx_15m_srzones_chart_description_2025_04_03.json",
        "3m": "credit_spread_framework/documents/Indicators/SRZones/spx_3m_srzones_chart_description_2025_04_03.json",
        "1m": "credit_spread_framework/documents/Indicators/SRZones/spx_1m_srzones_chart_description_2025_04_03.json"
    }
    
    for timeframe, json_file in timeframes.items():
        print(f"\n{'-'*80}")
        print(f"Timeframe: {timeframe}")
        
        # Load JSON levels
        json_levels = load_json_levels(json_file)
        print(f"Loaded {len(json_levels)} levels from {os.path.basename(json_file)}")
        
        # Get DB levels
        db_levels = get_db_levels(timeframe)
        print(f"Found {len(db_levels)} levels in the database for timeframe {timeframe}")
        
        # Compare levels
        matches, unmatched_json, unmatched_db = compare_levels(json_levels, db_levels)
        
        # Print results
        print(f"\nMatched levels ({len(matches)}):")
        if matches:
            match_df = pd.DataFrame(matches)
            print(match_df[['json_level', 'db_level', 'distance', 'qualifier', 'strength']])
        
        print(f"\nJSON levels not matched ({len(unmatched_json)}):")
        if unmatched_json:
            for level in unmatched_json:
                print(f"  {level['level']} ({level['type']})")
        
        print(f"\nDB levels not matched ({len(unmatched_db)}):")
        if unmatched_db:
            for level in unmatched_db:
                print(f"  {level['value']} ({level['type']}, {level['qualifier']}, strength: {level['strength']})")
        
        # Calculate match percentage
        if json_levels:
            match_percentage = len(matches) / len(json_levels) * 100
            print(f"\nMatch percentage: {match_percentage:.2f}%")
        
        # Overall assessment
        if match_percentage >= 70:
            print("✅ Good match between JSON and DB levels")
        elif match_percentage >= 50:
            print("⚠️ Moderate match between JSON and DB levels")
        else:
            print("❌ Poor match between JSON and DB levels")

if __name__ == "__main__":
    main()
