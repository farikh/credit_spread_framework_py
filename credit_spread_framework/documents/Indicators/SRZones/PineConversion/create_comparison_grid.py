"""
Create a comparison grid of all timeframe validations.

This script creates a grid of all timeframe validation images for easy comparison.
"""

import os
import sys
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from datetime import datetime

def create_comparison_grid(validation_dirs, output_path=None):
    """
    Create a grid of comparison images from validation directories.
    
    Parameters:
    -----------
    validation_dirs : dict
        Dictionary mapping timeframe names to validation directories
    output_path : str, optional
        Path to save the grid image
        
    Returns:
    --------
    str
        Path to the saved grid image
    """
    # Set default output path if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"validation/images/timeframe_comparison_grid_{timestamp}.png"
    
    # Normalize output path
    output_path = os.path.normpath(output_path)
    
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Create figure with subplots
    fig, axes = plt.subplots(len(validation_dirs), 1, figsize=(15, 5 * len(validation_dirs)))
    
    # If only one timeframe, axes will not be an array
    if len(validation_dirs) == 1:
        axes = [axes]
    
    # Sort timeframes in a logical order
    timeframe_order = ["1m", "3m", "15m", "1h", "1d"]
    sorted_timeframes = sorted(validation_dirs.keys(), 
                              key=lambda x: timeframe_order.index(x) if x in timeframe_order else 999)
    
    # Load and display each comparison image
    for i, timeframe in enumerate(sorted_timeframes):
        validation_dir = validation_dirs[timeframe]
        comparison_path = os.path.join(validation_dir, "visual_comparison.png")
        
        if os.path.exists(comparison_path):
            # Load image
            img = mpimg.imread(comparison_path)
            
            # Display image
            axes[i].imshow(img)
            axes[i].set_title(f"{timeframe.upper()} Timeframe Comparison", fontsize=14)
            axes[i].axis('off')
        else:
            axes[i].text(0.5, 0.5, f"No comparison image found for {timeframe}",
                        horizontalalignment='center', verticalalignment='center',
                        fontsize=14, color='red')
            axes[i].axis('off')
    
    # Add overall title
    plt.suptitle("SRZone Validation: TradingView vs. Python Implementation", fontsize=16, y=0.98)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # Save figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return output_path

def main():
    """
    Main function to create comparison grid.
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
    
    # Create timestamp for output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.normpath(f"validation/images/timeframe_comparison_grid_{timestamp}.png")
    
    # Create comparison grid
    grid_path = create_comparison_grid(validation_dirs, output_path)
    
    print(f"Comparison grid created: {grid_path}")

if __name__ == "__main__":
    main()
