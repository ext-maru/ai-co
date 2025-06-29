import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Optional, Union
import re
from urllib.parse import urljoin, urlparse
import time
import warnings

class WebAnalyzer:
    def __init__(self, headers: Optional[Dict[str, str]] = None, delay: float = 1.0):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.data = None
        self.df = None
        
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        warnings.filterwarnings('ignore')

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