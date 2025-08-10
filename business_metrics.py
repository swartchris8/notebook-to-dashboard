"""
Business Metrics Calculation Module for E-commerce Analysis

This module provides functions to calculate key business metrics including
revenue analysis, growth metrics, customer metrics, product performance,
and customer experience indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns


def calculate_revenue_metrics(df: pd.DataFrame, 
                            comparison_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculate comprehensive revenue metrics for the given dataset.
    
    Args:
        df: Primary dataset for analysis
        comparison_df: Optional comparison dataset (e.g., previous period)
        
    Returns:
        Dictionary containing revenue metrics and growth rates
    """
    metrics = {}
    
    # Basic revenue metrics
    metrics['total_revenue'] = df['total_revenue'].sum()
    metrics['total_orders'] = df['order_id'].nunique()
    metrics['total_items_sold'] = len(df)
    metrics['average_order_value'] = df.groupby('order_id')['total_revenue'].sum().mean()
    metrics['average_item_price'] = df['price'].mean()
    
    # Revenue distribution
    order_values = df.groupby('order_id')['total_revenue'].sum()
    metrics['median_order_value'] = order_values.median()
    metrics['revenue_std'] = order_values.std()
    
    # Calculate growth rates if comparison data provided
    if comparison_df is not None:
        comp_metrics = calculate_revenue_metrics(comparison_df)
        
        metrics['revenue_growth_rate'] = (
            (metrics['total_revenue'] - comp_metrics['total_revenue']) / 
            comp_metrics['total_revenue']
        )
        metrics['order_growth_rate'] = (
            (metrics['total_orders'] - comp_metrics['total_orders']) / 
            comp_metrics['total_orders']
        )
        metrics['aov_growth_rate'] = (
            (metrics['average_order_value'] - comp_metrics['average_order_value']) / 
            comp_metrics['average_order_value']
        )
    
    return metrics


def calculate_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate month-over-month growth trends and seasonal patterns.
    
    Args:
        df: Sales dataset with date columns
        
    Returns:
        DataFrame with monthly metrics and growth rates
    """
    # Monthly revenue aggregation
    monthly_data = df.groupby(['year', 'month']).agg({
        'total_revenue': 'sum',
        'order_id': 'nunique',
        'order_item_id': 'count'
    }).reset_index()
    
    # Rename columns for clarity
    monthly_data.columns = ['year', 'month', 'revenue', 'orders', 'items_sold']
    
    # Calculate month-over-month growth rates
    monthly_data = monthly_data.sort_values(['year', 'month'])
    monthly_data['revenue_mom_growth'] = monthly_data['revenue'].pct_change()
    monthly_data['orders_mom_growth'] = monthly_data['orders'].pct_change()
    
    # Calculate average order value
    monthly_data['avg_order_value'] = monthly_data['revenue'] / monthly_data['orders']
    monthly_data['aov_mom_growth'] = monthly_data['avg_order_value'].pct_change()
    
    return monthly_data


def analyze_product_performance(df: pd.DataFrame, top_n: int = 10) -> Dict[str, pd.DataFrame]:
    """
    Analyze product category performance and identify top performers.
    
    Args:
        df: Sales dataset with product information
        top_n: Number of top categories to return
        
    Returns:
        Dictionary containing various product performance metrics
    """
    results = {}
    
    # Revenue by product category
    category_revenue = df.groupby('product_category_name').agg({
        'total_revenue': 'sum',
        'order_id': 'nunique',
        'order_item_id': 'count',
        'price': 'mean'
    }).reset_index()
    
    category_revenue.columns = ['category', 'total_revenue', 'unique_orders', 'items_sold', 'avg_price']
    category_revenue = category_revenue.sort_values('total_revenue', ascending=False)
    
    results['category_performance'] = category_revenue.head(top_n)
    
    # Product category market share
    total_revenue = df['total_revenue'].sum()
    category_revenue['market_share'] = category_revenue['total_revenue'] / total_revenue
    results['market_share'] = category_revenue[['category', 'market_share']].head(top_n)
    
    # Items per order by category
    category_metrics = df.groupby(['order_id', 'product_category_name']).size().reset_index(name='items_per_order')
    avg_items_per_order = category_metrics.groupby('product_category_name')['items_per_order'].mean().reset_index()
    avg_items_per_order = avg_items_per_order.sort_values('items_per_order', ascending=False)
    results['items_per_order'] = avg_items_per_order.head(top_n)
    
    return results


def analyze_geographic_performance(df: pd.DataFrame, top_n: int = 10) -> Dict[str, pd.DataFrame]:
    """
    Analyze sales performance by geographic regions.
    
    Args:
        df: Sales dataset with customer geographic information
        top_n: Number of top regions to return
        
    Returns:
        Dictionary containing geographic performance metrics
    """
    results = {}
    
    # State-level analysis
    state_performance = df.groupby('customer_state').agg({
        'total_revenue': 'sum',
        'order_id': 'nunique',
        'customer_id': 'nunique',
        'price': 'mean'
    }).reset_index()
    
    state_performance.columns = ['state', 'total_revenue', 'total_orders', 'unique_customers', 'avg_item_price']
    state_performance = state_performance.sort_values('total_revenue', ascending=False)
    
    # Calculate revenue per customer by state
    state_performance['revenue_per_customer'] = (
        state_performance['total_revenue'] / state_performance['unique_customers']
    )
    
    results['state_performance'] = state_performance.head(top_n)
    
    # Top states by customer count
    results['top_customer_states'] = state_performance.nlargest(top_n, 'unique_customers')[
        ['state', 'unique_customers', 'total_revenue']
    ]
    
    return results


def analyze_customer_experience(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze customer experience metrics including delivery and satisfaction.
    
    Args:
        df: Sales dataset with customer experience data
        
    Returns:
        Dictionary containing customer experience metrics
    """
    metrics = {}
    
    # Review score analysis
    if 'review_score' in df.columns:
        review_data = df.dropna(subset=['review_score'])
        if len(review_data) > 0:
            metrics['avg_review_score'] = review_data['review_score'].mean()
            metrics['review_score_distribution'] = review_data['review_score'].value_counts(normalize=True)
            
            # Net Promoter Score approximation (5-star = promoter, 1-2 star = detractor)
            promoters = len(review_data[review_data['review_score'] == 5])
            detractors = len(review_data[review_data['review_score'].isin([1, 2])])
            total_reviews = len(review_data)
            
            if total_reviews > 0:
                metrics['nps_score'] = ((promoters - detractors) / total_reviews) * 100
    
    # Delivery performance analysis
    if 'delivery_days' in df.columns:
        delivery_data = df.dropna(subset=['delivery_days'])
        if len(delivery_data) > 0:
            metrics['avg_delivery_days'] = delivery_data['delivery_days'].mean()
            metrics['median_delivery_days'] = delivery_data['delivery_days'].median()
            
            # Delivery category performance
            if 'delivery_category' in df.columns:
                delivery_performance = delivery_data.groupby('delivery_category').agg({
                    'review_score': 'mean',
                    'order_id': 'nunique'
                }).reset_index()
                metrics['delivery_satisfaction'] = delivery_performance
    
    return metrics


def calculate_cohort_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform basic customer cohort analysis based on purchase patterns.
    
    Args:
        df: Sales dataset with customer and date information
        
    Returns:
        DataFrame with cohort metrics
    """
    # Customer first purchase month
    customer_cohorts = df.groupby('customer_id')['order_purchase_timestamp'].min().reset_index()
    customer_cohorts['first_purchase_month'] = customer_cohorts['order_purchase_timestamp'].dt.to_period('M')
    
    # Add cohort information back to main dataset
    df_cohort = df.merge(customer_cohorts[['customer_id', 'first_purchase_month']], on='customer_id')
    df_cohort['order_month'] = df_cohort['order_purchase_timestamp'].dt.to_period('M')
    
    # Calculate period number (months since first purchase)
    df_cohort['period_number'] = (
        df_cohort['order_month'] - df_cohort['first_purchase_month']
    ).apply(attrgetter('n'))
    
    # Cohort table
    cohort_data = df_cohort.groupby(['first_purchase_month', 'period_number'])['customer_id'].nunique().reset_index()
    cohort_table = cohort_data.pivot(index='first_purchase_month', 
                                   columns='period_number', 
                                   values='customer_id')
    
    return cohort_table


def calculate_business_health_score(df: pd.DataFrame, 
                                  comparison_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculate an overall business health score based on key metrics.
    
    Args:
        df: Primary dataset for analysis
        comparison_df: Optional comparison dataset for growth calculations
        
    Returns:
        Dictionary containing health score and component metrics
    """
    health_metrics = {}
    
    # Revenue health (30% weight)
    revenue_metrics = calculate_revenue_metrics(df, comparison_df)
    revenue_score = 70  # Base score
    
    if comparison_df is not None:
        if revenue_metrics['revenue_growth_rate'] > 0:
            revenue_score += min(revenue_metrics['revenue_growth_rate'] * 100, 30)
        else:
            revenue_score += max(revenue_metrics['revenue_growth_rate'] * 100, -30)
    
    health_metrics['revenue_score'] = min(max(revenue_score, 0), 100)
    
    # Customer experience health (25% weight)
    cx_metrics = analyze_customer_experience(df)
    cx_score = 70  # Base score
    
    if 'avg_review_score' in cx_metrics:
        # Scale review score to 0-30 range
        review_contribution = ((cx_metrics['avg_review_score'] - 1) / 4) * 30
        cx_score = 70 + review_contribution - 30  # Adjust to proper scale
    
    health_metrics['customer_experience_score'] = min(max(cx_score, 0), 100)
    
    # Operational efficiency health (20% weight) - based on delivery performance
    ops_score = 70  # Base score
    
    if 'avg_delivery_days' in cx_metrics:
        # Faster delivery = higher score
        if cx_metrics['avg_delivery_days'] <= 5:
            ops_score = 90
        elif cx_metrics['avg_delivery_days'] <= 10:
            ops_score = 80
        elif cx_metrics['avg_delivery_days'] <= 15:
            ops_score = 70
        else:
            ops_score = 50
    
    health_metrics['operational_score'] = ops_score
    
    # Order fulfillment health (25% weight)
    if 'order_status' in df.columns:
        delivered_rate = len(df[df['order_status'] == 'delivered']) / len(df)
        fulfillment_score = delivered_rate * 100
    else:
        fulfillment_score = 70  # Assume good fulfillment if no status data
    
    health_metrics['fulfillment_score'] = fulfillment_score
    
    # Calculate overall health score
    weights = {
        'revenue_score': 0.30,
        'customer_experience_score': 0.25,
        'operational_score': 0.20,
        'fulfillment_score': 0.25
    }
    
    overall_score = sum(health_metrics[metric] * weight for metric, weight in weights.items())
    health_metrics['overall_health_score'] = round(overall_score, 1)
    
    return health_metrics


def generate_executive_summary(df: pd.DataFrame, 
                             comparison_df: Optional[pd.DataFrame] = None,
                             period_label: str = "Analysis Period") -> Dict[str, Any]:
    """
    Generate a comprehensive executive summary of business performance.
    
    Args:
        df: Primary dataset for analysis
        comparison_df: Optional comparison dataset
        period_label: Label for the analysis period
        
    Returns:
        Dictionary containing executive summary metrics
    """
    summary = {'period': period_label}
    
    # Core revenue metrics
    revenue_metrics = calculate_revenue_metrics(df, comparison_df)
    summary.update(revenue_metrics)
    
    # Product performance
    product_performance = analyze_product_performance(df, top_n=5)
    summary['top_categories'] = product_performance['category_performance']['category'].tolist()
    
    # Geographic performance
    geo_performance = analyze_geographic_performance(df, top_n=5)
    summary['top_states'] = geo_performance['state_performance']['state'].tolist()
    
    # Customer experience
    cx_metrics = analyze_customer_experience(df)
    summary.update(cx_metrics)
    
    # Business health
    health_score = calculate_business_health_score(df, comparison_df)
    summary['health_score'] = health_score['overall_health_score']
    
    return summary


# Utility functions for data aggregation
def aggregate_by_time_period(df: pd.DataFrame, 
                           period: str = 'month',
                           metrics: List[str] = None) -> pd.DataFrame:
    """
    Aggregate data by specified time period.
    
    Args:
        df: Dataset to aggregate
        period: Time period ('day', 'week', 'month', 'quarter', 'year')
        metrics: List of metrics to calculate
        
    Returns:
        Aggregated DataFrame
    """
    if metrics is None:
        metrics = ['total_revenue', 'order_id', 'customer_id']
    
    # Create period column
    if period == 'day':
        df['period'] = df['order_purchase_timestamp'].dt.date
    elif period == 'week':
        df['period'] = df['order_purchase_timestamp'].dt.to_period('W')
    elif period == 'month':
        df['period'] = df['order_purchase_timestamp'].dt.to_period('M')
    elif period == 'quarter':
        df['period'] = df['order_purchase_timestamp'].dt.to_period('Q')
    elif period == 'year':
        df['period'] = df['order_purchase_timestamp'].dt.to_period('Y')
    
    # Aggregate metrics
    agg_dict = {}
    for metric in metrics:
        if metric in ['order_id', 'customer_id']:
            agg_dict[metric] = 'nunique'
        else:
            agg_dict[metric] = 'sum'
    
    result = df.groupby('period').agg(agg_dict).reset_index()
    return result


def compare_periods(current_df: pd.DataFrame, 
                   previous_df: pd.DataFrame,
                   metrics: List[str] = None) -> pd.DataFrame:
    """
    Compare metrics between two time periods.
    
    Args:
        current_df: Current period data
        previous_df: Previous period data
        metrics: List of metrics to compare
        
    Returns:
        DataFrame with comparison metrics
    """
    if metrics is None:
        metrics = ['total_revenue', 'total_orders', 'average_order_value']
    
    current_metrics = calculate_revenue_metrics(current_df)
    previous_metrics = calculate_revenue_metrics(previous_df)
    
    comparison = []
    for metric in metrics:
        if metric in current_metrics and metric in previous_metrics:
            current_val = current_metrics[metric]
            previous_val = previous_metrics[metric]
            
            if previous_val != 0:
                change_pct = ((current_val - previous_val) / previous_val) * 100
            else:
                change_pct = np.nan
            
            comparison.append({
                'metric': metric,
                'current_period': current_val,
                'previous_period': previous_val,
                'absolute_change': current_val - previous_val,
                'percent_change': change_pct
            })
    
    return pd.DataFrame(comparison)


# Import operator for cohort analysis
from operator import attrgetter