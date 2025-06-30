#!/usr/bin/env python3

import pandas as pd
import numpy as np
from web_analyzer import WebAnalyzer

def create_sample_data():
    """Create sample data for testing"""
    np.random.seed(42)
    data = {
        'price': np.random.normal(100, 20, 200),
        'quantity': np.random.poisson(50, 200),
        'rating': np.random.uniform(1, 5, 200),
        'category': np.random.choice(['A', 'B', 'C'], 200),
        'date': pd.date_range('2023-01-01', periods=200, freq='D')
    }
    return pd.DataFrame(data)

def test_web_analyzer():
    """Test the enhanced WebAnalyzer functionality"""
    
    print("=== Testing Enhanced WebAnalyzer ===\n")
    
    # Create analyzer instance
    analyzer = WebAnalyzer()
    
    # Create and load sample data
    sample_df = create_sample_data()
    analyzer.df = sample_df
    
    print("1. Basic Info:")
    print(f"   Shape: {analyzer.df.shape}")
    print(f"   Columns: {list(analyzer.df.columns)}")
    print()
    
    print("2. Basic Statistics:")
    basic_stats = analyzer.basic_stats()
    print(basic_stats.head())
    print()
    
    print("3. Advanced Statistics:")
    advanced_stats = analyzer.advanced_stats()
    for col, stats in advanced_stats.items():
        print(f"   {col}:")
        print(f"     - Mean: {stats['mean']:.2f}")
        print(f"     - Skewness: {stats['skewness']:.2f}")
        print(f"     - Outliers: {stats['outliers_count']}")
    print()
    
    print("4. Outlier Detection:")
    outliers = analyzer.detect_outliers(method='iqr')
    print(f"   Found {len(outliers)} outliers using IQR method")
    print()
    
    print("5. Correlation Analysis:")
    corr_matrix = analyzer.correlation_analysis()
    print(corr_matrix)
    print()
    
    print("6. Regression Analysis (price vs rating):")
    try:
        regression_results = analyzer.regression_analysis('rating', 'price', plot=False)
        print(f"   R-squared: {regression_results['r_squared']:.3f}")
        print(f"   Correlation: {regression_results['correlation']:.3f}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    print("7. Clustering Analysis:")
    try:
        clusters = analyzer.perform_clustering(['price', 'rating'], n_clusters=3, plot=False)
        print(f"   Clustered {len(clusters)} data points into 3 clusters")
        print(f"   Cluster distribution: {clusters['cluster'].value_counts().to_dict()}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    print("8. Comprehensive Analysis:")
    comprehensive = analyzer.comprehensive_analysis(target_column='price')
    print(f"   Dataset shape: {comprehensive['basic_info']['shape']}")
    print(f"   Missing values: {sum(comprehensive['basic_info']['missing_values'].values())}")
    print(f"   Outliers detected: {comprehensive['outliers_count']}")
    print()
    
    print("9. Export Test:")
    try:
        analyzer.export_data('test_output.csv', 'csv')
        print("   Data exported successfully to test_output.csv")
    except Exception as e:
        print(f"   Export error: {e}")
    print()
    
    print("=== Test Completed Successfully ===")

if __name__ == "__main__":
    test_web_analyzer()