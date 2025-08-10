"""
Data Loading and Preprocessing Module for E-commerce Analysis

This module provides functions to load, clean, and prepare e-commerce data
for analysis. It handles data type conversions, merging operations, and
filtering based on configurable date ranges.
"""

import pandas as pd
import warnings
from datetime import datetime
from typing import Dict, Tuple, Optional

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)


def load_raw_data(data_path: str = 'ecommerce_data/') -> Dict[str, pd.DataFrame]:
    """
    Load all raw e-commerce datasets from CSV files.
    
    Args:
        data_path: Path to the directory containing CSV files
        
    Returns:
        Dictionary containing all loaded DataFrames with descriptive keys
    """
    datasets = {
        'orders': pd.read_csv(f'{data_path}orders_dataset.csv'),
        'order_items': pd.read_csv(f'{data_path}order_items_dataset.csv'),
        'products': pd.read_csv(f'{data_path}products_dataset.csv'),
        'customers': pd.read_csv(f'{data_path}customers_dataset.csv'),
        'reviews': pd.read_csv(f'{data_path}order_reviews_dataset.csv')
    }
    
    print(f"Loaded {len(datasets)} datasets:")
    for name, df in datasets.items():
        print(f"  - {name}: {df.shape[0]:,} rows, {df.shape[1]} columns")
    
    return datasets


def prepare_sales_data(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Create a comprehensive sales dataset by merging orders and order items.
    
    Args:
        datasets: Dictionary containing raw DataFrames
        
    Returns:
        Merged sales DataFrame with proper date handling
    """
    # Merge order items with order details
    sales_data = pd.merge(
        left=datasets['order_items'][['order_id', 'order_item_id', 'product_id', 'price', 'freight_value']],
        right=datasets['orders'][['order_id', 'order_status', 'order_purchase_timestamp', 
                                 'order_delivered_customer_date', 'customer_id']],
        on='order_id'
    )
    
    # Convert timestamps to datetime
    sales_data['order_purchase_timestamp'] = pd.to_datetime(sales_data['order_purchase_timestamp'])
    sales_data['order_delivered_customer_date'] = pd.to_datetime(sales_data['order_delivered_customer_date'])
    
    # Extract date components
    sales_data['year'] = sales_data['order_purchase_timestamp'].dt.year
    sales_data['month'] = sales_data['order_purchase_timestamp'].dt.month
    sales_data['quarter'] = sales_data['order_purchase_timestamp'].dt.quarter
    
    # Calculate total revenue (price + freight)
    sales_data['total_revenue'] = sales_data['price'] + sales_data['freight_value']
    
    print(f"Created sales dataset: {sales_data.shape[0]:,} records")
    print(f"Date range: {sales_data['order_purchase_timestamp'].min()} to {sales_data['order_purchase_timestamp'].max()}")
    
    return sales_data


def filter_delivered_orders(sales_data: pd.DataFrame, 
                          year: Optional[int] = None, 
                          month: Optional[int] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Filter sales data for delivered orders within specified date range.
    
    Args:
        sales_data: Sales DataFrame to filter
        year: Specific year to filter (optional)
        month: Specific month to filter (optional, requires year)
        start_date: Start date in 'YYYY-MM-DD' format (optional)
        end_date: End date in 'YYYY-MM-DD' format (optional)
        
    Returns:
        Filtered DataFrame containing only delivered orders
    """
    # Filter for delivered orders
    filtered_data = sales_data[sales_data['order_status'] == 'delivered'].copy()
    
    # Apply date filters
    if year is not None:
        filtered_data = filtered_data[filtered_data['year'] == year]
        
    if month is not None and year is not None:
        filtered_data = filtered_data[filtered_data['month'] == month]
        
    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        filtered_data = filtered_data[filtered_data['order_purchase_timestamp'] >= start_dt]
        
    if end_date is not None:
        end_dt = pd.to_datetime(end_date)
        filtered_data = filtered_data[filtered_data['order_purchase_timestamp'] <= end_dt]
    
    date_filter_info = []
    if year: date_filter_info.append(f"Year: {year}")
    if month: date_filter_info.append(f"Month: {month}")
    if start_date: date_filter_info.append(f"From: {start_date}")
    if end_date: date_filter_info.append(f"To: {end_date}")
    
    filter_desc = ", ".join(date_filter_info) if date_filter_info else "No date filters"
    print(f"Filtered delivered orders: {filtered_data.shape[0]:,} records ({filter_desc})")
    
    return filtered_data


def add_product_categories(sales_data: pd.DataFrame, 
                          products_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add product category information to sales data.
    
    Args:
        sales_data: Sales DataFrame
        products_df: Products DataFrame with category information
        
    Returns:
        Sales DataFrame enriched with product category data
    """
    enriched_data = pd.merge(
        left=sales_data,
        right=products_df[['product_id', 'product_category_name']],
        on='product_id',
        how='left'
    )
    
    missing_categories = enriched_data['product_category_name'].isna().sum()
    if missing_categories > 0:
        print(f"Warning: {missing_categories:,} records missing product category")
    
    return enriched_data


def add_customer_geography(sales_data: pd.DataFrame, 
                          customers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add customer geographic information to sales data.
    
    Args:
        sales_data: Sales DataFrame
        customers_df: Customers DataFrame with geographic information
        
    Returns:
        Sales DataFrame enriched with customer location data
    """
    enriched_data = pd.merge(
        left=sales_data,
        right=customers_df[['customer_id', 'customer_state', 'customer_city']],
        on='customer_id',
        how='left'
    )
    
    missing_geography = enriched_data['customer_state'].isna().sum()
    if missing_geography > 0:
        print(f"Warning: {missing_geography:,} records missing customer geography")
    
    return enriched_data


def add_customer_experience_data(sales_data: pd.DataFrame, 
                                reviews_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add customer experience metrics including reviews and delivery times.
    
    Args:
        sales_data: Sales DataFrame
        reviews_df: Reviews DataFrame with customer feedback
        
    Returns:
        Sales DataFrame enriched with customer experience data
    """
    # Add review scores
    enriched_data = pd.merge(
        left=sales_data,
        right=reviews_df[['order_id', 'review_score']],
        on='order_id',
        how='left'
    )
    
    # Calculate delivery speed for delivered orders
    delivery_mask = enriched_data['order_delivered_customer_date'].notna()
    enriched_data.loc[delivery_mask, 'delivery_days'] = (
        enriched_data.loc[delivery_mask, 'order_delivered_customer_date'] - 
        enriched_data.loc[delivery_mask, 'order_purchase_timestamp']
    ).dt.days
    
    # Categorize delivery speed
    def categorize_delivery_speed(days):
        if pd.isna(days):
            return 'Unknown'
        elif days <= 3:
            return '1-3 days'
        elif days <= 7:
            return '4-7 days'
        else:
            return '8+ days'
    
    enriched_data['delivery_category'] = enriched_data['delivery_days'].apply(categorize_delivery_speed)
    
    missing_reviews = enriched_data['review_score'].isna().sum()
    missing_delivery = enriched_data['delivery_days'].isna().sum()
    
    if missing_reviews > 0:
        print(f"Warning: {missing_reviews:,} records missing review scores")
    if missing_delivery > 0:
        print(f"Warning: {missing_delivery:,} records missing delivery data")
    
    return enriched_data


def create_analysis_dataset(data_path: str = 'ecommerce_data/',
                           year: Optional[int] = None,
                           month: Optional[int] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Create a complete analysis-ready dataset with all enrichments and filters.
    
    Args:
        data_path: Path to the directory containing CSV files
        year: Specific year to filter (optional)
        month: Specific month to filter (optional, requires year)
        start_date: Start date in 'YYYY-MM-DD' format (optional)
        end_date: End date in 'YYYY-MM-DD' format (optional)
        
    Returns:
        Complete analysis-ready DataFrame
    """
    print("Creating analysis dataset...")
    print("=" * 50)
    
    # Load raw data
    datasets = load_raw_data(data_path)
    
    # Prepare base sales data
    sales_data = prepare_sales_data(datasets)
    
    # Filter for delivered orders in specified date range
    filtered_sales = filter_delivered_orders(sales_data, year, month, start_date, end_date)
    
    # Add enrichments
    print("\nEnriching data with additional dimensions...")
    enriched_data = add_product_categories(filtered_sales, datasets['products'])
    enriched_data = add_customer_geography(enriched_data, datasets['customers'])
    enriched_data = add_customer_experience_data(enriched_data, datasets['reviews'])
    
    print(f"\nFinal analysis dataset: {enriched_data.shape[0]:,} records, {enriched_data.shape[1]} columns")
    print("=" * 50)
    
    return enriched_data


def get_data_summary(df: pd.DataFrame) -> None:
    """
    Print a comprehensive summary of the dataset.
    
    Args:
        df: DataFrame to summarize
    """
    print("Dataset Summary:")
    print("=" * 30)
    print(f"Total Records: {df.shape[0]:,}")
    print(f"Total Columns: {df.shape[1]}")
    
    if 'year' in df.columns:
        print(f"\nYear Distribution:")
        year_counts = df['year'].value_counts().sort_index()
        for year, count in year_counts.items():
            print(f"  {year}: {count:,} records")
    
    if 'order_status' in df.columns:
        print(f"\nOrder Status Distribution:")
        status_counts = df['order_status'].value_counts()
        for status, count in status_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {status}: {count:,} records ({pct:.1f}%)")
    
    if 'total_revenue' in df.columns:
        print(f"\nRevenue Summary:")
        print(f"  Total Revenue: ${df['total_revenue'].sum():,.2f}")
        print(f"  Average Order Value: ${df.groupby('order_id')['total_revenue'].sum().mean():.2f}")