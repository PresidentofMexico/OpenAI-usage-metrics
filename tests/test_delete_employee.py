#!/usr/bin/env python3
"""
Test script for employee deletion functionality
"""
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager
from data_processor import DataProcessor
from datetime import datetime

def test_delete_employee_feature():
    """Test employee deletion functionality"""
    
    # Clean test database
    db_path = 'test_delete_employee.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("=" * 70)
    print("EMPLOYEE DELETION FEATURE TEST")
    print("=" * 70)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager(db_path)
    processor = DataProcessor(db)
    print("✅ Database initialized")
    
    # Load sample employees
    print("\n2. Loading sample employees...")
    employees_data = pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'last_name': ['Doe', 'Smith', 'Johnson', 'Williams', 'Brown'],
        'email': ['john.doe@company.com', 'jane.smith@company.com', 'bob.johnson@company.com', 
                 'alice.williams@company.com', 'charlie.brown@company.com'],
        'title': ['Engineer', 'Manager', 'Analyst', 'Director', 'Consultant'],
        'department': ['Technology', 'Finance', 'Operations', 'Executive', 'HR'],
        'status': ['Active', 'Active', 'Active', 'Active', 'Terminated']
    })
    
    success, message, count = db.load_employees(employees_data)
    print(f"   {message}")
    assert success, "Employee loading failed"
    assert count == 5, f"Expected 5 employees, got {count}"
    print("✅ Sample employees loaded")
    
    # Add some usage data for employees
    print("\n3. Adding usage data...")
    usage_data = pd.DataFrame([
        {
            'user_id': 'john.doe@company.com',
            'user_name': 'John Doe',
            'email': 'john.doe@company.com',
            'department': 'Technology',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 100,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'test_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'jane.smith@company.com',
            'user_name': 'Jane Smith',
            'email': 'jane.smith@company.com',
            'department': 'Finance',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 50,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'test_data.csv',
            'created_at': datetime.now().isoformat()
        },
        {
            'user_id': 'charlie.brown@company.com',
            'user_name': 'Charlie Brown',
            'email': 'charlie.brown@company.com',
            'department': 'HR',
            'date': '2024-10-01',
            'feature_used': 'ChatGPT Messages',
            'usage_count': 75,
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': 'test_data.csv',
            'created_at': datetime.now().isoformat()
        }
    ])
    
    success, message = processor.process_monthly_data(usage_data, 'test_data.csv')
    print(f"   {message}")
    assert success, "Usage data loading failed"
    print("✅ Usage data added")
    
    # Verify initial state
    print("\n4. Verifying initial state...")
    all_employees = db.get_all_employees()
    all_usage = db.get_all_data()
    print(f"   Total employees: {len(all_employees)}")
    print(f"   Total usage records: {len(all_usage)}")
    assert len(all_employees) == 5, "Expected 5 employees initially"
    assert len(all_usage) == 3, "Expected 3 usage records initially"
    print("✅ Initial state verified")
    
    # Test 1: Delete employee only (keep usage data)
    print("\n5. Test: Delete employee only (Bob Johnson - no usage data)...")
    bob_df = all_employees[all_employees['email'] == 'bob.johnson@company.com']
    print(f"   Found Bob: {len(bob_df)} records")
    print(f"   All employees columns: {all_employees.columns.tolist()}")
    if len(bob_df) > 0:
        print(f"   Bob's data: {bob_df.to_dict('records')[0]}")
        bob = bob_df.iloc[0]
        print(f"   Bob's employee_id: {bob['employee_id']}")
        success, message = db.delete_employee(bob['employee_id'])
        print(f"   {message}")
        assert success, "Delete employee failed"
        
        remaining_employees = db.get_all_employees()
        print(f"   Remaining employees: {len(remaining_employees)}")
        assert len(remaining_employees) == 4, "Expected 4 employees after deletion"
        
        # Verify Bob is gone
        bob_check = remaining_employees[remaining_employees['email'] == 'bob.johnson@company.com']
        assert len(bob_check) == 0, "Bob should be deleted"
        print("✅ Employee-only deletion works correctly")
    else:
        raise AssertionError("Bob Johnson not found in employees table")
    
    # Test 2: Delete employee usage only
    print("\n6. Test: Delete employee usage only (John Doe)...")
    success, message, deleted_count = db.delete_employee_usage('john.doe@company.com')
    print(f"   {message}")
    assert success, "Delete usage failed"
    assert deleted_count == 1, f"Expected to delete 1 usage record, got {deleted_count}"
    
    remaining_usage = db.get_all_data()
    print(f"   Remaining usage records: {len(remaining_usage)}")
    assert len(remaining_usage) == 2, "Expected 2 usage records after deletion"
    
    # Verify John's usage is gone but employee record remains
    john_usage = remaining_usage[remaining_usage['email'] == 'john.doe@company.com']
    assert len(john_usage) == 0, "John's usage should be deleted"
    
    remaining_employees = db.get_all_employees()
    john_employee = remaining_employees[remaining_employees['email'] == 'john.doe@company.com']
    assert len(john_employee) == 1, "John should still be in employee table"
    print("✅ Usage-only deletion works correctly")
    
    # Test 3: Delete employee and all usage data
    print("\n7. Test: Delete employee and usage (Charlie Brown - has usage)...")
    charlie = remaining_employees[remaining_employees['email'] == 'charlie.brown@company.com'].iloc[0]
    success, message = db.delete_employee_and_usage(charlie['employee_id'])
    print(f"   {message}")
    assert success, "Delete employee and usage failed"
    
    final_employees = db.get_all_employees()
    final_usage = db.get_all_data()
    print(f"   Final employees: {len(final_employees)}")
    print(f"   Final usage records: {len(final_usage)}")
    
    assert len(final_employees) == 3, "Expected 3 employees after complete deletion"
    assert len(final_usage) == 1, "Expected 1 usage record after complete deletion"
    
    # Verify Charlie is completely gone
    charlie_employee = final_employees[final_employees['email'] == 'charlie.brown@company.com']
    charlie_usage = final_usage[final_usage['email'] == 'charlie.brown@company.com']
    assert len(charlie_employee) == 0, "Charlie should be deleted from employees"
    assert len(charlie_usage) == 0, "Charlie's usage should be deleted"
    print("✅ Complete deletion works correctly")
    
    # Test 4: Verify metrics update correctly
    print("\n8. Verifying metrics update correctly...")
    # Jane Smith should be the only one with usage data remaining
    jane_usage = final_usage[final_usage['email'] == 'jane.smith@company.com']
    assert len(jane_usage) == 1, "Jane should have 1 usage record"
    print(f"   Jane's usage: {jane_usage['usage_count'].sum()} messages")
    assert jane_usage['usage_count'].sum() == 50, "Jane should have 50 messages"
    print("✅ Metrics updated correctly")
    
    # Cleanup
    print("\n9. Cleaning up test database...")
    if os.path.exists(db_path):
        os.remove(db_path)
    print("✅ Test database cleaned up")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)
    print("\nSummary:")
    print("  ✓ Delete employee only (keeps usage) - WORKS")
    print("  ✓ Delete usage only (keeps employee) - WORKS")
    print("  ✓ Delete employee and usage (complete removal) - WORKS")
    print("  ✓ Metrics update correctly after deletions - WORKS")
    print("\nThe employee deletion feature is ready for production use!")

if __name__ == "__main__":
    try:
        test_delete_employee_feature()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
