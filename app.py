"""
Multi-Tool AI Usage Analytics Dashboard

A Streamlit-based dashboard for analyzing AI tool usage metrics across multiple platforms
(OpenAI ChatGPT, BlueFlame AI, etc.) for enterprise management reporting.
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
import json

from data_processor import DataProcessor
from database import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="AI Usage Analytics Dashboard",
    page_icon="🤖",
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

# Department mapping storage file
DEPT_MAPPING_FILE = "department_mappings.json"

def load_department_mappings():
    """Load department mappings from JSON file."""
    if os.path.exists(DEPT_MAPPING_FILE):
        try:
            with open(DEPT_MAPPING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_department_mappings(mappings):
    """Save department mappings to JSON file."""
    with open(DEPT_MAPPING_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)

def apply_department_mappings(data, mappings):
    """Apply department mappings to the dataset."""
    if not mappings or data.empty:
        return data
    
    data = data.copy()
    for email, dept in mappings.items():
        if email in data['email'].values:
            data.loc[data['email'] == email, 'department'] = dept
    
    return data

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .tool-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .tool-chatgpt {
        background: #10a37f;
        color: white;
    }
    .tool-blueflame {
        background: #4f46e5;
        color: white;
    }
    .power-user-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .dept-mapper-container {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .insight-card {
        border-left: 4px solid;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .insight-success {
        border-color: #10b981;
        background: #d1fae5;
    }
    .insight-warning {
        border-color: #f59e0b;
        background: #fef3c7;
    }
    .insight-info {
        border-color: #3b82f6;
        background: #dbeafe;
    }
</style>
""", unsafe_allow_html=True)

def detect_data_source(df):
    """Detect which AI tool the data is from based on column structure."""
    columns = df.columns.tolist()
    
    # OpenAI ChatGPT detection
    if 'gpt_messages' in columns or 'tool_messages' in columns:
        return 'ChatGPT'
    
    # BlueFlame AI detection (adjust based on actual column names when you get the data)
    if 'blueflame_usage' in columns or 'bf_messages' in columns:
        return 'BlueFlame AI'
    
    # Default or ask user
    return 'Unknown'

def normalize_openai_data(df, filename):
    """Normalize OpenAI CSV export to standard schema."""
    normalized_records = []
    
    for _, row in df.iterrows():
        # Parse department - OpenAI exports it as a JSON array string
        dept = 'Unknown'
        if pd.notna(row.get('department', '')):
            dept_str = str(row['department'])
            if dept_str.startswith('['):
                try:
                    dept_list = json.loads(dept_str.replace("'", '"'))
                    dept = dept_list[0] if dept_list else 'Unknown'
                except:
                    dept = dept_str.strip('[]"\'')
            else:
                dept = dept_str
        
        # Get period dates
        period_start = pd.to_datetime(row.get('period_start', row.get('first_day_active_in_period', datetime.now())))
        period_end = pd.to_datetime(row.get('period_end', row.get('last_day_active_in_period', datetime.now())))
        
        # ChatGPT messages
        if row.get('messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': row.get('name', ''),
                'email': row.get('email', ''),
                'department': dept,
                'date': period_start,
                'feature_used': 'ChatGPT Messages',
                'usage_count': row.get('messages', 0),
                'cost_usd': row.get('messages', 0) * 0.02,
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # GPT-specific messages
        if row.get('gpt_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': row.get('name', ''),
                'email': row.get('email', ''),
                'department': dept,
                'date': period_start,
                'feature_used': 'GPT Messages',
                'usage_count': row.get('gpt_messages', 0),
                'cost_usd': row.get('gpt_messages', 0) * 0.02,
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # Tool messages
        if row.get('tool_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': row.get('name', ''),
                'email': row.get('email', ''),
                'department': dept,
                'date': period_start,
                'feature_used': 'Tool Messages',
                'usage_count': row.get('tool_messages', 0),
                'cost_usd': row.get('tool_messages', 0) * 0.01,
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # Project messages
        if row.get('project_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': row.get('name', ''),
                'email': row.get('email', ''),
                'department': dept,
                'date': period_start,
                'feature_used': 'Project Messages',
                'usage_count': row.get('project_messages', 0),
                'cost_usd': row.get('project_messages', 0) * 0.015,
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
    
    return pd.DataFrame(normalized_records)

def normalize_blueflame_data(df, filename):
    """Normalize BlueFlame AI data to standard schema."""
    # This will need to be updated once you share the BlueFlame data format
    # For now, creating a placeholder structure
    
    normalized_records = []
    
    # Adjust these column names based on actual BlueFlame export format
    for _, row in df.iterrows():
        normalized_records.append({
            'user_id': row.get('user_id', row.get('email', '')),
            'user_name': row.get('user_name', row.get('name', '')),
            'email': row.get('email', ''),
            'department': row.get('department', 'Unknown'),
            'date': pd.to_datetime(row.get('date', row.get('month', datetime.now()))),
            'feature_used': 'BlueFlame Messages',
            'usage_count': row.get('total_messages', row.get('messages', 0)),
            'cost_usd': row.get('cost', row.get('total_messages', 0) * 0.015),  # Adjust pricing
            'tool_source': 'BlueFlame AI',
            'file_source': filename
        })
    
    return pd.DataFrame(normalized_records)

def display_department_mapper():
    """Display department mapping interface."""
    st.subheader("🏢 Department Mapping Tool")
    
    st.markdown("""
    <div class="dept-mapper-container">
    <p><strong>Why use this?</strong> AI tool exports sometimes have incorrect or missing department data. 
    Use this tool to correct department assignments. Changes are saved and applied to all analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load existing mappings
    mappings = load_department_mappings()
    
    # Get all unique users from database
    all_data = db.get_all_data()
    if all_data.empty:
        st.info("No data available. Upload data first to use department mapping.")
        return
    
    # Get unique users
    users_df = all_data[['email', 'user_name', 'department']].drop_duplicates()
    users_df = users_df.sort_values('user_name')
    
    # Department options
    dept_options = [
        'Finance', 'IT', 'Analytics', 'Product', 'Legal', 'Research', 
        'Sales', 'Operations', 'HR', 'Marketing', 'Engineering', 
        'Customer Success', 'Other', 'Unknown'
    ]
    
    st.write(f"**Total Users:** {len(users_df)}")
    
    # Search filter
    search = st.text_input("🔍 Search users by name or email", "")
    
    if search:
        users_df = users_df[
            users_df['user_name'].str.contains(search, case=False, na=False) | 
            users_df['email'].str.contains(search, case=False, na=False)
        ]
    
    # Display in a clean table format with editable departments
    st.write("**Update Department Assignments:**")
    
    changes_made = False
    
    # Create columns for the table
    col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
    with col1:
        st.write("**Name**")
    with col2:
        st.write("**Email**")
    with col3:
        st.write("**Department**")
    with col4:
        st.write("**Action**")
    
    st.divider()
    
    # Show only first 20 users to avoid overwhelming the interface
    for idx, row in users_df.head(20).iterrows():
        col1, col2, col3, col4 = st.columns([3, 3, 3, 1])
        
        with col1:
            st.write(row['user_name'])
        
        with col2:
            st.write(row['email'])
        
        with col3:
            current_dept = mappings.get(row['email'], row['department'])
            new_dept = st.selectbox(
                "Dept",
                options=dept_options,
                index=dept_options.index(current_dept) if current_dept in dept_options else dept_options.index('Unknown'),
                key=f"dept_{row['email']}",
                label_visibility="collapsed"
            )
            
            if new_dept != mappings.get(row['email'], row['department']):
                mappings[row['email']] = new_dept
                changes_made = True
        
        with col4:
            if st.button("✓", key=f"save_{row['email']}", help="Save changes"):
                changes_made = True
    
    if len(users_df) > 20:
        st.info(f"Showing 20 of {len(users_df)} users. Use search to find specific users.")
    
    # Save button
    if changes_made or st.button("💾 Save All Department Mappings", type="primary"):
        save_department_mappings(mappings)
        st.success(f"✅ Saved department mappings for {len(mappings)} users")
        st.rerun()
    
    # Show current mappings count
    if mappings:
        st.info(f"📊 {len(mappings)} custom department mappings active")

def calculate_power_users(data, threshold_percentile=80):
    """Identify power users based on usage patterns."""
    if data.empty:
        return pd.DataFrame()
    
    # Group by user and calculate total usage
    user_usage = data.groupby(['user_name', 'email', 'department']).agg({
        'usage_count': 'sum',
        'cost_usd': 'sum',
        'tool_source': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    # Calculate threshold (top 20% by default)
    threshold = user_usage['usage_count'].quantile(threshold_percentile / 100)
    
    # Also include anyone with 200+ messages
    power_users = user_usage[
        (user_usage['usage_count'] >= threshold) | 
        (user_usage['usage_count'] >= 200)
    ].sort_values('usage_count', ascending=False)
    
    return power_users

def display_tool_comparison(data):
    """Display side-by-side tool comparison."""
    st.subheader("🔄 Tool Comparison View")
    
    # Get tool breakdown
    tools = data['tool_source'].unique()
    
    if len(tools) < 2:
        st.info("Upload data from multiple AI tools to see comparison metrics.")
        return
    
    # Create comparison columns
    cols = st.columns(len(tools))
    
    for idx, tool in enumerate(tools):
        tool_data = data[data['tool_source'] == tool]
        
        with cols[idx]:
            # Tool header with badge
            badge_class = f"tool-{tool.lower().replace(' ', '')}"
            st.markdown(f'<div class="tool-badge {badge_class}">{tool}</div>', unsafe_allow_html=True)
            
            # Key metrics
            active_users = tool_data['user_id'].nunique()
            total_usage = tool_data['usage_count'].sum()
            total_cost = tool_data['cost_usd'].sum()
            
            st.metric("Active Users", f"{active_users}")
            st.metric("Total Usage", f"{total_usage:,}")
            st.metric("Total Cost", f"${total_cost:,.2f}")
            st.metric("Avg per User", f"{total_usage / max(active_users, 1):.0f}")
    
    st.divider()
    
    # Overlap analysis
    st.subheader("🔗 User Overlap Analysis")
    
    user_tools = data.groupby('email')['tool_source'].apply(set).reset_index()
    multi_tool_users = user_tools[user_tools['tool_source'].apply(len) > 1]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Unique Users", data['email'].nunique())
    
    with col2:
        st.metric("Multi-Tool Users", len(multi_tool_users))
    
    with col3:
        overlap_pct = (len(multi_tool_users) / max(data['email'].nunique(), 1)) * 100
        st.metric("Overlap Rate", f"{overlap_pct:.1f}%")
    
    # Insights
    st.subheader("💡 Strategic Insights")
    
    if overlap_pct > 50:
        st.markdown("""
        <div class="insight-card insight-warning">
        <strong>⚠️ High Tool Overlap Detected</strong><br>
        Over 50% of users are using multiple AI tools. Consider:
        <ul>
            <li>Surveying users about distinct use cases for each tool</li>
            <li>Evaluating if tools have redundant capabilities</li>
            <li>Assessing potential cost savings from consolidation</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="insight-card insight-success">
        <strong>✅ Healthy Tool Distribution</strong><br>
        Tools appear to serve distinct user needs with minimal overlap.
        </div>
        """, unsafe_allow_html=True)
    
    # Cost comparison
    tool_costs = data.groupby('tool_source')['cost_usd'].sum().reset_index()
    
    fig = px.bar(
        tool_costs,
        x='tool_source',
        y='cost_usd',
        title='Total Cost by Tool',
        labels={'tool_source': 'Tool', 'cost_usd': 'Total Cost (USD)'},
        color='tool_source'
    )
    st.plotly_chart(fig, use_container_width=True)

def main():
    # Main header
    st.markdown('<h1 class="main-header">🤖 AI Usage Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.caption("Multi-Platform Analytics for Enterprise AI Tools")
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Executive Overview", 
        "🔄 Tool Comparison", 
        "⭐ Power Users",
        "🏢 Department Mapper",
        "🔧 Database Management"
    ])
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")
        
        # File upload section
        st.subheader("📁 Upload Data")
        
        # Tool selector
        tool_type = st.selectbox(
            "Select AI Tool",
            options=['Auto-Detect', 'OpenAI ChatGPT', 'BlueFlame AI', 'Other'],
            help="The system will try to auto-detect the data source"
        )
        
        uploaded_file = st.file_uploader(
            "Upload Usage Data (CSV/Excel)",
            type=['csv', 'xlsx'],
            help="Upload your AI tool usage export file"
        )
        
        if uploaded_file is not None:
            # Show file preview
            try:
                if uploaded_file.name.endswith('.csv'):
                    preview_df = pd.read_csv(uploaded_file, nrows=5)
                else:
                    preview_df = pd.read_excel(uploaded_file, nrows=5)
                
                st.write("**File Preview:**")
                st.dataframe(preview_df.head(3), height=120)
                st.caption(f"📊 {len(preview_df.columns)} columns detected")
                
            except Exception as e:
                st.error(f"Cannot preview file: {str(e)}")
            
            if st.button("Process Upload", type="primary"):
                with st.spinner("Processing data..."):
                    try:
                        # Read file
                        if uploaded_file.name.endswith('.csv'):
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        # Detect or use specified tool
                        if tool_type == 'Auto-Detect':
                            detected_tool = detect_data_source(df)
                            st.info(f"📡 Detected: {detected_tool}")
                        else:
                            detected_tool = tool_type.replace('OpenAI ', '')
                        
                        # Normalize based on tool
                        if 'ChatGPT' in detected_tool:
                            normalized_df = normalize_openai_data(df, uploaded_file.name)
                        elif 'BlueFlame' in detected_tool:
                            normalized_df = normalize_blueflame_data(df, uploaded_file.name)
                        else:
                            st.error("Unknown data format. Please select the correct tool.")
                            return
                        
                        # Store in database
                        if not normalized_df.empty:
                            # Use existing processor or direct database insert
                            success = processor.process_monthly_data(normalized_df, uploaded_file.name)
                            
                            if success:
                                st.success(f"✅ Processed {len(normalized_df)} records from {detected_tool}")
                                st.rerun()
                            else:
                                st.error("Error storing data")
                        else:
                            st.error("No data could be extracted from file")
                            
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
                        st.exception(e)
        
        st.divider()
        
        # Date range and filters
        st.subheader("📅 Filters")
        
        try:
            min_date, max_date = db.get_date_range()
        except:
            st.info("No data available. Upload your first file to begin.")
            return
        
        if min_date and max_date:
            st.info(f"📊 Data: {min_date} to {max_date}")
            
            date_range = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Tool filter
            all_data = db.get_all_data()
            if not all_data.empty and 'tool_source' in all_data.columns:
                available_tools = ['All Tools'] + list(all_data['tool_source'].unique())
                selected_tool = st.selectbox("Filter by Tool", available_tools)
            else:
                selected_tool = 'All Tools'
            
            # Department filter
            departments = db.get_unique_departments()
            selected_depts = st.multiselect(
                f"Departments ({len(departments)} total)",
                departments
            )
        else:
            st.info("Upload data to begin analysis")
            return
    
    # Load department mappings
    dept_mappings = load_department_mappings()
    
    # Get filtered data
    if len(date_range) == 2:
        start_date, end_date = date_range
        data = db.get_filtered_data(
            start_date=start_date,
            end_date=end_date,
            departments=selected_depts if selected_depts else None
        )
    else:
        data = db.get_all_data()
    
    # Apply department mappings
    data = apply_department_mappings(data, dept_mappings)
    
    # Apply tool filter
    if selected_tool != 'All Tools' and not data.empty:
        data = data[data['tool_source'] == selected_tool]
    
    if data.empty:
        st.warning("No data found for selected filters.")
        return
    
    # TAB 1: Executive Overview
    with tab1:
        st.header("📊 Executive Overview")
        
        # Key metrics
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
            avg_cost = total_cost / max(total_users, 1)
            st.metric("Avg Cost per User", f"${avg_cost:.2f}")
        
        # Tool breakdown
        if 'tool_source' in data.columns:
            st.subheader("🔧 Tool Adoption")
            
            tool_stats = data.groupby('tool_source').agg({
                'user_id': 'nunique',
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            
            cols = st.columns(len(tool_stats))
            for idx, row in tool_stats.iterrows():
                with cols[idx]:
                    st.metric(
                        f"{row['tool_source']}",
                        f"{row['user_id']} users",
                        f"${row['cost_usd']:,.2f}"
                    )
        
        # Usage trends
        st.subheader("📈 Usage Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            daily_usage = data.groupby('date')['usage_count'].sum().reset_index()
            fig = px.line(daily_usage, x='date', y='usage_count', title='Daily Usage Trend')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            daily_cost = data.groupby('date')['cost_usd'].sum().reset_index()
            fig = px.line(daily_cost, x='date', y='cost_usd', title='Daily Cost Trend')
            st.plotly_chart(fig, use_container_width=True)
        
        # Top users and departments
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Top 10 Users")
            top_users = data.groupby('user_name')['usage_count'].sum().nlargest(10).reset_index()
            fig = px.bar(top_users, x='usage_count', y='user_name', orientation='h')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Usage by Department")
            dept_usage = data.groupby('department')['usage_count'].sum().reset_index()
            fig = px.pie(dept_usage, values='usage_count', names='department')
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: Tool Comparison
    with tab2:
        display_tool_comparison(data)
    
    # TAB 3: Power Users
    with tab3:
        st.header("⭐ Power Users & Champions")
        
        power_users = calculate_power_users(data)
        
        if not power_users.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Power Users", len(power_users))
            
            with col2:
                pct = (len(power_users) / max(data['user_id'].nunique(), 1)) * 100
                st.metric("% of Active Users", f"{pct:.1f}%")
            
            with col3:
                power_usage = power_users['usage_count'].sum()
                st.metric("Power User Usage", f"{power_usage:,}")
            
            st.subheader("🏆 Power User Directory")
            st.caption("These users are ideal for feedback, beta testing, and advocacy programs")
            
            # Display power users in a nice table
            for idx, row in power_users.head(20).iterrows():
                col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
                
                with col1:
                    st.write(f"**{row['user_name']}**")
                    st.caption(row['email'])
                
                with col2:
                    st.write(row['department'])
                
                with col3:
                    st.write(f"{row['usage_count']:,} messages")
                
                with col4:
                    st.markdown(f'<span class="power-user-badge">{row["tool_source"]}</span>', 
                              unsafe_allow_html=True)
                
                st.divider()
        else:
            st.info("No power users identified yet. Add more usage data.")
    
    # TAB 4: Department Mapper
    with tab4:
        display_department_mapper()
    
    # TAB 5: Database Management
    with tab5:
        st.header("🔧 Database Management")
        
        db_info = get_database_info()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", db_info['total_stats']['total_records'])
        with col2:
            st.metric("Total Users", db_info['total_stats']['total_users'])
        with col3:
            st.metric("Date Range", f"{db_info['total_stats']['total_days']} days")
        with col4:
            st.metric("Total Cost", f"${db_info['total_stats']['total_cost']:,.2f}")
        
        # Upload history
        st.subheader("📂 Upload History")
        if db_info['upload_history']:
            upload_df = pd.DataFrame(db_info['upload_history'])
            st.dataframe(upload_df, use_container_width=True)
        else:
            st.info("No uploads yet")
        
        # Database actions
        st.subheader("🔧 Database Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear All Data", type="secondary"):
                if st.session_state.get('confirm_clear'):
                    db.delete_all_data()
                    st.success("Database cleared")
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm")
        
        with col2:
            all_data = db.get_all_data()
            if not all_data.empty:
                csv = all_data.to_csv(index=False)
                st.download_button(
                    "📥 Export All Data",
                    csv,
                    f"ai_usage_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )

def get_database_info():
    """Get database information."""
    all_data = db.get_all_data()
    
    if all_data.empty:
        return {
            'total_stats': {'total_records': 0, 'total_users': 0, 'total_days': 0, 'total_cost': 0.0},
            'upload_history': [],
            'date_coverage': pd.DataFrame()
        }
    
    total_cost = all_data['cost_usd'].sum() if 'cost_usd' in all_data.columns else 0.0
    
    total_stats = {
        'total_records': len(all_data),
        'total_users': all_data['user_id'].nunique(),
        'total_days': (pd.to_datetime(all_data['date'].max()) - pd.to_datetime(all_data['date'].min())).days + 1,
        'total_cost': float(total_cost)
    }
    
    upload_history = []
    if 'file_source' in all_data.columns:
        for filename in all_data['file_source'].unique():
            file_data = all_data[all_data['file_source'] == filename]
            upload_history.append({
                'filename': filename,
                'date_range': f"{file_data['date'].min()} to {file_data['date'].max()}",
                'records': len(file_data)
            })
    
    return {
        'total_stats': total_stats,
        'upload_history': upload_history,
        'date_coverage': pd.DataFrame()
    }

if __name__ == "__main__":
    main()