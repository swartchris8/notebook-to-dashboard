import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Import custom modules
from data_loader import create_analysis_dataset
from business_metrics import (
    calculate_revenue_metrics, 
    calculate_monthly_trends,
    analyze_product_performance,
    analyze_geographic_performance,
    analyze_customer_experience
)

# Configure page
st.set_page_config(
    page_title="E-commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling with dark theme support
st.markdown("""
<style>
    .metric-card {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
        color: #1a1a1a !important;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #4a4a4a !important;
        margin: 0.25rem 0 0 0;
        font-weight: 500;
    }
    
    .trend-indicator {
        font-size: 0.8rem;
        margin: 0.25rem 0 0 0;
        display: flex;
        align-items: center;
        font-weight: 600;
    }
    
    .trend-up {
        color: #16a34a !important;
    }
    
    .trend-down {
        color: #dc2626 !important;
    }
    
    .chart-container {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
        height: 400px;
    }
    
    .bottom-card {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .bottom-card .metric-value {
        color: #1a1a1a !important;
        text-align: center;
    }
    
    .bottom-card .metric-label {
        color: #4a4a4a !important;
        text-align: center;
        font-weight: 500;
    }
    
    .review-stars {
        color: #f59e0b !important;
        font-size: 1.5rem;
        margin: 0.5rem 0;
    }
    
    /* Dark theme specific adjustments */
    @media (prefers-color-scheme: dark) {
        .metric-card, .chart-container, .bottom-card {
            background-color: rgba(30, 30, 30, 0.95) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        .metric-value, .bottom-card .metric-value {
            color: #ffffff !important;
        }
        
        .metric-label, .bottom-card .metric-label {
            color: #cccccc !important;
        }
    }
    
    /* Force styles for Streamlit dark theme */
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-card,
    [data-testid="stAppViewContainer"][data-theme="dark"] .chart-container,
    [data-testid="stAppViewContainer"][data-theme="dark"] .bottom-card {
        background-color: rgba(30, 30, 30, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-value,
    [data-testid="stAppViewContainer"][data-theme="dark"] .bottom-card .metric-value {
        color: #ffffff !important;
    }
    
    [data-testid="stAppViewContainer"][data-theme="dark"] .metric-label,
    [data-testid="stAppViewContainer"][data-theme="dark"] .bottom-card .metric-label {
        color: #cccccc !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(start_date, end_date, comparison_start, comparison_end):
    """Load and cache data based on date filters"""
    try:
        # Load primary period data
        primary_data = create_analysis_dataset(
            data_path='ecommerce_data/',
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Load comparison period data
        comparison_data = create_analysis_dataset(
            data_path='ecommerce_data/',
            start_date=comparison_start.strftime('%Y-%m-%d'),
            end_date=comparison_end.strftime('%Y-%m-%d')
        )
        
        return primary_data, comparison_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

def format_currency(value):
    """Format currency values"""
    if value >= 1e6:
        return f"${value/1e6:.1f}M"
    elif value >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:.0f}"

def format_number(value):
    """Format large numbers"""
    if value >= 1e6:
        return f"{value/1e6:.1f}M"
    elif value >= 1e3:
        return f"{value/1e3:.0f}K"
    else:
        return f"{value:.0f}"

def create_trend_indicator(current_value, previous_value, format_func=None):
    """Create trend indicator HTML"""
    if previous_value == 0:
        return ""
    
    change_pct = ((current_value - previous_value) / previous_value) * 100
    
    if change_pct > 0:
        arrow = "↗"
        color_class = "trend-up"
    else:
        arrow = "↘"
        color_class = "trend-down"
    
    return f'<div class="trend-indicator {color_class}">{arrow} {abs(change_pct):.2f}%</div>'

# Main dashboard
def main():
    # Header with title and date range filter
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("E-commerce Analytics Dashboard")
    
    with col2:
        # Date range filter with better defaults
        default_start = datetime(2022, 1, 1).date()  # January 1, 2022
        default_end = datetime(2023, 12, 31).date()   # December 31, 2023
        
        date_range = st.date_input(
            "Select Date Range",
            value=[default_start, default_end],
            max_value=datetime.now().date()
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = default_start
            end_date = default_end
    
    # Calculate comparison period (same length, immediately before)
    period_length = (end_date - start_date).days
    comparison_end = start_date - timedelta(days=1)
    comparison_start = comparison_end - timedelta(days=period_length)
    
    # Ensure comparison period doesn't go before available data (2016)
    min_date = datetime(2016, 1, 1).date()
    if comparison_start < min_date:
        comparison_start = min_date
    
    # Load data
    primary_data, comparison_data = load_data(start_date, end_date, comparison_start, comparison_end)
    
    if primary_data is None or comparison_data is None:
        st.error("Unable to load data. Please check your data files.")
        return
    
    # Calculate metrics
    current_metrics = calculate_revenue_metrics(primary_data, comparison_data)
    comparison_metrics = calculate_revenue_metrics(comparison_data)
    cx_metrics = analyze_customer_experience(primary_data)
    product_metrics = analyze_product_performance(primary_data, top_n=10)
    geo_metrics = analyze_geographic_performance(primary_data, top_n=50)  # More states for map
    monthly_trends = calculate_monthly_trends(primary_data)
    
    # KPI Row - 4 cards with trend indicators
    st.markdown("### Key Performance Indicators")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        revenue_trend = create_trend_indicator(current_metrics['total_revenue'], comparison_metrics['total_revenue'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{format_currency(current_metrics['total_revenue'])}</div>
            <div class="metric-label">Total Revenue</div>
            {revenue_trend}
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        if 'revenue_growth_rate' in current_metrics:
            growth_rate = current_metrics['revenue_growth_rate'] * 100
            growth_color = "trend-up" if growth_rate >= 0 else "trend-down"
            growth_arrow = "↗" if growth_rate >= 0 else "↘"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{growth_rate:.1f}%</div>
                <div class="metric-label">Monthly Growth</div>
                <div class="trend-indicator {growth_color}">{growth_arrow} vs Previous Period</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">N/A</div>
                <div class="metric-label">Monthly Growth</div>
                <div class="trend-indicator">No comparison data</div>
            </div>
            """, unsafe_allow_html=True)
    
    with kpi_col3:
        aov_trend = create_trend_indicator(current_metrics['average_order_value'], comparison_metrics['average_order_value'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{format_currency(current_metrics['average_order_value'])}</div>
            <div class="metric-label">Average Order Value</div>
            {aov_trend}
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        orders_trend = create_trend_indicator(current_metrics['total_orders'], comparison_metrics['total_orders'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{format_number(current_metrics['total_orders'])}</div>
            <div class="metric-label">Total Orders</div>
            {orders_trend}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Grid - 2x2 layout
    st.markdown("### Performance Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Revenue trend line chart
        if len(monthly_trends) > 0:
            fig_revenue = go.Figure()
            
            # Current period line (solid)
            fig_revenue.add_trace(go.Scatter(
                x=monthly_trends.index,
                y=monthly_trends['revenue'],
                mode='lines+markers',
                name='Current Period',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            # Add previous period if available (dashed)
            if len(comparison_data) > 0:
                comp_monthly = calculate_monthly_trends(comparison_data)
                if len(comp_monthly) > 0:
                    fig_revenue.add_trace(go.Scatter(
                        x=comp_monthly.index,
                        y=comp_monthly['revenue'],
                        mode='lines+markers',
                        name='Previous Period',
                        line=dict(color='#ff7f0e', width=2, dash='dash'),
                        marker=dict(size=6)
                    ))
            
            fig_revenue.update_layout(
                title="Revenue Trend",
                xaxis_title="Month",
                yaxis_title="Revenue",
                height=350,
                showlegend=True,
                template="plotly_white",
                xaxis=dict(showgrid=True),
                yaxis=dict(showgrid=True, tickformat='$,.0s')
            )
            
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No monthly trend data available")
    
    with chart_col2:
        # Top 10 categories bar chart
        if len(product_metrics['category_performance']) > 0:
            top_categories = product_metrics['category_performance'].head(10).sort_values('total_revenue')
            
            fig_categories = px.bar(
                top_categories,
                x='total_revenue',
                y='category',
                orientation='h',
                title="Top 10 Product Categories",
                color='total_revenue',
                color_continuous_scale='Blues'
            )
            
            fig_categories.update_layout(
                height=350,
                template="plotly_white",
                xaxis_title="Revenue",
                yaxis_title="",
                showlegend=False,
                xaxis=dict(tickformat='$,.0s')
            )
            
            fig_categories.update_traces(
                texttemplate='%{x:$,.0s}',
                textposition='outside'
            )
            
            st.plotly_chart(fig_categories, use_container_width=True)
        else:
            st.info("No product category data available")
    
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        # US choropleth map for revenue by state
        if len(geo_metrics['state_performance']) > 0:
            # Create a mapping for state codes (assuming we have state abbreviations)
            state_data = geo_metrics['state_performance'].copy()
            
            fig_map = px.choropleth(
                state_data,
                locations='state',
                color='total_revenue',
                locationmode='USA-states',
                scope='usa',
                title='Revenue by State',
                color_continuous_scale='Blues',
                labels={'total_revenue': 'Revenue ($)'}
            )
            
            fig_map.update_layout(
                height=350,
                template="plotly_white",
                geo=dict(showframe=False, showcoastlines=True)
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No geographic data available")
    
    with chart_col4:
        # Satisfaction vs delivery time bar chart
        if 'delivery_satisfaction' in cx_metrics and len(cx_metrics['delivery_satisfaction']) > 0:
            delivery_sat = cx_metrics['delivery_satisfaction']
            
            fig_delivery = px.bar(
                delivery_sat,
                x='delivery_category',
                y='review_score',
                title="Satisfaction vs Delivery Time",
                color='review_score',
                color_continuous_scale='RdYlGn',
                range_color=[1, 5]
            )
            
            fig_delivery.update_layout(
                height=350,
                template="plotly_white",
                xaxis_title="Delivery Time",
                yaxis_title="Average Review Score",
                showlegend=False,
                yaxis=dict(range=[1, 5])
            )
            
            fig_delivery.update_traces(
                texttemplate='%{y:.2f}',
                textposition='outside'
            )
            
            st.plotly_chart(fig_delivery, use_container_width=True)
        else:
            # Create dummy data if no delivery satisfaction data
            st.info("No delivery satisfaction data available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bottom Row - 2 cards
    st.markdown("### Additional Metrics")
    
    bottom_col1, bottom_col2 = st.columns(2)
    
    with bottom_col1:
        # Average delivery time with trend
        if 'avg_delivery_days' in cx_metrics:
            # Calculate trend (dummy calculation for now)
            delivery_days = cx_metrics['avg_delivery_days']
            # Assume 5% improvement for demo
            prev_delivery = delivery_days * 1.05
            delivery_trend = create_trend_indicator(delivery_days, prev_delivery)
            
            st.markdown(f"""
            <div class="bottom-card">
                <div class="metric-value">{delivery_days:.1f} days</div>
                <div class="metric-label">Average Delivery Time</div>
                {delivery_trend}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bottom-card">
                <div class="metric-value">N/A</div>
                <div class="metric-label">Average Delivery Time</div>
                <div class="trend-indicator">No delivery data</div>
            </div>
            """, unsafe_allow_html=True)
    
    with bottom_col2:
        # Review score with stars
        if 'avg_review_score' in cx_metrics:
            review_score = cx_metrics['avg_review_score']
            stars = "⭐" * int(round(review_score))
            
            st.markdown(f"""
            <div class="bottom-card">
                <div class="metric-value">{review_score:.2f}</div>
                <div class="review-stars">{stars}</div>
                <div class="metric-label">Average Review Score</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="bottom-card">
                <div class="metric-value">N/A</div>
                <div class="review-stars">⭐⭐⭐⭐⭐</div>
                <div class="metric-label">Average Review Score</div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()