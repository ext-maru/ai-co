#!/usr/bin/env python3
"""
Comprehensive Data Analysis Script
Analyzes CSV data and generates summary statistics, patterns, anomalies, and visualizations.
"""

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
import warnings

import seaborn as sns
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


class DataAnalyzer:
    """DataAnalyzerクラス"""
    def __init__(self, csv_path):
        """Initialize the data analyzer with a CSV file path."""
        self.csv_path = csv_path
        self.data = None
        self.numeric_columns = []
        self.categorical_columns = []
        self.analysis_results = {}

    def load_data(self):
        """Load and prepare the data."""
        try:
            self.data = pd.read_csv(self.csv_path)
            print(
                f"✓ Data loaded successfully: {self.data.shape[0]} rows, {self.data.shape[1]} columns"
            )

            # Identify column types
            self.numeric_columns = self.data.select_dtypes(
                include=[np.number]
            ).columns.tolist()
            self.categorical_columns = self.data.select_dtypes(
                include=["object"]
            ).columns.tolist()

            return True
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            return False

    def generate_summary_statistics(self):
        """Generate comprehensive summary statistics."""
        print("\n=== SUMMARY STATISTICS ===")

        # Basic info
        self.analysis_results["basic_info"] = {
            "shape": self.data.shape,
            "memory_usage": self.data.memory_usage(deep=True).sum(),
            "missing_values": self.data.isnull().sum().sum(),
            "duplicate_rows": self.data.duplicated().sum(),
        }

        # Numeric statistics
        if self.numeric_columns:
            numeric_stats = self.data[self.numeric_columns].describe()
            self.analysis_results["numeric_stats"] = numeric_stats
            print("\nNumeric Columns Summary:")
            print(numeric_stats)

        # Categorical statistics
        if self.categorical_columns:
            cat_stats = {}
            for col in self.categorical_columns:
                cat_stats[col] = {
                    "unique_values": self.data[col].nunique(),
                    "most_common": self.data[col].mode().iloc[0]
                    if not self.data[col].empty
                    else None,
                    "frequency": self.data[col].value_counts().head(5).to_dict(),
                }
            self.analysis_results["categorical_stats"] = cat_stats
            print("\nCategorical Columns Summary:")
            for col, stats in cat_stats.items():
                print(
                    f"{col}: {stats['unique_values']} unique values, most common: {stats['most_common']}"
                )

        # Missing values analysis
        missing_data = self.data.isnull().sum()
        missing_percent = (missing_data / len(self.data)) * 100
        self.analysis_results["missing_analysis"] = {
            "missing_counts": missing_data.to_dict(),
            "missing_percentages": missing_percent.to_dict(),
        }

        if missing_data.sum() > 0:
            print(f"\nMissing Data:")
            for col, count in missing_data[missing_data > 0].items():
                print(f"  {col}: {count} ({missing_percent[col]:.1f}%)")

    def identify_patterns_and_anomalies(self):
        """Identify patterns and anomalies in the data."""
        print("\n=== PATTERNS & ANOMALIES ===")

        patterns = {}
        anomalies = {}

        # Correlation analysis for numeric columns
        if len(self.numeric_columns) > 1:
            correlation_matrix = self.data[self.numeric_columns].corr()

            # Find strong correlations
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # Strong correlation threshold
                        strong_correlations.append(
                            {
                                "columns": (
                                    correlation_matrix.columns[i],
                                    correlation_matrix.columns[j],
                                ),
                                "correlation": corr_value,
                            }
                        )

            patterns["strong_correlations"] = strong_correlations
            print(f"\nStrong Correlations (>0.7):")
            for corr in strong_correlations:
                print(
                    f"  {corr['columns'][0]} ↔ {corr['columns'][1]}: {corr['correlation']:.3f}"
                )

        # Outlier detection using IQR and Isolation Forest
        if self.numeric_columns:
            outliers = {}

            # IQR method
            for col in self.numeric_columns:
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_mask = (self.data[col] < lower_bound) | (
                    self.data[col] > upper_bound
                )
                outlier_count = outlier_mask.sum()

                if outlier_count > 0:
                    outliers[col] = {
                        "count": outlier_count,
                        "percentage": (outlier_count / len(self.data)) * 100,
                        "method": "IQR",
                    }

            # Isolation Forest for multivariate outliers
            if len(self.numeric_columns) > 1:
                # Handle missing values
                numeric_data = self.data[self.numeric_columns].fillna(
                    self.data[self.numeric_columns].mean()
                )

                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                outlier_labels = iso_forest.fit_predict(numeric_data)
                outlier_count = (outlier_labels == -1).sum()

                outliers["multivariate"] = {
                    "count": outlier_count,
                    "percentage": (outlier_count / len(self.data)) * 100,
                    "method": "Isolation Forest",
                }

            anomalies["outliers"] = outliers
            print(f"\nOutliers Detected:")
            for col, info in outliers.items():
                print(
                    f"  {col}: {info['count']} outliers ({info['percentage']:.1f}%) - {info['method']}"
                )

        # Pattern detection in categorical data
        if self.categorical_columns:
            cat_patterns = {}
            for col in self.categorical_columns:
                value_counts = self.data[col].value_counts()

                # Check for highly skewed distributions
                if len(value_counts) > 1:
                    top_category_percentage = (
                        value_counts.iloc[0] / len(self.data)
                    ) * 100
                    if top_category_percentage > 80:
                        cat_patterns[col] = {
                            "type": "highly_skewed",
                            "dominant_category": value_counts.index[0],
                            "percentage": top_category_percentage,
                        }

            if cat_patterns:
                patterns["categorical_patterns"] = cat_patterns
                print(f"\nCategorical Patterns:")
                for col, pattern in cat_patterns.items():
                    print(
                        f"  {col}: {pattern['type']} - {pattern['dominant_category']} ({pattern['percentage']:.1f}%)"
                    )

        self.analysis_results["patterns"] = patterns
        self.analysis_results["anomalies"] = anomalies

    def create_visualizations(self):
        """Create comprehensive visualizations."""
        print("\n=== CREATING VISUALIZATIONS ===")

        # Set up the plotting style
        plt.style.use("seaborn-v0_8")
        fig_count = 0

        # 1. Data Overview
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle("Data Overview", fontsize=16, fontweight="bold")

        # Missing values heatmap
        if self.data.isnull().sum().sum() > 0:
            sns.heatmap(self.data.isnull(), ax=axes[0, 0], cbar=True, yticklabels=False)
            axes[0, 0].set_title("Missing Values Pattern")
        else:
            axes[0, 0].text(
                0.5,
                0.5,
                "No Missing Values",
                ha="center",
                va="center",
                transform=axes[0, 0].transAxes,
            )
            axes[0, 0].set_title("Missing Values Pattern")

        # Data types distribution
        dtype_counts = self.data.dtypes.value_counts()
        axes[0, 1].pie(
            dtype_counts.values, labels=dtype_counts.index, autopct="%1.1f%%"
        )
        axes[0, 1].set_title("Data Types Distribution")

        # Numeric vs Categorical columns
        col_types = ["Numeric", "Categorical"]
        col_counts = [len(self.numeric_columns), len(self.categorical_columns)]
        axes[1, 0].bar(col_types, col_counts, color=["skyblue", "lightcoral"])
        axes[1, 0].set_title("Column Types")
        axes[1, 0].set_ylabel("Count")

        # Memory usage by column
        memory_usage = self.data.memory_usage(deep=True)
        top_memory = memory_usage.nlargest(10)
        axes[1, 1].barh(range(len(top_memory)), top_memory.values)
        axes[1, 1].set_yticks(range(len(top_memory)))
        axes[1, 1].set_yticklabels(top_memory.index)
        axes[1, 1].set_title("Memory Usage by Column (Top 10)")
        axes[1, 1].set_xlabel("Bytes")

        plt.tight_layout()
        plt.savefig("data_overview.png", dpi=300, bbox_inches="tight")
        plt.close()
        fig_count += 1

        # 2. Numeric columns analysis
        if self.numeric_columns:
            n_numeric = len(self.numeric_columns)
            if n_numeric > 1:
                # Correlation heatmap
                plt.figure(figsize=(10, 8))
                correlation_matrix = self.data[self.numeric_columns].corr()
                sns.heatmap(
                    correlation_matrix,
                    annot=True,
                    cmap="coolwarm",
                    center=0,
                    square=True,
                    linewidths=0.5,
                )
                plt.title("Correlation Matrix - Numeric Variables")
                plt.tight_layout()
                plt.savefig("correlation_heatmap.png", dpi=300, bbox_inches="tight")
                plt.close()
                fig_count += 1

            # Distribution plots
            n_cols = min(4, n_numeric)
            n_rows = (n_numeric + n_cols - 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
            if n_rows == 1:
                axes = axes.reshape(1, -1) if n_numeric > 1 else [axes]

            for i, col in enumerate(self.numeric_columns):
                row = i // n_cols
                col_idx = i % n_cols

                if n_rows == 1:
                    ax = axes[col_idx] if n_numeric > 1 else axes
                else:
                    ax = axes[row, col_idx]

                self.data[col].hist(bins=30, ax=ax, alpha=0.7, color="skyblue")
                ax.set_title(f"{col} Distribution")
                ax.set_xlabel(col)
                ax.set_ylabel("Frequency")

            # Hide empty subplots
            for i in range(n_numeric, n_rows * n_cols):
                row = i // n_cols
                col_idx = i % n_cols
                if n_rows == 1:
                    if n_numeric > 1:
                        axes[col_idx].set_visible(False)
                else:
                    axes[row, col_idx].set_visible(False)

            plt.suptitle(
                "Numeric Variables Distribution", fontsize=16, fontweight="bold"
            )
            plt.tight_layout()
            plt.savefig("numeric_distributions.png", dpi=300, bbox_inches="tight")
            plt.close()
            fig_count += 1

        # 3. Categorical columns analysis
        if self.categorical_columns:
            n_cat = len(self.categorical_columns)
            n_cols = min(2, n_cat)
            n_rows = (n_cat + n_cols - 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
            if n_rows == 1:
                axes = axes.reshape(1, -1) if n_cat > 1 else [axes]

            for i, col in enumerate(self.categorical_columns):
                row = i // n_cols
                col_idx = i % n_cols

                if n_rows == 1:
                    ax = axes[col_idx] if n_cat > 1 else axes
                else:
                    ax = axes[row, col_idx]

                # Show only top 10 categories
                top_categories = self.data[col].value_counts().head(10)
                top_categories.plot(kind="bar", ax=ax, color="lightcoral")
                ax.set_title(f"{col} - Top Categories")
                ax.set_xlabel(col)
                ax.set_ylabel("Count")
                ax.tick_params(axis="x", rotation=45)

            # Hide empty subplots
            for i in range(n_cat, n_rows * n_cols):
                row = i // n_cols
                col_idx = i % n_cols
                if n_rows == 1:
                    if n_cat > 1:
                        axes[col_idx].set_visible(False)
                else:
                    axes[row, col_idx].set_visible(False)

            plt.suptitle(
                "Categorical Variables Distribution", fontsize=16, fontweight="bold"
            )
            plt.tight_layout()
            plt.savefig("categorical_distributions.png", dpi=300, bbox_inches="tight")
            plt.close()
            fig_count += 1

        # 4. Outliers visualization
        if self.numeric_columns:
            n_cols = min(3, len(self.numeric_columns))
            n_rows = (len(self.numeric_columns) + n_cols - 1) // n_cols

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
            if n_rows == 1:
                axes = axes.reshape(1, -1) if len(self.numeric_columns) > 1 else [axes]

            for i, col in enumerate(self.numeric_columns):
                row = i // n_cols
                col_idx = i % n_cols

                if n_rows == 1:
                    ax = axes[col_idx] if len(self.numeric_columns) > 1 else axes
                else:
                    ax = axes[row, col_idx]

                # Box plot for outlier detection
                self.data[col].plot(kind="box", ax=ax, color="lightgreen")
                ax.set_title(f"{col} - Outlier Detection")
                ax.set_ylabel(col)

            # Hide empty subplots
            for i in range(len(self.numeric_columns), n_rows * n_cols):
                row = i // n_cols
                col_idx = i % n_cols
                if n_rows == 1:
                    if len(self.numeric_columns) > 1:
                        axes[col_idx].set_visible(False)
                else:
                    axes[row, col_idx].set_visible(False)

            plt.suptitle(
                "Outlier Detection - Box Plots", fontsize=16, fontweight="bold"
            )
            plt.tight_layout()
            plt.savefig("outlier_detection.png", dpi=300, bbox_inches="tight")
            plt.close()
            fig_count += 1

        print(f"✓ Created {fig_count} visualization files")
        return fig_count

    def generate_actionable_insights(self):
        """Generate actionable insights based on the analysis."""
        print("\n=== ACTIONABLE INSIGHTS ===")

        insights = []

        # Data quality insights
        missing_pct = (
            self.data.isnull().sum().sum() / (self.data.shape[0] * self.data.shape[1])
        ) * 100
        if missing_pct > 5:
            insights.append(
                {
                    "category": "Data Quality",
                    "priority": "High",
                    "insight": f"Dataset has {missing_pct:.1f}% missing values",
                    "action": "Consider data imputation strategies or investigate data collection process",
                }
            )

        if self.data.duplicated().sum() > 0:
            insights.append(
                {
                    "category": "Data Quality",
                    "priority": "Medium",
                    "insight": f"Found {self.data.duplicated().sum()} duplicate rows",
                    "action": "Review and remove duplicate records if they are truly duplicates",
                }
            )

        # Statistical insights
        if "strong_correlations" in self.analysis_results.get("patterns", {}):
            correlations = self.analysis_results["patterns"]["strong_correlations"]
            if correlations:
                insights.append(
                    {
                        "category": "Statistical",
                        "priority": "Medium",
                        "insight": f"Found {len(correlations)} strong correlations between variables",
                        "action": "Consider feature engineering or multicollinearity handling in modeling",
                    }
                )

        # Outlier insights
        if "outliers" in self.analysis_results.get("anomalies", {}):
            outliers = self.analysis_results["anomalies"]["outliers"]
            high_outlier_cols = [
                col for col, info in outliers.items() if info["percentage"] > 5
            ]
            if high_outlier_cols:
                insights.append(
                    {
                        "category": "Anomalies",
                        "priority": "High",
                        "insight": f'Columns with >5% outliers: {", ".join(high_outlier_cols)}',
                        "action": "Investigate outliers for data entry errors or consider robust analysis methods",
                    }
                )

        # Categorical insights
        if "categorical_patterns" in self.analysis_results.get("patterns", {}):
            skewed_cols = self.analysis_results["patterns"]["categorical_patterns"]
            if skewed_cols:
                insights.append(
                    {
                        "category": "Distribution",
                        "priority": "Medium",
                        "insight": f'Highly skewed categorical variables: {", ".join(skewed_cols.keys())}',
                        "action": "Consider stratified sampling or class balancing techniques",
                    }
                )

        # Sample size insights
        if self.data.shape[0] < 1000:
            insights.append(
                {
                    "category": "Sample Size",
                    "priority": "Medium",
                    "insight": f"Small sample size: {self.data.shape[0]} rows",
                    "action": "Consider collecting more data or using appropriate small-sample techniques",
                }
            )

        # Memory usage insights
        memory_mb = self.data.memory_usage(deep=True).sum() / 1024 / 1024
        if memory_mb > 100:
            insights.append(
                {
                    "category": "Performance",
                    "priority": "Low",
                    "insight": f"Large memory usage: {memory_mb:.1f} MB",
                    "action": "Consider data type optimization or chunked processing",
                }
            )

        self.analysis_results["insights"] = insights

        print("\nKey Insights:")
        for i, insight in enumerate(insights, 1):
            print(f"{i}. [{insight['priority']}] {insight['insight']}")
            print(f"   Action: {insight['action']}\n")

        return insights

    def generate_report(self):
        """Generate a comprehensive markdown report."""
        report = f"""# Data Analysis Report

## Dataset Overview
- **File:** {self.csv_path}
- **Dimensions:** {self.data.shape[0]} rows × {self.data.shape[1]} columns
- **Memory Usage:** {self.data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB
- **Missing Values:** {self.data.isnull().sum().sum()} ({( \
    self.data.isnull().sum().sum() / (self.data.shape[0] * self.data.shape[1]) * 100):.1f}%)
- **Duplicate Rows:** {self.data.duplicated().sum()}

## Column Types
- **Numeric Columns:** {len(self.numeric_columns)} ({', '.join(self.numeric_columns[:5])}{'...' \
    if len(self.numeric_columns) > 5 \
    else ''})
- **Categorical Columns:** {len(self.categorical_columns)} ({', '.join(self.categorical_columns[:5])}{'...' \
    if len(self.categorical_columns) > 5 \
    else ''})

## Summary Statistics

### Numeric Variables
"""

        if self.numeric_columns:
            numeric_stats = self.data[self.numeric_columns].describe()
            report += f"```\n{numeric_stats.to_string()}\n```\n\n"

        report += "### Categorical Variables\n"
        if self.categorical_columns:
            for col in self.categorical_columns[:3]:  # Show first 3 categorical columns
                unique_count = self.data[col].nunique()
                most_common = (
                    self.data[col].mode().iloc[0] if not self.data[col].empty else "N/A"
                )
                report += f"- **{col}:** {unique_count} unique values, most common: '{most_common}'\n"

        report += "\n## Patterns & Anomalies\n\n"

        # Strong correlations
        if "strong_correlations" in self.analysis_results.get("patterns", {}):
            correlations = self.analysis_results["patterns"]["strong_correlations"]
            if correlations:
                report += "### Strong Correlations (>0.7)\n"
                for corr in correlations:
                    report += f"- {corr['columns'][0]} ↔ {corr['columns'][1]}: {corr['correlation']:.3f}\n"
                report += "\n"

        # Outliers
        if "outliers" in self.analysis_results.get("anomalies", {}):
            outliers = self.analysis_results["anomalies"]["outliers"]
            if outliers:
                report += "### Outliers Detected\n"
                for col, info in outliers.items():
                    report += f"- **{col}:** {info['count']} " \
                        "outliers ({info['percentage']:.1f}%) using {info['method']}\n"
                report += "\n"

        # Categorical patterns
        if "categorical_patterns" in self.analysis_results.get("patterns", {}):
            patterns = self.analysis_results["patterns"]["categorical_patterns"]
            if patterns:
                report += "### Categorical Patterns\n"
                for col, pattern in patterns.items():
                    report += f"- **{col}:** {pattern['type']} - {pattern['dominant_category']} " \
                        "dominates ({pattern['percentage']:.1f}%)\n"
                report += "\n"

        # Visualizations
        report += "## Visualizations\n\n"
        report += "The following visualizations have been generated:\n"
        report += "- `data_overview.png` - General data overview and structure\n"
        if self.numeric_columns:
            if len(self.numeric_columns) > 1:
                report += "- `correlation_heatmap.png` - Correlation matrix of numeric variables\n"
            report += "- `numeric_distributions.png` - Distribution plots for numeric variables\n"
            report += "- `outlier_detection.png` - Box plots for outlier detection\n"
        if self.categorical_columns:
            report += "- `categorical_distributions.png` - Distribution plots for categorical " \
                "variables\n"

        # Actionable insights
        report += "\n## Actionable Insights\n\n"

        insights = self.analysis_results.get("insights", [])
        if insights:
            for i, insight in enumerate(insights, 1):
                report += (
                    f"### {i}. {insight['category']} - {insight['priority']} Priority\n"
                )
                report += f"**Insight:** {insight['insight']}\n\n"
                report += f"**Recommended Action:** {insight['action']}\n\n"

        report += "## Recommendations\n\n"

        # Generate specific recommendations
        recommendations = []

        if self.data.isnull().sum().sum() > 0:
            recommendations.append(
                "Address missing values through imputation or removal strategies"
            )

        if self.data.duplicated().sum() > 0:
            recommendations.append("Investigate and handle duplicate records")

        if "outliers" in self.analysis_results.get("anomalies", {}):
            recommendations.append(
                "Analyze outliers to determine if they represent errors or genuine extreme values"
            )

        if len(self.numeric_columns) > 1:
            recommendations.append(
                "Consider feature engineering based on correlation patterns"
            )

        if self.categorical_columns:
            recommendations.append(
                "Evaluate categorical variable encoding strategies for modeling"
            )

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "The dataset appears to be in good condition with no major issues identified.\n" \
                "The dataset appears to be in good condition with no major issues identified.\n" \
                "The dataset appears to be in good condition with no major issues identified.\n"

        report += f"\n---\n*Report generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return report

    def run_complete_analysis(self):
        """Run the complete analysis pipeline."""
        print("🔍 Starting Comprehensive Data Analysis...")

        # Load data
        if not self.load_data():
            return False

        # Generate summary statistics
        self.generate_summary_statistics()

        # Identify patterns and anomalies
        self.identify_patterns_and_anomalies()

        # Create visualizations
        self.create_visualizations()

        # Generate actionable insights
        self.generate_actionable_insights()

        # Generate report
        report = self.generate_report()

        # Save report
        with open("data_analysis_report.md", "w") as f:
            f.write(report)

        print("✅ Analysis complete! Generated files:")
        print("   - data_analysis_report.md (comprehensive report)")
        print("   - Various .png files (visualizations)")

        return True


def main():
    """Main function to run the data analysis."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python data_analysis.py <path_to_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Create analyzer and run analysis
    analyzer = DataAnalyzer(csv_path)
    success = analyzer.run_complete_analysis()

    if success:
        print("\n🎉 Data analysis completed successfully!")
    else:
        print("\n❌ Data analysis failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
