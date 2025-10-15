"""
Test suite for employee department assignment fix.

Tests that the employee master file drives all department assignments,
not just for power users, fixing the discrepancy between Department Performance
and Unidentified Users sections.
"""

import pandas as pd
import sys
import sqlite3
import os
from datetime import datetime

def setup_test_database():
    """Create a test database with sample employee and usage data."""
    test_db_path = "test_dept_fix.db"
    
    # Remove old test database if exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    conn = sqlite3.connect(test_db_path)
    
    # Create employees table
    conn.execute("""
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            title TEXT,
            department TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create usage_metrics table
    conn.execute("""
        CREATE TABLE usage_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT,
            email TEXT,
            department TEXT,
            date TEXT NOT NULL,
            feature_used TEXT,
            usage_count INTEGER,
            cost_usd REAL,
            tool_source TEXT DEFAULT 'ChatGPT',
            file_source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert test employees with correct departments
    employees = [
        ('Jack', 'Steed', 'jack.steed@company.com', 'Analyst', 'Corporate Credit', 'Active'),
        ('Tyler', 'Mackesy', 'tyler.mackesy@company.com', 'Manager', 'Corporate Credit', 'Active'),
        ('Alice', 'Johnson', 'alice.j@company.com', 'Developer', 'Engineering', 'Active'),
    ]
    
    for emp in employees:
        conn.execute("""
            INSERT INTO employees (first_name, last_name, email, title, department, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, emp)
    
    # Insert usage data with INCORRECT departments (as they were stored from CSV)
    # This simulates the bug where usage_metrics has wrong departments
    usage_data = [
        # Jack Steed - has 150k messages but stored as 'Unknown' in usage_metrics
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 100000, 60.0, 'ChatGPT'),
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Unknown', '2024-10-01', 'Tool Messages', 50000, 0.0, 'ChatGPT'),
        
        # Tyler Mackesy - has 80k messages, also stored as 'Unknown'
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 60000, 60.0, 'ChatGPT'),
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-10-01', 'Tool Messages', 20000, 0.0, 'ChatGPT'),
        
        # Alice Johnson - correctly stored as 'Engineering'
        ('alice.j@company.com', 'Alice Johnson', 'alice.j@company.com', 'Engineering', '2024-10-01', 'ChatGPT Messages', 30000, 60.0, 'ChatGPT'),
        
        # Unknown user (not in employee table) - correctly stored as 'Unknown'
        ('unknown@external.com', 'Unknown User', 'unknown@external.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 5000, 60.0, 'ChatGPT'),
    ]
    
    for data in usage_data:
        conn.execute("""
            INSERT INTO usage_metrics (user_id, user_name, email, department, date, feature_used, usage_count, cost_usd, tool_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
    
    conn.commit()
    conn.close()
    
    return test_db_path

def test_employee_department_application():
    """Test that employee departments are correctly applied to all data."""
    print("\n🧪 Testing Employee Department Application Fix...")
    
    # Setup test database
    test_db_path = setup_test_database()
    
    # Import required modules
    sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')
    from database import DatabaseManager
    from app import apply_employee_departments
    
    # Initialize database manager with test database
    db = DatabaseManager(test_db_path)
    
    # Get all data (simulating what happens in the dashboard)
    data = db.get_all_data()
    
    print(f"\n📊 BEFORE applying employee departments:")
    dept_counts_before = data.groupby('department')['usage_count'].sum().sort_values(ascending=False)
    print(dept_counts_before)
    
    # Check that 'Unknown' is incorrectly the top department (the bug)
    if 'Unknown' in dept_counts_before.index:
        unknown_usage_before = dept_counts_before['Unknown']
        print(f"\n❌ BUG PRESENT: 'Unknown' department has {unknown_usage_before:,} messages")
    
    # Apply employee departments (the fix)
    data_fixed = apply_employee_departments(data, db)
    
    print(f"\n📊 AFTER applying employee departments:")
    dept_counts_after = data_fixed.groupby('department')['usage_count'].sum().sort_values(ascending=False)
    print(dept_counts_after)
    
    # Verify the fix
    success = True
    
    # Check 1: Corporate Credit should now be the top department (150k + 80k = 230k messages)
    if 'Corporate Credit' in dept_counts_after.index:
        cc_usage = dept_counts_after['Corporate Credit']
        expected_cc_usage = 230000  # Jack (150k) + Tyler (80k)
        if cc_usage == expected_cc_usage:
            print(f"✅ Corporate Credit department has correct usage: {cc_usage:,} messages")
        else:
            print(f"❌ Corporate Credit usage incorrect: expected {expected_cc_usage:,}, got {cc_usage:,}")
            success = False
    else:
        print("❌ Corporate Credit department not found!")
        success = False
    
    # Check 2: Unknown should only have the actual unknown user (5k messages)
    if 'Unknown' in dept_counts_after.index:
        unknown_usage_after = dept_counts_after['Unknown']
        expected_unknown_usage = 5000  # Only the external user
        if unknown_usage_after == expected_unknown_usage:
            print(f"✅ 'Unknown' department has correct usage: {unknown_usage_after:,} messages (only non-employees)")
        else:
            print(f"❌ 'Unknown' usage incorrect: expected {expected_unknown_usage:,}, got {unknown_usage_after:,}")
            success = False
    
    # Check 3: Jack Steed should be in Corporate Credit
    jack_data = data_fixed[data_fixed['email'] == 'jack.steed@company.com']
    jack_depts = jack_data['department'].unique()
    if len(jack_depts) == 1 and jack_depts[0] == 'Corporate Credit':
        print(f"✅ Jack Steed correctly assigned to 'Corporate Credit'")
    else:
        print(f"❌ Jack Steed has incorrect departments: {jack_depts}")
        success = False
    
    # Check 4: Tyler Mackesy should be in Corporate Credit
    tyler_data = data_fixed[data_fixed['email'] == 'tyler.mackesy@company.com']
    tyler_depts = tyler_data['department'].unique()
    if len(tyler_depts) == 1 and tyler_depts[0] == 'Corporate Credit':
        print(f"✅ Tyler Mackesy correctly assigned to 'Corporate Credit'")
    else:
        print(f"❌ Tyler Mackesy has incorrect departments: {tyler_depts}")
        success = False
    
    # Check 5: Unknown user should remain Unknown
    unknown_data = data_fixed[data_fixed['email'] == 'unknown@external.com']
    unknown_depts = unknown_data['department'].unique()
    if len(unknown_depts) == 1 and unknown_depts[0] == 'Unknown':
        print(f"✅ Non-employee correctly remains 'Unknown'")
    else:
        print(f"❌ Non-employee has incorrect departments: {unknown_depts}")
        success = False
    
    # Cleanup
    os.remove(test_db_path)
    
    return success

def test_department_performance_accuracy():
    """Test that Department Performance section shows accurate data."""
    print("\n🧪 Testing Department Performance Accuracy...")
    
    # Setup test database
    test_db_path = setup_test_database()
    
    # Import required modules
    sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')
    from database import DatabaseManager
    from app import apply_employee_departments
    
    # Initialize database manager
    db = DatabaseManager(test_db_path)
    
    # Simulate what happens in Department Performance section
    data = db.get_all_data()
    data = apply_employee_departments(data, db)
    
    # Calculate department stats (exactly as done in app.py line 2391)
    dept_stats = data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    dept_stats = dept_stats.sort_values('Total Usage', ascending=False)
    
    print("\n📊 Department Performance (Top 3):")
    print(dept_stats.head(3).to_string(index=False))
    
    # Verify top department is NOT 'Unknown' (unless it legitimately should be)
    top_dept = dept_stats.iloc[0]['Department']
    top_usage = dept_stats.iloc[0]['Total Usage']
    
    success = True
    
    if top_dept == 'Corporate Credit':
        print(f"\n✅ Top department is correctly 'Corporate Credit' with {top_usage:,} messages")
    elif top_dept == 'Unknown':
        print(f"\n❌ Top department is incorrectly 'Unknown' - this is the bug!")
        success = False
    else:
        print(f"\n⚠️ Top department is '{top_dept}' with {top_usage:,} messages")
    
    # Cleanup
    os.remove(test_db_path)
    
    return success

def run_all_tests():
    """Run all department employee fix tests."""
    print("\n" + "="*70)
    print("TESTING: Employee Department Assignment Fix")
    print("="*70)
    
    results = []
    
    # Test 1: Employee department application
    results.append(("Employee Department Application", test_employee_department_application()))
    
    # Test 2: Department performance accuracy
    results.append(("Department Performance Accuracy", test_department_performance_accuracy()))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! ✓")
        print("\nThe fix ensures:")
        print("- Employee master file drives all department assignments")
        print("- Department Performance shows correct departments")
        print("- No more 'Unknown' department for verified employees")
        print("- Consistency between Department Performance and Unidentified Users")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
