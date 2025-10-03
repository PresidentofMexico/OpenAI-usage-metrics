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
from file_reader import read_file_robust, display_file_error

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

# Enhanced CSS with micro UI improvements
st.markdown("""
<style>
    /* Main header with improved typography */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
    }
    
    /* Improved metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Tool badges with better styling */
    .tool-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 1.25rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .tool-badge:hover {
        transform: scale(1.05);
    }
    
    .tool-chatgpt {
        background: linear-gradient(135deg, #10a37f 0%, #0d8c6d 100%);
        color: white;
    }
    
    .tool-blueflame {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        color: white;
    }
    
    /* Enhanced power user badge */
    .power-user-badge {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.35rem 0.85rem;
        border-radius: 1.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Department mapper with improved styling */
    .dept-mapper-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 2px solid #e9ecef;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: #1e293b;
    }
    
    /* Enhanced insight cards */
    .insight-card {
        border-left: 4px solid;
        padding: 1.25rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .insight-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .insight-success {
        border-color: #10b981;
        background: linear-gradient(135deg, #d1fae5 0%, #ecfdf5 100%);
    }
    
    .insight-warning {
        border-color: #f59e0b;
        background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
    }
    
    .insight-info {
        border-color: #3b82f6;
        background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
    }
    
    /* Enhanced file upload zone */
    .upload-zone {
        border: 2px dashed #cbd5e1;
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        border-color: #667eea;
        background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 100%);
    }
    
    .upload-requirements {
        background: #f1f5f9;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        border: 1px solid #e2e8f0;
        color: #1e293b;
    }
    
    /* Loading states */
    .loading-skeleton {
        background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
        background-size: 200% 100%;
        animation: loading 1.5s ease-in-out infinite;
        border-radius: 0.5rem;
        height: 200px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
        border-radius: 0.75rem;
        border: 2px dashed #cbd5e1;
        margin: 2rem 0;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .empty-state-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 0.5rem;
    }
    
    .empty-state-text {
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    
    /* Data quality indicators */
    .quality-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: 600;
        font-size: 0.875rem;
        margin: 0.25rem;
    }
    
    .quality-excellent {
        background: #d1fae5;
        color: #065f46;
        border: 1px solid #10b981;
    }
    
    .quality-good {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #3b82f6;
    }
    
    .quality-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #f59e0b;
    }
    
    .quality-poor {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #ef4444;
    }
    
    /* Enhanced buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Help tooltips */
    .help-tooltip {
        background: #eff6ff;
        border: 1px solid #3b82f6;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        color: #1e40af;
    }
    
    /* Better spacing */
    .section-header {
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    /* Responsive improvements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.75rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
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
        
        # Get period dates with robust error handling
        period_start = pd.to_datetime(row.get('period_start', row.get('first_day_active_in_period', datetime.now())), errors='coerce')
        period_end = pd.to_datetime(row.get('period_end', row.get('last_day_active_in_period', datetime.now())), errors='coerce')
        
        # Fallback to current date if parsing fails
        if pd.isna(period_start):
            period_start = datetime.now()
        if pd.isna(period_end):
            period_end = datetime.now()
        
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
        # Parse date with robust error handling
        date_val = pd.to_datetime(row.get('date', row.get('month', datetime.now())), errors='coerce')
        if pd.isna(date_val):
            date_val = datetime.now()
        
        normalized_records.append({
            'user_id': row.get('user_id', row.get('email', '')),
            'user_name': row.get('user_name', row.get('name', '')),
            'email': row.get('email', ''),
            'department': row.get('department', 'Unknown'),
            'date': date_val,
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

def calculate_power_users(data, threshold_percentile=95):
    """Identify power users based on usage patterns."""
    if data.empty:
        return pd.DataFrame()
    
    # Group by user and calculate total usage
    user_usage = data.groupby(['user_name', 'email', 'department']).agg({
        'usage_count': 'sum',
        'cost_usd': 'sum',
        'tool_source': lambda x: ', '.join(x.unique())
    }).reset_index()
    
    # Calculate threshold (top 5% by default)
    threshold = user_usage['usage_count'].quantile(threshold_percentile / 100)
    
    # Identify power users (top 5% by usage)
    power_users = user_usage[
        user_usage['usage_count'] >= threshold
    ].sort_values('usage_count', ascending=False)
    
    return power_users

def get_user_message_breakdown(data, email):
    """Get message type breakdown for a specific user."""
    user_data = data[data['email'] == email]
    
    breakdown = {
        'ChatGPT Messages': 0,
        'GPT Messages': 0,
        'Tool Messages': 0,
        'Project Messages': 0
    }
    
    if not user_data.empty:
        message_counts = user_data.groupby('feature_used')['usage_count'].sum().to_dict()
        for msg_type in breakdown.keys():
            breakdown[msg_type] = message_counts.get(msg_type, 0)
    
    return breakdown

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
        
        # Enhanced file upload section
        st.subheader("📁 Upload Data")
        
        # File requirements info box
        st.markdown("""
        <div class="upload-requirements">
            <strong>📋 Accepted Formats:</strong><br>
            • CSV files (.csv)<br>
            • Excel files (.xlsx)<br>
            <strong>📏 Max Size:</strong> 200MB
        </div>
        """, unsafe_allow_html=True)
        
        # Tool selector with enhanced help
        tool_type = st.selectbox(
            "Select AI Tool",
            options=['Auto-Detect', 'OpenAI ChatGPT', 'BlueFlame AI', 'Other'],
            help="💡 Auto-Detect will analyze your file and identify the data source automatically"
        )
        
        uploaded_file = st.file_uploader(
            "Upload Usage Data (CSV/Excel)",
            type=['csv', 'xlsx'],
            help="🔼 Drag and drop your file here or click to browse"
        )
        
        if uploaded_file is not None:
            # Show file info with enhanced styling
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.success(f"✅ File loaded: **{uploaded_file.name}** ({file_size_mb:.2f} MB)")
            
            # Show file preview with better error handling
            try:
                with st.spinner("🔍 Reading file preview..."):
                    preview_df, preview_error = read_file_robust(uploaded_file, nrows=5)
                    
                    if preview_error:
                        display_file_error(preview_error)
                    else:
                        st.write("**📊 File Preview:**")
                        st.dataframe(preview_df.head(3), height=120)
                        
                        # Enhanced file statistics
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Columns", len(preview_df.columns))
                        with col2:
                            # Get full row count
                            try:
                                full_df, full_error = read_file_robust(uploaded_file)
                                if full_error:
                                    st.metric("Rows", "~")
                                else:
                                    st.metric("Rows", len(full_df))
                            except:
                                st.metric("Rows", "~")
                
            except Exception as e:
                st.error(f"❌ Cannot preview file: {str(e)}")
                st.info("💡 Please ensure your file is a valid CSV or Excel file")
            
            if st.button("🚀 Process Upload", type="primary", use_container_width=True):
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Reading file
                    status_text.text("📖 Reading file...")
                    progress_bar.progress(20)
                    
                    df, read_error = read_file_robust(uploaded_file)
                    
                    if read_error:
                        progress_bar.empty()
                        status_text.empty()
                        display_file_error(read_error)
                        return
                    
                    if df is None or df.empty:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("❌ The uploaded file contains no data")
                        return
                    
                    # Step 2: Detecting data source
                    status_text.text("🔍 Detecting data source...")
                    progress_bar.progress(40)
                    
                    if tool_type == 'Auto-Detect':
                        detected_tool = detect_data_source(df)
                        st.info(f"📡 Detected: **{detected_tool}**")
                    else:
                        detected_tool = tool_type.replace('OpenAI ', '')
                    
                    # Step 3: Normalizing data
                    status_text.text("⚙️ Normalizing data structure...")
                    progress_bar.progress(60)
                    
                    if 'ChatGPT' in detected_tool:
                        normalized_df = normalize_openai_data(df, uploaded_file.name)
                    elif 'BlueFlame' in detected_tool:
                        normalized_df = normalize_blueflame_data(df, uploaded_file.name)
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("❌ Unknown data format. Please select the correct tool.")
                        return
                    
                    # Step 4: Storing in database
                    status_text.text("💾 Storing in database...")
                    progress_bar.progress(80)
                    
                    if not normalized_df.empty:
                        success = processor.process_monthly_data(normalized_df, uploaded_file.name)
                        
                        progress_bar.progress(100)
                        
                        if success:
                            status_text.empty()
                            progress_bar.empty()
                            
                            # Success message with details
                            st.success(f"""
                            ✅ **Upload Complete!**
                            - Processed **{len(normalized_df)}** records
                            - Source: **{detected_tool}**
                            - File: {uploaded_file.name}
                            """)
                            
                            # Show summary metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Users Found", normalized_df['user_id'].nunique())
                            with col2:
                                st.metric("Total Usage", f"{normalized_df['usage_count'].sum():,}")
                            
                            st.balloons()
                            st.rerun()
                        else:
                            progress_bar.empty()
                            status_text.empty()
                            st.error("❌ Error storing data in database")
                    else:
                        progress_bar.empty()
                        status_text.empty()
                        st.error("❌ No data could be extracted from file")
                        st.info("💡 Please verify your file format matches the selected tool type")
                        
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ **Error processing file:** {str(e)}")
                    
                    # Provide helpful error context
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        **Common issues:**
                        - Ensure your CSV/Excel file is not corrupted
                        - Check that column names match the expected format
                        - Verify the file contains the required data fields
                        - Try selecting the tool type manually instead of Auto-Detect
                        """)
                    st.exception(e)
        
        st.divider()
        
        # Date range and filters
        st.subheader("📅 Filters")
        
        try:
            min_date, max_date = db.get_date_range()
        except:
            # Enhanced empty state for no data
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-title">No Data Available</div>
                <div class="empty-state-text">
                    Upload your first AI usage export file to start analyzing data
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Helpful guidance
            with st.expander("📚 Getting Started Guide"):
                st.markdown("""
                **To get started:**
                1. Export your AI tool usage data (CSV or Excel)
                2. Select the tool type or use Auto-Detect
                3. Upload your file using the uploader above
                4. Wait for processing to complete
                
                **Supported Tools:**
                - OpenAI ChatGPT Enterprise exports
                - BlueFlame AI usage reports
                - Other AI platforms (manual mapping)
                """)
            return
        
        if min_date and max_date:
            # Enhanced data availability indicator
            date_diff = (max_date - min_date).days
            st.markdown(f"""
            <div class="help-tooltip">
                📊 <strong>Data Available:</strong> {min_date} to {max_date} ({date_diff + 1} days)
            </div>
            """, unsafe_allow_html=True)
            
            date_range = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                help="📅 Filter data by date range for focused analysis"
            )
            
            # Tool filter with enhanced UI
            all_data = db.get_all_data()
            if not all_data.empty and 'tool_source' in all_data.columns:
                available_tools = ['All Tools'] + list(all_data['tool_source'].unique())
                selected_tool = st.selectbox(
                    "Filter by Tool", 
                    available_tools,
                    help="🔧 View data from specific AI tools or all combined"
                )
            else:
                selected_tool = 'All Tools'
            
            # Department filter with count
            departments = db.get_unique_departments()
            selected_depts = st.multiselect(
                f"Departments ({len(departments)} total)",
                departments,
                help="🏢 Filter by specific departments (leave empty for all)"
            )
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <div class="empty-state-title">Upload Data to Begin</div>
            </div>
            """, unsafe_allow_html=True)
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
        # Enhanced empty state for no filtered data
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🔍</div>
            <div class="empty-state-title">No Data Found</div>
            <div class="empty-state-text">
                No data matches your current filter selections.<br>
                Try adjusting your date range, tool, or department filters.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick reset options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reset All Filters", type="secondary"):
                st.rerun()
        with col2:
            if st.button("📊 View All Data", type="primary"):
                st.session_state.clear()
                st.rerun()
        return
    
    # TAB 1: Executive Overview
    with tab1:
        st.header("📊 Executive Overview")
        
        # Data Quality Dashboard
        st.markdown('<div class="section-header"><h3>🛡️ Data Quality</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate data quality metrics
        completeness = (1 - data.isnull().sum().sum() / (len(data) * len(data.columns))) * 100
        unique_users = data['user_id'].nunique()
        
        # Robust date handling - convert dates and filter out invalid values
        try:
            valid_dates = pd.to_datetime(data['date'], errors='coerce').dropna()
            if len(valid_dates) > 0:
                date_coverage = (valid_dates.max() - valid_dates.min()).days + 1
            else:
                date_coverage = 0
        except Exception as e:
            st.warning(f"⚠️ Date parsing issue: {str(e)}")
            date_coverage = 0
        
        with col1:
            quality_class = "quality-excellent" if completeness >= 95 else "quality-good" if completeness >= 80 else "quality-warning"
            st.markdown(f'<div class="{quality_class}" style="padding: 0.75rem; border-radius: 0.5rem; text-align: center;"><strong>{completeness:.1f}%</strong><br><small>Completeness</small></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="quality-good" style="padding: 0.75rem; border-radius: 0.5rem; text-align: center;"><strong>{unique_users}</strong><br><small>Active Users</small></div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'<div class="quality-good" style="padding: 0.75rem; border-radius: 0.5rem; text-align: center;"><strong>{date_coverage}</strong><br><small>Days Coverage</small></div>', unsafe_allow_html=True)
        
        with col4:
            total_records = len(data)
            st.markdown(f'<div class="quality-good" style="padding: 0.75rem; border-radius: 0.5rem; text-align: center;"><strong>{total_records:,}</strong><br><small>Total Records</small></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Key metrics with enhanced styling
        st.markdown('<div class="section-header"><h3>📈 Key Metrics</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_users = data['user_id'].nunique()
            st.metric("Total Active Users", total_users, help="Number of unique users in the selected period")
        
        with col2:
            total_usage = data['usage_count'].sum()
            st.metric("Total Usage Events", f"{total_usage:,}", help="Total number of AI interactions across all message types")
        
        with col3:
            total_cost = data['cost_usd'].sum()
            st.metric("Total Cost", f"${total_cost:,.2f}", help="Estimated total cost based on usage")
        
        with col4:
            avg_cost = total_cost / max(total_users, 1)
            st.metric("Avg Cost per User", f"${avg_cost:.2f}", help="Average cost per active user")
        
        # Message Type Breakdown
        st.markdown('<div class="section-header"><h3>💬 Message Type Breakdown</h3></div>', unsafe_allow_html=True)
        
        # Calculate metrics for each message type
        message_types = data.groupby('feature_used')['usage_count'].sum().to_dict()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            chatgpt_msgs = message_types.get('ChatGPT Messages', 0)
            st.metric(
                "ChatGPT Messages", 
                f"{chatgpt_msgs:,}", 
                help="Base model usage - standard ChatGPT conversations"
            )
        
        with col2:
            gpt_msgs = message_types.get('GPT Messages', 0)
            st.metric(
                "GPT Messages", 
                f"{gpt_msgs:,}", 
                help="Custom GPT usage - interactions with custom GPTs"
            )
        
        with col3:
            tool_msgs = message_types.get('Tool Messages', 0)
            st.metric(
                "Tool Messages", 
                f"{tool_msgs:,}", 
                help="Tool interactions - code interpreter, web browsing, etc."
            )
        
        with col4:
            project_msgs = message_types.get('Project Messages', 0)
            st.metric(
                "Project Messages", 
                f"{project_msgs:,}", 
                help="ChatGPT Projects usage - project-specific conversations"
            )
        
        # Tool breakdown with enhanced styling
        if 'tool_source' in data.columns:
            st.markdown('<div class="section-header"><h3>🔧 Tool Adoption</h3></div>', unsafe_allow_html=True)
            
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
        st.markdown('<div class="section-header"><h3>📈 Usage & Cost Trends</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            daily_usage = data.groupby('date')['usage_count'].sum().reset_index()
            fig = px.line(
                daily_usage, 
                x='date', 
                y='usage_count', 
                title='Daily Usage Trend',
                labels={'date': 'Date', 'usage_count': 'Usage Count'}
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            daily_cost = data.groupby('date')['cost_usd'].sum().reset_index()
            fig = px.line(
                daily_cost, 
                x='date', 
                y='cost_usd', 
                title='Daily Cost Trend',
                labels={'date': 'Date', 'cost_usd': 'Cost (USD)'}
            )
            fig.update_traces(line_color='#10b981', line_width=3)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top users and departments
        st.markdown('<div class="section-header"><h3>🏆 Top Performers & Department Analysis</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Top 10 Users")
            top_users = data.groupby('user_name')['usage_count'].sum().nlargest(10).reset_index()
            fig = px.bar(
                top_users, 
                x='usage_count', 
                y='user_name', 
                orientation='h',
                labels={'usage_count': 'Usage Count', 'user_name': 'User'}
            )
            fig.update_traces(marker_color='#667eea')
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Usage by Department")
            dept_usage = data.groupby('department')['usage_count'].sum().reset_index()
            fig = px.pie(
                dept_usage, 
                values='usage_count', 
                names='department',
                hole=0.4
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label'
            )
            fig.update_layout(
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: Tool Comparison
    with tab2:
        display_tool_comparison(data)
    
    # TAB 3: Power Users
    with tab3:
        st.header("⭐ Power Users & Champions")
        
        # Help text
        st.markdown("""
        <div class="help-tooltip">
            💡 <strong>Power Users</strong> are defined as the top 5% of users by total usage.
            These elite users demonstrate exceptional engagement and are ideal candidates for feedback, beta testing, and advocacy programs.
        </div>
        """, unsafe_allow_html=True)
        
        power_users = calculate_power_users(data)
        
        if not power_users.empty:
            # Enhanced metrics row
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Power Users", 
                    len(power_users),
                    help="Number of users identified as power users"
                )
            
            with col2:
                pct = (len(power_users) / max(data['user_id'].nunique(), 1)) * 100
                st.metric(
                    "% of Active Users", 
                    f"{pct:.1f}%",
                    help="Percentage of all users who are power users"
                )
            
            with col3:
                power_usage = power_users['usage_count'].sum()
                total_usage_pct = (power_usage / data['usage_count'].sum()) * 100
                st.metric(
                    "Power User Usage", 
                    f"{power_usage:,}",
                    delta=f"{total_usage_pct:.1f}% of total",
                    help="Total usage by power users"
                )
            
            st.divider()
            st.subheader("🏆 Power User Directory")
            st.caption("These users are ideal for feedback, beta testing, and advocacy programs")
            
            # Enhanced table display with better formatting
            for idx, row in power_users.head(20).iterrows():
                # Get message breakdown for this user
                breakdown = get_user_message_breakdown(data, row['email'])
                total_messages = sum(breakdown.values())
                
                # Create a card-like container for each power user
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); 
                            padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; 
                            border-left: 4px solid #667eea;">
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 4, 3])
                
                with col1:
                    st.write(f"**{row['user_name']}**")
                    st.caption(row['email'])
                    st.caption(f"🏢 {row['department']}")
                
                with col2:
                    st.write("**Message Breakdown:**")
                    # Display breakdown of message types
                    if breakdown['ChatGPT Messages'] > 0:
                        st.caption(f"💬 ChatGPT Messages: {breakdown['ChatGPT Messages']:,}")
                    if breakdown['GPT Messages'] > 0:
                        st.caption(f"🤖 GPT Messages: {breakdown['GPT Messages']:,}")
                    if breakdown['Tool Messages'] > 0:
                        st.caption(f"🔧 Tool Messages: {breakdown['Tool Messages']:,}")
                    if breakdown['Project Messages'] > 0:
                        st.caption(f"📁 Project Messages: {breakdown['Project Messages']:,}")
                
                with col3:
                    st.write(f"**Total: {total_messages:,}**")
                    st.caption(f"💰 ${row['cost_usd']:.2f} cost")
                    st.markdown(f'<span class="power-user-badge">{row["tool_source"]}</span>', 
                              unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Enhanced empty state for power users
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">⭐</div>
                <div class="empty-state-title">No Power Users Yet</div>
                <div class="empty-state-text">
                    Power users will appear here once you have sufficient usage data.<br>
                    Upload more monthly reports to identify your most active users.
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # TAB 4: Department Mapper
    with tab4:
        display_department_mapper()
    
    # TAB 5: Database Management
    with tab5:
        st.header("🔧 Database Management")
        
        st.markdown("""
        <div class="help-tooltip">
            💡 Monitor your database health, manage uploads, and export data for external analysis
        </div>
        """, unsafe_allow_html=True)
        
        db_info = get_database_info()
        
        # Enhanced database stats
        st.markdown('<div class="section-header"><h3>📊 Database Statistics</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Total Records", 
                f"{db_info['total_stats']['total_records']:,}",
                help="Total number of records in database"
            )
        with col2:
            st.metric(
                "Total Users", 
                db_info['total_stats']['total_users'],
                help="Unique users across all data"
            )
        with col3:
            st.metric(
                "Date Range", 
                f"{db_info['total_stats']['total_days']} days",
                help="Total days of data coverage"
            )
        with col4:
            st.metric(
                "Total Cost", 
                f"${db_info['total_stats']['total_cost']:,.2f}",
                help="Total estimated cost across all records"
            )
        
        st.divider()
        
        # Upload history with better styling
        st.markdown('<div class="section-header"><h3>📂 Upload History</h3></div>', unsafe_allow_html=True)
        
        if db_info['upload_history']:
            upload_df = pd.DataFrame(db_info['upload_history'])
            st.dataframe(upload_df, use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <div class="empty-state-title">No Upload History</div>
                <div class="empty-state-text">Upload your first file to see history here</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Database actions with better UX
        st.markdown('<div class="section-header"><h3>⚙️ Database Actions</h3></div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Export Data**")
            all_data = db.get_all_data()
            if not all_data.empty:
                csv = all_data.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"ai_usage_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True,
                    help="Download all data as CSV for external analysis"
                )
            else:
                st.button("📥 Download CSV", disabled=True, use_container_width=True)
        
        with col2:
            st.write("**Refresh Data**")
            if st.button("🔄 Refresh Dashboard", type="secondary", use_container_width=True):
                st.cache_resource.clear()
                st.success("Cache cleared!")
                st.rerun()
        
        with col3:
            st.write("**Clear Database**")
            if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
                if st.session_state.get('confirm_clear'):
                    db.delete_all_data()
                    st.session_state.confirm_clear = False
                    st.success("✅ Database cleared successfully")
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("⚠️ Click again to confirm deletion")
        
        # Warning about clear action
        if st.session_state.get('confirm_clear'):
            st.error("⚠️ **Warning:** This action will permanently delete all data. Click the button again to confirm.")

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
    
    # Calculate total days with robust date handling
    try:
        valid_dates = pd.to_datetime(all_data['date'], errors='coerce').dropna()
        if len(valid_dates) > 0:
            total_days = (valid_dates.max() - valid_dates.min()).days + 1
        else:
            total_days = 0
    except Exception:
        total_days = 0
    
    total_stats = {
        'total_records': len(all_data),
        'total_users': all_data['user_id'].nunique(),
        'total_days': total_days,
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