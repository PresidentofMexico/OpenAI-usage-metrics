#!/usr/bin/env python3
"""
Setup script to create a test database with sample data for UI testing
"""
import sys
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

import pandas as pd
from database import DatabaseManager
from data_processor import DataProcessor
from datetime import datetime
import os

def setup_test_database():
    """Create a test database with sample employees and usage data"""
    
    # Use a test database
    db_path = 'test_ui.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("Setting up test database for UI testing...")
    
    # Initialize database
    db = DatabaseManager(db_path)
    processor = DataProcessor(db)
    
    # Load sample employees from existing test file
    print("\n1. Loading employees from test_employees.csv...")
    emp_df = pd.read_csv('test_employees.csv')
    
    normalized_emp_df = pd.DataFrame({
        'first_name': emp_df['First Name'],
        'last_name': emp_df['Last Name'],
        'email': emp_df['Email'],
        'title': emp_df['Title'],
        'department': emp_df['Function'],
        'status': emp_df['Status']
    })
    
    success, message, count = db.load_employees(normalized_emp_df)
    print(f"   {message}")
    
    # Create sample usage data
    print("\n2. Creating sample usage data...")
    usage_data = pd.DataFrame([
        {
            'user_id': 'sarah.johnson@company.com',
            'user_name': 'Sarah Johnson',
            'email': 'sarah.johnson@company.com',
            'department': 'Technology',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 150,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'setup_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'michael.chen@company.com',
            'user_name': 'Michael Chen',
            'email': 'michael.chen@company.com',
            'department': 'Finance',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 200,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'setup_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'emily.rodriguez@company.com',
            'user_name': 'Emily Rodriguez',
            'email': 'emily.rodriguez@company.com',
            'department': 'Operations',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 75,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'setup_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'david.wilson@company.com',
            'user_name': 'David Wilson',
            'email': 'david.wilson@company.com',
            'department': 'Marketing',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 100,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'setup_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'alex.thompson@company.com',
            'user_name': 'Alex Thompson',
            'email': 'alex.thompson@company.com',
            'department': 'Human Capital',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 50,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'setup_data.csv',
            'created_at': datetime.now().isoformat()
        }
    ])
    
    success, message = processor.process_monthly_data(usage_data, 'setup_data.csv')
    print(f"   {message}")
    
    # Verify database contents
    print("\n3. Verifying database contents...")
    all_employees = db.get_all_employees()
    all_usage = db.get_all_data()
    print(f"   Total employees: {len(all_employees)}")
    print(f"   Total usage records: {len(all_usage)}")
    
    print(f"\n✅ Test database created: {db_path}")
    print("\nYou can now run the Streamlit app and test the employee deletion feature.")
    print("The database will persist between runs until you delete the test_ui.db file.")
    
    return db_path

if __name__ == "__main__":
    setup_test_database()
