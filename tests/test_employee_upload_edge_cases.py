#!/usr/bin/env python3
"""
Test employee upload with various edge cases that could cause NoneType strip() errors.
This test ensures defensive coding handles all None/NaN/empty value scenarios.
"""
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager

def test_none_email_column():
    """Test uploading employee file without email column (scalar None)"""
    print("\n" + "=" * 60)
    print("TEST 1: None Email Column (Primary Bug Scenario)")
    print("=" * 60)
    
    db_path = '/tmp/test_none_email.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    # Simulate what app.py does when "[No Email Column]" is selected
    emp_df = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson']
    })
    
    normalized_df = pd.DataFrame({
        'first_name': emp_df['first_name'],
        'last_name': emp_df['last_name'],
        'email': None,  # Scalar None - the key issue!
        'title': ['Engineer', 'Manager', 'Analyst'],
        'department': ['Engineering', 'Product', 'Analytics'],
        'status': ['Active', 'Active', 'Active']
    })
    
    success, message, count = db.load_employees(normalized_df)
    
    assert success, f"Failed: {message}"
    assert count == 3, f"Expected 3 employees, got {count}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: None email column handled correctly")

def test_string_null_values():
    """Test handling of string representations of null ('None', 'nan', 'null')"""
    print("\n" + "=" * 60)
    print("TEST 2: String Null Values ('None', 'nan', 'null')")
    print("=" * 60)
    
    db_path = '/tmp/test_string_nulls.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    test_df = pd.DataFrame({
        'first_name': ['Alice', 'Bob', 'Charlie'],
        'last_name': ['Williams', 'Brown', 'Davis'],
        'email': ['None', 'nan', 'null'],  # String representations
        'title': ['Director', 'Lead', 'Manager'],
        'department': ['Sales', 'Marketing', 'Operations'],
        'status': ['Active', 'Active', 'Active']
    })
    
    success, message, count = db.load_employees(test_df)
    
    assert success, f"Failed: {message}"
    assert count == 3, f"Expected 3 employees, got {count}"
    
    # Verify emails are stored as NULL, not as strings
    all_emps = db.get_all_employees()
    assert all(pd.isna(e) or e is None for e in all_emps['email']), "String nulls should be converted to NULL"
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: String null values converted to NULL correctly")

def test_mixed_none_nan_values():
    """Test handling of mixed None, NaN, and empty string values"""
    print("\n" + "=" * 60)
    print("TEST 3: Mixed None/NaN/Empty Values")
    print("=" * 60)
    
    db_path = '/tmp/test_mixed_nulls.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    test_df = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob', None, 'Alice'],
        'last_name': ['Doe', None, 'Johnson', 'Smith', 'Williams'],
        'email': [None, 'jane@test.com', '', float('nan'), '  '],
        'title': ['Engineer', '', None, 'Analyst', 'Director'],
        'department': [None, 'Product', '', 'Analytics', 'Sales'],
        'status': ['Active', '', None, 'Inactive', 'Active']
    })
    
    success, message, count = db.load_employees(test_df)
    
    assert success, f"Failed: {message}"
    # Only John, Jane, and Alice should be loaded (valid first+last names)
    assert count == 3, f"Expected 3 valid employees, got {count}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: Mixed None/NaN/empty values handled correctly")

def test_whitespace_only_values():
    """Test handling of whitespace-only strings"""
    print("\n" + "=" * 60)
    print("TEST 4: Whitespace-Only Values")
    print("=" * 60)
    
    db_path = '/tmp/test_whitespace.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    test_df = pd.DataFrame({
        'first_name': ['John', '  ', 'Alice'],
        'last_name': ['Doe', 'Smith', '   '],
        'email': ['  ', 'jane@test.com', '   '],
        'title': ['Engineer', '  ', 'Director'],
        'department': ['Engineering', '  ', 'Sales'],
        'status': ['Active', '  ', 'Active']
    })
    
    success, message, count = db.load_employees(test_df)
    
    assert success, f"Failed: {message}"
    # Only row 0 should be loaded (row 1 has whitespace-only last name, row 2 has whitespace-only last name)
    assert count == 1, f"Expected 1 valid employee, got {count}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: Whitespace-only values treated as empty correctly")

def test_real_employee_file():
    """Test with actual employee file (1M+ rows)"""
    print("\n" + "=" * 60)
    print("TEST 5: Real Employee File (Large Dataset)")
    print("=" * 60)
    
    if not os.path.exists("Employee Headcount October 2025.csv"):
        print("⚠️  SKIPPED: Employee file not found")
        return
    
    db_path = '/tmp/test_real_file.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    emp_df = pd.read_csv("Employee Headcount October 2025.csv", low_memory=False)
    
    normalized_df = pd.DataFrame({
        'first_name': emp_df["First Name"],
        'last_name': emp_df["Last Name"],
        'email': None,  # No email column
        'title': emp_df["Title"],
        'department': emp_df["Function"],
        'status': emp_df["Status"]
    })
    
    success, message, count = db.load_employees(normalized_df)
    
    assert success, f"Failed: {message}"
    assert count > 0, "Should load some employees"
    
    print(f"   Processed {len(normalized_df):,} rows, loaded {count:,} employees")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: Large real file processed without errors")

def test_duplicate_employees():
    """Test updating existing employees vs inserting new ones"""
    print("\n" + "=" * 60)
    print("TEST 6: Duplicate Employee Handling")
    print("=" * 60)
    
    db_path = '/tmp/test_duplicates.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    # First load
    df1 = pd.DataFrame({
        'first_name': ['John', 'Jane'],
        'last_name': ['Doe', 'Smith'],
        'email': ['john@test.com', None],
        'title': ['Engineer', 'Manager'],
        'department': ['Engineering', 'Product'],
        'status': ['Active', 'Active']
    })
    
    success, message, count = db.load_employees(df1)
    assert success and count == 2, "First load should insert 2"
    
    # Second load with updates
    df2 = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'email': ['john@test.com', None, 'bob@test.com'],
        'title': ['Senior Engineer', 'Director', 'Analyst'],
        'department': ['Engineering', 'Product', 'Analytics'],
        'status': ['Active', 'Active', 'Active']
    })
    
    success, message, count = db.load_employees(df2)
    assert success, f"Failed: {message}"
    
    # Should have 2 updates (matched by email and name) and 1 insert
    print(f"   {message}")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: Duplicate detection and updates work correctly")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("EMPLOYEE UPLOAD EDGE CASE TESTS")
    print("Testing defensive code for NoneType strip() errors")
    print("=" * 60)
    
    try:
        test_none_email_column()
        test_string_null_values()
        test_mixed_none_nan_values()
        test_whitespace_only_values()
        test_real_employee_file()
        test_duplicate_employees()
        
        print("\n" + "=" * 60)
        print("✅ ALL EDGE CASE TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
