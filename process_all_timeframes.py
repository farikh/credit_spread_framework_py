"""
Script to process SR zones for all timeframes.

This script will:
1. Clean the SR zone tables
2. Process SR zones for all timeframes (1d, 1h, 15m, 3m, 1m)
3. Compare the calculated SR zones with the levels in the JSON files
"""
import subprocess
import time
import os

def main():
    # Step 1: Clean the SR zone tables
    print("Step 1: Cleaning SR zone tables...")
    
    # Use the Python interpreter from the virtual environment
    python_exe = os.path.join(".venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = "python"  # Fallback to system Python
        
    subprocess.run([python_exe, "clean_sr_zone_tables.py"], check=True)
    print("SR zone tables cleaned successfully.")
    
    # Step 2: Process SR zones for all timeframes
    timeframes = ["1d", "1h", "15m", "3m", "1m"]
    
    for timeframe in timeframes:
        print(f"\nProcessing SR zones for timeframe: {timeframe}")
        
        # Run the process_historical_sr_zones.py script for this timeframe
        cmd = [
            python_exe, 
            "process_historical_sr_zones.py", 
            "process-specific-dates", 
            "--date", "2025-04-03", 
            "--timeframe", timeframe, 
            "--lookback", "180"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"SR zones for {timeframe} processed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error processing SR zones for {timeframe}: {e}")
            continue
        
        # Wait a bit to ensure the database is updated
        time.sleep(2)
    
    # Step 3: Compare the calculated SR zones with the levels in the JSON files
    print("\nStep 3: Comparing calculated SR zones with JSON levels...")
    subprocess.run([python_exe, "compare_sr_zones.py"], check=True)
    print("Comparison complete.")

if __name__ == "__main__":
    main()
