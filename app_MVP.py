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
import sqlite3

from data_processor import DataProcessor
from database import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="OpenAI Usage Metrics Dashboard",
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

# Enhanced CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00A67E;
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
    .admin-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
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
            st.write("**OpenAI Pricing Model:**")
            st.info("""
            📊 **OpenAI Cost Model:**
            - ChatGPT Messages: $0.02 per message
            - Tool Messages: $0.01 per message  
            - Project Messages: $0.015 per message
            
            💡 **Note:** Based on typical OpenAI enterprise pricing.
            Actual costs may vary based on your specific agreement.
            """)

def check_data_quality(data):
    """Enhanced data quality checks."""
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

def get_database_info():
    """Get comprehensive database information."""
    try:
        all_data = db.get_all_data()
        
        if all_data.empty:
            return {
                'total_stats': {
                    'total_records': 0,
                    'total_users': 0,
                    'total_days': 0,
                    'total_cost': 0.0
                },
                'upload_history': [],
                'date_coverage': pd.DataFrame()
            }
        
        # Calculate total statistics
        total_cost = all_data['cost_usd'].sum() if 'cost_usd' in all_data.columns else 0.0
        if pd.isna(total_cost):
            total_cost = 0.0
            
        total_stats = {
            'total_records': len(all_data),
            'total_users': all_data['user_id'].nunique(),
            'total_days': (pd.to_datetime(all_data['date'].max()) - pd.to_datetime(all_data['date'].min())).days + 1,
            'total_cost': float(total_cost)
        }
        
        # Get upload history
        upload_history = []
        if 'file_source' in all_data.columns:
            # Group by file_source and get stats
            file_groups = all_data.groupby('file_source')
            
            for filename, group in file_groups:
                upload_history.append({
                    'filename': str(filename),
                    'date_range': f"{group['date'].min()} to {group['date'].max()}",
                    'records': len(group)
                })
        
        # Date coverage analysis
        date_coverage = all_data.groupby('date').agg({
            'usage_count': 'sum',
            'user_id': 'nunique',
            'cost_usd': 'sum'
        }).reset_index()
        date_coverage.columns = ['Date', 'Total Usage', 'Active Users', 'Cost']
        
        return {
            'total_stats': total_stats,
            'upload_history': upload_history,
            'date_coverage': date_coverage
        }
        
    except Exception as e:
        st.error(f"Error getting database info: {str(e)}")
        return {
            'total_stats': {
                'total_records': 0,
                'total_users': 0,
                'total_days': 0,
                'total_cost': 0.0
            },
            'upload_history': [],
            'date_coverage': pd.DataFrame()
        }

def display_admin_dashboard():
    """Display the admin/database management dashboard."""
    st.header("🛠️ Database Administration")
    
    # Get database information
    db_info = get_database_info()
    
    # Database Overview Metrics
    st.subheader("📊 Database Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", db_info['total_stats']['total_records'])
    with col2:
        st.metric("Total Users", db_info['total_stats']['total_users'])
    with col3:
        st.metric("Date Range", f"{db_info['total_stats']['total_days']} days")
    with col4:
        total_cost = db_info['total_stats']['total_cost'] or 0.0
        st.metric("Total Cost", f"${total_cost:,.2f}")
    
    # Upload History
    st.subheader("📂 Upload History")
    if db_info['upload_history']:
        upload_df = pd.DataFrame(db_info['upload_history'])
        st.dataframe(upload_df, use_container_width=True)
        
        # Get list of filenames for selection
        file_list = [str(item['filename']) for item in db_info['upload_history']]
    else:
        st.info("No uploads yet")
        file_list = []
    
    # Database Management Actions
    st.subheader("🔧 Database Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Delete by file
        if file_list:
            selected_file = st.selectbox(
                "Select file to delete:",
                options=file_list
            )
            
            if st.button("🗑️ Delete Selected File", type="secondary"):
                if not st.session_state.get('confirm_delete_file', False):
                    st.session_state.confirm_delete_file = True
                    st.warning(f"⚠️ Are you sure? Click again to confirm deletion of {selected_file}")
                else:
                    if db.delete_by_file(selected_file):
                        st.success(f"✅ Deleted all records from {selected_file}")
                        del st.session_state.confirm_delete_file
                        st.rerun()
                    else:
                        st.error("Error deleting file")
    
    with col2:
        # Clear entire database
        if st.button("🧹 Clear All Data", type="secondary"):
            if not st.session_state.get('confirm_clear_db', False):
                st.session_state.confirm_clear_db = True
                st.warning("⚠️ Are you sure? Click again to confirm clearing entire database")
            else:
                if db.delete_all_data():
                    st.success("✅ Database cleared successfully")
                    del st.session_state.confirm_clear_db
                    st.rerun()
                else:
                    st.error("Error clearing database")
    
    # Date Coverage Chart
    if not db_info['date_coverage'].empty:
        st.subheader("📅 Data Coverage Over Time")
        
        coverage_chart = px.bar(
            db_info['date_coverage'],
            x='Date',
            y='Total Usage',
            title='Daily Usage Coverage'
        )
        st.plotly_chart(coverage_chart, use_container_width=True)
    
    # Raw Database View
    with st.expander("🔍 View All Database Records"):
        all_data = db.get_all_data()
        if not all_data.empty:
            st.dataframe(all_data, use_container_width=True)
            
            # Download option
            csv = all_data.to_csv(index=False)
            st.download_button(
                label="📥 Download All Data as CSV",
                data=csv,
                file_name=f"openai_metrics_full_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data in database")

def main():
    # Main header
    st.markdown('<h1 class="main-header">🤖 OpenAI Usage Metrics Dashboard</h1>', unsafe_allow_html=True)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🔧 Database Management"])
    
    with tab2:
        display_admin_dashboard()
    
    with tab1:
        # Sidebar for navigation and controls
        with st.sidebar:
            st.header("🔧 Controls")
            
            # File upload section
            st.subheader("📁 Upload OpenAI Data")
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
            
            # Date range selector
            st.subheader("📅 Date Range")
            try:
                min_date, max_date = db.get_date_range()
            except AttributeError:
                st.error("⚠️ Cache error detected: The database object is missing the 'get_date_range()' method.")
                st.warning("This usually happens when the code is updated while the app is running.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Clear Cache & Reload", type="primary"):
                        st.cache_resource.clear()
                        st.rerun()
                with col2:
                    st.info("Or restart the app manually: Press Ctrl+C in terminal and run `streamlit run app.py`")
                return
            
            if min_date and max_date:
                st.info(f"📊 Data available from {min_date} to {max_date}")
                
                date_range = st.date_input(
                    "Select date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    help="Select the date range for analysis. Monthly uploads cover the entire month."
                )
            else:
                st.info("No data available. Please upload your first monthly export.")
                return
            
            st.divider()
            
            # Filters
            st.subheader("🔍 Filters")
            users = db.get_unique_users()
            selected_users = st.multiselect(
                f"Select Users (leave empty for all {len(users)} users)", 
                users,
                help="Filter by specific users"
            )
            
            departments = db.get_unique_departments()
            selected_departments = st.multiselect(
                f"Select Departments (leave empty for all {len(departments)} departments)", 
                departments,
                help="Filter by departments"
            )
        
        # Main dashboard content
        if not min_date or not max_date:
            st.info("👋 Welcome! Please upload your first OpenAI usage metrics file using the sidebar.")
            
            # Show sample data format
            st.subheader("📋 Expected OpenAI Data Format")
            sample_data = pd.DataFrame({
                'email': ['user1@company.com', 'user2@company.com'],
                'name': ['John Doe', 'Jane Smith'],
                'department': ['["engineering"]', '["marketing"]'],
                'period_start': ['2024-01-01', '2024-01-01'],
                'messages': [25, 15],
                'tool_messages': [5, 3],
                'project_messages': [10, 8]
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
        
        # Data Quality Check Section
        st.subheader("🛡️ Data Quality Check")
        quality_issues, quality_stats = check_data_quality(data)
        
        # Display quality metrics in 3 columns
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
        
        # Cost calculation details
        display_cost_calculation_details(total_cost, total_users, data)
        
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
        
        with col2:
            st.write("**Usage Distribution**")
            
            # Most active users
            top_active = data.groupby('user_name')['usage_count'].sum().nlargest(3)
            st.write("**Most Active Users:**")
            for user, count in top_active.items():
                st.write(f"• {user}: {count:,} events")
            
            # Feature distribution
            st.write("**Most Used Features:**")
            top_features = data.groupby('feature_used')['usage_count'].sum().nlargest(3)
            for feature, count in top_features.items():
                st.write(f"• {feature}: {count:,} events")
        
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
