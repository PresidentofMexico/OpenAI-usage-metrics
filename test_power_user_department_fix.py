"""
Test to verify that power users show correct departments from employee database.

This test validates the fix for the issue where verified employees like Jack Steed 
and Tyler Mackesy were showing 'Unknown' department in the Power Users section
despite being verified in the employee master file with locked departments.
"""

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime

# Import the functions we need to test
sys.path.insert(0, os.path.dirname(__file__))
from app import calculate_power_users, get_employee_for_user, db

def setup_test_database():
    """Create a test database with employees and usage data."""
    # Use a test database
    test_db_path = 'test_power_users.db'
    
    # Remove old test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    conn = sqlite3.connect(test_db_path)
    
    # Create employees table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
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
        CREATE TABLE IF NOT EXISTS usage_metrics (
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
    employees_data = [
        ('Jack', 'Steed', 'jack.steed@company.com', 'Senior Analyst', 'Corporate Credit', 'Active'),
        ('Tyler', 'Mackesy', 'tyler.mackesy@company.com', 'Manager', 'Corporate Credit', 'Active'),
        ('Alice', 'Johnson', 'alice.johnson@company.com', 'Developer', 'Engineering', 'Active'),
    ]
    
    for emp in employees_data:
        conn.execute(
            "INSERT INTO employees (first_name, last_name, email, title, department, status) VALUES (?, ?, ?, ?, ?, ?)",
            emp
        )
    
    # Insert usage data with WRONG/MIXED departments to simulate the issue
    # Jack Steed has some records with 'Unknown' and some with 'Corporate Credit'
    usage_data = [
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Unknown', '2024-01-15', 'ChatGPT Messages', 150, 30.0, 'ChatGPT'),
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Unknown', '2024-02-15', 'ChatGPT Messages', 200, 30.0, 'ChatGPT'),
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Corporate Credit', '2024-03-15', 'ChatGPT Messages', 180, 30.0, 'ChatGPT'),
        
        # Tyler Mackesy has all records as 'Unknown'
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-01-15', 'ChatGPT Messages', 160, 30.0, 'ChatGPT'),
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-02-15', 'ChatGPT Messages', 190, 30.0, 'ChatGPT'),
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-03-15', 'ChatGPT Messages', 170, 30.0, 'ChatGPT'),
        
        # Alice has correct department
        ('alice.johnson@company.com', 'Alice Johnson', 'alice.johnson@company.com', 'Engineering', '2024-01-15', 'ChatGPT Messages', 100, 30.0, 'ChatGPT'),
        ('alice.johnson@company.com', 'Alice Johnson', 'alice.johnson@company.com', 'Engineering', '2024-02-15', 'ChatGPT Messages', 120, 30.0, 'ChatGPT'),
        
        # Unknown user (not in employees table)
        ('unknown@company.com', 'Unknown User', 'unknown@company.com', 'Unknown', '2024-01-15', 'ChatGPT Messages', 50, 30.0, 'ChatGPT'),
    ]
    
    for usage in usage_data:
        conn.execute(
            "INSERT INTO usage_metrics (user_id, user_name, email, department, date, feature_used, usage_count, cost_usd, tool_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            usage
        )
    
    conn.commit()
    conn.close()
    
    return test_db_path


def test_power_users_department_fix():
    """Test that power users show correct departments from employee database."""
    print("=" * 70)
    print("Testing Power Users Department Fix")
    print("=" * 70)
    
    # Setup test database
    test_db_path = setup_test_database()
    
    # Update the global db object to use test database
    original_db_path = db.db_path
    db.db_path = test_db_path
    
    try:
        # Load usage data
        conn = sqlite3.connect(test_db_path)
        usage_data = pd.read_sql_query("SELECT * FROM usage_metrics", conn)
        conn.close()
        
        print(f"\nTotal usage records: {len(usage_data)}")
        print("\nUsage data departments before fix:")
        print(usage_data.groupby(['email', 'department']).size())
        
        # Calculate power users (should use threshold that includes all test users)
        power_users = calculate_power_users(usage_data, threshold_percentile=0)
        
        print("\n" + "=" * 70)
        print("Power Users Results:")
        print("=" * 70)
        
        for idx, row in power_users.iterrows():
            print(f"\nUser: {row['user_name']}")
            print(f"  Email: {row['email']}")
            print(f"  Department: {row['department']}")
            print(f"  Usage Count: {row['usage_count']}")
        
        # Verify results
        print("\n" + "=" * 70)
        print("Verification:")
        print("=" * 70)
        
        # Test 1: Jack Steed should show 'Corporate Credit', not 'Unknown'
        jack_row = power_users[power_users['email'] == 'jack.steed@company.com']
        if not jack_row.empty:
            jack_dept = jack_row.iloc[0]['department']
            print(f"\n✓ Jack Steed department: {jack_dept}")
            assert jack_dept == 'Corporate Credit', f"Expected 'Corporate Credit', got '{jack_dept}'"
            print("  PASS: Jack Steed shows correct department!")
        else:
            print("\n✗ FAIL: Jack Steed not found in power users")
            raise AssertionError("Jack Steed not found")
        
        # Test 2: Tyler Mackesy should show 'Corporate Credit', not 'Unknown'
        tyler_row = power_users[power_users['email'] == 'tyler.mackesy@company.com']
        if not tyler_row.empty:
            tyler_dept = tyler_row.iloc[0]['department']
            print(f"\n✓ Tyler Mackesy department: {tyler_dept}")
            assert tyler_dept == 'Corporate Credit', f"Expected 'Corporate Credit', got '{tyler_dept}'"
            print("  PASS: Tyler Mackesy shows correct department!")
        else:
            print("\n✗ FAIL: Tyler Mackesy not found in power users")
            raise AssertionError("Tyler Mackesy not found")
        
        # Test 3: Alice should still show Engineering
        alice_row = power_users[power_users['email'] == 'alice.johnson@company.com']
        if not alice_row.empty:
            alice_dept = alice_row.iloc[0]['department']
            print(f"\n✓ Alice Johnson department: {alice_dept}")
            assert alice_dept == 'Engineering', f"Expected 'Engineering', got '{alice_dept}'"
            print("  PASS: Alice Johnson shows correct department!")
        else:
            print("\n✗ FAIL: Alice Johnson not found in power users")
            raise AssertionError("Alice Johnson not found")
        
        # Test 4: Unknown user should still show 'Unknown' (not in employee DB)
        unknown_row = power_users[power_users['email'] == 'unknown@company.com']
        if not unknown_row.empty:
            unknown_dept = unknown_row.iloc[0]['department']
            print(f"\n✓ Unknown User department: {unknown_dept}")
            assert unknown_dept == 'Unknown', f"Expected 'Unknown', got '{unknown_dept}'"
            print("  PASS: Non-employee users still show Unknown!")
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED! ✓")
        print("=" * 70)
        print("\nSummary:")
        print("- Verified employees now show their locked departments")
        print("- Jack Steed: Corporate Credit (was showing Unknown)")
        print("- Tyler Mackesy: Corporate Credit (was showing Unknown)")
        print("- Non-employees still correctly show Unknown")
        print("- Fix prevents 'Unknown' from being the largest category")
        
    finally:
        # Restore original database path
        db.db_path = original_db_path
        
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


if __name__ == '__main__':
    test_power_users_department_fix()
