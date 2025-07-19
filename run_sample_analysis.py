#!/usr/bin/env python3
"""
Run analysis on sample_data.csv
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_analysis import DataAnalyzer


def main():
    # Run analysis on sample data
    analyzer = DataAnalyzer("sample_data.csv")
    success = analyzer.run_complete_analysis()

    if success:
        print("\n🎉 Data analysis completed successfully!")
        return 0
    else:
        print("\n❌ Data analysis failed!")
        return 1


if __name__ == "__main__":
    exit(main())
