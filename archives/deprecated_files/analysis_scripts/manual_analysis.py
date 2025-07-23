#!/usr/bin/env python3
"""
Manual data analysis execution
"""
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # Use non-interactive backend
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
from datetime import datetime

import seaborn as sns

# Load the data
print("Loading data...")
data = pd.read_csv("sample_data.csv")

# Basic statistics
print(f"Dataset shape: {data.shape}")
print(f"Memory usage: {data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
print(f"Missing values: {data.isnull().sum().sum()}")
print(f"Duplicate rows: {data.duplicated().sum()}")

# Column types
numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
categorical_columns = data.select_dtypes(include=["object"]).columns.tolist()

print(f"\nNumeric columns: {numeric_columns}")
print(f"Categorical columns: {categorical_columns}")

# Generate summary statistics
print("\n=== SUMMARY STATISTICS ===")
if numeric_columns:
    print("Numeric statistics:")
    print(data[numeric_columns].describe())

if categorical_columns:
    print("\nCategorical statistics:")
    for col in categorical_columns:
        print(
            f"{col}: {data[col].nunique()} unique values, most common: {data[col].mode().iloc[0]}"
        )

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
                        "columns": (corr_matrix.columns[i], corr_matrix.columns[j]),
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

# Print analysis results
print("\n=== PATTERNS & ANOMALIES ===")
if correlations:
    print("Strong correlations (>0.7):")
    for corr in correlations:
        print(
            f"  {corr['columns'][0]} ↔ {corr['columns'][1]}: {corr['correlation']:.3f}"
        )

if outliers:
    print("Outliers detected:")
    for col, info in outliers.items():
        print(f"  {col}: {info['count']} outliers ({info['percentage']:.1f}%)")

# Generate insights
insights = []

# Missing data insight
missing_pct = (data.isnull().sum().sum() / (data.shape[0] * data.shape[1])) * 100
if missing_pct > 0:
    insights.append(f"Dataset has {missing_pct:.1f}% missing values")

# Duplicate insight
if data.duplicated().sum() > 0:
    insights.append(f"Found {data.duplicated().sum()} duplicate rows")

# Correlation insight
if correlations:
    insights.append(f"Found {len(correlations)} strong correlations between variables")

# Outlier insight
high_outlier_cols = [col for col, info in outliers.items() if info["percentage"] > 5]
if high_outlier_cols:
    insights.append(f"High outlier columns (>5%): {', '.join(high_outlier_cols)}")

# Sample size insight
if data.shape[0] < 100:
    insights.append(f"Small sample size: {data.shape[0]} rows")

print("\n=== ACTIONABLE INSIGHTS ===")
for i, insight in enumerate(insights, 1):
    print(f"{i}. {insight}")

# Create markdown report
report = f"""# Data Analysis Report

## Dataset Overview
- **File:** sample_data.csv
- **Dimensions:** {data.shape[0]} rows × {data.shape[1]} columns
- **Memory Usage:** {data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB
- **Missing Values:** {data.isnull().sum().sum()} ({missing_pct:.1f}%)
- **Duplicate Rows:** {data.duplicated().sum()}

## Column Types
- **Numeric Columns:** {len(numeric_columns)} ({', '.join(numeric_columns)})
- **Categorical Columns:** {len(categorical_columns)} ({', '.join(categorical_columns)})

## Summary Statistics

### Numeric Variables
```
{data[numeric_columns].describe().to_string()}
```

### Categorical Variables
"""

for col in categorical_columns:
    unique_count = data[col].nunique()
    most_common = data[col].mode().iloc[0] if not data[col].empty else "N/A"
    report += (
        f"- **{col}:** {unique_count} unique values, most common: '{most_common}'\n"
    )

report += "\n## Patterns & Anomalies\n\n"

if correlations:
    report += "### Strong Correlations (>0.7)\n"
    for corr in correlations:
        report += f"- {corr['columns'][0]} ↔ {corr['columns'][1]}: {corr['correlation']:.3f}\n"
    report += "\n"

if outliers:
    report += "### Outliers Detected\n"
    for col, info in outliers.items():
        report += f"- **{col}:** {info['count']} outliers ({info['percentage']:.1f}%)\n"
    report += "\n"

report += "## Actionable Insights\n\n"
for i, insight in enumerate(insights, 1):
    report += f"{i}. {insight}\n"

report += "\n## Recommendations\n\n"

recommendations = []
if data.isnull().sum().sum() > 0:
    recommendations.append(
        "Address missing values through imputation or removal strategies"
    )
if data.duplicated().sum() > 0:
    recommendations.append("Investigate and handle duplicate records")
if outliers:
    recommendations.append(
        "Analyze outliers to determine if they represent errors or genuine extreme values"
    )
if len(numeric_columns) > 1:
    recommendations.append("Consider feature engineering based on correlation patterns")
if categorical_columns:
    recommendations.append(
        "Evaluate categorical variable encoding strategies for modeling"
    )

if recommendations:
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"
else:
    report += (
        "The dataset appears to be in good condition with no major issues identified.\n"
    )

report += (
    f"\n---\n*Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
)

# Save report
with open("data_analysis_report.md", "w") as f:
    f.write(report)

print(f"\n✅ Analysis complete! Generated data_analysis_report.md")
print("📊 Report saved successfully")
