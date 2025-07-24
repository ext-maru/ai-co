#!/usr/bin/env python3
"""
Simple data analysis for sample_data.csv
"""
from datetime import datetime

import numpy as np
import pandas as pd


def analyze_data():
    # Load data
    """analyze_dataメソッド"""
    data = pd.read_csv("sample_data.csv")

    # Basic info
    shape = data.shape
    memory_usage = data.memory_usage(deep=True).sum() / 1024 / 1024
    missing_values = data.isnull().sum().sum()
    duplicate_rows = data.duplicated().sum()

    # Column types
    numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()

    # Summary statistics
    numeric_stats = data[numeric_columns].describe() if numeric_columns else None

    # Categorical stats
    cat_stats = {}
    for col in categorical_columns:
        cat_stats[col] = {
            "unique": data[col].nunique(),
            "most_common": data[col].mode().iloc[0] if not data[col].empty else "N/A",
        }

    # Correlation analysis
    correlations = []
    if len(numeric_columns) > 1:
        corr_matrix = data[numeric_columns].corr()
        # 繰り返し処理
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    correlations.append(
                        {
                            "col1": corr_matrix.columns[i],
                            "col2": corr_matrix.columns[j],
                            "correlation": corr_value,
                        }
                    )

    # Outlier detection
    outliers = {}
    for col in numeric_columns:
        Q1 = data[col].quantile(0.25)
        Q3 = data[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (data[col] < lower_bound) | (data[col] > upper_bound)
        outlier_count = outlier_mask.sum()

        if outlier_count > 0:
            outliers[col] = {
                "count": outlier_count,
                "percentage": (outlier_count / len(data)) * 100,
            }

    # Generate insights
    insights = []

    missing_pct = (missing_values / (shape[0] * shape[1])) * 100
    if missing_pct > 0:
        insights.append(f"Dataset has {missing_pct:0.1f}% missing values")

    if duplicate_rows > 0:
        insights.append(f"Found {duplicate_rows} duplicate rows")

    if correlations:
        insights.append(
            f"Found {len(correlations)} strong correlations between variables"
        )

    high_outlier_cols = [
        col for col, info in outliers.items() if info["percentage"] > 5
    ]
    if high_outlier_cols:
        insights.append(f"High outlier columns (>5%): {', '.join(high_outlier_cols)}")

    if shape[0] < 100:
        insights.append(f"Small sample size: {shape[0]} rows")

    # Create markdown report
    report = f"""# Data Analysis Report

## Dataset Overview
- **File:** sample_data.csv
- **Dimensions:** {shape[0]} rows × {shape[1]} columns
- **Memory Usage:** {memory_usage:0.1f} MB
- **Missing Values:** {missing_values} ({missing_pct:0.1f}%)
- **Duplicate Rows:** {duplicate_rows}

## Column Types
- **Numeric Columns:** {len(numeric_columns)} ({', '.join(numeric_columns)})
- **Categorical Columns:** {len(categorical_columns)} ({', '.join(categorical_columns)})

## Summary Statistics

### Numeric Variables
```
{numeric_stats.to_string() if numeric_stats is not None else 'No numeric columns'}
```

### Categorical Variables
"""

    for col, stats in cat_stats.items():
        report += f"- **{col}:** {stats['unique']} unique values, most common: '{stats['most_common']}'\n"

    report += "\n## Patterns & Anomalies\n\n"

    if correlations:
        report += "### Strong Correlations (>0.7)\n"
        for corr in correlations:
            report += f"- {corr['col1']} ↔ {corr['col2']}: {corr['correlation']:0.3f}\n"
        report += "\n"

    if outliers:
        report += "### Outliers Detected\n"
        for col, info in outliers.items():
            report += (
                f"- **{col}:** {info['count']} outliers ({info['percentage']:0.1f}%)\n"
            )
        report += "\n"

    report += "## Actionable Insights\n\n"
    for i, insight in enumerate(insights, 1):
        report += f"{i}. {insight}\n"

    report += "\n## Recommendations\n\n"

    recommendations = []
    if missing_values > 0:
        recommendations.append(
            "Address missing values through imputation or removal strategies"
        )
    if duplicate_rows > 0:
        recommendations.append("Investigate and handle duplicate records")
    if outliers:
        recommendations.append(
            "Analyze outliers to determine if they represent errors or genuine extreme values"
        )
    if len(numeric_columns) > 1:
        recommendations.append(
            "Consider feature engineering based on correlation patterns"
        )
    if categorical_columns:
        recommendations.append(
            "Evaluate categorical variable encoding strategies for modeling"
        )

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
    else:
        report += "The dataset appears to be in good condition with no major issues identified.\n"

    report += (
        f"\n---\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    )

    # Print results
    print("🔍 Data Analysis Results:")
    print(f"Shape: {shape}")
    print(f"Memory: {memory_usage:0.1f} MB")
    print(f"Missing values: {missing_values}")
    print(f"Duplicates: {duplicate_rows}")
    print(f"Numeric columns: {len(numeric_columns)}")
    print(f"Categorical columns: {len(categorical_columns)}")
    print(f"Strong correlations: {len(correlations)}")
    print(f"Outliers found in: {len(outliers)} columns")
    print(f"Key insights: {len(insights)}")

    return report


if __name__ == "__main__":
    report = analyze_data()
    with open("data_analysis_report.md", "w") as f:
        f.write(report)
    print("✅ Report saved to data_analysis_report.md")
