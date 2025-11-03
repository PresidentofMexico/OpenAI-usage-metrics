#!/usr/bin/env python3
"""
Comprehensive test for employee master file integration
"""
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager
from data_processor import DataProcessor

def test_employee_integration():
    """Test complete employee integration workflow"""
    
    # Clean database
    db_path = 'test_full_integration.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("=" * 60)
    print("EMPLOYEE MASTER FILE INTEGRATION TEST")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager(db_path)
    processor = DataProcessor(db)
    print("✅ Database initialized")
    
    # Step 2: Load employee master file
    print("\n2. Loading employee master file...")
    emp_df = pd.read_csv('/tmp/test_employees.csv')
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
    assert success, "Employee loading failed"
    assert count == 10, f"Expected 10 employees, got {count}"
    print("✅ Employee master file loaded")
    
    # Step 3: Verify employee departments
    print("\n3. Verifying employee departments...")
    depts = db.get_employee_departments()
    print(f"   Found departments: {', '.join(depts)}")
    assert len(depts) > 0, "No departments found"
    print("✅ Employee departments verified")
    
    # Step 4: Create test usage data (mix of employees and non-employees)
    print("\n4. Creating test usage data...")
    usage_data = {
        'email': [
            'john.doe@company.com',       # Employee in Engineering
            'jane.smith@company.com',     # Employee in Product
            'contractor@external.com',    # Not an employee
            'alice.williams@company.com', # Employee in Marketing
        ],
        'name': ['John Doe', 'Jane Smith', 'External Contractor', 'Alice Williams'],
        'department': ['["engineering"]', '["product"]', '["unknown"]', '["marketing"]'],
        'period_start': ['2024-09-01', '2024-09-01', '2024-09-01', '2024-09-01'],
        'messages': [100, 150, 80, 120],
        'gpt_messages': [20, 30, 10, 15]
    }
    
    # Manually normalize (simulating what app.py does)
    normalized_records = []
    for idx, row in pd.DataFrame(usage_data).iterrows():
        user_email = row['email']
        employee = db.get_employee_by_email(user_email)
        
        if employee:
            dept = employee['department']
            user_name = f"{employee['first_name']} {employee['last_name']}"
        else:
            dept = 'Unknown'
            user_name = row['name']
        
        # Create record
        normalized_records.append({
            'user_id': user_email,
            'user_name': user_name,
            'email': user_email,
            'department': dept,
            'date': row['period_start'],
            'feature_used': 'ChatGPT Messages',
            'usage_count': row['messages'],
            'cost_usd': row['messages'] * 0.02,
            'tool_source': 'ChatGPT',
            'file_source': 'test_usage.csv'
        })
    
    normalized_df = pd.DataFrame(normalized_records)
    print("   Sample normalized data:")
    print(normalized_df[['email', 'user_name', 'department', 'usage_count']].to_string(index=False))
    print("✅ Test usage data created and normalized")
    
    # Step 5: Verify department assignments
    print("\n5. Verifying department assignments...")
    for idx, row in normalized_df.iterrows():
        email = row['email']
        dept = row['department']
        employee = db.get_employee_by_email(email)
        
        if employee:
            assert dept == employee['department'], f"Department mismatch for {email}"
            print(f"   ✅ {email}: {dept} (from employee roster)")
        else:
            assert dept == 'Unknown', f"Expected 'Unknown' for {email}, got {dept}"
            print(f"   ⚠️  {email}: {dept} (not in employee roster)")
    
    print("✅ All department assignments verified")
    
    # Step 6: Insert into database
    print("\n6. Inserting usage data into database...")
    success, msg = processor.process_monthly_data(normalized_df, 'test_usage.csv')
    assert success, f"Failed to insert data: {msg}"
    print(f"   {msg}")
    print("✅ Usage data inserted")
    
    # Step 7: Test unidentified users query
    print("\n7. Querying unidentified users...")
    unidentified = db.get_unidentified_users()
    print(f"   Found {len(unidentified)} unidentified user(s)")
    
    if not unidentified.empty:
        print("   Unidentified users:")
        for idx, row in unidentified.iterrows():
            print(f"      - {row['email']}: {row['user_name']} ({int(row['total_usage'])} messages)")
    
    assert len(unidentified) == 1, f"Expected 1 unidentified user, got {len(unidentified)}"
    assert unidentified.iloc[0]['email'] == 'contractor@external.com', "Wrong unidentified user"
    print("✅ Unidentified users correctly identified")
    
    # Step 8: Test employee count
    print("\n8. Verifying employee count...")
    emp_count = db.get_employee_count()
    print(f"   Total employees: {emp_count}")
    assert emp_count == 10, f"Expected 10 employees, got {emp_count}"
    print("✅ Employee count verified")
    
    # Step 9: Verify all users
    print("\n9. Verifying all users in usage data...")
    all_data = db.get_all_data()
    unique_users = all_data['email'].nunique()
    print(f"   Total unique users in usage data: {unique_users}")
    assert unique_users == 4, f"Expected 4 users, got {unique_users}"
    print("✅ All users verified")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
        print("\n🧹 Test database cleaned up")

if __name__ == '__main__':
    test_employee_integration()
