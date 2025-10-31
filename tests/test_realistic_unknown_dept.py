#!/usr/bin/env python3
"""
Test to verify the fix with realistic numbers matching the problem statement:
- Department Performance shows 35 active users in "Unknown"
- Database shows 19 unidentified users
- Difference should be 16 employees with department="Unknown"
"""
import pandas as pd
import sqlite3
import sys
from database import DatabaseManager
from app import apply_employee_departments

def test_realistic_scenario():
    """Test with realistic numbers from the problem statement"""
    
    # Initialize database
    db = DatabaseManager()
    
    # Create 16 employees with "Unknown" department
    employee_data = []
    for i in range(1, 17):
        employee_data.append({
            'first_name': f'Employee{i}',
            'last_name': f'Unknown{i}',
            'email': f'employee{i}@company.com',
            'department': 'Unknown',
            'title': 'Staff',
            'status': 'Active'
        })
    
    # Add some employees with real departments too
    employee_data.extend([
        {'first_name': 'Alice', 'last_name': 'Engineer', 'email': 'alice@company.com', 'department': 'Engineering', 'title': 'Engineer', 'status': 'Active'},
        {'first_name': 'Bob', 'last_name': 'Manager', 'email': 'bob@company.com', 'department': 'Sales', 'title': 'Manager', 'status': 'Active'},
    ])
    
    employee_df = pd.DataFrame(employee_data)
    
    # Load employees into database
    success, msg, count = db.load_employees(employee_df)
    print(f"✓ Loaded {count} employees into database")
    print(f"  - 16 employees with department='Unknown'")
    print(f"  - 2 employees with other departments")
    
    # Create usage data
    usage_records = []
    
    # Add usage for the 16 employees with Unknown dept
    for i in range(1, 17):
        usage_records.append({
            'email': f'employee{i}@company.com',
            'user_name': f'Employee{i} Unknown{i}',
            'department': 'OldDept',  # CSV has wrong dept, will be corrected by employee master
            'date': '2024-01-01',
            'usage_count': 100,
            'cost_usd': 10,
            'user_id': f'employee{i}@company.com',
            'feature_used': 'ChatGPT',
            'tool_source': 'ChatGPT',
            'file_source': 'test.csv',
            'created_at': '2024-01-01'
        })
    
    # Add usage for other employees
    usage_records.extend([
        {
            'email': 'alice@company.com',
            'user_name': 'Alice Engineer',
            'department': 'OldDept',
            'date': '2024-01-01',
            'usage_count': 200,
            'cost_usd': 20,
            'user_id': 'alice@company.com',
            'feature_used': 'ChatGPT',
            'tool_source': 'ChatGPT',
            'file_source': 'test.csv',
            'created_at': '2024-01-01'
        },
        {
            'email': 'bob@company.com',
            'user_name': 'Bob Manager',
            'department': 'OldDept',
            'date': '2024-01-01',
            'usage_count': 150,
            'cost_usd': 15,
            'user_id': 'bob@company.com',
            'feature_used': 'ChatGPT',
            'tool_source': 'ChatGPT',
            'file_source': 'test.csv',
            'created_at': '2024-01-01'
        }
    ])
    
    # Add 19 unidentified users (not in employee master)
    for i in range(1, 20):
        usage_records.append({
            'email': f'contractor{i}@vendor.com',
            'user_name': f'Contractor {i}',
            'department': 'Unknown',
            'date': '2024-01-01',
            'usage_count': 50,
            'cost_usd': 5,
            'user_id': f'contractor{i}@vendor.com',
            'feature_used': 'ChatGPT',
            'tool_source': 'ChatGPT',
            'file_source': 'test.csv',
            'created_at': '2024-01-01'
        })
    
    usage_df = pd.DataFrame(usage_records)
    
    # Insert usage data into database
    conn = sqlite3.connect(db.db_path)
    usage_df.to_sql('usage_metrics', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"✓ Loaded {len(usage_records)} usage records")
    print(f"  - 16 employee records (with Unknown dept)")
    print(f"  - 2 employee records (with other depts)")
    print(f"  - 19 unidentified user records")
    
    # Apply employee departments (this is what happens in the main app)
    all_data = db.get_all_data()
    print(f"\n✓ Retrieved {len(all_data)} records from database")
    
    data_with_emp_depts = apply_employee_departments(all_data, db)
    print(f"✓ Applied employee departments to data")
    
    # Calculate department stats like the Department Performance section
    dept_stats = data_with_emp_depts.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    dept_stats = dept_stats.sort_values('Total Usage', ascending=False)
    
    print("\n=== Department Performance Stats ===")
    print(dept_stats)
    
    # Get unidentified users from database
    unidentified_users = db.get_unidentified_users()
    unidentified_count = len(unidentified_users)
    
    print(f"\n=== Unidentified Users (from database) ===")
    print(f"Count: {unidentified_count}")
    
    # Verify the breakdown for Unknown department
    unknown_row = dept_stats[dept_stats['Department'] == 'Unknown']
    if not unknown_row.empty:
        total_unknown = int(unknown_row['Active Users'].values[0])
        employees_with_unknown_dept = total_unknown - unidentified_count
        
        print(f"\n=== Unknown Department Breakdown ===")
        print(f"Total users in 'Unknown' department: {total_unknown}")
        print(f"  - Employees with department='Unknown': {employees_with_unknown_dept}")
        print(f"  - Unidentified users (not in employee master): {unidentified_count}")
        
        # Verify against problem statement
        print(f"\n=== Verification Against Problem Statement ===")
        print(f"Problem: Department Performance shows 35 active users, but only 19 unidentified")
        print(f"Expected: 35 - 19 = 16 employees with Unknown department")
        print(f"\nOur Test Results:")
        print(f"  Department Performance 'Unknown' users: {total_unknown}")
        print(f"  Unidentified users count: {unidentified_count}")
        print(f"  Employees with Unknown dept: {employees_with_unknown_dept}")
        
        # Assertions
        assert total_unknown == 35, f"Expected 35 total users in Unknown, got {total_unknown}"
        assert employees_with_unknown_dept == 16, f"Expected 16 employees with Unknown dept, got {employees_with_unknown_dept}"
        assert unidentified_count == 19, f"Expected 19 unidentified users, got {unidentified_count}"
        
        print("\n✅ All assertions passed!")
        print("\n📊 The breakdown display will show:")
        print(f"   ℹ️ 'Unknown' Department Breakdown:")
        print(f"   • {employees_with_unknown_dept} employees with department = 'Unknown' in employee master file")
        print(f"   • {unidentified_count} unidentified users (not in employee master file)")
        print(f"\nThis resolves the confusion in the original problem statement!")
        return True
    else:
        print("\n❌ Unknown department not found in stats")
        return False

if __name__ == '__main__':
    try:
        success = test_realistic_scenario()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
