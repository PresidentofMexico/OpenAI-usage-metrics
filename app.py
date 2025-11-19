import streamlit as st
import pandas as pd
from config import DASHBOARD_TITLE, DASHBOARD_ICON
from styles import load_css
from database import DatabaseManager
from data_processor import DataProcessor
from file_reader import read_file_robust, display_file_error
from ui_components import render_kpi_row, render_trend_chart

# 1. Page Config
st.set_page_config(page_title=DASHBOARD_TITLE, page_icon=DASHBOARD_ICON, layout="wide")
load_css()

# 2. Initialization (Cached to prevent reloading on every interaction)
@st.cache_resource
def get_managers():
    db = DatabaseManager()
    processor = DataProcessor(db)
    return db, processor

db, processor = get_managers()

# 3. Sidebar - Controls
with st.sidebar:
    st.header("🔧 Controls")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Usage Data", type=['csv', 'xlsx'])
    tool_type = st.selectbox("Tool Type", ["ChatGPT", "BlueFlame AI"])
    
    if uploaded_file and st.button("Process File", type="primary"):
        with st.spinner("Reading file..."):
            raw_df, error = read_file_robust(uploaded_file)
            if error:
                display_file_error(error)
            else:
                with st.spinner("Processing & Saving to Database..."):
                    success, msg = processor.process_upload(raw_df, uploaded_file.name, tool_type)
                    if success:
                        st.success(msg)
                        st.cache_data.clear() # Clear data cache on update
                    else:
                        st.error(msg)

    st.divider()
    st.subheader("Filters")
    # Note: Get min/max date from DB for Date Input defaults
    date_range = st.date_input("Date Range", [])

# 4. Main Content
st.markdown(f'<h1 class="main-header">{DASHBOARD_TITLE}</h1>', unsafe_allow_html=True)

# Tabs
tab_overview, tab_directory, tab_admin = st.tabs(["📊 Executive Overview", "👥 User Directory", "⚙️ Admin"])

with tab_overview:
    # Fetch Aggregated Metrics (Efficient SQL Query)
    metrics = db.get_aggregated_metrics()
    
    # KPI Row
    kpi_data = {
        "Total Active Users": {"value": f"{metrics['total_users']:,}", "subtext": "Unique Emails"},
        "Total Messages": {"value": f"{metrics['total_messages']:,}", "subtext": "All Providers"},
        "Est. Monthly Cost": {"value": f"${metrics['total_cost']:,.2f}", "subtext": "License Based"}
    }
    render_kpi_row(kpi_data)
    
    st.divider()
    
    # Charts (Example: Fetch chart data specifically)
    # chart_data = db.get_chart_data(...) 
    # render_trend_chart(chart_data, ...)
    st.info("Charts would populate here using optimized SQL queries.")

with tab_directory:
    st.subheader("User Usage Directory")
    
    # Server-Side Pagination Logic
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search User", placeholder="Name or Email...")
    with col2:
        page = st.number_input("Page", min_value=1, value=1)
    
    # Fetch only the slice we need
    df_users = db.get_filtered_data_paginated(page=page-1, page_size=20, search_term=search)
    
    if not df_users.empty:
        st.dataframe(
            df_users[['user_name', 'email', 'department', 'feature_used', 'usage_count', 'date']], 
            use_container_width=True
        )
    else:
        st.warning("No users found matching criteria.")

with tab_admin:
    st.subheader("Database Management")
    if st.button("Reset Database (Caution)", type="primary"):
        # Implementation for hard reset
        pass
