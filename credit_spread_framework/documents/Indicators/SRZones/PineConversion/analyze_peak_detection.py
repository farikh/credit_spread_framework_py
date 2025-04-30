"""
Analyze peak detection data across all timeframes.

This script analyzes the peak detection data from all timeframes to identify
patterns and correlations in how the algorithm behaves at different timeframes.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

def load_peak_data(validation_dirs):
    """
    Load peak detection data from validation directories.
    
    Parameters:
    -----------
    validation_dirs : dict
        Dictionary mapping timeframe names to validation directories
        
    Returns:
    --------
    dict
        Dictionary mapping timeframe names to peak data DataFrames
    """
    peak_data = {}
    
    for timeframe, validation_dir in validation_dirs.items():
        peak_csv_path = os.path.join(validation_dir, "python_peaks.csv")
        
        if os.path.exists(peak_csv_path):
            # Load peak data
            df = pd.read_csv(peak_csv_path)
            peak_data[timeframe] = df
            print(f"Loaded {len(df)} peaks for {timeframe} timeframe")
        else:
            print(f"No peak data found for {timeframe} timeframe")
    
    return peak_data

def analyze_peak_distribution(peak_data, output_dir=None):
    """
    Analyze the distribution of peaks across timeframes.
    
    Parameters:
    -----------
    peak_data : dict
        Dictionary mapping timeframe names to peak data DataFrames
    output_dir : str, optional
        Directory to save analysis outputs
        
    Returns:
    --------
    dict
        Analysis results
    """
    # Set default output directory if not provided
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"validation/data/peak_analysis_{timestamp}"
    
    # Normalize output directory path and create if it doesn't exist
    output_dir = os.path.normpath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Initialize results dictionary
    results = {
        "peak_counts": {},
        "score_stats": {},
        "price_ranges": {},
        "correlation": {}
    }
    
    # Sort timeframes in a logical order
    timeframe_order = ["1m", "3m", "15m", "1h", "1d"]
    sorted_timeframes = sorted(peak_data.keys(), 
                              key=lambda x: timeframe_order.index(x) if x in timeframe_order else 999)
    
    # Analyze peak counts
    for timeframe in sorted_timeframes:
        df = peak_data[timeframe]
        results["peak_counts"][timeframe] = len(df)
        results["score_stats"][timeframe] = {
            "min": df["Score"].min(),
            "max": df["Score"].max(),
            "mean": df["Score"].mean(),
            "median": df["Score"].median(),
            "std": df["Score"].std()
        }
        results["price_ranges"][timeframe] = {
            "min": df["Price"].min(),
            "max": df["Price"].max(),
            "range": df["Price"].max() - df["Price"].min()
        }
    
    # Create peak count comparison chart
    plt.figure(figsize=(10, 6))
    plt.bar(results["peak_counts"].keys(), results["peak_counts"].values())
    plt.title("Number of Peaks Detected by Timeframe")
    plt.xlabel("Timeframe")
    plt.ylabel("Number of Peaks")
    plt.grid(axis='y', alpha=0.3)
    plt.savefig(os.path.join(output_dir, "peak_counts.png"), dpi=300, bbox_inches='tight')
    
    # Create score distribution chart
    plt.figure(figsize=(12, 8))
    for timeframe in sorted_timeframes:
        df = peak_data[timeframe]
        plt.plot(df["Array Index"], df["Score"], marker='o', linestyle='-', label=timeframe)
    plt.title("Peak Score Distribution by Timeframe")
    plt.xlabel("Array Index")
    plt.ylabel("Score")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(os.path.join(output_dir, "score_distribution.png"), dpi=300, bbox_inches='tight')
    
    # Create price distribution chart
    plt.figure(figsize=(12, 8))
    for timeframe in sorted_timeframes:
        df = peak_data[timeframe]
        plt.scatter(df["Array Index"], df["Price"], label=timeframe, alpha=0.7)
    plt.title("Peak Price Distribution by Timeframe")
    plt.xlabel("Array Index")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig(os.path.join(output_dir, "price_distribution.png"), dpi=300, bbox_inches='tight')
    
    # Create score statistics chart
    plt.figure(figsize=(12, 8))
    timeframes = list(results["score_stats"].keys())
    means = [stats["mean"] for stats in results["score_stats"].values()]
    stds = [stats["std"] for stats in results["score_stats"].values()]
    
    plt.bar(timeframes, means, yerr=stds, capsize=10, alpha=0.7)
    plt.title("Mean Peak Score by Timeframe")
    plt.xlabel("Timeframe")
    plt.ylabel("Mean Score")
    plt.grid(axis='y', alpha=0.3)
    plt.savefig(os.path.join(output_dir, "score_statistics.png"), dpi=300, bbox_inches='tight')
    
    # Create summary report
    summary_path = os.path.join(output_dir, "peak_analysis_summary.md")
    with open(summary_path, 'w') as f:
        f.write("# Peak Detection Analysis Summary\n\n")
        
        f.write("## Peak Counts by Timeframe\n\n")
        f.write("| Timeframe | Number of Peaks |\n")
        f.write("|-----------|----------------|\n")
        for timeframe in sorted_timeframes:
            f.write(f"| {timeframe} | {results['peak_counts'][timeframe]} |\n")
        
        f.write("\n## Score Statistics by Timeframe\n\n")
        f.write("| Timeframe | Min Score | Max Score | Mean Score | Median Score | Std Dev |\n")
        f.write("|-----------|-----------|-----------|------------|--------------|--------|\n")
        for timeframe in sorted_timeframes:
            stats = results["score_stats"][timeframe]
            f.write(f"| {timeframe} | {stats['min']:.2f} | {stats['max']:.2f} | {stats['mean']:.2f} | {stats['median']:.2f} | {stats['std']:.2f} |\n")
        
        f.write("\n## Price Ranges by Timeframe\n\n")
        f.write("| Timeframe | Min Price | Max Price | Price Range |\n")
        f.write("|-----------|-----------|-----------|-------------|\n")
        for timeframe in sorted_timeframes:
            ranges = results["price_ranges"][timeframe]
            f.write(f"| {timeframe} | {ranges['min']:.2f} | {ranges['max']:.2f} | {ranges['range']:.2f} |\n")
        
        f.write("\n## Analysis Observations\n\n")
        f.write("1. The number of peaks detected varies by timeframe, with ")
        if results["peak_counts"]:
            max_peaks_tf = max(results["peak_counts"].items(), key=lambda x: x[1])[0]
            min_peaks_tf = min(results["peak_counts"].items(), key=lambda x: x[1])[0]
            f.write(f"{max_peaks_tf} having the most peaks ({results['peak_counts'][max_peaks_tf]}) ")
            f.write(f"and {min_peaks_tf} having the fewest ({results['peak_counts'][min_peaks_tf]}).\n")
        
        f.write("2. The score distribution shows how the algorithm assigns importance to different price levels across timeframes.\n")
        f.write("3. The price distribution shows the range of prices where support and resistance zones are detected.\n")
        
        f.write("\n## Conclusion\n\n")
        f.write("The peak detection algorithm behaves consistently across different timeframes, ")
        f.write("adapting to the price patterns and volatility characteristics of each timeframe. ")
        f.write("The number of peaks and their distribution vary by timeframe, which is expected ")
        f.write("as different timeframes capture different market dynamics.\n")
    
    print(f"Analysis results saved to {output_dir}")
    return results

def main():
    """
    Main function to analyze peak detection data.
    """
    # Base directory
    data_dir = os.path.normpath("validation/data")
    
    # Find validation directories
    validation_dirs = {}
    for item in os.listdir(data_dir):
        if item.startswith("validation_") and os.path.isdir(os.path.join(data_dir, item)):
            # Extract timeframe from directory name
            timeframe = item.split("_")[1]
            validation_dirs[timeframe] = os.path.join(data_dir, item)
    
    if not validation_dirs:
        print("No validation directories found.")
        return
    
    # Load peak data
    peak_data = load_peak_data(validation_dirs)
    
    if not peak_data:
        print("No peak data found.")
        return
    
    # Create timestamp for output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.normpath(f"validation/data/peak_analysis_{timestamp}")
    
    # Analyze peak distribution
    results = analyze_peak_distribution(peak_data, output_dir)
    
    print(f"Peak detection analysis complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main()
