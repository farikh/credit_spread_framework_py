"""
Run Validation Tests

This script runs validation tests for the SRZone implementation using different timeframes and data sources.
It demonstrates how to use the validate_srzone_implementation.py script with various parameters.

Usage:
    python run_validation_tests.py
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command):
    """
    Run a command and print the output.
    
    Parameters:
    -----------
    command : str
        Command to run
    """
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    for line in process.stdout:
        print(line.decode('utf-8').strip())
    
    process.wait()
    print(f"Command completed with return code: {process.returncode}")
    print("-" * 80)
    return process.returncode

def main():
    """
    Main function to run validation tests.
    """
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define test cases
    test_cases = [
        # 1-minute timeframe with CSV data
        {
            "name": "1-minute CSV",
            "command": f"python validate_srzone_implementation.py --timeframe 1m --source csv --file \"SP_SPX, 1m__Linear.csv\" --weight-style Linear --debug"
        },
        # 3-minute timeframe with CSV data
        {
            "name": "3-minute CSV",
            "command": f"python validate_srzone_implementation.py --timeframe 3m --source csv --file \"SP_SPX, 3m__Linear.csv\" --weight-style Linear --debug"
        },
        # 15-minute timeframe with CSV data
        {
            "name": "15-minute CSV",
            "command": f"python validate_srzone_implementation.py --timeframe 15m --source csv --file \"SP_SPX, 15m__Linear.csv\" --weight-style Linear --debug"
        },
        # 1-hour timeframe with CSV data
        {
            "name": "1-hour CSV",
            "command": f"python validate_srzone_implementation.py --timeframe 1h --source csv --file \"SP_SPX, 60m__Linear.csv\" --weight-style Linear --debug"
        },
        # 1-day timeframe with CSV data
        {
            "name": "1-day CSV",
            "command": f"python validate_srzone_implementation.py --timeframe 1d --source csv --file \"SP_SPX, 1d_Linear.csv\" --weight-style Linear --debug"
        },
        # SQL data example (commented out as it requires database access)
        # {
        #     "name": "15-minute SQL",
        #     "command": f"python validate_srzone_implementation.py --timeframe 15m --source sql --start 2025-04-01 --end 2025-04-03 --weight-style Linear --debug"
        # }
    ]
    
    # Run each test case
    for test_case in test_cases:
        print(f"\n=== Running Test: {test_case['name']} ===\n")
        run_command(test_case["command"])
    
    print("\nAll validation tests completed.")

if __name__ == "__main__":
    main()
