"""
OpenAI Usage Metrics Dashboard v2

A Streamlit-based dashboard for analyzing OpenAI enterprise usage metrics.
Enhanced with cost transparency, data quality checks, database management, and improved analytics.
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
import re

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
    .admin-section {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
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
    if data['cost_usd'].max() > 0:
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
    """Check data coverage for selected date range."""
    available_months = db.get_available_months()
    
    if not available_months:
        return False, "No data available in database"
    
    # Convert to datetime for comparison
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    available_dates = [pd.to_datetime(d) for d in available_months]
    
    # Check if we have data for the requested range
    min_available = min(available_dates)
    max_available = max(available_dates)
    
    if start_dt < min_available or end_dt > max_available:
        return False, f"Data only available from {min_available.strftime('%Y-%m-%d')} to {max_available.strftime('%Y-%m-%d')}"
    
    return True, "Data coverage OK"

def get_database_info():
    """Get comprehensive database information for admin dashboard."""
    try:
        conn = sqlite3.connect(db.db_path)
        
        # Get table info
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(tables_query, conn)
        
        # Get upload summary by file source
        uploads_query = """
        SELECT 
            file_source,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            COUNT(*) as record_count,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(cost_usd) as total_cost
        FROM usage_metrics 
        WHERE file_source IS NOT NULL
        GROUP BY file_source
        ORDER BY MAX(created_at) DESC
        """
        uploads_df = pd.read_sql_query(uploads_query, conn)
        
        # Get monthly summary
        monthly_query = """
        SELECT 
            strftime('%Y-%m', date) as month,
            COUNT(*) as records,
            COUNT(DISTINCT user_id) as unique_users,
            SUM(usage_count) as total_usage,
            SUM(cost_usd) as total_cost
        FROM usage_metrics
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        """
        monthly_df = pd.read_sql_query(monthly_query, conn)
        
        # Get total database stats
        total_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT user_id) as total_users,
            COUNT(DISTINCT date) as total_days,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            SUM(cost_usd) as total_cost
        FROM usage_metrics
        """
        total_stats = pd.read_sql_query(total_query, conn).iloc[0]
        
        conn.close()
        
        return {
            'tables': tables,
            'uploads': uploads_df,
            'monthly': monthly_df,
            'total_stats': total_stats
        }
    except Exception as e:
        st.error(f"Error getting database info: {str(e)}")
        return None

def clear_database():
    """Clear all data from the database."""
    try:
        conn = sqlite3.connect(db.db_path)
        conn.execute("DELETE FROM usage_metrics")
        conn.commit()
        conn.close()
        return True, "Database cleared successfully"
    except Exception as e:
        return False, f"Error clearing database: {str(e)}"

def delete_upload_by_source(file_source):
    """Delete specific upload by file source."""
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usage_metrics WHERE file_source = ?", (file_source,))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return True, f"Deleted {deleted_rows} records from {file_source}"
    except Exception as e:
        return False, f"Error deleting upload: {str(e)}"

def extract_month_from_filename(filename):
    """Extract month information from filename for better tracking."""
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }
    
    filename_lower = filename.lower()
    
    # Look for month names
    for month_name, month_num in months.items():
        if month_name in filename_lower:
            # Try to find year
            year_match = re.search(r'20\d{2}', filename)
            if year_match:
                return f"{year_match.group()}-{month_num}"
            else:
                return f"2025-{month_num}"  # Default to current year
    
    # Look for date patterns like 2025-07 or 07-2025
    date_match = re.search(r'(20\d{2})[_-](\d{1,2})|(\d{1,2})[_-](20\d{2})', filename)
    if date_match:
        if date_match.group(1):  # Format: 2025-07
            return f"{date_match.group(1)}-{date_match.group(2).zfill(2)}"
        else:  # Format: 07-2025
            return f"{date_match.group(4)}-{date_match.group(3).zfill(2)}"
    
    return None

def display_admin_dashboard():
    """Display administrative dashboard for database management."""
    st.subheader("🔧 Database Administration")
    
    db_info = get_database_info()
    
    if not db_info:
        st.error("Could not retrieve database information")
        return
    
    # Database Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{db_info['total_stats']['total_records']:,}")
    with col2:
        st.metric("Total Users", f"{db_info['total_stats']['total_users']:,}")
    with col3:
        st.metric("Date Range", f"{db_info['total_stats']['total_days']} days")
    with col4:
        st.metric("Total Cost", f"${db_info['total_stats']['total_cost']:,.2f}")
    
    # Upload History Management
    st.write("### 📁 Upload History")
    
    if not db_info['uploads'].empty:
        # Display uploads with management options
        for idx, upload in db_info['uploads'].iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    # Extract month from filename
                    detected_month = extract_month_from_filename(upload['file_source'])
                    month_indicator = f" (📅 {detected_month})" if detected_month else ""
                    
                    st.write(f"**{upload['file_source']}**{month_indicator}")
                    st.caption(f"📊 {upload['record_count']} records | 👥 {upload['unique_users']} users | 💰 ${upload['total_cost']:.2f}")
                    st.caption(f"📅 Data range: {upload['earliest_date']} to {upload['latest_date']}")
                
                with col2:
                    if st.button(f"🔍 View", key=f"view_{idx}"):
                        st.session_state[f'view_upload_{idx}'] = not st.session_state.get(f'view_upload_{idx}', False)
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"del_{idx}", type="secondary"):
                        if st.session_state.get(f'confirm_delete_{idx}', False):
                            success, message = delete_upload_by_source(upload['file_source'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.session_state[f'confirm_delete_{idx}'] = True
                            st.warning("Click delete again to confirm")
                
                # Show detailed view if requested
                if st.session_state.get(f'view_upload_{idx}', False):
                    try:
                        conn = sqlite3.connect(db.db_path)
                        upload_data = pd.read_sql_query(
                            "SELECT * FROM usage_metrics WHERE file_source = ? LIMIT 100", 
                            conn, 
                            params=[upload['file_source']]
                        )
                        conn.close()
                        
                        st.dataframe(upload_data, height=200)
                    except Exception as e:
                        st.error(f"Error loading upload data: {str(e)}")
                
                st.divider()
    else:
        st.info("No uploads found in database")
    
    # Monthly Data Summary
    st.write("### 📅 Monthly Data Summary")
    
    if not db_info['monthly'].empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly records chart
            fig_monthly = px.bar(
                db_info['monthly'], 
                x='month', 
                y='records',
                title='Records by Month',
                labels={'records': 'Number of Records', 'month': 'Month'}
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        with col2:
            # Monthly cost chart
            fig_cost = px.bar(
                db_info['monthly'], 
                x='month', 
                y='total_cost',
                title='Cost by Month',
                labels={'total_cost': 'Total Cost ($)', 'month': 'Month'}
            )
            st.plotly_chart(fig_cost, use_container_width=True)
        
        # Monthly summary table
        st.dataframe(db_info['monthly'], use_container_width=True)
    else:
        st.info("No monthly data available")
    
    # Database Actions
    st.write("### 🛠️ Database Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="admin-section">', unsafe_allow_html=True)
        st.write("**🗑️ Clear Database**")
        st.write("Remove all data from the database. This action cannot be undone.")
        
        if st.button("⚠️ Clear All Data", type="secondary"):
            if st.session_state.get('confirm_clear', False):
                success, message = clear_database()
                if success:
                    st.success(message)
                    # Clear session state
                    if 'upload_history' in st.session_state:
                        st.session_state.upload_history = []
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.session_state['confirm_clear'] = True
                st.warning("⚠️ Click again to confirm database clearing")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="admin-section">', unsafe_allow_html=True)
        st.write("**📥 Export Database**")
        st.write("Download complete database as CSV for backup.")
        
        try:
            all_data = db.get_all_data()
            if not all_data.empty:
                csv = all_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Complete Database",
                    data=csv,
                    file_name=f"openai_database_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data to export")
        except Exception as e:
            st.error(f"Error preparing export: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Main header with version indicator
    st.markdown('<h1 class="main-header">📊 OpenAI Usage Metrics Dashboard v2.1</h1>', unsafe_allow_html=True)
    
    # Add navigation tabs
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🔧 Database Management"])
    
    with tab2:
        display_admin_dashboard()
        return
    
    with tab1:
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
                # Show file preview and month detection
                try:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    preview_df = pd.read_csv(stringio, nrows=5)
                    
                    st.write("**File Preview:**")
                    st.dataframe(preview_df.head(3), height=120)
                    
                    # Get full file info
                    full_df = pd.read_csv(StringIO(uploaded_file.getvalue().decode('utf-8')))
                    st.caption(f"📊 {len(full_df)} rows, {len(full_df.columns)} columns")
                    
                    # Show detected month
                    detected_month = extract_month_from_filename(uploaded_file.name)
                    if detected_month:
                        st.success(f"📅 Detected period: {detected_month}")
                    else:
                        st.warning("⚠️ Could not detect month from filename")
                    
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
                                upload_entry = f"{uploaded_file.name} ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                                if detected_month:
                                    upload_entry += f" [{detected_month}]"
                                st.session_state.upload_history.append(upload_entry)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Error processing file: {str(e)}")
            
            st.divider()
            
            # Enhanced date range selector with validation
            st.subheader("📅 Date Range")
            available_months = db.get_available_months()
            
            if available_months:
                default_end = max(available_months)
                default_start = min(available_months)
                
                # Show data coverage info
                st.info(f"📊 Data available from {default_start} to {default_end}")
                
                date_range = st.date_input(
                    "Select date range",
                    value=(default_start, default_end),
                    min_value=default_start,
                    max_value=default_end,
                    help="Select any date range for analysis - supports cross-month periods like July 15 to August 15."
                )
                
                # Validate date range
                if len(date_range) == 2:
                    coverage_ok, coverage_msg = check_date_coverage(db, date_range[0], date_range[1])
                    if not coverage_ok:
                        st.warning(f"⚠️ {coverage_msg}")
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
        
        # Get filtered data with enhanced validation (supports cross-month ranges)
        if len(date_range) == 2:
            start_date, end_date = date_range
            
            # Enhanced cross-month support - don't restrict by coverage
            data = db.get_filtered_data(
                start_date=start_date,
                end_date=end_date,
                users=selected_users if selected_users else None,
                departments=selected_departments if selected_departments else None
            )
            
            # Show info about cross-month ranges
            if start_date.month != end_date.month:
                st.info(f"📅 Cross-month analysis: {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}")
            
        else:
            st.warning("Please select both start and end dates.")
            return
        
        if data.empty:
            st.warning("No data found for the selected filters and date range.")
            return
        
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
            st.write(f"**Showing {len(data)} records**")
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