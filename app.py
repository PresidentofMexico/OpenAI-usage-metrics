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
from file_reader import read_file_robust, display_file_error, read_file_from_path
from file_scanner import FileScanner
from config import AUTO_SCAN_FOLDERS, FILE_TRACKING_PATH, ENTERPRISE_PRICING
from export_utils import generate_excel_export, generate_pdf_report_html
from cost_calculator import EnterpriseCostCalculator

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
    scanner = FileScanner(FILE_TRACKING_PATH)
    return db, processor, scanner

db, processor, scanner = init_app()

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

def apply_employee_departments(data, db_manager=None):
    """
    Apply employee master file departments to all data.
    
    This ensures the employee master file is the authoritative source for 
    department assignments for all employees, not just power users.
    
    Args:
        data: DataFrame with usage data
        db_manager: DatabaseManager instance (optional, will use global db if not provided)
        
    Returns:
        DataFrame with employee departments applied
    """
    if data.empty:
        return data
    
    data = data.copy()
    
    # Use provided db_manager or fall back to global db
    database = db_manager if db_manager is not None else db
    
    # Get all employees for efficient lookup
    try:
        employees_df = database.get_all_employees()
        if employees_df.empty:
            return data
        
        # Create lookup dictionaries for fast matching
        email_to_dept = {}
        name_to_dept = {}
        
        for _, emp in employees_df.iterrows():
            # Email-based lookup (primary)
            if pd.notna(emp.get('email')) and emp.get('email'):
                email_to_dept[emp['email'].lower().strip()] = emp.get('department', 'Unknown')
            
            # Name-based lookup (fallback)
            if pd.notna(emp.get('first_name')) and pd.notna(emp.get('last_name')):
                full_name = f"{emp['first_name']} {emp['last_name']}".lower().strip()
                name_to_dept[full_name] = emp.get('department', 'Unknown')
        
        # Apply employee departments to data
        for idx, row in data.iterrows():
            employee_dept = None
            
            # Try email match first
            if pd.notna(row.get('email')) and row.get('email'):
                email_key = row['email'].lower().strip()
                if email_key in email_to_dept:
                    employee_dept = email_to_dept[email_key]
            
            # Try name match if email didn't work
            if not employee_dept and pd.notna(row.get('user_name')) and row.get('user_name'):
                name_key = row['user_name'].lower().strip()
                if name_key in name_to_dept:
                    employee_dept = name_to_dept[name_key]
            
            # Update department if employee found
            if employee_dept:
                data.at[idx, 'department'] = employee_dept
        
        return data
        
    except AttributeError as e:
        # Handle case where db doesn't have employee methods (cache error)
        print(f"AttributeError in apply_employee_departments: {e}")
        return data
    except Exception as e:
        print(f"Error applying employee departments: {e}")
        import traceback
        traceback.print_exc()
        return data

def is_employee_user(email, user_name):
    """
    Check if a user is an employee by email or name.
    
    Args:
        email: User email address
        user_name: User full name
        
    Returns:
        bool: True if user is an employee, False otherwise
    """
    try:
        # First try by email
        if email:
            employee = db.get_employee_by_email(email)
            if employee:
                return True
        
        # Try by name if email lookup fails
        if user_name:
            name_parts = user_name.strip().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                employee = db.get_employee_by_name(first_name, last_name)
                if employee:
                    return True
        
        return False
    except AttributeError:
        # Handle cache error - database object missing methods
        # This happens when code is updated while app is running
        return False

def get_employee_for_user(email, user_name):
    """
    Get employee record for a user by email or name.
    
    Args:
        email: User email address
        user_name: User full name
        
    Returns:
        dict or None: Employee record if found
    """
    try:
        # First try by email
        if email:
            employee = db.get_employee_by_email(email)
            if employee:
                return employee
        
        # Try by name if email lookup fails
        if user_name:
            name_parts = user_name.strip().split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                employee = db.get_employee_by_name(first_name, last_name)
                if employee:
                    return employee
        
        return None
    except AttributeError:
        # Handle cache error - database object missing methods
        # This happens when code is updated while app is running
        return None

# Enhanced CSS with dark mode support
st.markdown("""
<style>
    /* CSS Variables for Light and Dark Mode */
    :root {
        /* Light mode colors (default) */
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9fa;
        --bg-tertiary: #f1f5f9;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-tertiary: #64748b;
        --border-color: #e9ecef;
        --border-color-light: #e2e8f0;
        --border-dashed: #cbd5e1;
        --shadow-sm: rgba(0,0,0,0.05);
        --shadow-md: rgba(0,0,0,0.1);
        --shadow-lg: rgba(0,0,0,0.15);
        
        /* Card backgrounds */
        --card-bg-start: #f8f9fa;
        --card-bg-end: #ffffff;
        
        /* State colors with good contrast */
        --success-bg: #d1fae5;
        --success-text: #065f46;
        --success-border: #10b981;
        
        --warning-bg: #fef3c7;
        --warning-text: #92400e;
        --warning-border: #f59e0b;
        
        --info-bg: #dbeafe;
        --info-text: #1e40af;
        --info-border: #3b82f6;
        
        --error-bg: #fee2e2;
        --error-text: #991b1b;
        --error-border: #ef4444;
    }
    
    /* Dark mode colors */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #1e293b;
            --bg-secondary: #334155;
            --bg-tertiary: #475569;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-tertiary: #94a3b8;
            --border-color: #475569;
            --border-color-light: #64748b;
            --border-dashed: #64748b;
            --shadow-sm: rgba(0,0,0,0.3);
            --shadow-md: rgba(0,0,0,0.4);
            --shadow-lg: rgba(0,0,0,0.5);
            
            /* Card backgrounds for dark mode */
            --card-bg-start: #334155;
            --card-bg-end: #1e293b;
            
            /* State colors optimized for dark mode */
            --success-bg: #065f46;
            --success-text: #a7f3d0;
            --success-border: #34d399;
            
            --warning-bg: #78350f;
            --warning-text: #fde68a;
            --warning-border: #fbbf24;
            
            --info-bg: #1e3a8a;
            --info-text: #bfdbfe;
            --info-border: #60a5fa;
            
            --error-bg: #7f1d1d;
            --error-text: #fecaca;
            --error-border: #f87171;
        }
    }
    
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
        background: linear-gradient(135deg, var(--card-bg-start) 0%, var(--card-bg-end) 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px var(--shadow-sm);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        color: var(--text-primary);
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 8px var(--shadow-md);
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
        box-shadow: 0 2px 4px var(--shadow-md);
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
        background: linear-gradient(135deg, var(--card-bg-start) 0%, var(--card-bg-end) 100%);
        border: 2px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px var(--shadow-sm);
        color: var(--text-primary);
    }
    
    /* Enhanced insight cards */
    .insight-card {
        border-left: 4px solid;
        padding: 1.25rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    .insight-card:hover {
        box-shadow: 0 4px 8px var(--shadow-md);
    }
    
    .insight-success {
        border-color: var(--success-border);
        background: var(--success-bg);
        color: var(--success-text);
    }
    
    .insight-warning {
        border-color: var(--warning-border);
        background: var(--warning-bg);
        color: var(--warning-text);
    }
    
    .insight-info {
        border-color: var(--info-border);
        background: var(--info-bg);
        color: var(--info-text);
    }
    
    /* Enhanced file upload zone */
    .upload-zone {
        border: 2px dashed var(--border-dashed);
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        background: var(--bg-secondary);
        margin: 1rem 0;
        transition: all 0.3s ease;
        color: var(--text-primary);
    }
    
    .upload-zone:hover {
        border-color: #667eea;
        background: var(--bg-tertiary);
    }
    
    .upload-requirements {
        background: var(--bg-tertiary);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        border: 1px solid var(--border-color-light);
        color: var(--text-primary);
    }
    
    /* Loading states */
    .loading-skeleton {
        background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--border-color-light) 50%, var(--bg-tertiary) 75%);
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
        background: var(--bg-secondary);
        border-radius: 0.75rem;
        border: 2px dashed var(--border-dashed);
        margin: 2rem 0;
        color: var(--text-primary);
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .empty-state-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }
    
    .empty-state-text {
        color: var(--text-tertiary);
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
        background: var(--success-bg);
        color: var(--success-text);
        border: 1px solid var(--success-border);
    }
    
    .quality-good {
        background: var(--info-bg);
        color: var(--info-text);
        border: 1px solid var(--info-border);
    }
    
    .quality-warning {
        background: var(--warning-bg);
        color: var(--warning-text);
        border: 1px solid var(--warning-border);
    }
    
    .quality-poor {
        background: var(--error-bg);
        color: var(--error-text);
        border: 1px solid var(--error-border);
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.75rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .metrics-grid {
            grid-template-columns: 1fr !important;
        }
        
        /* Stack columns on mobile */
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            max-width: 100% !important;
        }
    }
    
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem;
        }
        
        body {
            font-size: 14px;
        }
    }
    
    /* Enhanced tooltips */
    .help-tooltip {
        background: var(--info-bg);
        border-left: 4px solid var(--info-border);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        font-size: 0.875rem;
        border: 1px solid var(--info-border);
        color: var(--info-text);
    }
    
    .help-tooltip strong {
        color: var(--info-text);
        font-weight: 700;
    }
    
    /* Info cards with icons */
    .info-card {
        background: var(--bg-primary);
        border: 2px solid var(--border-color);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px var(--shadow-md);
        color: var(--text-primary);
    }
    
    .info-card-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Responsive tables */
    @media (max-width: 768px) {
        .data-table {
            font-size: 0.875rem;
        }
        
        .data-table th, .data-table td {
            padding: 0.5rem;
        }
    }
    
    /* Enhanced buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px var(--shadow-md);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px var(--shadow-lg);
    }
    
    /* Better spacing */
    .section-header {
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
        color: var(--text-primary);
    }
</style>
""", unsafe_allow_html=True)

def detect_data_source(df):
    """Detect which AI tool the data is from based on column structure."""
    columns = df.columns.tolist()
    
    # OpenAI ChatGPT detection
    if 'gpt_messages' in columns or 'tool_messages' in columns:
        return 'ChatGPT'
    
    # BlueFlame AI detection - updated for all formats
    # Check for month columns in format 'Mon-YY' (e.g., 'Sep-24', 'Oct-25')
    has_month_cols = any(col for col in columns if len(col.split('-')) == 2 and 
                        col.split('-')[0] in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    
    if ('Metric' in columns and any(col.startswith('MoM Var') for col in columns)) or \
       ('Total Messages' in df.values if not df.empty else False) or \
       ('User ID' in columns and has_month_cols) or \
       ('Table' in columns and has_month_cols):
        return 'BlueFlame AI'
    
    # Default or ask user
    return 'Unknown'

def normalize_openai_data(df, filename):
    """Normalize OpenAI CSV export to standard schema with enterprise license costs."""
    normalized_records = []
    
    # Get enterprise pricing
    cost_calc = EnterpriseCostCalculator()
    pricing_info = cost_calc.get_pricing_info('ChatGPT')
    monthly_license_cost = pricing_info['license_cost_per_user_monthly']
    
    for _, row in df.iterrows():
        # Get user email and name
        user_email = row.get('email', '')
        user_name = row.get('name', '')
        
        # Look up employee by email to get authoritative department
        employee = None
        try:
            if user_email:
                employee = db.get_employee_by_email(user_email)
            
            # If no match by email, try matching by name
            if not employee and user_name:
                # Try to parse name into first and last
                name_parts = user_name.strip().split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = ' '.join(name_parts[1:])  # Handle multi-part last names
                    employee = db.get_employee_by_name(first_name, last_name)
        except AttributeError:
            # Handle cache error - database object missing methods
            employee = None
        
        if employee:
            # Use employee data as source of truth
            dept = employee['department'] if employee['department'] else 'Unknown'
            user_name = f"{employee['first_name']} {employee['last_name']}".strip()
            if not user_name:
                user_name = row.get('name', '')
        else:
            # User not in employee roster - flag as unidentified
            # Parse department - OpenAI exports it as a JSON array string
            dept = 'Unknown'
            user_name = row.get('name', '')
        
        # Get period dates with robust error handling
        period_start = pd.to_datetime(row.get('period_start', row.get('first_day_active_in_period', datetime.now())), errors='coerce')
        period_end = pd.to_datetime(row.get('period_end', row.get('last_day_active_in_period', datetime.now())), errors='coerce')
        
        # Fallback to current date if parsing fails
        if pd.isna(period_start):
            period_start = datetime.now()
        if pd.isna(period_end):
            period_end = datetime.now()
        
        # ChatGPT messages - cost is enterprise license per user per month
        if row.get('messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': user_name,
                'email': user_email,
                'department': dept,
                'date': period_start,
                'feature_used': 'ChatGPT Messages',
                'usage_count': row.get('messages', 0),
                'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # GPT-specific messages - included in license, cost is 0
        if row.get('gpt_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': user_name,
                'email': user_email,
                'department': dept,
                'date': period_start,
                'feature_used': 'GPT Messages',
                'usage_count': row.get('gpt_messages', 0),
                'cost_usd': 0,  # Included in base license
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # Tool messages - included in license, cost is 0
        if row.get('tool_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': user_name,
                'email': user_email,
                'department': dept,
                'date': period_start,
                'feature_used': 'Tool Messages',
                'usage_count': row.get('tool_messages', 0),
                'cost_usd': 0,  # Included in base license
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
        
        # Project messages - included in license, cost is 0
        if row.get('project_messages', 0) > 0:
            normalized_records.append({
                'user_id': row.get('public_id', row.get('email', '')),
                'user_name': user_name,
                'email': user_email,
                'department': dept,
                'date': period_start,
                'feature_used': 'Project Messages',
                'usage_count': row.get('project_messages', 0),
                'cost_usd': 0,  # Included in base license
                'tool_source': 'ChatGPT',
                'file_source': filename
            })
    
    return pd.DataFrame(normalized_records)

def normalize_blueflame_data(df, filename):
    """Normalize BlueFlame AI data to standard schema with enterprise license costs."""
    normalized_records = []
    
    # Get enterprise pricing for BlueFlame AI
    cost_calc = EnterpriseCostCalculator()
    pricing_info = cost_calc.get_pricing_info('BlueFlame AI')
    monthly_license_cost = pricing_info['license_cost_per_user_monthly']
    
    # Check if this is the combined format with 'Table' column
    if 'Table' in df.columns:
        # Split the dataframe by table type
        monthly_trends = df[df['Table'] == 'Overall Monthly Trends']
        user_data = df[(df['Table'] == 'Top 20 Users Total') | 
                      (df['Table'] == 'Top 10 Increasing Users') | 
                      (df['Table'] == 'Top 10 Decreasing Users')]
        
        # Note: We skip processing monthly trends/aggregate metrics in favor of real user data
        # The user data from Top 20/Top 10 tables provides the actual usage information
        
        # Process user data (from Top 20 Users, Top 10 Increasing, etc.)
        if not user_data.empty:
            # Get month columns (excluding MoM variance columns and non-month columns)
            month_cols = [col for col in user_data.columns if col not in ['Table', 'Rank', 'Metric', 'User ID'] 
                         and not col.startswith('MoM Var')]
            
            # Deduplicate user data - same user may appear in multiple tables (e.g., Top 20 AND Top 10 Increasing)
            # Keep first occurrence for each user
            user_data_deduped = user_data.drop_duplicates(subset=['User ID'], keep='first')
            
            # Process each user
            for _, row in user_data_deduped.iterrows():
                user_email = row['User ID']
                if pd.isna(user_email) or not user_email:
                    continue
                
                # Look up employee by email to get authoritative department
                employee = None
                try:
                    employee = db.get_employee_by_email(user_email) if user_email else None
                    
                    # If no match by email, try to extract name from email and match
                    if not employee and user_email:
                        # Try to parse name from email (e.g., john.doe@company.com -> John Doe)
                        email_name = user_email.split('@')[0].replace('.', ' ').strip()
                        name_parts = email_name.split()
                        if len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = ' '.join(name_parts[1:])
                            employee = db.get_employee_by_name(first_name, last_name)
                except AttributeError:
                    # Handle cache error - database object missing methods
                    employee = None
                
                if employee:
                    # Use employee data as source of truth
                    dept = employee['department'] if employee['department'] else 'Unknown'
                    user_name = f"{employee['first_name']} {employee['last_name']}".strip()
                    if not user_name:
                        user_name = user_email.split('@')[0].replace('.', ' ').title()
                else:
                    # User not in employee roster - flag as unidentified
                    dept = 'Unknown'
                    user_name = user_email.split('@')[0].replace('.', ' ').title()
                
                # Process each month for this user
                for month_col in month_cols:
                    try:
                        # Parse month to a datetime (format like '25-Sep' or 'Sep-25')
                        month_date = None
                        for fmt in ['%y-%b', '%b-%y', '%Y-%b', '%b-%Y']:
                            try:
                                month_date = pd.to_datetime(month_col, format=fmt, errors='coerce')
                                if not pd.isna(month_date):
                                    break
                            except:
                                continue
                        
                        if pd.isna(month_date):
                            continue
                        
                        # Get message count for this month
                        message_count = row[month_col]
                        
                        # Handle dash placeholders and formatting
                        if isinstance(message_count, str):
                            if message_count in ['–', '-', '—', 'N/A', '']:
                                continue
                            message_count = int(message_count.replace(',', ''))
                        
                        # Skip months with no meaningful data
                        if pd.isna(message_count) or message_count == 0:
                            continue
                        
                        # Create user record for this month with enterprise license cost
                        normalized_records.append({
                            'user_id': user_email,
                            'user_name': user_name,
                            'email': user_email,
                            'department': dept,
                            'date': month_date,
                            'feature_used': 'BlueFlame Messages',
                            'usage_count': int(message_count),
                            'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                            'tool_source': 'BlueFlame AI',
                            'file_source': filename
                        })
                    except Exception as e:
                        print(f"Error processing month {month_col} for user {user_email}: {str(e)}")
    
    # Check if this is the summary report format with 'Metric' column (but no Table column)
    elif 'Metric' in df.columns and 'User ID' not in df.columns:
        # This format only has aggregate metrics, no individual user data
        # Skip processing as we prefer real user data from other formats
        print("Skipping aggregate-only format without user data")
    
    # If we have the top users file format with User ID column
    elif 'User ID' in df.columns:
        # Get month columns (excluding MoM variance columns)
        month_cols = [col for col in df.columns if col not in ['User ID'] and not col.startswith('MoM Var')]
        
        # Process each user record
        for _, row in df.iterrows():
            user_email = row['User ID']
            user_name = user_email.split('@')[0].replace('.', ' ').title()
            
            # Process each month for this user
            for month_col in month_cols:
                try:
                    # Parse month to a datetime
                    month_date = pd.to_datetime(month_col, format='%b-%y', errors='coerce')
                    if pd.isna(month_date):
                        continue
                    
                    # Get message count for this month
                    message_count = row[month_col]
                    
                    # Handle dash placeholders and formatting
                    if isinstance(message_count, str):
                        if message_count in ['–', '-', '—', 'N/A']:
                            continue
                        message_count = int(message_count.replace(',', ''))
                    
                    # Skip months with no meaningful data
                    if pd.isna(message_count) or message_count == 0:
                        continue
                    
                    # Create user record for this month with enterprise license cost
                    normalized_records.append({
                        'user_id': user_email,
                        'user_name': user_name,
                        'email': user_email,
                        'department': 'BlueFlame Users',  # Default department, can be updated later
                        'date': month_date,
                        'feature_used': 'BlueFlame Messages',
                        'usage_count': message_count,
                        'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                        'tool_source': 'BlueFlame AI',
                        'file_source': filename
                    })
                
                except Exception as e:
                    print(f"Error processing month {month_col} for user {user_email}: {str(e)}")
    
    # Other formats (possibly old BlueFlame format or future formats)
    else:
        # Process each user record using best effort detection
        for idx, row in df.iterrows():
            user = row.get('User', row.get('Email', f'blueflame-user-{idx}'))
            email = row.get('Email', f'{user.lower().replace(" ", ".")}@company.com')
            messages = row.get('Messages', row.get('Usage', 0))
            date_col = next((col for col in df.columns if 'Date' in col or 'Month' in col), None)
            
            if date_col:
                try:
                    date = pd.to_datetime(row[date_col], errors='coerce')
                    if pd.isna(date):
                        date = datetime.now()
                except:
                    date = datetime.now()
            else:
                date = datetime.now()
            
            if messages > 0:
                normalized_records.append({
                    'user_id': email,
                    'user_name': user,
                    'email': email,
                    'department': row.get('Department', 'BlueFlame Users'),
                    'date': date,
                    'feature_used': 'BlueFlame Messages',
                    'usage_count': messages,
                    'cost_usd': monthly_license_cost,  # Enterprise license cost per user per month
                    'tool_source': 'BlueFlame AI',
                    'file_source': filename
                })
    
    return pd.DataFrame(normalized_records)

def display_department_mapper():
    """Display department mapping interface with improved user deduplication and pagination."""
    st.subheader("🏢 Department Mapping Tool")
    
    st.markdown("""
    <div class="dept-mapper-container">
    <p><strong>Why use this?</strong> AI tool exports sometimes have incorrect or missing department data. 
    Use this tool to correct department assignments. Changes are saved and applied to all analytics.</p>
    <p><strong>Note:</strong> Employee departments are sourced from the master employee file and are read-only. 
    You can only map departments for unidentified users.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load existing mappings
    mappings = load_department_mappings()
    
    # Get all unique users from database
    all_data = db.get_all_data()
    if all_data.empty:
        st.info("No data available. Upload data first to use department mapping.")
        return
    
    # Get unidentified users
    unidentified_users_df = db.get_unidentified_users()
    
    # Show unidentified users section prominently
    if not unidentified_users_df.empty:
        st.markdown('<div class="section-header"><h3>⚠️ Unidentified Users</h3></div>', unsafe_allow_html=True)
        st.warning(f"Found {len(unidentified_users_df)} users not in the employee master file")
        
        with st.expander(f"👥 View {len(unidentified_users_df)} Unidentified Users", expanded=True):
            # Display unidentified users
            for idx, row in unidentified_users_df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    # Handle NULL/empty user_name
                    display_name = row['user_name'] if pd.notna(row['user_name']) and row['user_name'] else 'Unknown User'
                    st.write(f"**{display_name}**")
                    # Handle NULL/empty email
                    display_email = row['email'] if pd.notna(row['email']) and row['email'] else 'No email'
                    st.caption(display_email)
                
                with col2:
                    # Handle NULL tools_used
                    display_tools = row['tools_used'] if pd.notna(row['tools_used']) and row['tools_used'] else 'Unknown'
                    st.write(f"🔧 {display_tools}")
                
                with col3:
                    # Handle NaN/NULL total_usage
                    if pd.notna(row['total_usage']):
                        st.write(f"📊 {int(row['total_usage']):,} messages")
                    else:
                        st.write("📊 0 messages")
                    
                    # Handle NaN/NULL total_cost
                    if pd.notna(row['total_cost']):
                        st.caption(f"${row['total_cost']:.2f}")
                    else:
                        st.caption("$0.00")
                
                with col4:
                    # Handle NaN/NULL days_active
                    if pd.notna(row['days_active']):
                        st.caption(f"{int(row['days_active'])} days")
                    else:
                        st.caption("0 days")
                
                st.divider()
        
        st.divider()
    
    # Department options - hardcoded list of 59 departments
    dept_options = [
        'Administrative - Capital Formation',
        'Administrative - Communications',
        'Administrative - Corporate Credit',
        'Administrative - Events & Premises',
        'Administrative - Finance',
        'Administrative - GPS',
        'Administrative - Investments',
        'Administrative - Legal',
        'Administrative - President',
        'Administrative - TBO',
        'Administrative - TMO',
        'Adminstrative - Investments',
        'CEO Office',
        'Capital Formation',
        'Communications',
        'Compliance',
        'Corporate Credit - Asset Based',
        'Corporate Credit - Asset Management',
        'Corporate Credit - Capital Markets',
        'Corporate Credit - Consumer',
        'Corporate Credit - Credit',
        'Corporate Credit - Diversified Credit',
        'Corporate Credit - Healthcare',
        'Corporate Credit - Industrials',
        'Corporate Credit - Manufacturing',
        'Corporate Credit - Media',
        'Corporate Credit - Middle Market',
        'Corporate Credit - Origination',
        'Corporate Credit - Risk & Restructuring',
        'Corporate Credit - Technology',
        'Corporate Credit - Trading',
        'Corporate Credit -Industrials',
        'Cross Asset Specialists',
        'Cross Platform Solutions',
        'Events',
        'Executive',
        'Finance',
        'Finance - Capital Markets',
        'Finance - Controllership',
        'Finance - Diversified Credit',
        'Finance - FP&A',
        'Finance - Tax',
        'GP Solutions',
        'Human Capital ',
        'Investments',
        'Legal',
        'Operations',
        'Operations - Project Management',
        'Ops - Client Service & Invest. Ops ',
        'Ops - Portfolio & Fund Ops',
        'Premises',
        'Private Wealth',
        'Product Development',
        'Real Estate Credit',
        'Real Estate Credit - Portfolio Management',
        'SME',
        'Structured Credit',
        'Technology',
        'Unknown'
    ]
    
    # Deduplicate users by email only, using smart department selection
    # This prevents users who appear in both OpenAI and BlueFlame from showing as duplicates
    users_df = all_data.groupby('email').agg({
        'user_name': 'first',
        'department': lambda x: _select_primary_department(x),
        'tool_source': lambda x: ', '.join(sorted(x.unique()))
    }).reset_index()
    users_df = users_df.sort_values('user_name')
    
    # Check which users are employees (by email or name)
    users_df['is_employee'] = users_df.apply(lambda row: is_employee_user(row['email'], row['user_name']), axis=1)
    
    st.markdown('<div class="section-header"><h3>📋 All Users</h3></div>', unsafe_allow_html=True)
    st.write(f"**Total Users:** {len(users_df)} ({users_df['is_employee'].sum()} employees, {(~users_df['is_employee']).sum()} unidentified)")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.radio("Filter by:", ["All Users", "Employees Only", "Unidentified Only"], horizontal=True)
    
    # Apply filter
    if filter_type == "Employees Only":
        users_df = users_df[users_df['is_employee']]
    elif filter_type == "Unidentified Only":
        users_df = users_df[~users_df['is_employee']]
    
    # Search filter
    with col2:
        search = st.text_input("🔍 Search by name or email", "")
    
    # Initialize pagination state if not exists
    if 'dept_mapper_page' not in st.session_state:
        st.session_state.dept_mapper_page = 0
    
    # Users per page
    users_per_page = 20
    
    # Apply search filter if provided
    if search:
        users_df = users_df[
            users_df['user_name'].str.contains(search, case=False, na=False) | 
            users_df['email'].str.contains(search, case=False, na=False)
        ]
        # Reset pagination when searching
        st.session_state.dept_mapper_page = 0
    
    # Calculate total pages
    total_pages = max(1, (len(users_df) + users_per_page - 1) // users_per_page)
    
    # Ensure current page is valid
    st.session_state.dept_mapper_page = min(st.session_state.dept_mapper_page, total_pages - 1)
    st.session_state.dept_mapper_page = max(0, st.session_state.dept_mapper_page)
    
    # Pagination controls - place them at top and bottom
    def pagination_controls(position="top"):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 3, 1, 2])
        
        with col1:
            if st.button("◀️ Previous", key=f"prev_{position}", 
                         disabled=(st.session_state.dept_mapper_page <= 0)):
                st.session_state.dept_mapper_page -= 1
        
        with col3:
            # Show page selector with page numbers
            page_options = [f"Page {i+1} of {total_pages}" for i in range(total_pages)]
            selected_page = st.selectbox(
                "Page",
                options=page_options,
                index=st.session_state.dept_mapper_page,
                key=f"page_select_{position}",
                label_visibility="collapsed"
            )
            if page_options.index(selected_page) != st.session_state.dept_mapper_page:
                st.session_state.dept_mapper_page = page_options.index(selected_page)
        
        with col5:
            if st.button("Next ▶️", key=f"next_{position}", 
                         disabled=(st.session_state.dept_mapper_page >= total_pages - 1)):
                st.session_state.dept_mapper_page += 1
    
    # Display pagination at top
    pagination_controls("top")
    
    # Get current page of users
    start_idx = st.session_state.dept_mapper_page * users_per_page
    end_idx = start_idx + users_per_page
    current_page_users = users_df.iloc[start_idx:end_idx]
    
    # Display in a clean table format with editable departments
    st.write("**Update Department Assignments:**")
    
    changes_made = False
    
    # Create columns for the table
    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
    with col1:
        st.write("**Name**")
    with col2:
        st.write("**Email**")
    with col3:
        st.write("**Type**")
    with col4:
        st.write("**Department**")
    with col5:
        st.write("**Action**")
    
    st.divider()
    
    # Show current page of users
    for position, (idx, row) in enumerate(current_page_users.iterrows()):
        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
        
        with col1:
            # Show user name with multi-tool indicator
            # Handle NULL/empty user_name
            user_display = row['user_name'] if pd.notna(row['user_name']) and row['user_name'] else 'Unknown User'
            # Handle NULL/empty tool_source
            tool_source = row['tool_source'] if pd.notna(row['tool_source']) and row['tool_source'] else ''
            if ', ' in tool_source:  # User has multiple AI tools
                user_display = f"🔗 {user_display}"
            st.write(user_display)
        
        with col2:
            # Show email with tool sources on hover
            # Handle NULL/empty email and tool_source
            display_email = row['email'] if pd.notna(row['email']) and row['email'] else 'No email'
            display_tool_help = tool_source if tool_source else 'Unknown'
            st.text(display_email, help=f"Tools: {display_tool_help}")
        
        with col3:
            # Show if employee or unidentified
            if row['is_employee']:
                st.write("✅ Employee")
            else:
                st.write("⚠️ Unidentified")
        
        with col4:
            current_dept = mappings.get(row['email'], row['department'])
            
            # If employee, show department as read-only
            if row['is_employee']:
                employee = get_employee_for_user(row['email'], row['user_name'])
                if employee and employee.get('department'):
                    st.write(f"🔒 {employee['department']}")
                else:
                    # Handle NULL/empty department
                    display_dept = current_dept if pd.notna(current_dept) and current_dept else 'Unknown'
                    st.write(display_dept)
            else:
                # For unidentified users, allow editing
                new_dept = st.selectbox(
                    "Dept",
                    options=dept_options,
                    index=dept_options.index(current_dept) if current_dept in dept_options else dept_options.index('Unknown'),
                    key=f"dept_{start_idx + position}_{row['email']}",
                    label_visibility="collapsed"
                )
                
                if new_dept != mappings.get(row['email'], row['department']):
                    mappings[row['email']] = new_dept
                    changes_made = True
        
        with col5:
            if not row['is_employee']:
                if st.button("✓", key=f"save_{start_idx + position}_{row['email']}", help="Save changes"):
                    changes_made = True
        
        st.divider()
    
    # Display pagination at bottom too
    pagination_controls("bottom")
    
    # User info message
    showing_text = f"Showing users {start_idx + 1}-{min(end_idx, len(users_df))} of {len(users_df)}"
    if search:
        showing_text += f" (filtered by '{search}')"
    st.info(showing_text)
    
    # Save button
    if changes_made or st.button("💾 Save All Department Mappings", type="primary"):
        save_department_mappings(mappings)
        st.success(f"✅ Saved department mappings for {len(mappings)} users")
    
    # Show current mappings count
    if mappings:
        st.info(f"📊 {len(mappings)} custom department mappings active")

def process_auto_file(file_info, tool_type='Auto-Detect'):
    """
    Process a file from auto-scan folders.
    
    Args:
        file_info: Dictionary with file information from FileScanner
        tool_type: Type of AI tool (Auto-Detect, OpenAI ChatGPT, etc.)
        
    Returns:
        tuple: (success: bool, message: str, records_count: int)
    """
    try:
        file_path = file_info['path']
        
        # Read file from filesystem
        df, read_error = read_file_from_path(file_path)
        
        if read_error:
            return False, f"Error reading file: {read_error}", 0
        
        if df is None or df.empty:
            return False, "File contains no data", 0
        
        # Detect data source
        if tool_type == 'Auto-Detect':
            detected_tool = detect_data_source(df)
        else:
            detected_tool = tool_type.replace('OpenAI ', '')
        
        # Normalize data based on detected tool
        if 'ChatGPT' in detected_tool:
            normalized_df = normalize_openai_data(df, file_info['filename'])
        elif 'BlueFlame' in detected_tool:
            normalized_df = normalize_blueflame_data(df, file_info['filename'])
        else:
            return False, f"Unknown data format: {detected_tool}", 0
        
        # Process the normalized data
        if not normalized_df.empty:
            success, message = processor.process_monthly_data(normalized_df, file_info['filename'])
            
            if success:
                # Mark file as processed
                scanner.mark_processed(
                    file_path, 
                    success=True, 
                    records_count=len(normalized_df)
                )
                return True, f"Successfully processed {len(normalized_df)} records", len(normalized_df)
            else:
                scanner.mark_processed(
                    file_path, 
                    success=False, 
                    error=message
                )
                return False, message, 0
        else:
            return False, "No valid data found after normalization", 0
    
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        scanner.mark_processed(
            file_info['path'], 
            success=False, 
            error=error_msg
        )
        return False, error_msg, 0

def calculate_power_users(data, threshold_percentile=95):
    """Identify power users based on usage patterns."""
    if data.empty:
        return pd.DataFrame()
    
    # Group by email only to avoid duplicates across different departments/tools
    user_usage = data.groupby('email').agg({
        'user_name': 'first',  # Take first user_name (should be same for same email)
        'usage_count': 'sum',
        'cost_usd': 'sum',
        'tool_source': lambda x: ', '.join(sorted(x.unique())),
        'department': lambda x: _select_primary_department(x)
    }).reset_index()
    
    # Update departments from employee database as authoritative source
    # This ensures verified employees show their correct locked departments
    for idx, row in user_usage.iterrows():
        employee = get_employee_for_user(row['email'], row['user_name'])
        if employee and employee.get('department'):
            user_usage.at[idx, 'department'] = employee['department']
    
    # Calculate threshold (top 5% by default)
    threshold = user_usage['usage_count'].quantile(threshold_percentile / 100)
    
    # Identify power users (top 5% by usage)
    power_users = user_usage[
        user_usage['usage_count'] >= threshold
    ].sort_values('usage_count', ascending=False)
    
    return power_users

def _select_primary_department(departments):
    """Select the most appropriate department from a list.
    
    Prefers valid department names over placeholder values like 'BlueFlame Users' 
    or 'Unknown'. If multiple valid departments exist, returns the first one.
    Returns placeholder values only if that's all that's available.
    """
    unique_depts = list(departments.unique())
    
    # Filter out placeholder departments if real departments exist
    real_depts = [d for d in unique_depts if d not in ('BlueFlame Users', 'Unknown')]
    
    if real_depts:
        return real_depts[0]  # Return first real department
    
    # If only placeholders available, prefer 'BlueFlame Users' over 'Unknown'
    if 'BlueFlame Users' in unique_depts:
        return 'BlueFlame Users'
    
    return unique_depts[0] if unique_depts else 'Unknown'

def get_user_message_breakdown(data, email):
    """Get message type breakdown for a specific user, organized by tool source."""
    user_data = data[data['email'] == email]
    
    breakdown = {
        'openai': {
            'ChatGPT Messages': 0,
            'GPT Messages': 0,
            'Tool Messages': 0,
            'Project Messages': 0
        },
        'blueflame': {
            'BlueFlame Messages': 0
        }
    }
    
    if not user_data.empty:
        # Get counts grouped by feature type
        message_counts = user_data.groupby('feature_used')['usage_count'].sum().to_dict()
        
        # Map to breakdown structure
        for msg_type, count in message_counts.items():
            if msg_type in breakdown['openai']:
                breakdown['openai'][msg_type] = count
            elif msg_type == 'BlueFlame Messages':
                breakdown['blueflame']['BlueFlame Messages'] = count
    
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
    # Main header - professional title without emoji
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="main-header">AI Usage Analytics Dashboard</h1>', unsafe_allow_html=True)
        st.caption("Multi-Platform Analytics for Enterprise AI Tools")
    with col2:
        # Compact actions menu in top-right
        st.markdown('<div style="text-align: right; padding-top: 0.5rem;"></div>', unsafe_allow_html=True)
    
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
        
        # Auto-scan section for files in folders
        st.subheader("📂 Auto-Detect Files")
        
        # Scan for files
        detected_files = scanner.scan_folders(AUTO_SCAN_FOLDERS)
        
        if detected_files:
            # Show summary stats
            new_files = [f for f in detected_files if f['status'] in ['new', 'modified']]
            processed_files = [f for f in detected_files if f['status'] == 'processed']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📁 Total Files", len(detected_files))
            with col2:
                st.metric("🆕 New Files", len(new_files))
            
            # Refresh button
            if st.button("🔄 Refresh Files", use_container_width=True):
                st.rerun()
            
            # Show new/unprocessed files
            if new_files:
                with st.expander(f"🆕 New Files ({len(new_files)})", expanded=True):
                    for file_info in new_files:
                        st.markdown(f"""
                        **{file_info['filename']}**  
                        📁 Folder: {file_info['folder']} | 📊 {file_info['size_mb']} MB
                        """)
                        
                        # Process button for individual file
                        if st.button(f"▶️ Process", key=f"process_{file_info['path']}", use_container_width=True):
                            with st.spinner(f"Processing {file_info['filename']}..."):
                                success, message, records = process_auto_file(file_info, tool_type)
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        
                        st.divider()
                
                # Batch process button for all new files
                if len(new_files) > 1:
                    if st.button(f"⚡ Process All {len(new_files)} New Files", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        processed_count = 0
                        total_records = 0
                        errors = []
                        
                        for i, file_info in enumerate(new_files):
                            status_text.text(f"Processing {file_info['filename']}...")
                            progress_bar.progress((i + 1) / len(new_files))
                            
                            success, message, records = process_auto_file(file_info, tool_type)
                            
                            if success:
                                processed_count += 1
                                total_records += records
                            else:
                                errors.append(f"{file_info['filename']}: {message}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        if processed_count > 0:
                            st.success(f"""
                            ✅ **Batch Processing Complete!**
                            - Processed: {processed_count}/{len(new_files)} files
                            - Total Records: {total_records:,}
                            """)
                            
                            if errors:
                                with st.expander(f"⚠️ {len(errors)} Errors"):
                                    for error in errors:
                                        st.error(error)
                            
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Failed to process any files")
                            for error in errors:
                                st.error(error)
            
            # Show processed files
            if processed_files:
                with st.expander(f"✅ Processed Files ({len(processed_files)})"):
                    for file_info in processed_files:
                        st.markdown(f"""
                        **{file_info['filename']}**  
                        📁 {file_info['folder']} | 📊 {file_info['size_mb']} MB | ✅ {file_info.get('last_processed', 'Unknown')}
                        """)
        else:
            st.info("""
            📂 **No files detected in scan folders**
            
            Place your CSV files in these folders:
            - `OpenAI User Data/`
            - `BlueFlame User Data/`
            - `data/uploads/`
            
            Then click Refresh to detect them.
            """)
        
        # Help Section
        with st.expander("❓ Metrics Guide", expanded=False):
            st.markdown("""
            ### 📊 Understanding Key Metrics
            
            **YTD Spending**
            - Total cost spent on AI tools this year
            - Based on usage counts and estimated per-message rates
            
            **Projected Annual Cost**
            - Estimated full-year spending based on current trends
            - Calculated from months of available data
            
            **Cost per User**
            - Average spending per active user
            - Helps identify cost efficiency
            
            **Cost Efficiency**
            - Average cost per message/interaction
            - Lower values indicate better efficiency
            
            **Power Users**
            - Top 5% of users by total usage
            - Key candidates for feedback and beta testing
            
            **Month-over-Month Growth**
            - % change in users, usage, or cost vs previous month
            - Positive values show adoption growth
            
            ### 📁 Data Sources
            
            **OpenAI ChatGPT**
            - Enterprise usage exports
            - Includes: ChatGPT Messages, Tool Messages, Project Messages, GPT Messages
            
            **BlueFlame AI**
            - Custom AI platform usage
            - Monthly message counts per user
            
            ### 🔄 Export Options
            
            **PDF Report (HTML)**
            - Executive summary with key metrics
            - Download and print to PDF from browser
            
            **Excel with Pivots**
            - Multiple sheets with analysis
            - User, Department, Monthly, and Feature summaries
            """)
        
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
            
            # Enhanced data provider selector
            st.markdown("""
            <div class="help-tooltip">
                🔧 <strong>Data Provider Filter:</strong> Toggle between AI platforms to analyze specific tool usage
            </div>
            """, unsafe_allow_html=True)
            
            all_data = db.get_all_data()
            if not all_data.empty and 'tool_source' in all_data.columns:
                available_tools = list(all_data['tool_source'].unique())
                
                # Create toggle buttons for providers
                st.write("**Select Data Provider:**")
                
                # Use radio buttons for clear selection
                selected_tool = st.radio(
                    "Provider",
                    options=['All Tools'] + available_tools,
                    index=0,
                    help="📊 Filter dashboard to show data from specific AI platform",
                    label_visibility="collapsed"
                )
                
                # Show provider-specific stats
                if selected_tool != 'All Tools':
                    tool_data = all_data[all_data['tool_source'] == selected_tool]
                    st.info(f"📈 {selected_tool}: {tool_data['user_id'].nunique()} users, {len(tool_data):,} records")
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
    
    # Get filtered data with loading indicator
    with st.spinner("📊 Loading data..."):
        if len(date_range) == 2:
            start_date, end_date = date_range
            data = db.get_filtered_data(
                start_date=start_date,
                end_date=end_date,
                departments=selected_depts if selected_depts else None
            )
        else:
            data = db.get_all_data()
    
    # Apply employee departments FIRST (authoritative source for employees)
    # This ensures the employee master file drives all employee department tagging
    data = apply_employee_departments(data)
    
    # Apply manual department mappings for non-employees (secondary/override)
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
        # Clean header without emoji, with compact export menu
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown('<h2 style="color: var(--text-primary); margin-bottom: 0;">Executive Summary</h2>', unsafe_allow_html=True)
            st.caption("Key performance metrics and trends")
        with col2:
            # Compact export menu in dropdown
            with st.expander("📥 Export", expanded=False):
                # PDF Export (HTML version)
                try:
                    html_content = generate_pdf_report_html(data, "AI Usage Executive Report")
                    st.download_button(
                        label="PDF Report",
                        data=html_content,
                        file_name=f"ai_usage_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                        mime="text/html",
                        use_container_width=True,
                        help="Download as HTML (print to PDF from browser)"
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
                
                # Excel Export with pivot tables
                try:
                    excel_file = generate_excel_export(data, include_pivots=True)
                    st.download_button(
                        label="Excel Report",
                        data=excel_file,
                        file_name=f"ai_usage_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        help="Excel with pivot tables and summaries"
                    )
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        st.divider()
        
        # Calculate key financial metrics
        total_cost = data['cost_usd'].sum()
        total_users = data['user_id'].nunique()
        total_usage = data['usage_count'].sum()
        
        # Calculate YTD and projections
        try:
            data_with_dates = data.copy()
            data_with_dates['date'] = pd.to_datetime(data_with_dates['date'], errors='coerce')
            data_with_dates = data_with_dates.dropna(subset=['date'])
            
            # Get current year data
            current_year = datetime.now().year
            ytd_data = data_with_dates[data_with_dates['date'].dt.year == current_year]
            ytd_cost = ytd_data['cost_usd'].sum()
            
            # Calculate months of data for projection
            if not ytd_data.empty:
                min_month = ytd_data['date'].min().month
                max_month = ytd_data['date'].max().month
                months_of_data = max_month - min_month + 1
                projected_annual_cost = (ytd_cost / months_of_data) * 12 if months_of_data > 0 else ytd_cost * 12
            else:
                ytd_cost = total_cost
                projected_annual_cost = total_cost * 12
        except:
            ytd_cost = total_cost
            projected_annual_cost = total_cost * 12
        
        # Enterprise Pricing Model Information
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">Enterprise Pricing Model</h3>', unsafe_allow_html=True)
        
        with st.expander("ℹ️ About Cost Calculations - Based on Enterprise SaaS Licenses", expanded=False):
            st.markdown("""
            **Cost Model:** Enterprise license-based pricing (per user per month)
            
            This dashboard calculates costs based on **actual enterprise SaaS license fees**, not per-message usage.
            Each active user in a month incurs the full monthly license cost, regardless of message volume.
            
            ### Current Enterprise Pricing:
            """)
            
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown("""
                **🤖 ChatGPT Enterprise**
                - **License Cost:** $60 per user per month
                - **Annual Cost:** $720 per user per year
                - **Minimum Seats:** 150 users
                - **Included Features:**
                  - Standard messages (unlimited)
                  - Custom GPTs
                  - Tool usage (code interpreter, browsing)
                  - Project messages
                
                *Source: Reported enterprise pricing (~$60/user/month)*
                """)
            
            with col_info2:
                st.markdown("""
                **🔥 BlueFlame AI**
                - **License Cost:** $125 per user per month
                - **Annual Cost:** $1,500 per user per year
                - **Minimum Seats:** 1 user
                - **Included Features:**
                  - AI-powered insights
                  - Document analysis
                  - Investment workflow automation
                  - Data integration
                
                *Source: Estimated based on typical enterprise AI software ($100-150/user/month)*
                """)
            
            st.markdown("""
            ---
            ### Key Metrics to Monitor:
            
            1. **Cost per User** - Primary metric for license efficiency
            2. **Messages per User** - Indicates engagement and value delivered
            3. **Annual Cost Projection** - Budget planning and ROI analysis
            4. **License Utilization** - Which users are actively using their licenses
            
            ### Why This Matters:
            
            - **Budget Accuracy:** True costs are based on seat licenses, not message volume
            - **ROI Analysis:** Cost per user helps justify software investments
            - **Utilization Insights:** Identify underutilized licenses to optimize spending
            - **Future Planning:** Better annual cost projections for budgeting
            """)
        
        # Executive Summary Cards with detailed breakdowns
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">Financial Overview</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "YTD Spending", 
                f"${ytd_cost:,.2f}",
                help="Year-to-date total spending on AI tools"
            )
            with st.expander("📊 Details"):
                st.write("**Calculation:**")
                st.code(f"Total cost for {datetime.now().year}")
                if not data.empty and 'tool_source' in data.columns:
                    st.write("**By Provider:**")
                    provider_costs = data.groupby('tool_source')['cost_usd'].sum().sort_values(ascending=False)
                    for provider, cost in provider_costs.items():
                        pct = (cost / ytd_cost * 100) if ytd_cost > 0 else 0
                        st.write(f"• {provider}: ${cost:,.2f} ({pct:.1f}%)")
        
        with col2:
            st.metric(
                "Projected Annual Cost", 
                f"${projected_annual_cost:,.2f}", 
                delta=f"{((projected_annual_cost - ytd_cost) / max(ytd_cost, 1) * 100):.0f}% vs YTD",
                help="Projected full-year cost based on current usage trends"
            )
            with st.expander("📊 Details"):
                st.write("**Calculation:**")
                try:
                    data_with_dates = data.copy()
                    data_with_dates['date'] = pd.to_datetime(data_with_dates['date'], errors='coerce')
                    ytd_data = data_with_dates[data_with_dates['date'].dt.year == datetime.now().year]
                    if not ytd_data.empty:
                        min_month = ytd_data['date'].min().month
                        max_month = ytd_data['date'].max().month
                        months_of_data = max_month - min_month + 1
                        st.code(f"({ytd_cost:,.2f} / {months_of_data} months) × 12 = ${projected_annual_cost:,.2f}")
                        st.write(f"**Data Coverage:** {months_of_data} months")
                    else:
                        st.code(f"${ytd_cost:,.2f} × 12 = ${projected_annual_cost:,.2f}")
                except:
                    st.code(f"${ytd_cost:,.2f} × 12 = ${projected_annual_cost:,.2f}")
        
        with col3:
            avg_cost_per_user = total_cost / max(total_users, 1)
            st.metric(
                "Avg Monthly Cost per User", 
                f"${avg_cost_per_user:.2f}", 
                help="Average monthly license cost per active user - key metric for enterprise SaaS ROI"
            )
            with st.expander("📊 Details"):
                st.write("**Enterprise License Pricing:**")
                st.code(f"${total_cost:,.2f} ÷ {total_users} users = ${avg_cost_per_user:.2f}/user/month")
                st.write("**Context:**")
                st.write(f"• Total active users: {total_users:,}")
                st.write(f"• Total monthly cost: ${total_cost:,.2f}")
                
                # Show pricing by provider
                if not data.empty and 'tool_source' in data.columns:
                    st.write("**Cost per User by Provider:**")
                    provider_user_cost = data.groupby('tool_source').agg({
                        'user_id': 'nunique',
                        'cost_usd': 'sum'
                    })
                    provider_user_cost['cost_per_user'] = provider_user_cost['cost_usd'] / provider_user_cost['user_id']
                    for provider, row in provider_user_cost.iterrows():
                        st.write(f"• {provider}: ${row['cost_per_user']:.2f}/user ({row['user_id']} users)")
                
                # Annual cost per user
                annual_cost_per_user = avg_cost_per_user * 12
                st.write("**Annual Projection:**")
                st.write(f"• ${annual_cost_per_user:,.2f} per user per year")
        
        with col4:
            cost_per_interaction = total_cost / max(total_usage, 1)
            st.metric(
                "Messages per User", 
                f"{total_usage / max(total_users, 1):,.0f}", 
                help="Average messages per user - indicates engagement and license utilization"
            )
            with st.expander("📊 Details"):
                st.write("**Engagement Metrics:**")
                st.code(f"{total_usage:,} messages ÷ {total_users} users = {total_usage / max(total_users, 1):,.0f} msgs/user")
                st.write("**License Value:**")
                st.write(f"• Cost per message: ${cost_per_interaction:.3f}")
                st.write(f"• Total messages: {total_usage:,}")
                
                # Show message volume by provider
                if not data.empty and 'tool_source' in data.columns:
                    st.write("**Messages per User by Provider:**")
                    provider_engagement = data.groupby('tool_source').agg({
                        'user_id': 'nunique',
                        'usage_count': 'sum'
                    })
                    provider_engagement['msgs_per_user'] = provider_engagement['usage_count'] / provider_engagement['user_id']
                    for provider, row in provider_engagement.iterrows():
                        st.write(f"• {provider}: {row['msgs_per_user']:,.0f} msgs/user")
        
        st.divider()
        
        # License Utilization Analysis
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">License Utilization & ROI Analysis</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div style="background: var(--card-bg); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid var(--primary-color);">', unsafe_allow_html=True)
            st.markdown("**🎯 Cost Justification Analysis**")
            
            if not data.empty and 'tool_source' in data.columns:
                for provider in data['tool_source'].unique():
                    provider_data = data[data['tool_source'] == provider]
                    provider_users = provider_data['user_id'].nunique()
                    provider_cost = provider_data['cost_usd'].sum()
                    provider_messages = provider_data['usage_count'].sum()
                    
                    # Get pricing info
                    cost_calc = EnterpriseCostCalculator()
                    pricing_info = cost_calc.get_pricing_info(provider)
                    monthly_cost_per_user = pricing_info['license_cost_per_user_monthly']
                    annual_cost_per_user = pricing_info['annual_cost_per_user']
                    
                    st.write(f"**{provider}:**")
                    st.write(f"• Active users: {provider_users}")
                    st.write(f"• Total messages: {provider_messages:,}")
                    st.write(f"• Monthly cost: ${provider_cost:,.2f}")
                    st.write(f"• Annual projection: ${provider_cost * 12:,.2f}")
                    st.write(f"• Cost per user: ${monthly_cost_per_user}/month (${annual_cost_per_user}/year)")
                    
                    # Calculate engagement
                    msgs_per_user = provider_messages / max(provider_users, 1)
                    st.write(f"• Engagement: {msgs_per_user:.0f} messages/user/month")
                    
                    # License efficiency
                    if msgs_per_user > 50:
                        st.success(f"✅ High utilization - strong license value")
                    elif msgs_per_user > 20:
                        st.info(f"ℹ️ Moderate utilization - good license value")
                    else:
                        st.warning(f"⚠️ Low utilization - review license needs")
                    
                    st.write("")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div style="background: var(--card-bg); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid var(--success-border);">', unsafe_allow_html=True)
            st.markdown("**💡 Key Insights**")
            
            # Calculate overall metrics
            msgs_per_user_overall = total_usage / max(total_users, 1)
            cost_per_msg_overall = total_cost / max(total_usage, 1)
            
            st.write("**License Value Metrics:**")
            st.write(f"• Average messages per user: {msgs_per_user_overall:.0f}/month")
            st.write(f"• Effective cost per message: ${cost_per_msg_overall:.3f}")
            st.write(f"• Total active user licenses: {total_users}")
            
            st.write("")
            st.write("**Budget Planning:**")
            st.write(f"• Current monthly spend: ${total_cost:,.2f}")
            st.write(f"• Projected annual spend: ${projected_annual_cost:,.2f}")
            
            # Calculate savings opportunities
            if not data.empty:
                # Find low-usage users (less than 10 messages per month)
                user_usage = data.groupby('user_id')['usage_count'].sum()
                low_usage_users = (user_usage < 10).sum()
                
                if low_usage_users > 0:
                    st.write("")
                    st.write("**Optimization Opportunities:**")
                    st.write(f"• {low_usage_users} users with <10 messages/month")
                    
                    # Calculate potential savings
                    if 'tool_source' in data.columns:
                        # Estimate potential savings (assuming ChatGPT $60/user/month)
                        potential_monthly_savings = low_usage_users * 60
                        potential_annual_savings = potential_monthly_savings * 12
                        st.write(f"• Potential monthly savings: ~${potential_monthly_savings:,.2f}")
                        st.write(f"• Potential annual savings: ~${potential_annual_savings:,.2f}")
                        st.info(f"💡 Consider reviewing license needs for low-usage users")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Data Quality & Validation Panel
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">Data Quality & Validation</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate completeness
        completeness = 100.0
        if not data.empty:
            required_cols = ['user_id', 'date', 'usage_count', 'cost_usd']
            for col in required_cols:
                if col in data.columns:
                    col_completeness = (data[col].notna().sum() / len(data)) * 100
                    completeness = min(completeness, col_completeness)
        
        # Get unique users count
        unique_users = data['user_id'].nunique() if not data.empty else 0
        
        # Calculate date coverage
        try:
            if not data.empty and 'date' in data.columns:
                valid_dates = pd.to_datetime(data['date'], errors='coerce').dropna()
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
        
        # Data source breakdown
        if not data.empty and 'tool_source' in data.columns:
            st.markdown('<div style="margin-top: 1rem; padding: 1rem; background: #f8fafc; border-radius: 0.5rem; border: 1px solid #e2e8f0;">', unsafe_allow_html=True)
            st.write("**Data Sources:**")
            source_summary = data.groupby('tool_source').agg({
                'user_id': 'nunique',
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            source_summary.columns = ['Provider', 'Users', 'Messages', 'Cost']
            
            for _, row in source_summary.iterrows():
                cost_pct = (row['Cost'] / total_cost * 100) if total_cost > 0 else 0
                st.write(f"**{row['Provider']}**: {row['Users']} users, {row['Messages']:,} messages, ${row['Cost']:,.2f} ({cost_pct:.1f}% of total)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Month-over-Month Trends
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">Month-over-Month Trends</h3>', unsafe_allow_html=True)
        
        try:
            # Prepare monthly data
            monthly_data = data.copy()
            monthly_data['date'] = pd.to_datetime(monthly_data['date'], errors='coerce')
            monthly_data = monthly_data.dropna(subset=['date'])
            monthly_data['month'] = monthly_data['date'].dt.to_period('M').astype(str)
            
            # Calculate monthly metrics
            monthly_metrics = monthly_data.groupby('month').agg({
                'user_id': 'nunique',
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            monthly_metrics.columns = ['Month', 'Active Users', 'Total Usage', 'Total Cost']
            
            # Calculate MoM changes
            if len(monthly_metrics) > 1:
                monthly_metrics['User Growth %'] = monthly_metrics['Active Users'].pct_change() * 100
                monthly_metrics['Usage Growth %'] = monthly_metrics['Total Usage'].pct_change() * 100
                monthly_metrics['Cost Growth %'] = monthly_metrics['Total Cost'].pct_change() * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                # User adoption trend
                fig = px.line(
                    monthly_metrics, 
                    x='Month', 
                    y='Active Users',
                    title='Monthly Active Users Trend',
                    markers=True
                )
                fig.update_traces(line_color='#667eea', line_width=3, marker=dict(size=10))
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Cost trend
                fig = px.bar(
                    monthly_metrics, 
                    x='Month', 
                    y='Total Cost',
                    title='Monthly Cost Trend',
                    color='Total Cost',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # MoM Summary Table
            if len(monthly_metrics) > 1:
                st.markdown("**Month-over-Month Growth Summary:**")
                display_cols = ['Month', 'Active Users', 'User Growth %', 'Total Usage', 'Usage Growth %', 'Total Cost', 'Cost Growth %']
                st.dataframe(
                    monthly_metrics[display_cols].tail(6).style.format({
                        'Active Users': '{:,.0f}',
                        'User Growth %': '{:+.1f}%',
                        'Total Usage': '{:,.0f}',
                        'Usage Growth %': '{:+.1f}%',
                        'Total Cost': '${:,.2f}',
                        'Cost Growth %': '{:+.1f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
        except Exception as e:
            st.warning(f"Unable to calculate monthly trends: {str(e)}")
        
        st.divider()
        
        # Department Performance Analytics
        st.markdown('<h3 style="color: var(--text-primary); margin-top: 1.5rem; margin-bottom: 1rem;">Department Performance</h3>', unsafe_allow_html=True)
        
        # Calculate comprehensive department statistics
        dept_stats = data.groupby('department').agg({
            'user_id': 'nunique',
            'usage_count': 'sum',
            'cost_usd': 'sum'
        }).reset_index()
        dept_stats.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
        
        # Calculate derived metrics
        total_usage_all = dept_stats['Total Usage'].sum()
        dept_stats['Usage Share %'] = (dept_stats['Total Usage'] / total_usage_all * 100).round(1)
        dept_stats['Avg Messages/User'] = (dept_stats['Total Usage'] / dept_stats['Active Users']).round(0)
        dept_stats['Cost per Message'] = (dept_stats['Total Cost'] / dept_stats['Total Usage']).round(3)
        dept_stats = dept_stats.sort_values('Total Usage', ascending=False)
        
        # Add interactive filtering for departments
        st.markdown("**🎯 Filter Chart Data**")
        filter_col1, filter_col2 = st.columns([2, 1])
        
        with filter_col1:
            # Department filter - allow excluding specific departments
            all_departments = dept_stats['Department'].tolist()
            excluded_depts = st.multiselect(
                "Exclude departments from chart (e.g., to remove outliers)",
                all_departments,
                help="Select departments to exclude from the visualization below"
            )
        
        with filter_col2:
            # Minimum user threshold filter
            min_users = st.number_input(
                "Min. Active Users",
                min_value=0,
                max_value=int(dept_stats['Active Users'].max()),
                value=0,
                help="Only show departments with at least this many active users"
            )
        
        # Apply filters to create filtered dataset for visualization
        dept_stats_filtered = dept_stats.copy()
        if excluded_depts:
            dept_stats_filtered = dept_stats_filtered[~dept_stats_filtered['Department'].isin(excluded_depts)]
        if min_users > 0:
            dept_stats_filtered = dept_stats_filtered[dept_stats_filtered['Active Users'] >= min_users]
        
        # Add view toggle for monthly breakdown
        view_mode = st.radio(
            "Chart View Mode",
            options=["Total Usage", "Monthly Breakdown"],
            horizontal=True,
            help="Toggle between total usage view and monthly breakdown by department"
        )
        
        # Create two-column layout for better space utilization
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Department comparison bar chart (filtered)
            if not dept_stats_filtered.empty:
                if view_mode == "Monthly Breakdown":
                    # Create monthly breakdown chart
                    try:
                        # Prepare monthly data by department
                        monthly_dept_data = data.copy()
                        monthly_dept_data['date'] = pd.to_datetime(monthly_dept_data['date'], errors='coerce')
                        monthly_dept_data = monthly_dept_data.dropna(subset=['date'])
                        monthly_dept_data['month'] = monthly_dept_data['date'].dt.to_period('M').astype(str)
                        
                        # Filter to only departments in the filtered list
                        filtered_depts = dept_stats_filtered['Department'].tolist()
                        monthly_dept_data = monthly_dept_data[monthly_dept_data['department'].isin(filtered_depts)]
                        
                        # Aggregate by department and month
                        dept_month_stats = monthly_dept_data.groupby(['department', 'month'])['usage_count'].sum().reset_index()
                        dept_month_stats.columns = ['Department', 'Month', 'Usage']
                        
                        # Create grouped bar chart
                        fig_dept_comparison = px.bar(
                            dept_month_stats,
                            x='Department',
                            y='Usage',
                            color='Month',
                            barmode='group',
                            title=f'Department Usage by Month (Grouped Bars)',
                            labels={'Usage': 'Messages', 'Department': 'Department'},
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        
                        # Update layout with proper margins and height
                        fig_dept_comparison.update_layout(
                            xaxis_title='Department',
                            yaxis_title='Total Messages',
                            height=450,
                            hovermode='x unified',
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            margin=dict(t=100, b=80, l=60, r=40)
                        )
                        
                        # Add value labels on bars
                        fig_dept_comparison.update_traces(
                            texttemplate='%{y:,.0f}',
                            textposition='outside',
                            textfont_size=9
                        )
                        
                        st.plotly_chart(fig_dept_comparison, use_container_width=True)
                    except Exception as e:
                        st.error(f"Unable to create monthly breakdown: {str(e)}")
                        st.info("Please ensure your data contains valid date information.")
                else:
                    # Total usage view (original)
                    fig_dept_comparison = go.Figure()
                    
                    # Add usage bars
                    fig_dept_comparison.add_trace(go.Bar(
                        name='Total Usage',
                        x=dept_stats_filtered['Department'],
                        y=dept_stats_filtered['Total Usage'],
                        marker_color='#667eea',
                        text=dept_stats_filtered['Total Usage'],
                        texttemplate='%{text:,.0f}',
                        textposition='outside',
                        hovertemplate='<b>%{x}</b><br>Usage: %{y:,.0f}<extra></extra>'
                    ))
                    
                    # Update title based on filters
                    title_suffix = ""
                    if excluded_depts or min_users > 0:
                        title_suffix = f" (Filtered: {len(dept_stats_filtered)} of {len(dept_stats)} depts)"
                    else:
                        title_suffix = f" (All {len(dept_stats)} Departments)"
                    
                    fig_dept_comparison.update_layout(
                        title=f'Department Usage Comparison{title_suffix}',
                        xaxis_title='Department',
                        yaxis_title='Total Messages',
                        showlegend=False,
                        height=450,
                        hovermode='x unified',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=80, b=80, l=60, r=40)
                    )
                    
                    st.plotly_chart(fig_dept_comparison, use_container_width=True)
            else:
                st.info("No departments match the current filter criteria.")
        
        with col2:
            # Top 3 departments with detailed insights
            st.markdown("**Top 3 Departments by Usage**")
            
            top_3_depts = dept_stats.head(3)
            
            for idx, row in top_3_depts.iterrows():
                # Medal emojis instead of generic trophy
                medal = ['🥇', '🥈', '🥉'][idx] if idx < 3 else '🏅'
                
                # Determine efficiency rating
                avg_cost_per_msg = dept_stats['Cost per Message'].mean()
                is_efficient = row['Cost per Message'] <= avg_cost_per_msg
                efficiency_icon = '💰' if is_efficient else '💸'
                
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 1rem; padding: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0; color: var(--text-primary);">{medal} {row['Department']}</h4>
                        <span style="background: #667eea; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.75rem; font-weight: 600;">{row['Usage Share %']}% of total</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.75rem;">
                        <div>
                            <p style="margin: 0; font-size: 0.75rem; color: var(--text-tertiary);">Total Messages</p>
                            <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: var(--text-primary);">{row['Total Usage']:,.0f}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 0.75rem; color: var(--text-tertiary);">Active Users</p>
                            <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: var(--text-primary);">{row['Active Users']}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 0.75rem; color: var(--text-tertiary);">Avg/User {efficiency_icon}</p>
                            <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: var(--success-border);">{row['Avg Messages/User']:,.0f}</p>
                        </div>
                        <div>
                            <p style="margin: 0; font-size: 0.75rem; color: var(--text-tertiary);">Total Cost</p>
                            <p style="margin: 0; font-size: 1.25rem; font-weight: bold; color: var(--success-border);">${row['Total Cost']:,.2f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Department efficiency insights below
        st.markdown("**Key Insights**")
        insight_cols = st.columns(3)
        
        with insight_cols[0]:
            most_efficient = dept_stats.loc[dept_stats['Cost per Message'].idxmin()]
            st.markdown(f"""
            <div class="insight-card insight-success">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--success-text);">🎯 Most Cost-Efficient</h4>
                <p style="margin: 0; font-weight: 600; color: var(--success-text);">{most_efficient['Department']}</p>
                <p style="margin: 0; font-size: 0.875rem; color: var(--success-text);">${most_efficient['Cost per Message']:.3f} per message</p>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_cols[1]:
            most_active = dept_stats.loc[dept_stats['Active Users'].idxmax()]
            st.markdown(f"""
            <div class="insight-card insight-info">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--info-text);">👥 Highest Adoption</h4>
                <p style="margin: 0; font-weight: 600; color: var(--info-text);">{most_active['Department']}</p>
                <p style="margin: 0; font-size: 0.875rem; color: var(--info-text);">{most_active['Active Users']} active users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with insight_cols[2]:
            most_engaged = dept_stats.loc[dept_stats['Avg Messages/User'].idxmax()]
            st.markdown(f"""
            <div class="insight-card insight-warning">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--warning-text);">🚀 Most Engaged</h4>
                <p style="margin: 0; font-weight: 600; color: var(--warning-text);">{most_engaged['Department']}</p>
                <p style="margin: 0; font-size: 0.875rem; color: var(--warning-text);">{most_engaged['Avg Messages/User']:,.0f} avg messages/user</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
    
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
        
        # Add filtering controls for Power Users
        st.markdown("**🎯 Customize Power User Threshold**")
        filter_col1, filter_col2 = st.columns([1, 1])
        
        with filter_col1:
            # Percentile threshold for power users
            power_user_percentile = st.slider(
                "Top % of users to include",
                min_value=1,
                max_value=25,
                value=5,
                step=1,
                help="Adjust the percentage threshold for identifying power users"
            )
        
        with filter_col2:
            # Minimum message threshold
            min_messages = st.number_input(
                "Min. Total Messages",
                min_value=0,
                max_value=int(data.groupby('user_id')['usage_count'].sum().max()) if not data.empty else 1000,
                value=0,
                help="Only show users with at least this many total messages"
            )
        
        power_users = calculate_power_users(data, threshold_percentile=(100 - power_user_percentile))
        
        # Apply minimum message filter
        if min_messages > 0 and not power_users.empty:
            power_users = power_users[power_users['usage_count'] >= min_messages]
        
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
                
                # Calculate totals
                openai_total = sum(breakdown['openai'].values())
                blueflame_total = sum(breakdown['blueflame'].values())
                total_messages = openai_total + blueflame_total
                
                # Create a card-like container for each power user
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%); 
                            padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; 
                            border-left: 4px solid #667eea;">
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([3, 4, 3])
                
                with col1:
                    # Handle NULL/empty user_name
                    display_name = row['user_name'] if pd.notna(row['user_name']) and row['user_name'] else 'Unknown User'
                    st.write(f"**{display_name}**")
                    # Handle NULL/empty email
                    display_email = row['email'] if pd.notna(row['email']) and row['email'] else 'No email'
                    st.caption(display_email)
                    # Handle NULL/empty department
                    display_dept = row['department'] if pd.notna(row['department']) and row['department'] else 'Unknown'
                    st.caption(f"🏢 {display_dept}")
                
                with col2:
                    st.write("**Message Breakdown:**")
                    
                    # OpenAI Messages Section
                    if openai_total > 0:
                        st.caption(f"**OpenAI Data:** {openai_total:,} messages")
                        if breakdown['openai']['ChatGPT Messages'] > 0:
                            st.caption(f"  💬 ChatGPT: {breakdown['openai']['ChatGPT Messages']:,}")
                        if breakdown['openai']['GPT Messages'] > 0:
                            st.caption(f"  🤖 GPTs: {breakdown['openai']['GPT Messages']:,}")
                        if breakdown['openai']['Tool Messages'] > 0:
                            st.caption(f"  🔧 Tools: {breakdown['openai']['Tool Messages']:,}")
                        if breakdown['openai']['Project Messages'] > 0:
                            st.caption(f"  📁 Projects: {breakdown['openai']['Project Messages']:,}")
                    
                    # BlueFlame Messages Section
                    if blueflame_total > 0:
                        st.caption(f"**BlueFlame Data:** {blueflame_total:,} messages")
                
                with col3:
                    st.write(f"**Total: {total_messages:,}**")
                    # Handle NaN/NULL cost_usd
                    if pd.notna(row['cost_usd']):
                        st.caption(f"💰 ${row['cost_usd']:.2f} cost")
                    else:
                        st.caption("💰 $0.00 cost")
                    # Handle NULL/empty tool_source
                    display_tools = row['tool_source'] if pd.notna(row['tool_source']) and row['tool_source'] else 'Unknown'
                    st.markdown(f'<span class="power-user-badge">{display_tools}</span>', 
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
        
        # Employee File Management
        st.markdown('<div class="section-header"><h3>👥 Employee Master File</h3></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="help-tooltip">
            📋 Upload your employee roster to enable department assignment and identify non-employee tool usage
        </div>
        """, unsafe_allow_html=True)
        
        try:
            employee_count = db.get_employee_count()
        except AttributeError:
            # Handle cache error - database object missing methods
            employee_count = 0
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.metric("Employees Loaded", f"{employee_count:,}", help="Total employees in master roster")
        
        with col2:
            if st.button("👁️ View Employees", help="View all loaded employees"):
                st.session_state.show_employees = not st.session_state.get('show_employees', False)
        
        # Show employee table if requested
        if st.session_state.get('show_employees', False):
            try:
                employees_df = db.get_all_employees()
            except AttributeError:
                # Handle cache error - database object missing methods
                employees_df = pd.DataFrame()
            
            if not employees_df.empty:
                st.dataframe(employees_df, use_container_width=True)
            else:
                st.info("No employees loaded yet")
        
        # Employee file uploader
        employee_file = st.file_uploader(
            "📤 Upload Employee Master File",
            type=['csv', 'xlsx'],
            help="Upload CSV or Excel file with columns: First Name, Last Name, Email, Title, Function (for department), Status",
            key="employee_uploader"
        )
        
        if employee_file is not None:
            try:
                # Read the file
                if employee_file.name.endswith('.csv'):
                    emp_df = pd.read_csv(employee_file, low_memory=False)
                else:
                    emp_df = pd.read_excel(employee_file)
                
                st.write(f"**Preview of {employee_file.name}:**")
                st.dataframe(emp_df.head(5), use_container_width=True)
                
                # Map columns
                st.write("**Column Mapping:**")
                st.info("ℹ️ Email column is optional. If your file doesn't have email addresses, employees will be matched by name.")
                col_map_col1, col_map_col2 = st.columns(2)
                
                with col_map_col1:
                    first_name_col = st.selectbox("First Name Column", emp_df.columns, 
                                                  index=next((i for i, c in enumerate(emp_df.columns) if 'first' in c.lower()), 0))
                    last_name_col = st.selectbox("Last Name Column", emp_df.columns,
                                                index=next((i for i, c in enumerate(emp_df.columns) if 'last' in c.lower()), 1))
                    # Make email optional
                    email_col_options = ['[No Email Column]'] + list(emp_df.columns)
                    email_col_idx = next((i+1 for i, c in enumerate(emp_df.columns) if 'email' in c.lower()), 0)
                    email_col_selection = st.selectbox("Email Column (Optional)", email_col_options, index=email_col_idx)
                
                with col_map_col2:
                    title_col = st.selectbox("Title Column", emp_df.columns,
                                           index=next((i for i, c in enumerate(emp_df.columns) if 'title' in c.lower() or 'position' in c.lower()), 3))
                    dept_col = st.selectbox("Department Column (Function)", emp_df.columns,
                                          index=next((i for i, c in enumerate(emp_df.columns) if 'function' in c.lower() or 'department' in c.lower() or 'dept' in c.lower()), 4))
                    status_col = st.selectbox("Status Column", emp_df.columns,
                                            index=next((i for i, c in enumerate(emp_df.columns) if 'status' in c.lower()), 5))
                
                if st.button("📥 Load Employees", type="primary"):
                    # Create normalized dataframe
                    normalized_emp_df = pd.DataFrame({
                        'first_name': emp_df[first_name_col],
                        'last_name': emp_df[last_name_col],
                        'email': emp_df[email_col_selection] if email_col_selection != '[No Email Column]' else None,
                        'title': emp_df[title_col],
                        'department': emp_df[dept_col],
                        'status': emp_df[status_col]
                    })
                    
                    # Load into database
                    success, message, count = db.load_employees(normalized_emp_df)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                        
            except Exception as e:
                st.error(f"❌ Error processing employee file: {str(e)}")
        
        st.divider()
        
        # Upload history with better styling and file management
        st.markdown('<div class="section-header"><h3>📂 Upload History & File Management</h3></div>', unsafe_allow_html=True)
        
        if db_info['upload_history']:
            upload_df = pd.DataFrame(db_info['upload_history'])
            
            # Display upload history with delete option
            for idx, row in upload_df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**📄 {row['filename']}**")
                
                with col2:
                    st.write(f"📅 {row['date_range']}")
                
                with col3:
                    st.write(f"📊 {row['records']:,} records")
                
                with col4:
                    # Delete button for individual file
                    if st.button("🗑️", key=f"delete_file_{idx}", help=f"Delete {row['filename']}"):
                        confirm_key = f"confirm_delete_{idx}"
                        if st.session_state.get(confirm_key, False):
                            # Actually delete the file
                            success = db.delete_by_file(row['filename'])
                            if success:
                                st.success(f"✅ Deleted {row['filename']}")
                                st.session_state[confirm_key] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Error deleting {row['filename']}")
                        else:
                            # Set confirmation flag
                            st.session_state[confirm_key] = True
                            st.warning(f"⚠️ Click again to confirm deletion of {row['filename']}")
                
                # Show confirmation warning if needed
                confirm_key = f"confirm_delete_{idx}"
                if st.session_state.get(confirm_key, False):
                    st.error(f"⚠️ **Confirm deletion:** Click 🗑️ again to permanently delete {row['filename']} ({row['records']:,} records)")
                
                st.divider()
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