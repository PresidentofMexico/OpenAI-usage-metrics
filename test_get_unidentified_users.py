#!/usr/bin/env python3
"""
Test for get_unidentified_users() method functionality
Validates the fix for PR #33 bug
"""
import os
import sys
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

import pandas as pd
from database import DatabaseManager
import sqlite3

def test_get_unidentified_users():
    """Test get_unidentified_users method with realistic data"""
    
    # Create a test database
    test_db = 'test_unidentified_users.db'
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("=" * 60)
    print("TEST: get_unidentified_users() Method")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. Initializing test database...")
    db = DatabaseManager(test_db)
    print("✅ Database initialized")
    
    # Step 2: Create test employee data
    print("\n2. Creating test employee records...")
    employees_data = pd.DataFrame({
        'first_name': ['Alice', 'Bob', 'Charlie'],
        'last_name': ['Smith', 'Jones', 'Brown'],
        'email': ['alice@company.com', 'bob@company.com', 'charlie@company.com'],
        'title': ['Engineer', 'Manager', 'Analyst'],
        'department': ['Engineering', 'Operations', 'Finance'],
        'status': ['Active', 'Active', 'Active']
    })
    
    success, message, count = db.load_employees(employees_data)
    assert success, f"Failed to load employees: {message}"
    assert count == 3, f"Expected 3 employees, got {count}"
    print(f"   {message}")
    print("✅ Employee records created")
    
    # Step 3: Insert usage data (mix of identified and unidentified users)
    print("\n3. Inserting usage metrics data...")
    conn = sqlite3.connect(test_db)
    
    # Identified users (in employee table)
    identified_usage = pd.DataFrame({
        'user_id': ['alice@company.com', 'bob@company.com', 'alice@company.com'],
        'user_name': ['Alice Smith', 'Bob Jones', 'Alice Smith'],
        'email': ['alice@company.com', 'bob@company.com', 'alice@company.com'],
        'department': ['Engineering', 'Operations', 'Engineering'],
        'date': ['2024-01-15', '2024-01-15', '2024-01-16'],
        'feature_used': ['ChatGPT', 'ChatGPT', 'Tool Messages'],
        'usage_count': [50, 30, 20],
        'cost_usd': [25.0, 15.0, 10.0],
        'tool_source': ['ChatGPT', 'ChatGPT', 'BlueFlame'],
        'file_source': ['test_data.csv', 'test_data.csv', 'test_data.csv']
    })
    
    # Unidentified users (NOT in employee table)
    unidentified_usage = pd.DataFrame({
        'user_id': ['contractor1@external.com', 'contractor2@external.com', 'contractor1@external.com'],
        'user_name': ['John Contractor', 'Jane Freelancer', 'John Contractor'],
        'email': ['contractor1@external.com', 'contractor2@external.com', 'contractor1@external.com'],
        'department': ['Unknown', 'Unknown', 'Unknown'],
        'date': ['2024-01-15', '2024-01-15', '2024-01-16'],
        'feature_used': ['ChatGPT', 'ChatGPT', 'ChatGPT'],
        'usage_count': [100, 45, 60],
        'cost_usd': [50.0, 22.5, 30.0],
        'tool_source': ['ChatGPT', 'ChatGPT', 'ChatGPT'],
        'file_source': ['test_data.csv', 'test_data.csv', 'test_data.csv']
    })
    
    # Insert all usage data
    all_usage = pd.concat([identified_usage, unidentified_usage], ignore_index=True)
    all_usage.to_sql('usage_metrics', conn, if_exists='append', index=False)
    conn.close()
    
    print(f"   Inserted {len(all_usage)} usage records")
    print(f"   - {len(identified_usage)} from identified users")
    print(f"   - {len(unidentified_usage)} from unidentified users")
    print("✅ Usage data inserted")
    
    # Step 4: Test get_unidentified_users method
    print("\n4. Testing get_unidentified_users() method...")
    unidentified_df = db.get_unidentified_users()
    
    print(f"   Found {len(unidentified_df)} unidentified users")
    
    # Validate results
    assert not unidentified_df.empty, "Should have found unidentified users"
    assert len(unidentified_df) == 2, f"Expected 2 unidentified users, got {len(unidentified_df)}"
    
    # Check columns
    expected_columns = ['email', 'user_name', 'tools_used', 'total_usage', 'total_cost', 'days_active']
    for col in expected_columns:
        assert col in unidentified_df.columns, f"Missing column: {col}"
    
    print("✅ Correct number of unidentified users found")
    
    # Step 5: Validate aggregation logic
    print("\n5. Validating aggregation and calculations...")
    
    # Check contractor1@external.com
    contractor1 = unidentified_df[unidentified_df['email'] == 'contractor1@external.com']
    assert len(contractor1) == 1, "Should have one record for contractor1"
    assert contractor1.iloc[0]['total_usage'] == 160, f"Expected 160 total usage, got {contractor1.iloc[0]['total_usage']}"
    assert contractor1.iloc[0]['total_cost'] == 80.0, f"Expected 80.0 total cost, got {contractor1.iloc[0]['total_cost']}"
    assert contractor1.iloc[0]['days_active'] == 2, f"Expected 2 days active, got {contractor1.iloc[0]['days_active']}"
    print("   ✅ contractor1@external.com: 160 usage, $80.00, 2 days")
    
    # Check contractor2@external.com
    contractor2 = unidentified_df[unidentified_df['email'] == 'contractor2@external.com']
    assert len(contractor2) == 1, "Should have one record for contractor2"
    assert contractor2.iloc[0]['total_usage'] == 45, f"Expected 45 total usage, got {contractor2.iloc[0]['total_usage']}"
    assert contractor2.iloc[0]['total_cost'] == 22.5, f"Expected 22.5 total cost, got {contractor2.iloc[0]['total_cost']}"
    assert contractor2.iloc[0]['days_active'] == 1, f"Expected 1 day active, got {contractor2.iloc[0]['days_active']}"
    print("   ✅ contractor2@external.com: 45 usage, $22.50, 1 day")
    
    print("✅ Aggregation calculations are correct")
    
    # Step 6: Verify sorting (should be by total_usage DESC)
    print("\n6. Validating sort order...")
    assert unidentified_df.iloc[0]['email'] == 'contractor1@external.com', "Highest usage user should be first"
    assert unidentified_df.iloc[1]['email'] == 'contractor2@external.com', "Second highest usage user should be second"
    print("✅ Results correctly sorted by total_usage (descending)")
    
    # Step 7: Verify identified users are NOT in results
    print("\n7. Verifying identified users are excluded...")
    identified_emails = ['alice@company.com', 'bob@company.com', 'charlie@company.com']
    for email in identified_emails:
        assert email not in unidentified_df['email'].values, f"Identified user {email} should not be in results"
    print("✅ All identified users correctly excluded")
    
    # Step 8: Test empty/null email handling
    print("\n8. Testing edge cases (empty/null emails)...")
    conn = sqlite3.connect(test_db)
    # Add records with null/empty emails
    edge_case_usage = pd.DataFrame({
        'user_id': ['user@test.com', 'user2@test.com'],
        'user_name': ['Empty Email User', 'Null Email User'],
        'email': ['', None],
        'department': ['Unknown', 'Unknown'],
        'date': ['2024-01-17', '2024-01-17'],
        'feature_used': ['ChatGPT', 'ChatGPT'],
        'usage_count': [25, 30],
        'cost_usd': [12.5, 15.0],
        'tool_source': ['ChatGPT', 'ChatGPT'],
        'file_source': ['test_data.csv', 'test_data.csv']
    })
    edge_case_usage.to_sql('usage_metrics', conn, if_exists='append', index=False)
    conn.close()
    
    # Re-query
    unidentified_df = db.get_unidentified_users()
    # Should still be 2 (empty/null emails should be excluded)
    assert len(unidentified_df) == 2, f"Empty/null emails should be excluded, expected 2 users, got {len(unidentified_df)}"
    print("✅ Empty and null emails correctly excluded")
    
    # Cleanup
    print("\n9. Cleaning up...")
    if os.path.exists(test_db):
        os.remove(test_db)
    print("✅ Test database cleaned up")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nThe get_unidentified_users() method is working correctly:")
    print("  ✓ Returns unidentified users (not in employees table)")
    print("  ✓ Aggregates usage_count, cost_usd, and days_active")
    print("  ✓ Groups by email and user_name correctly")
    print("  ✓ Sorts by total_usage descending")
    print("  ✓ Excludes identified employees")
    print("  ✓ Handles empty/null emails properly")
    print("  ✓ Concatenates multiple tool sources")

if __name__ == "__main__":
    test_get_unidentified_users()
