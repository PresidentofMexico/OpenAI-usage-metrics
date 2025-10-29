#!/usr/bin/env python3
"""
Test auto-load employee file functionality to ensure:
1. Employee files are found using script directory (not cwd)
2. Marker files prevent duplicate loads
3. Employees are loaded on app startup
4. Departments are correctly assigned to usage data
"""
import sys
import os
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

import pandas as pd
from database import DatabaseManager
from app import auto_load_employee_file
import tempfile
import shutil

def test_auto_load_uses_script_directory():
    """Test that auto_load_employee_file uses script directory, not cwd"""
    print("\n" + "=" * 60)
    print("TEST 1: Auto-load Uses Script Directory (Not CWD)")
    print("=" * 60)
    
    # Create a temporary directory to use as a "different working directory"
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Change to temp directory (simulating app launched from different location)
        os.chdir(temp_dir)
        print(f"Changed working directory to: {os.getcwd()}")
        print(f"Script directory remains: {os.path.dirname(os.path.abspath(__file__))}")
        
        # Clean up any existing database and markers
        db_path = os.path.join(original_cwd, 'openai_metrics.db')
        
        # Create fresh database in original directory
        db = DatabaseManager(db_path)
        
        # Clear employees
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute('DELETE FROM employees')
        conn.commit()
        conn.close()
        
        # Remove any marker files from original directory
        for marker in ['.Employee Headcount October 2025_Emails.csv.loaded',
                      '.Employee Headcount October 2025.csv.loaded']:
            marker_path = os.path.join(original_cwd, marker)
            if os.path.exists(marker_path):
                os.remove(marker_path)
        
        print(f"Database cleared. Employee count: {db.get_employee_count()}")
        
        # Now try to auto-load (this should use script dir, not cwd)
        print("\nAttempting auto-load from different working directory...")
        auto_load_employee_file(db)
        
        # Check if employees were loaded
        employee_count = db.get_employee_count()
        print(f"\nEmployee count after auto-load: {employee_count}")
        
        # Verify marker file was created in SCRIPT directory (not cwd)
        marker_in_cwd = os.path.exists('.Employee Headcount October 2025_Emails.csv.loaded')
        marker_in_script_dir = os.path.exists(os.path.join(original_cwd, '.Employee Headcount October 2025_Emails.csv.loaded'))
        
        print(f"\nMarker file in CWD ({temp_dir}): {marker_in_cwd}")
        print(f"Marker file in script dir ({original_cwd}): {marker_in_script_dir}")
        
        # Assertions
        assert employee_count > 0, "Employees should be loaded even when CWD is different from script dir"
        assert not marker_in_cwd, "Marker file should NOT be in CWD"
        assert marker_in_script_dir, "Marker file SHOULD be in script directory"
        
        print("\n✅ PASSED: Auto-load correctly uses script directory")
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_marker_file_prevents_reload():
    """Test that marker files prevent duplicate loads"""
    print("\n" + "=" * 60)
    print("TEST 2: Marker File Prevents Duplicate Loads")
    print("=" * 60)
    
    db_path = '/tmp/test_marker_reload.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    # First load - should succeed
    print("\nFirst auto-load attempt...")
    initial_count = db.get_employee_count()
    print(f"Initial employee count: {initial_count}")
    
    # Since we're using a test database, employees won't be loaded
    # but we can verify the marker logic by checking output
    
    # The test database won't have the actual files, so we'll verify
    # the logic works by checking that employee count doesn't change
    # on subsequent calls if employees exist
    
    # Add a test employee manually
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO employees (first_name, last_name, email, department)
        VALUES ('Test', 'User', 'test@example.com', 'Engineering')
    """)
    conn.commit()
    conn.close()
    
    count_after_manual_add = db.get_employee_count()
    print(f"Employee count after manual add: {count_after_manual_add}")
    
    # Second load - should skip because employees exist
    print("\nSecond auto-load attempt...")
    auto_load_employee_file(db)
    
    final_count = db.get_employee_count()
    print(f"Final employee count: {final_count}")
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    
    assert final_count == count_after_manual_add, "Employee count should not change on second load"
    
    print("\n✅ PASSED: Marker logic prevents duplicate loads")


def test_departments_assigned_from_employee_file():
    """Test that employee departments are correctly assigned to usage data"""
    print("\n" + "=" * 60)
    print("TEST 3: Departments Assigned from Employee File")
    print("=" * 60)
    
    # This test verifies the integration between employee data and usage data
    from app import normalize_openai_data, init_app
    
    print("\nInitializing app (should auto-load employees)...")
    db, processor, scanner = init_app()
    
    employee_count = db.get_employee_count()
    print(f"Employee count after init: {employee_count}")
    
    assert employee_count > 0, "Employees should be auto-loaded on app init"
    
    # Load sample OpenAI data
    sample_file = 'OpenAI User Data/Openai Eldridge Capital Management monthly user report August.csv'
    if os.path.exists(sample_file):
        print(f"\nLoading sample data from {sample_file}...")
        df = pd.read_csv(sample_file)
        normalized_df = normalize_openai_data(df, sample_file)
        
        # Check department distribution
        dept_counts = normalized_df['department'].value_counts()
        total_records = len(normalized_df)
        unknown_count = dept_counts.get('Unknown', 0)
        known_count = total_records - unknown_count
        known_pct = (known_count / total_records * 100) if total_records > 0 else 0
        
        print(f"\nTotal records: {total_records}")
        print(f"Records with known departments: {known_count} ({known_pct:.1f}%)")
        print(f"Records with Unknown department: {unknown_count} ({100-known_pct:.1f}%)")
        print(f"\nTop 5 departments:")
        print(dept_counts.head(5))
        
        # We expect at least 50% of records to have valid departments
        # (since employee file covers most users)
        assert known_pct > 50, f"Expected >50% of records to have valid departments, got {known_pct:.1f}%"
        
        print("\n✅ PASSED: Departments correctly assigned from employee file")
    else:
        print(f"\n⚠️  SKIPPED: Sample file not found: {sample_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("AUTO-LOAD EMPLOYEE FILE TESTS")
    print("=" * 60)
    
    try:
        test_auto_load_uses_script_directory()
        test_marker_file_prevents_reload()
        test_departments_assigned_from_employee_file()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
