"""
Simple OpenAI Usage Metrics Dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import os

from file_reader import read_file_robust, display_file_error

# Page config
st.set_page_config(
    page_title="OpenAI Usage Analytics",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 OpenAI Usage Metrics Dashboard")

# Initialize database
@st.cache_resource
def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('usage_data.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            user_name TEXT,
            department TEXT,
            date TEXT,
            feature_used TEXT,
            usage_count INTEGER,
            cost_usd REAL
        )
    ''')
    conn.commit()
    return conn

# Initialize database
db = init_database()

# Sidebar
with st.sidebar:
    st.header("📁 Upload Data")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload your OpenAI usage metrics CSV file"
    )
    
    if uploaded_file is not None:
        try:
            # Read the uploaded file using robust reader
            df, error = read_file_robust(uploaded_file)
            
            if error:
                display_file_error(error)
            else:
                st.success(f"✅ File uploaded: {len(df)} rows")
                
                # Show preview
                st.subheader("Data Preview")
                st.dataframe(df.head())
            
            # Process button
            if st.button("Process Data", type="primary"):
                try:
                    # Ensure required columns exist
                    required_cols = ['user_id', 'user_name', 'department', 'date', 'feature_used', 'usage_count', 'cost_usd']
                    
                    for col in required_cols:
                        if col not in df.columns:
                            if col == 'user_id':
                                df[col] = 'user@company.com'
                            elif col == 'user_name':
                                df[col] = 'Unknown User'
                            elif col == 'department':
                                df[col] = 'General'
                            elif col == 'date':
                                df[col] = datetime.now().strftime('%Y-%m-%d')
                            elif col == 'feature_used':
                                df[col] = 'ChatGPT'
                            elif col == 'usage_count':
                                df[col] = 1
                            elif col == 'cost_usd':
                                df[col] = 0.0
                    
                    # Clean data
                    df['usage_count'] = pd.to_numeric(df['usage_count'], errors='coerce').fillna(0)
                    df['cost_usd'] = pd.to_numeric(df['cost_usd'], errors='coerce').fillna(0.0)
                    
                    # Save to database
                    df.to_sql('metrics', db, if_exists='append', index=False)
                    
                    st.success("✅ Data processed and saved!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Main dashboard
try:
    # Load data from database
    data = pd.read_sql_query("SELECT * FROM metrics", db)
    
    if not data.empty:
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_users = data['user_id'].nunique()
            st.metric("Total Active Users", total_users)
        
        with col2:
            total_usage = data['usage_count'].sum()
            st.metric("Total Messages", f"{total_usage:,}")
        
        with col3:
            avg_usage = total_usage / max(total_users, 1)
            st.metric("Messages per User", f"{avg_usage:,.0f}")
        
        # Charts
        st.subheader("📈 Usage Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top users
            top_users = data.groupby('user_name')['usage_count'].sum().sort_values(ascending=False).head(10)
            fig1 = px.bar(
                x=top_users.values,
                y=top_users.index,
                orientation='h',
                title="Top 10 Users by Usage"
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Department breakdown
            dept_data = data.groupby('department')['usage_count'].sum()
            fig2 = px.pie(
                values=dept_data.values,
                names=dept_data.index,
                title="Usage by Department"
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # Raw data
        with st.expander("📋 View Raw Data"):
            st.dataframe(data)
    
    else:
        st.info("👋 Welcome! Upload your first CSV file using the sidebar to get started.")
        
        # Show expected format
        st.subheader("Expected CSV Format")
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

except Exception as e:
    st.error(f"Database error: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🔧 **OpenAI Usage Analytics Dashboard**")