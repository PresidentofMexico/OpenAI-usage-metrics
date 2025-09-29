"""
OpenAI Usage Metrics Dashboard

A Streamlit-based dashboard for analyzing OpenAI enterprise usage metrics.
Provides interactive visualizations and insights for management reporting.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from io import StringIO
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_processor import DataProcessor
from database import DatabaseManager
import config

# Page configuration
st.set_page_config(
    page_title="OpenAI Usage Metrics Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and data processor
@st.cache_resource
def init_app():
    db = DatabaseManager()
    processor = DataProcessor(db)
    return db, processor

db, processor = init_app()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        width: 300px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Main header
    st.markdown('<h1 class="main-header">📊 OpenAI Usage Metrics Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("🔧 Controls")
        
        # File upload section
        st.subheader("📁 Upload Monthly Data")
        uploaded_file = st.file_uploader(
            "Upload OpenAI Usage Metrics CSV",
            type=['csv'],
            help="Select your monthly OpenAI enterprise usage export file"
        )
        
        if uploaded_file is not None:
            if st.button("Process Upload", type="primary"):
                with st.spinner("Processing data..."):
                    try:
                        # Read uploaded file
                        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                        df = pd.read_csv(stringio)
                        
                        # Process and store data
                        success, message = processor.process_monthly_data(df, uploaded_file.name)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
        
        st.divider()
        
        # Date range selector
        st.subheader("📅 Date Range")
        available_months = db.get_available_months()
        
        if available_months:
            default_end = max(available_months)
            default_start = min(available_months)
            
            date_range = st.date_input(
                "Select date range",
                value=(default_start, default_end),
                min_value=default_start,
                max_value=default_end
            )
        else:
            st.info("No data available. Please upload your first monthly export.")
            return
        
        st.divider()
        
        # Filters
        st.subheader("🔍 Filters")
        users = db.get_unique_users()
        selected_users = st.multiselect("Select Users (leave empty for all)", users)
        
        departments = db.get_unique_departments()
        selected_departments = st.multiselect("Select Departments (leave empty for all)", departments)
    
    # Main dashboard content
    if not available_months:
        st.info("👋 Welcome! Please upload your first OpenAI usage metrics file using the sidebar.")
        
        # Show sample data format
        st.subheader("📋 Expected Data Format")
        sample_data = pd.DataFrame({
            'user_id': ['user1@company.com', 'user2@company.com'],
            'user_name': ['John Doe', 'Jane Smith'],
            'department': ['Engineering', 'Marketing'],
            'date': ['2024-01-15', '2024-01-16'],
            'feature_used': ['ChatGPT', 'API'],
            'usage_count': [25, 15],
            'cost_usd': [12.50, 8.75]
        })
        st.dataframe(sample_data)
        return
    
    # Get filtered data
    if len(date_range) == 2:
        start_date, end_date = date_range
        data = db.get_filtered_data(
            start_date=start_date,
            end_date=end_date,
            users=selected_users if selected_users else None,
            departments=selected_departments if selected_departments else None
        )
    else:
        data = db.get_all_data()
    
    if data.empty:
        st.warning("No data found for the selected filters.")
        return
    
    # Key Metrics Row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = data['user_id'].nunique()
        st.metric("Total Active Users", total_users)
    
    with col2:
        total_usage = data['usage_count'].sum()
        st.metric("Total Usage Events", f"{total_usage:,}")
    
    with col3:
        total_cost = data['cost_usd'].sum()
        st.metric("Total Cost", f"${total_cost:,.2f}")
    
    with col4:
        avg_cost_per_user = total_cost / max(total_users, 1)
        st.metric("Avg Cost per User", f"${avg_cost_per_user:.2f}")
    
    # Usage Trends
    st.subheader("📊 Usage Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily usage trend
        daily_usage = data.groupby('date')['usage_count'].sum().reset_index()
        daily_usage['date'] = pd.to_datetime(daily_usage['date'])
        
        fig_daily = px.line(
            daily_usage, 
            x='date', 
            y='usage_count',
            title='Daily Usage Trend',
            labels={'usage_count': 'Usage Count', 'date': 'Date'}
        )
        fig_daily.update_layout(height=300)
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        # Cost trend
        daily_cost = data.groupby('date')['cost_usd'].sum().reset_index()
        daily_cost['date'] = pd.to_datetime(daily_cost['date'])
        
        fig_cost = px.line(
            daily_cost, 
            x='date', 
            y='cost_usd',
            title='Daily Cost Trend',
            labels={'cost_usd': 'Cost (USD)', 'date': 'Date'}
        )
        fig_cost.update_layout(height=300)
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # User Analysis
    st.subheader("👥 User Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top users by usage
        top_users = data.groupby(['user_name', 'user_id'])['usage_count'].sum().reset_index()
        top_users = top_users.nlargest(10, 'usage_count')
        
        fig_users = px.bar(
            top_users, 
            x='usage_count', 
            y='user_name',
            orientation='h',
            title='Top 10 Users by Usage',
            labels={'usage_count': 'Total Usage', 'user_name': 'User'}
        )
        fig_users.update_layout(height=400)
        st.plotly_chart(fig_users, use_container_width=True)
    
    with col2:
        # Department breakdown
        dept_usage = data.groupby('department')['usage_count'].sum().reset_index()
        
        fig_dept = px.pie(
            dept_usage, 
            values='usage_count', 
            names='department',
            title='Usage by Department'
        )
        fig_dept.update_layout(height=400)
        st.plotly_chart(fig_dept, use_container_width=True)
    
    # Feature Usage Analysis
    st.subheader("🔧 Feature Usage Analysis")
    
    feature_usage = data.groupby('feature_used')['usage_count'].sum().reset_index()
    feature_usage = feature_usage.sort_values('usage_count', ascending=True)
    
    fig_features = px.bar(
        feature_usage, 
        x='usage_count', 
        y='feature_used',
        orientation='h',
        title='Feature Usage Distribution',
        labels={'usage_count': 'Total Usage', 'feature_used': 'Feature'}
    )
    fig_features.update_layout(height=300)
    st.plotly_chart(fig_features, use_container_width=True)
    
    # Management Insights
    st.subheader("💡 Management Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Usage Growth Analysis**")
        growth_data = processor.calculate_growth_metrics(data)
        
        if not growth_data.empty:
            for _, row in growth_data.iterrows():
                growth_rate = row['growth_rate']
                period = row['period']
                
                if growth_rate > 0:
                    st.success(f"📈 {period}: +{growth_rate:.1f}% growth")
                else:
                    st.error(f"📉 {period}: {growth_rate:.1f}% decline")
    
    with col2:
        st.write("**Cost Efficiency Metrics**")
        
        # Cost per usage event
        cost_per_event = total_cost / max(total_usage, 1)
        st.metric("Cost per Usage Event", f"${cost_per_event:.3f}")
        
        # Most expensive departments
        dept_cost = data.groupby('department')['cost_usd'].sum().reset_index()
        dept_cost = dept_cost.nlargest(3, 'cost_usd')
        
        st.write("**Top Cost Centers:**")
        for _, row in dept_cost.iterrows():
            st.write(f"• {row['department']}: ${row['cost_usd']:,.2f}")
    
    # Raw Data View
    with st.expander("📋 View Raw Data", expanded=False):
        st.dataframe(data, use_container_width=True)
        
        # Download filtered data
        csv = data.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"openai_metrics_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()