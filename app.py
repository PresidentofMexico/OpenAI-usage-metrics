"""
AI Usage Metrics Dashboard v3.0

A Streamlit-based dashboard for analyzing AI provider usage metrics.
Multi-Provider Support: OpenAI, BlueFlame AI, Anthropic, Google AI, and Custom providers.
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

from data_processor import DataProcessor
from database import DatabaseManager
import config

# Page configuration
st.set_page_config(
    page_title="AI Usage Metrics Dashboard v3.0",
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
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def display_cost_calculation_details(total_cost, total_users, data, provider='OpenAI'):
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
            
            # Get provider-specific cost model
            cost_model = config.PROVIDER_CONFIGS.get(provider, {}).get('cost_model', {})
            
            cost_info = f"📊 **{provider} Cost Model:**\n"
            for feature, rate in cost_model.items():
                cost_info += f"- {feature}: ${rate} per unit\n"
            
            cost_info += f"\n💡 **Note:** These are estimated costs based on typical {provider} pricing."
            
            st.info(cost_info)

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

def check_date_coverage(db, start_date, end_date, provider=None):
    """Check data coverage for selected date range."""
    available_months = db.get_available_months(provider=provider)
    
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

def get_database_info(provider=None):
    """Get comprehensive database information."""
    try:
        all_data = db.get_all_data(provider=provider)
        
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
        
        # Calculate total statistics with null checks
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
            file_sources = all_data['file_source'].value_counts()
            for file_name, count in file_sources.items():
                file_data = all_data[all_data['file_source'] == file_name]
                provider_info = file_data['provider'].iloc[0] if 'provider' in file_data.columns else 'Unknown'
                upload_history.append({
                    'file_name': file_name,
                    'records': count,
                    'users': file_data['user_id'].nunique(),
                    'date_range': f"{file_data['date'].min()} to {file_data['date'].max()}",
                    'provider': provider_info
                })
        
        # Get date coverage
        date_coverage = all_data.groupby('date').agg({
            'user_id': 'nunique',
            'usage_count': 'sum',
            'cost_usd': 'sum'
        }).reset_index()
        
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
    
    # Upload History Management
    st.subheader("📁 Upload History")
    if db_info['upload_history']:
        upload_df = pd.DataFrame(db_info['upload_history'])
        st.dataframe(upload_df, width="stretch")
        
        # File Management Actions
        st.subheader("🗂️ File Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Delete specific upload
            if len(db_info['upload_history']) > 0:
                selected_file = st.selectbox(
                    "Select file to delete:",
                    [item['file_name'] for item in db_info['upload_history']]
                )
                
                if st.button("🗑️ Delete Selected Upload", type="secondary"):
                    if st.session_state.get('confirm_delete_file') != selected_file:
                        st.session_state.confirm_delete_file = selected_file
                        st.warning(f"⚠️ Click again to confirm deletion of: {selected_file}")
                    else:
                        try:
                            # Delete records from specific file using sqlite3 directly
                            conn = sqlite3.connect(db.db_path)
                            conn.execute("DELETE FROM usage_metrics WHERE file_source = ?", (selected_file,))
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Deleted all records from {selected_file}")
                            del st.session_state.confirm_delete_file
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting file: {str(e)}")
        
        with col2:
            # Clear entire database
            if st.button("🧹 Clear Entire Database", type="secondary"):
                if not st.session_state.get('confirm_clear_db', False):
                    st.session_state.confirm_clear_db = True
                    st.error("⚠️ **DANGER**: This will delete ALL data! Click again to confirm.")
                else:
                    try:
                        conn = sqlite3.connect(db.db_path)
                        conn.execute("DELETE FROM usage_metrics")
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ Database cleared successfully")
                        del st.session_state.confirm_clear_db
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing database: {str(e)}")
    else:
        st.info("No upload history available. Upload some data first.")
    
    # Date Coverage Analysis
    st.subheader("📅 Date Coverage Analysis")
    if not db_info['date_coverage'].empty:
        coverage_df = db_info['date_coverage'].copy()
        coverage_df['date'] = pd.to_datetime(coverage_df['date'])
        
        # Plot date coverage
        fig = px.bar(
            coverage_df, 
            x='date', 
            y='user_id',
            title='Daily User Activity Coverage',
            labels={'user_id': 'Active Users', 'date': 'Date'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, width="stretch")
        
        # Show data gaps
        date_range = pd.date_range(
            start=coverage_df['date'].min(),
            end=coverage_df['date'].max(),
            freq='D'
        )
        
        missing_dates = set(date_range) - set(coverage_df['date'])
        if missing_dates:
            st.warning(f"⚠️ {len(missing_dates)} days with missing data detected")
            
            # Show missing date ranges
            missing_list = sorted(missing_dates)
            if len(missing_list) <= 10:
                st.write("**Missing dates:**")
                for date in missing_list:
                    st.write(f"• {date.strftime('%Y-%m-%d')}")
            else:
                st.write(f"**Missing date range:** {missing_list[0].strftime('%Y-%m-%d')} to {missing_list[-1].strftime('%Y-%m-%d')}")
        else:
            st.success("✅ No data gaps detected in date range")
    else:
        st.info("No data available for coverage analysis.")

def main():
    # Main header with version indicator
    st.markdown('<h1 class="main-header">📊 AI Usage Metrics Dashboard v3.0</h1>', unsafe_allow_html=True)
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["📊 Analytics Dashboard", "🔧 Database Management"])
    
    with tab2:
        display_admin_dashboard()
    
    with tab1:
        # Sidebar for navigation and controls
        with st.sidebar:
            st.header("🔧 Controls")
            
            # Provider Selection
            st.subheader("🤖 Provider Selection")
            
            # Get available providers from database
            available_providers = db.get_available_providers()
            
            # Add "All Providers" option if there are multiple providers
            provider_options = config.SUPPORTED_PROVIDERS.copy()
            if len(available_providers) > 1:
                provider_options.insert(0, "All Providers")
            
            selected_provider = st.selectbox(
                "Select AI Provider",
                provider_options,
                index=0 if "All Providers" in provider_options else provider_options.index("OpenAI") if "OpenAI" in provider_options else 0,
                help="Choose the AI provider to analyze. This affects both data upload processing and analytics display."
            )
            
            # Store selected provider in session state
            if 'selected_provider' not in st.session_state or st.session_state.selected_provider != selected_provider:
                st.session_state.selected_provider = selected_provider
            
            # Show provider info
            if selected_provider != "All Providers" and selected_provider in config.PROVIDER_CONFIGS:
                provider_config = config.PROVIDER_CONFIGS[selected_provider]
                st.markdown(f"{provider_config['icon']} **{selected_provider}** selected")
            
            st.divider()
            
            # Enhanced file upload section
            st.subheader("📁 Upload Monthly Data")
            
            # Update upload label based on selected provider
            upload_label = f"Upload {selected_provider} Usage Metrics CSV" if selected_provider != "All Providers" else "Upload Usage Metrics CSV"
            upload_help = f"Select your monthly {selected_provider} usage export file" if selected_provider != "All Providers" else "Select your monthly usage export file"
            
            uploaded_file = st.file_uploader(
                upload_label,
                type=['csv'],
                help=upload_help
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
                            # Determine which provider to use for processing
                            processing_provider = selected_provider if selected_provider != "All Providers" else "OpenAI"
                            
                            # Read uploaded file
                            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                            df = pd.read_csv(stringio)
                            
                            # Process and store data with provider
                            success, message = processor.process_monthly_data(df, uploaded_file.name, provider=processing_provider)
                            
                            if success:
                                st.success(f"✅ {message}")
                                # Track upload history
                                if 'upload_history' not in st.session_state:
                                    st.session_state.upload_history = []
                                st.session_state.upload_history.append(
                                    f"{uploaded_file.name} ({datetime.now().strftime('%Y-%m-%d %H:%M')}) - {processing_provider}"
                                )
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Error processing file: {str(e)}")
            
            st.divider()
            
            # Enhanced date range selector with validation
            st.subheader("📅 Date Range")
            available_months = db.get_available_months(provider=selected_provider if selected_provider != "All Providers" else None)
            
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
                    help="Select the date range for analysis. Data must be available for selected dates."
                )
                
                # Validate date range
                if len(date_range) == 2:
                    coverage_ok, coverage_msg = check_date_coverage(db, date_range[0], date_range[1], provider=selected_provider if selected_provider != "All Providers" else None)
                    if not coverage_ok:
                        st.warning(f"⚠️ {coverage_msg}")
            else:
                provider_msg = f" for {selected_provider}" if selected_provider != "All Providers" else ""
                st.info(f"No data available{provider_msg}. Please upload your first monthly export.")
                return
            
            st.divider()
            
            # Enhanced filters with counts
            st.subheader("🔍 Filters")
            users = db.get_unique_users(provider=selected_provider if selected_provider != "All Providers" else None)
            selected_users = st.multiselect(
                f"Select Users (leave empty for all {len(users)} users)", 
                users,
                help=f"Filter by specific users. Currently {len(users)} users available."
            )
            
            departments = db.get_unique_departments(provider=selected_provider if selected_provider != "All Providers" else None)
            selected_departments = st.multiselect(
                f"Select Departments (leave empty for all {len(departments)} departments)", 
                departments,
                help=f"Filter by departments. Currently {len(departments)} departments available."
            )
        
        # Main dashboard content
        if not available_months:
            provider_msg = f" for {selected_provider}" if selected_provider != "All Providers" else ""
            st.info(f"👋 Welcome! Please upload your first usage metrics file{provider_msg} using the sidebar.")
            
            # Show sample data format based on selected provider
            st.subheader("📋 Expected Data Format")
            
            if selected_provider != "All Providers" and selected_provider in config.PROVIDER_CONFIGS:
                sample_format = config.PROVIDER_CONFIGS[selected_provider]['sample_format']
                sample_data = pd.DataFrame([sample_format])
                st.write(f"**{selected_provider} Format:**")
                st.dataframe(sample_data)
            else:
                # Show generic format
                sample_data = pd.DataFrame({
                    'user_id': ['user1@company.com', 'user2@company.com'],
                    'user_name': ['John Doe', 'Jane Smith'],
                    'department': ['Engineering', 'Marketing'],
                    'date': ['2024-01-15', '2024-01-16'],
                    'feature_used': ['Feature A', 'Feature B'],
                    'usage_count': [25, 15],
                    'cost_usd': [12.50, 8.75]
                })
                st.dataframe(sample_data)
            return
        
        # Get filtered data with enhanced validation
        if len(date_range) == 2:
            start_date, end_date = date_range
            coverage_ok, coverage_msg = check_date_coverage(db, start_date, end_date, provider=selected_provider if selected_provider != "All Providers" else None)
            
            if not coverage_ok:
                st.error(f"❌ Cannot load data: {coverage_msg}")
                st.info("Please select a different date range or upload data for the requested period.")
                return
            
            data = db.get_filtered_data(
                start_date=start_date,
                end_date=end_date,
                users=selected_users if selected_users else None,
                departments=selected_departments if selected_departments else None,
                provider=selected_provider if selected_provider != "All Providers" else None
            )
        else:
            st.warning("Please select both start and end dates.")
            return
        
        if data.empty:
            st.warning("No data found for the selected filters.")
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
        
        # MVP2: Cost calculation transparency with provider awareness
        display_cost_calculation_details(total_cost, total_users, data, provider=selected_provider if selected_provider != "All Providers" else "OpenAI")
        
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
            st.plotly_chart(fig_daily, width="stretch")
        
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
            st.plotly_chart(fig_cost, width="stretch")
        
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
            st.plotly_chart(fig_users, width="stretch")
        
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
            st.plotly_chart(fig_dept, width="stretch")
        
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
        st.plotly_chart(fig_features, width="stretch")
        
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
            st.dataframe(data, width="stretch")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download filtered data
                csv = data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data as CSV",
                    data=csv,
                    file_name=f"ai_metrics_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
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
                    file_name=f"ai_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()