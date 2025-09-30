"""
OpenAI Usage Metrics Dashboard v2

A Streamlit-based dashboard for analyzing OpenAI enterprise usage metrics.
Enhanced with cost transparency, data quality checks, and improved analytics.
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
    page_title="OpenAI Usage Metrics Dashboard v2",
    page_icon="📊",
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

# Enhanced CSS for MVP2
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
    .calculation-tooltip {
        background: #e8f4fd;
        border-left: 4px solid #1f77b4;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .data-quality-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .data-quality-success {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def display_cost_calculation_details(total_cost, total_users, data):
    """Display detailed cost calculation breakdown."""
    with st.expander("💡 Cost Calculation Details", expanded=False):
        st.markdown("""
        <div class="calculation-tooltip">
        <h4>How we calculate Cost per User:</h4>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Formula:**")
            st.code(f"""
Total Cost ÷ Active Users = Cost per User
${total_cost:,.2f} ÷ {total_users} = ${total_cost/max(total_users,1):.2f}
            """)
            
            st.write("**Cost Components:**")
            if not data.empty:
                feature_costs = data.groupby('feature_used')['cost_usd'].sum().sort_values(ascending=False)
                for feature, cost in feature_costs.items():
                    percentage = (cost / total_cost) * 100 if total_cost > 0 else 0
                    st.write(f"• {feature}: ${cost:,.2f} ({percentage:.1f}%)")
        
        with col2:
            st.write("**Pricing Assumptions:**")
            st.info("""
            📊 **Current Cost Model:**
            - ChatGPT Messages: $0.02 per message
            - Tool Messages: $0.01 per message  
            - Model Usage: $0.025 per interaction
            - Project Messages: $0.015 per message
            
            💡 **Note:** These are estimated costs based on typical OpenAI enterprise pricing.
            """)

def check_data_quality(data):
    """Enhanced data quality checks for MVP2."""
    quality_issues = []
    quality_stats = {}

    if data.empty:
        return quality_issues, quality_stats
    
    # Check for duplicate records
    duplicates = data.duplicated(subset=['user_id', 'date', 'feature_used']).sum()
    if duplicates > 0:
        quality_issues.append(f"⚠️ {duplicates} potential duplicate records found")
    
    # Check for missing user names
    missing_names = data['user_name'].isna().sum()
    if missing_names > 0:
        quality_issues.append(f"⚠️ {missing_names} records missing user names")
    
    # Check for zero or negative usage
    invalid_usage = (data['usage_count'] <= 0).sum()
    if invalid_usage > 0:
        quality_issues.append(f"⚠️ {invalid_usage} records with zero or negative usage")
    
    # Check for extremely high costs (potential data errors)
    if len(data) > 0 and data['cost_usd'].max() > 0:
        high_cost_threshold = data['cost_usd'].quantile(0.95) * 3
        high_costs = (data['cost_usd'] > high_cost_threshold).sum()
        if high_costs > 0:
            quality_issues.append(f"⚠️ {high_costs} records with unusually high costs")
    
    # Calculate quality statistics
    quality_stats = {
        'total_records': len(data),
        'unique_users': data['user_id'].nunique(),
        'data_completeness': (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100,
        'duplicate_rate': (duplicates / len(data)) * 100 if len(data) > 0 else 0
    }

    return quality_issues, quality_stats

def check_date_coverage(db, start_date, end_date):
    """Check data coverage for selected date range and allow cross-month analysis."""
    available_months = db.get_available_months()
    
    if not available_months:
        return False, "No data available in database"
    
    # Convert to datetime for comparison
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    available_dates = [pd.to_datetime(d) for d in available_months]
    
    # Enhanced: Allow flexible date ranges that span across available data
    min_available = min(available_dates)
    max_available = max(available_dates)
    
    # Check if there's ANY overlap with available data
    if end_dt < min_available or start_dt > max_available:
        return False, f"Selected range ({start_date} to {end_date}) has no overlap with available data ({min_available.strftime('%Y-%m-%d')} to {max_available.strftime('%Y-%m-%d')})"
    
    # If there's partial overlap, show warning but allow
    if start_dt < min_available or end_dt > max_available:
        overlap_start = max(start_dt, min_available).strftime('%Y-%m-%d')
        overlap_end = min(end_dt, max_available).strftime('%Y-%m-%d')
        return True, f"Partial data coverage: showing data from {overlap_start} to {overlap_end}"
    
    return True, "Full data coverage for selected range"

def main():
    # Main header with version indicator
    st.markdown('<h1 class="main-header">📊 OpenAI Usage Metrics Dashboard v2.0</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("🔧 Controls")
        
        # Enhanced file upload section
        st.subheader("📁 Upload Monthly Data")
        uploaded_file = st.file_uploader(
            "Upload OpenAI Usage Metrics CSV",
            type=['csv'],
            help="Select your monthly OpenAI enterprise usage export file"
        )
        
        # Show upload history if available
        if hasattr(st.session_state, 'upload_history') and st.session_state.upload_history:
            st.write("**Recent Uploads:**")
            for upload in st.session_state.upload_history[-3:]:
                st.caption(f"✅ {upload}")
        
        if uploaded_file is not None:
            # Show file preview
            try:
                stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                preview_df = pd.read_csv(stringio, nrows=5)
                
                st.write("**File Preview:**")
                st.dataframe(preview_df.head(3), height=120)
                
                # Get full file info
                full_df = pd.read_csv(StringIO(uploaded_file.getvalue().decode('utf-8')))
                st.caption(f"📊 {len(full_df)} rows, {len(full_df.columns)} columns")
                
                # Show date range in file
                if 'period_start' in full_df.columns:
                    min_date = full_df['period_start'].min()
                    max_date = full_df['period_start'].max()
                    st.caption(f"📅 Date range: {min_date} to {max_date}")
                
            except Exception as e:
                st.error(f"Cannot preview file: {str(e)}")
            
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
                            # Track upload history
                            if 'upload_history' not in st.session_state:
                                st.session_state.upload_history = []
                            st.session_state.upload_history.append(
                                f"{uploaded_file.name} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                            )
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
        
        st.divider()
        
        # Enhanced date range selector with flexible cross-month analysis
        st.subheader("📅 Date Range")
        available_months = db.get_available_months()
        
        if available_months:
            default_end = max(available_months)
            default_start = min(available_months)
            
            # Show data coverage info
            st.info(f"📊 Data available from {default_start} to {default_end}")
            st.caption("💡 You can select any date range - even across months!")
            
            # Allow flexible date selection - not restricted to available data
            date_range = st.date_input(
                "Select date range for analysis",
                value=(default_start, default_end),
                help="Select any date range for analysis. The system will use available data within your selection."
            )
            
            # Show coverage information for selected range
            if len(date_range) == 2:
                coverage_ok, coverage_msg = check_date_coverage(db, date_range[0], date_range[1])
                if coverage_ok:
                    if "Partial" in coverage_msg:
                        st.warning(f"ℹ️ {coverage_msg}")
                    else:
                        st.success("✅ Full data coverage for selected range")
                else:
                    st.error(f"❌ {coverage_msg}")
        else:
            st.info("No data available. Please upload your first monthly export.")
            return
        
        st.divider()
        
        # Enhanced filters with counts
        st.subheader("🔍 Filters")
        users = db.get_unique_users()
        selected_users = st.multiselect(
            f"Select Users (leave empty for all {len(users)} users)", 
            users,
            help=f"Filter by specific users. Currently {len(users)} users available."
        )
        
        departments = db.get_unique_departments()
        selected_departments = st.multiselect(
            f"Select Departments (leave empty for all {len(departments)} departments)", 
            departments,
            help=f"Filter by departments. Currently {len(departments)} departments available."
        )
    
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
    
    # Get filtered data with enhanced cross-month validation
    if len(date_range) == 2:
        start_date, end_date = date_range
        coverage_ok, coverage_msg = check_date_coverage(db, start_date, end_date)
        
        if not coverage_ok:
            st.error(f"❌ Cannot analyze data: {coverage_msg}")
            st.info("Please select a different date range or upload data for the requested period.")
            return
        
        # Get data for the selected range (will automatically filter to available data)
        data = db.get_filtered_data(
            start_date=start_date,
            end_date=end_date,
            users=selected_users if selected_users else None,
            departments=selected_departments if selected_departments else None
        )
    else:
        st.warning("Please select both start and end dates.")
        return
    
    if data.empty:
        st.warning("No data found for the selected filters and date range.")
        st.info("Try expanding your date range or removing some filters.")
        return
    
    # Show actual date range of data being displayed
    if not data.empty:
        actual_start = data['date'].min()
        actual_end = data['date'].max()
        if actual_start != str(start_date) or actual_end != str(end_date):
            st.info(f"📊 Showing data from {actual_start} to {actual_end} (based on available data)")
    
    # MVP2: Data Quality Dashboard
    st.subheader("🛡️ Data Quality Check")
    quality_issues, quality_stats = check_data_quality(data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        completeness = quality_stats.get('data_completeness', 0)
        st.metric("Data Completeness", f"{completeness:.1f}%", 
                 help="Percentage of non-null values in the dataset")
        
    with col2:
        duplicate_rate = quality_stats.get('duplicate_rate', 0)
        st.metric("Duplicate Rate", f"{duplicate_rate:.1f}%",
                 help="Percentage of potentially duplicate records")
        
    with col3:
        unique_users = quality_stats.get('unique_users', 0)
        st.metric("Active Users", f"{unique_users}",
                 help="Number of unique users in current data")
    
    # Display quality issues
    if quality_issues:
        st.markdown('<div class="data-quality-warning">', unsafe_allow_html=True)
        st.warning("⚠️ Data Quality Issues Detected:")
        for issue in quality_issues:
            st.write(f"• {issue}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="data-quality-success">', unsafe_allow_html=True)
        st.success("✅ No data quality issues detected")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced Key Metrics Row with explanations
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = data['user_id'].nunique()
        st.metric("Total Active Users", total_users, 
                 help="Number of unique users with activity in selected period")
    
    with col2:
        total_usage = data['usage_count'].sum()
        st.metric("Total Usage Events", f"{total_usage:,}", 
                 help="Sum of all usage interactions across all users")
    
    with col3:
        total_cost = data['cost_usd'].sum()
        st.metric("Total Cost", f"${total_cost:,.2f}", 
                 help="Estimated total cost based on usage and pricing model")
    
    with col4:
        avg_cost_per_user = total_cost / max(total_users, 1)
        st.metric("Avg Cost per User", f"${avg_cost_per_user:.2f}", 
                 help="Total cost divided by number of active users")
    
    # MVP2: Cost calculation transparency
    display_cost_calculation_details(total_cost, total_users, data)
    
    # Usage Trends (enhanced)
    st.subheader("📊 Usage Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily usage trend
        daily_usage = data.groupby('date')['usage_count'].sum().reset_index()
        daily_usage['date'] = pd.to_datetime(daily_usage['date'])
        daily_usage = daily_usage.sort_values('date')
        
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
        daily_cost = daily_cost.sort_values('date')
        
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
    
    # Enhanced Management Insights
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
        else:
            st.info("💡 Upload multiple months of data to see growth trends")
    
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
            percentage = (row['cost_usd'] / total_cost) * 100 if total_cost > 0 else 0
            st.write(f"• {row['department']}: ${row['cost_usd']:,.2f} ({percentage:.1f}%)")
    
    # Enhanced Raw Data View
    with st.expander("📋 View Raw Data", expanded=False):
        st.write(f"**Showing {len(data)} records** from {data['date'].min()} to {data['date'].max()}")
        st.dataframe(data, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download filtered data
            csv = data.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"openai_metrics_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Download summary report
            summary_data = pd.DataFrame([{
                'Metric': 'Total Active Users',
                'Value': total_users
            }, {
                'Metric': 'Total Usage Events', 
                'Value': total_usage
            }, {
                'Metric': 'Total Cost (USD)',
                'Value': total_cost
            }, {
                'Metric': 'Average Cost per User (USD)',
                'Value': avg_cost_per_user
            }])
            
            summary_csv = summary_data.to_csv(index=False)
            st.download_button(
                label="📊 Download Summary Report",
                data=summary_csv,
                file_name=f"openai_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()