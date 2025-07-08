#!/usr/bin/env python3
"""
Script to run the data analysis
"""

import os
import sys
sys.path.append('/home/aicompany/ai_co')

from data_analysis import DataAnalyzer

def main():
    # Try to find the data file
    data_path = "/path/to/data.csv"
    
    # If the specified path doesn't exist, use our sample data
    if not os.path.exists(data_path):
        data_path = "/home/aicompany/ai_co/sample_data.csv"
        print(f"Using sample data at: {data_path}")
    
    if not os.path.exists(data_path):
        print("No data file found. Please provide a valid CSV file path.")
        return
    
    # Create analyzer and run analysis
    analyzer = DataAnalyzer(data_path)
    success = analyzer.run_complete_analysis()
    
    if success:
        print("\n🎉 Data analysis completed successfully!")
        print("\nGenerated files:")
        print("- data_analysis_report.md")
        print("- data_overview.png")
        print("- correlation_heatmap.png") 
        print("- numeric_distributions.png")
        print("- categorical_distributions.png")
        print("- outlier_detection.png")
    else:
        print("\n❌ Data analysis failed!")

if __name__ == "__main__":
    main()