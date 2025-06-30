import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Union, Any
import re
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class WebAnalyzer:
    def __init__(self, headers: Optional[Dict] = None, delay: float = 1.0):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.delay = delay
        self.data = None
        self.df = None
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def scrape_table_data(self, url: str, table_selector: str = 'table', 
                         column_names: Optional[List[str]] = None) -> pd.DataFrame:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tables = soup.select(table_selector)
            if not tables:
                raise ValueError(f"No tables found with selector: {table_selector}")
            
            table = tables[0]
            rows = table.find_all('tr')
            
            data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    data.append(row_data)
            
            if not data:
                raise ValueError("No data found in table")
            
            if column_names:
                df = pd.DataFrame(data[1:], columns=column_names)
            else:
                df = pd.DataFrame(data[1:], columns=data[0])
            
            self.df = df
            time.sleep(self.delay)
            return df
            
        except Exception as e:
            print(f"Error scraping table data: {e}")
            return pd.DataFrame()

    def scrape_list_data(self, url: str, list_selector: str, 
                        item_selectors: Dict[str, str]) -> pd.DataFrame:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            container = soup.select_one(list_selector)
            if not container:
                raise ValueError(f"No container found with selector: {list_selector}")
            
            items = container.find_all(recursive=True)
            data = []
            
            for item in items:
                item_data = {}
                for key, selector in item_selectors.items():
                    element = item.select_one(selector)
                    item_data[key] = element.get_text(strip=True) if element else None
                
                if any(item_data.values()):
                    data.append(item_data)
            
            df = pd.DataFrame(data)
            self.df = df
            time.sleep(self.delay)
            return df
            
        except Exception as e:
            print(f"Error scraping list data: {e}")
            return pd.DataFrame()

    def scrape_custom_data(self, url: str, selectors: Dict[str, str]) -> pd.DataFrame:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {}
            for key, selector in selectors.items():
                elements = soup.select(selector)
                data[key] = [elem.get_text(strip=True) for elem in elements]
            
            max_len = max(len(values) for values in data.values()) if data else 0
            for key in data:
                while len(data[key]) < max_len:
                    data[key].append(None)
            
            df = pd.DataFrame(data)
            self.df = df
            time.sleep(self.delay)
            return df
            
        except Exception as e:
            print(f"Error scraping custom data: {e}")
            return pd.DataFrame()

    def clean_numeric_data(self, columns: List[str], remove_chars: str = r'[^\d.-]') -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        df_clean = self.df.copy()
        for col in columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(str).str.replace(remove_chars, '', regex=True)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        self.df = df_clean
        return df_clean

    def basic_stats(self, numeric_only: bool = True) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        if numeric_only:
            return self.df.select_dtypes(include=[np.number]).describe()
        return self.df.describe(include='all')

    def correlation_analysis(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            raise ValueError("No numeric columns found for correlation analysis")
        
        return numeric_df.corr()

    def plot_distribution(self, column: str, plot_type: str = 'hist', 
                         figsize: tuple = (10, 6), bins: int = 30):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        plt.figure(figsize=figsize)
        
        if plot_type == 'hist':
            plt.hist(self.df[column].dropna(), bins=bins, alpha=0.7, edgecolor='black')
            plt.title(f'Distribution of {column}')
            plt.xlabel(column)
            plt.ylabel('Frequency')
        elif plot_type == 'box':
            sns.boxplot(y=self.df[column].dropna())
            plt.title(f'Box Plot of {column}')
        elif plot_type == 'violin':
            sns.violinplot(y=self.df[column].dropna())
            plt.title(f'Violin Plot of {column}')
        
        plt.tight_layout()
        plt.show()

    def plot_correlation_heatmap(self, figsize: tuple = (12, 8), annot: bool = True):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        corr_matrix = self.correlation_analysis()
        
        plt.figure(figsize=figsize)
        sns.heatmap(corr_matrix, annot=annot, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5)
        plt.title('Correlation Heatmap')
        plt.tight_layout()
        plt.show()

    def plot_scatter(self, x_col: str, y_col: str, hue_col: str = None, 
                    figsize: tuple = (10, 6)):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        plt.figure(figsize=figsize)
        if hue_col:
            sns.scatterplot(data=self.df, x=x_col, y=y_col, hue=hue_col)
        else:
            sns.scatterplot(data=self.df, x=x_col, y=y_col)
        
        plt.title(f'{y_col} vs {x_col}')
        plt.tight_layout()
        plt.show()

    def plot_bar_chart(self, x_col: str, y_col: str = None, agg_func: str = 'count',
                      figsize: tuple = (12, 6), top_n: int = None):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        plt.figure(figsize=figsize)
        
        if y_col is None:
            data = self.df[x_col].value_counts()
            if top_n:
                data = data.head(top_n)
            data.plot(kind='bar')
            plt.title(f'Count of {x_col}')
        else:
            if agg_func == 'count':
                data = self.df.groupby(x_col)[y_col].count()
            elif agg_func == 'sum':
                data = self.df.groupby(x_col)[y_col].sum()
            elif agg_func == 'mean':
                data = self.df.groupby(x_col)[y_col].mean()
            
            if top_n:
                data = data.head(top_n)
            data.plot(kind='bar')
            plt.title(f'{agg_func.title()} of {y_col} by {x_col}')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def plot_time_series(self, date_col: str, value_col: str, 
                        date_format: str = None, figsize: tuple = (12, 6)):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        df_time = self.df.copy()
        if date_format:
            df_time[date_col] = pd.to_datetime(df_time[date_col], format=date_format)
        else:
            df_time[date_col] = pd.to_datetime(df_time[date_col])
        
        df_time = df_time.sort_values(date_col)
        
        plt.figure(figsize=figsize)
        plt.plot(df_time[date_col], df_time[value_col], marker='o')
        plt.title(f'{value_col} over Time')
        plt.xlabel('Date')
        plt.ylabel(value_col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def generate_report(self, title: str = "Web Scraping Analysis Report") -> str:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        report = f"\n{'='*50}\n{title}\n{'='*50}\n\n"
        
        report += f"Dataset Overview:\n"
        report += f"- Shape: {self.df.shape}\n"
        report += f"- Columns: {list(self.df.columns)}\n"
        report += f"- Memory usage: {self.df.memory_usage().sum()} bytes\n\n"
        
        report += f"Missing Values:\n{self.df.isnull().sum()}\n\n"
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report += f"Numeric Columns Summary:\n{self.basic_stats()}\n\n"
        
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            report += f"Categorical Columns:\n"
            for col in categorical_cols:
                unique_count = self.df[col].nunique()
                report += f"- {col}: {unique_count} unique values\n"
        
        return report

    def export_data(self, filename: str, format: str = 'csv'):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        if format.lower() == 'csv':
            self.df.to_csv(filename, index=False)
        elif format.lower() == 'json':
            self.df.to_json(filename, orient='records', indent=2)
        elif format.lower() == 'excel':
            self.df.to_excel(filename, index=False)
        else:
            raise ValueError("Supported formats: csv, json, excel")
        
        print(f"Data exported to {filename}")

    def get_data(self) -> pd.DataFrame:
        return self.df.copy() if self.df is not None else pd.DataFrame()
    
    def advanced_stats(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {"error": "No numeric columns found"}
        
        stats_dict = {}
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) > 0:
                stats_dict[col] = {
                    'mean': data.mean(),
                    'median': data.median(),
                    'mode': data.mode().iloc[0] if not data.mode().empty else np.nan,
                    'std': data.std(),
                    'variance': data.var(),
                    'skewness': stats.skew(data),
                    'kurtosis': stats.kurtosis(data),
                    'q25': data.quantile(0.25),
                    'q75': data.quantile(0.75),
                    'iqr': data.quantile(0.75) - data.quantile(0.25),
                    'outliers_count': len(data[(data < data.quantile(0.25) - 1.5 * (data.quantile(0.75) - data.quantile(0.25))) | 
                                                (data > data.quantile(0.75) + 1.5 * (data.quantile(0.75) - data.quantile(0.25)))])
                }
        
        return stats_dict
    
    def detect_outliers(self, method: str = 'iqr') -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        outliers_df = pd.DataFrame()
        
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            
            if method == 'iqr':
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)]
            
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(data))
                outliers = self.df[np.abs(stats.zscore(self.df[col].fillna(0))) > 3]
            
            if not outliers.empty:
                outliers_df = pd.concat([outliers_df, outliers])
        
        return outliers_df.drop_duplicates()
    
    def perform_clustering(self, columns: List[str], n_clusters: int = 3, 
                          plot: bool = True, figsize: tuple = (10, 8)) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        cluster_data = self.df[columns].select_dtypes(include=[np.number]).dropna()
        if cluster_data.empty:
            raise ValueError("No numeric data available for clustering")
        
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(cluster_data)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(scaled_data)
        
        result_df = cluster_data.copy()
        result_df['cluster'] = clusters
        
        if plot and len(columns) >= 2:
            plt.figure(figsize=figsize)
            scatter = plt.scatter(result_df[columns[0]], result_df[columns[1]], 
                                c=result_df['cluster'], cmap='viridis', alpha=0.7)
            plt.colorbar(scatter)
            plt.xlabel(columns[0])
            plt.ylabel(columns[1])
            plt.title(f'K-Means Clustering ({n_clusters} clusters)')
            plt.tight_layout()
            plt.show()
        
        return result_df
    
    def regression_analysis(self, x_col: str, y_col: str, plot: bool = True, 
                           figsize: tuple = (10, 6)) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        data = self.df[[x_col, y_col]].dropna()
        if data.empty:
            raise ValueError("No valid data for regression analysis")
        
        X = data[x_col].values.reshape(-1, 1)
        y = data[y_col].values
        
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        
        r2 = r2_score(y, y_pred)
        correlation = data[x_col].corr(data[y_col])
        
        if plot:
            plt.figure(figsize=figsize)
            plt.scatter(data[x_col], data[y_col], alpha=0.6, label='Data points')
            plt.plot(data[x_col], y_pred, color='red', linewidth=2, label=f'Regression line (R² = {r2:.3f})')
            plt.xlabel(x_col)
            plt.ylabel(y_col)
            plt.title(f'Linear Regression: {y_col} vs {x_col}')
            plt.legend()
            plt.tight_layout()
            plt.show()
        
        return {
            'slope': model.coef_[0],
            'intercept': model.intercept_,
            'r_squared': r2,
            'correlation': correlation,
            'model': model
        }
    
    def plot_advanced_distribution(self, column: str, figsize: tuple = (15, 10)):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        data = self.df[column].dropna()
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        axes[0, 0].hist(data, bins=30, alpha=0.7, edgecolor='black')
        axes[0, 0].set_title(f'Histogram of {column}')
        axes[0, 0].set_xlabel(column)
        axes[0, 0].set_ylabel('Frequency')
        
        sns.boxplot(y=data, ax=axes[0, 1])
        axes[0, 1].set_title(f'Box Plot of {column}')
        
        stats.probplot(data, dist="norm", plot=axes[1, 0])
        axes[1, 0].set_title(f'Q-Q Plot of {column}')
        
        sns.violinplot(y=data, ax=axes[1, 1])
        axes[1, 1].set_title(f'Violin Plot of {column}')
        
        plt.tight_layout()
        plt.show()
    
    def plot_correlation_matrix(self, method: str = 'pearson', figsize: tuple = (12, 10)):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            raise ValueError("No numeric columns found")
        
        corr_matrix = numeric_df.corr(method=method)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, ax=ax1)
        ax1.set_title(f'{method.title()} Correlation Heatmap')
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, ax=ax2)
        ax2.set_title(f'{method.title()} Correlation (Lower Triangle)')
        
        plt.tight_layout()
        plt.show()
        
        return corr_matrix
    
    def plot_pairwise_relationships(self, columns: List[str] = None, sample_size: int = 1000):
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        if columns is None:
            numeric_df = self.df.select_dtypes(include=[np.number])
            columns = numeric_df.columns.tolist()
        
        plot_data = self.df[columns].select_dtypes(include=[np.number])
        
        if len(plot_data) > sample_size:
            plot_data = plot_data.sample(n=sample_size, random_state=42)
        
        sns.pairplot(plot_data, diag_kind='hist')
        plt.suptitle('Pairwise Relationships', y=1.02)
        plt.tight_layout()
        plt.show()
    
    def comprehensive_analysis(self, target_column: str = None) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError("No data available. Please scrape data first.")
        
        analysis = {
            'basic_info': {
                'shape': self.df.shape,
                'columns': list(self.df.columns),
                'dtypes': self.df.dtypes.to_dict(),
                'missing_values': self.df.isnull().sum().to_dict(),
                'memory_usage': self.df.memory_usage().sum()
            },
            'descriptive_stats': self.basic_stats().to_dict() if not self.df.select_dtypes(include=[np.number]).empty else {},
            'advanced_stats': self.advanced_stats(),
            'outliers_count': len(self.detect_outliers()) if not self.df.select_dtypes(include=[np.number]).empty else 0
        }
        
        if target_column and target_column in self.df.columns:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if target_column in numeric_cols and len(numeric_cols) > 1:
                correlations = {}
                for col in numeric_cols:
                    if col != target_column:
                        try:
                            corr = self.df[col].corr(self.df[target_column])
                            if not np.isnan(corr):
                                correlations[col] = corr
                        except:
                            pass
                analysis['target_correlations'] = correlations
        
        return analysis