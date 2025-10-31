#!/usr/bin/env python3
"""
Test to verify the Unknown department breakdown fix
"""
import pandas as pd
import sqlite3
import sys
from database import DatabaseManager
from app import apply_employee_departments

def test_unknown_department_breakdown():
    """Test that Unknown department correctly shows breakdown"""
    
    # Initialize database
    db = DatabaseManager()
    
    # Create sample employee data - some with "Unknown" department
    employee_data = pd.DataFrame([
        {'first_name': 'Alice', 'last_name': 'Employee', 'email': 'alice@company.com', 'department': 'Engineering', 'title': 'Engineer', 'status': 'Active'},
        {'first_name': 'Bob', 'last_name': 'Unknown1', 'email': 'bob@company.com', 'department': 'Unknown', 'title': 'Manager', 'status': 'Active'},
        {'first_name': 'Charlie', 'last_name': 'Unknown2', 'email': 'charlie@company.com', 'department': 'Unknown', 'title': 'Analyst', 'status': 'Active'},
    ])
    
    # Load employees into database
    success, msg, count = db.load_employees(employee_data)
    print(f"✓ Loaded {count} employees into database")
    
    # Create usage data with both employees and non-employees
    usage_data = pd.DataFrame([
        # Employees (in employee master)
        {'email': 'alice@company.com', 'user_name': 'Alice Employee', 'department': 'OldDept', 'date': '2024-01-01', 'usage_count': 100, 'cost_usd': 10, 'user_id': 'alice@company.com', 'feature_used': 'ChatGPT', 'tool_source': 'ChatGPT', 'file_source': 'test.csv', 'created_at': '2024-01-01'},
        {'email': 'bob@company.com', 'user_name': 'Bob Unknown1', 'department': 'OldDept', 'date': '2024-01-01', 'usage_count': 50, 'cost_usd': 5, 'user_id': 'bob@company.com', 'feature_used': 'ChatGPT', 'tool_source': 'ChatGPT', 'file_source': 'test.csv', 'created_at': '2024-01-01'},
        {'email': 'charlie@company.com', 'user_name': 'Charlie Unknown2', 'department': 'OldDept', 'date': '2024-01-01', 'usage_count': 75, 'cost_usd': 7.5, 'user_id': 'charlie@company.com', 'feature_used': 'ChatGPT', 'tool_source': 'ChatGPT', 'file_source': 'test.csv', 'created_at': '2024-01-01'},
        
        # Non-employees (NOT in employee master)
        {'email': 'contractor1@vendor.com', 'user_name': 'Contractor One', 'department': 'Unknown', 'date': '2024-01-01', 'usage_count': 30, 'cost_usd': 3, 'user_id': 'contractor1@vendor.com', 'feature_used': 'ChatGPT', 'tool_source': 'ChatGPT', 'file_source': 'test.csv', 'created_at': '2024-01-01'},
        {'email': 'contractor2@vendor.com', 'user_name': 'Contractor Two', 'department': 'Unknown', 'date': '2024-01-01', 'usage_count': 20, 'cost_usd': 2, 'user_id': 'contractor2@vendor.com', 'feature_used': 'ChatGPT', 'tool_source': 'ChatGPT', 'file_source': 'test.csv', 'created_at': '2024-01-01'},
    ])
    
    # Insert usage data into database
    conn = sqlite3.connect(db.db_path)
    usage_data.to_sql('usage_metrics', conn, if_exists='replace', index=False)
    conn.close()
    
    print("✓ Loaded usage data into database")
    
    # Apply employee departments (this is what happens in the main app)
    all_data = db.get_all_data()
    data_with_emp_depts = apply_employee_departments(all_data, db)
    
    # Calculate department stats like the Department Performance section
    dept_stats = data_with_emp_depts.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    
    print("\n=== Department Performance Stats ===")
    print(dept_stats)
    
    # Get unidentified users from database
    unidentified_users = db.get_unidentified_users()
    unidentified_count = len(unidentified_users)
    
    print(f"\n=== Unidentified Users (from database) ===")
    print(f"Count: {unidentified_count}")
    print(unidentified_users[['email', 'user_name', 'total_usage']])
    
    # Verify the breakdown for Unknown department
    unknown_row = dept_stats[dept_stats['Department'] == 'Unknown']
    if not unknown_row.empty:
        total_unknown = int(unknown_row['Active Users'].values[0])
        employees_with_unknown_dept = total_unknown - unidentified_count
        
        print(f"\n=== Unknown Department Breakdown ===")
        print(f"Total users in 'Unknown' department: {total_unknown}")
        print(f"  - Employees with department='Unknown': {employees_with_unknown_dept}")
        print(f"  - Unidentified users (not in employee master): {unidentified_count}")
        
        # Assertions
        assert total_unknown == 4, f"Expected 4 total users in Unknown, got {total_unknown}"
        assert employees_with_unknown_dept == 2, f"Expected 2 employees with Unknown dept, got {employees_with_unknown_dept}"
        assert unidentified_count == 2, f"Expected 2 unidentified users, got {unidentified_count}"
        
        print("\n✅ All assertions passed!")
        print("\nThis breakdown will now be shown in the Department Performance section")
        print("when the 'Unknown' department is displayed in the top 3.")
        return True
    else:
        print("\n❌ Unknown department not found in stats")
        return False

if __name__ == '__main__':
    try:
        success = test_unknown_department_breakdown()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
