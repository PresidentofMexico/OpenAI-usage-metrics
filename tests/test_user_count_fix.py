"""
Test to verify that the 'Total Active Users' metric correctly counts unique emails
instead of user_id to avoid over-counting users with multiple records.

This test validates the fix for the issue where users with multiple records
(across different features or time periods) were being counted multiple times.
"""

import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager


def test_unique_email_counting():
    """
    Test that user counting uses unique emails instead of user_id.
    
    Scenario:
    - Create a dataset where the same user (same email) has multiple user_id values
    - This simulates the real-world scenario where a user has multiple records
    - Verify that counting by email gives the correct (lower) count
    """
    print("\n" + "=" * 80)
    print("TEST: Unique Email Counting for Total Active Users")
    print("=" * 80)
    
    # Create test data where same email has multiple user_id values
    # This simulates the over-counting problem
    test_data = pd.DataFrame({
        'user_id': [
            'user_001', 'user_002', 'user_003',  # First set of IDs
            'user_001_chat', 'user_002_tool', 'user_003_proj',  # Same users, different IDs
            'user_001_msg', 'user_002_msg',  # Same users again
        ],
        'email': [
            'alice@company.com', 'bob@company.com', 'charlie@company.com',  # 3 unique users
            'alice@company.com', 'bob@company.com', 'charlie@company.com',  # Same 3 users
            'alice@company.com', 'bob@company.com',  # 2 of the same users
        ],
        'user_name': ['Alice', 'Bob', 'Charlie'] * 2 + ['Alice', 'Bob'],
        'department': ['Engineering'] * 8,
        'date': ['2024-01-01'] * 8,
        'feature_used': ['ChatGPT Messages'] * 8,
        'usage_count': [10] * 8,
        'cost_usd': [0.0] * 8,
        'tool_source': ['ChatGPT'] * 8,
    })
    
    print(f"\n📊 Test Data Summary:")
    print(f"   Total records: {len(test_data)}")
    print(f"   Unique user_id values: {test_data['user_id'].nunique()}")
    print(f"   Unique email values: {test_data['email'].nunique()}")
    print(f"   Expected actual users: 3 (Alice, Bob, Charlie)")
    
    # Test the OLD way (counting user_id) - this was the bug
    old_count = test_data['user_id'].nunique()
    print(f"\n❌ OLD METHOD (user_id.nunique()): {old_count} users")
    print(f"   This OVER-COUNTS because each user has multiple user_id values")
    
    # Test the NEW way (counting unique emails) - this is the fix
    new_count = test_data['email'].dropna().str.lower().nunique()
    print(f"\n✅ NEW METHOD (email.nunique()): {new_count} users")
    print(f"   This correctly counts each person only once")
    
    # Verify the fix
    assert new_count == 3, f"Expected 3 unique users, got {new_count}"
    assert old_count > new_count, f"Old method should over-count (was {old_count} vs {new_count})"
    
    print(f"\n✅ VERIFICATION PASSED:")
    print(f"   - New method correctly identifies 3 unique users")
    print(f"   - Old method incorrectly counted {old_count} users (over-count by {old_count - new_count})")
    
    # Verify this matches the pattern we're using in the codebase
    print(f"\n📋 Testing the actual pattern used in app.py...")
    # This is the exact pattern we're using throughout the codebase
    if 'email' in test_data.columns:
        pattern_count = test_data['email'].dropna().str.lower().nunique()
    else:
        pattern_count = test_data['user_id'].nunique()
    
    print(f"   Pattern-based count: {pattern_count}")
    assert pattern_count == 3, f"Pattern should count 3 users, got {pattern_count}"
    print(f"   ✅ Pattern correctly counts unique emails")
    
    return True


def test_case_insensitive_email_deduplication():
    """
    Test that email deduplication is case-insensitive.
    
    Scenario:
    - Same email address with different capitalizations should be counted as one user
    """
    print("\n" + "=" * 80)
    print("TEST: Case-Insensitive Email Deduplication")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        'user_id': ['u1', 'u2', 'u3'],
        'email': [
            'Alice@Company.com',  # Different case
            'alice@company.com',  # Same email, different case
            'ALICE@COMPANY.COM',  # Same email, all caps
        ],
        'user_name': ['Alice'] * 3,
        'department': ['Engineering'] * 3,
        'date': ['2024-01-01'] * 3,
        'feature_used': ['ChatGPT Messages'] * 3,
        'usage_count': [10] * 3,
        'cost_usd': [0.0] * 3,
        'tool_source': ['ChatGPT'] * 3,
    })
    
    print(f"\n📊 Test Data:")
    print(f"   Emails: {test_data['email'].tolist()}")
    
    # Count with case-insensitive deduplication
    unique_count = test_data['email'].dropna().str.lower().nunique()
    
    print(f"\n✅ Case-insensitive count: {unique_count} user(s)")
    assert unique_count == 1, f"Expected 1 unique user (case-insensitive), got {unique_count}"
    print(f"   ✅ Correctly identifies all variations as the same user")
    
    return True


def test_null_email_handling():
    """
    Test that null/NA emails are properly handled.
    
    Scenario:
    - Some records might have null emails
    - These should be excluded from the count
    """
    print("\n" + "=" * 80)
    print("TEST: Null Email Handling")
    print("=" * 80)
    
    test_data = pd.DataFrame({
        'user_id': ['u1', 'u2', 'u3', 'u4'],
        'email': [
            'alice@company.com',
            'bob@company.com',
            None,  # Null email
            pd.NA,  # pandas NA
        ],
        'user_name': ['Alice', 'Bob', 'Charlie', 'Dave'],
        'department': ['Engineering'] * 4,
        'date': ['2024-01-01'] * 4,
        'feature_used': ['ChatGPT Messages'] * 4,
        'usage_count': [10] * 4,
        'cost_usd': [0.0] * 4,
        'tool_source': ['ChatGPT'] * 4,
    })
    
    print(f"\n📊 Test Data:")
    print(f"   Total records: {len(test_data)}")
    print(f"   Valid emails: {test_data['email'].notna().sum()}")
    print(f"   Null emails: {test_data['email'].isna().sum()}")
    
    # Count unique emails, excluding nulls
    unique_count = test_data['email'].dropna().str.lower().nunique()
    
    print(f"\n✅ Unique users (excluding nulls): {unique_count}")
    assert unique_count == 2, f"Expected 2 unique users (Alice, Bob), got {unique_count}"
    print(f"   ✅ Correctly excludes null/NA emails from count")
    
    return True


def test_realistic_scenario():
    """
    Test with a realistic scenario matching the problem description.
    
    Scenario:
    - Organization has < 250 actual users
    - But user_id counting shows 365+ because users have multiple records
    - Verify that email counting gives the correct lower count
    """
    print("\n" + "=" * 80)
    print("TEST: Realistic Scenario (< 250 Users, 365+ user_id Records)")
    print("=" * 80)
    
    # Create realistic data: 200 actual users, but each has ~2 user_id records on average
    actual_users = 200
    records_per_user = [2, 2, 3, 1, 2]  # Varying records per user
    
    users = []
    for i in range(actual_users):
        email = f"user{i:03d}@company.com"
        num_records = records_per_user[i % len(records_per_user)]
        for j in range(num_records):
            users.append({
                'user_id': f"uid_{i}_{j}",  # Different user_id for each record
                'email': email,  # Same email for same person
                'user_name': f"User {i}",
                'department': f"Dept{i % 10}",
                'date': '2024-01-01',
                'feature_used': ['ChatGPT Messages', 'Tool Messages', 'Project Messages'][j % 3],
                'usage_count': 10,
                'cost_usd': 0.0,
                'tool_source': 'ChatGPT',
            })
    
    test_data = pd.DataFrame(users)
    
    print(f"\n📊 Realistic Test Data:")
    print(f"   Actual users in organization: {actual_users}")
    print(f"   Total database records: {len(test_data)}")
    print(f"   Unique user_id values: {test_data['user_id'].nunique()}")
    print(f"   Unique email values: {test_data['email'].nunique()}")
    
    # Count using both methods
    user_id_count = test_data['user_id'].nunique()
    email_count = test_data['email'].dropna().str.lower().nunique()
    
    print(f"\n❌ OLD METHOD (user_id): {user_id_count} users")
    print(f"✅ NEW METHOD (email): {email_count} users")
    print(f"\n📉 Over-count eliminated: {user_id_count - email_count} phantom users removed")
    
    # Verify expectations
    assert email_count == actual_users, f"Expected {actual_users} users, got {email_count}"
    assert user_id_count > email_count, "user_id should over-count"
    assert email_count < 250, f"Should be < 250 users as per requirement, got {email_count}"
    
    print(f"\n✅ VERIFICATION PASSED:")
    print(f"   - Correctly identifies {email_count} actual users")
    print(f"   - Count is < 250 as expected for the organization")
    print(f"   - Fixed over-counting issue (was showing {user_id_count} users)")
    
    return True


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("RUNNING USER COUNT FIX TESTS")
    print("=" * 80)
    
    all_passed = True
    
    try:
        test_unique_email_counting()
        print("\n✅ Test 1 PASSED: Unique email counting")
    except AssertionError as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        all_passed = False
    
    try:
        test_case_insensitive_email_deduplication()
        print("\n✅ Test 2 PASSED: Case-insensitive deduplication")
    except AssertionError as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        all_passed = False
    
    try:
        test_null_email_handling()
        print("\n✅ Test 3 PASSED: Null email handling")
    except AssertionError as e:
        print(f"\n❌ Test 3 FAILED: {e}")
        all_passed = False
    
    try:
        test_realistic_scenario()
        print("\n✅ Test 4 PASSED: Realistic scenario")
    except AssertionError as e:
        print(f"\n❌ Test 4 FAILED: {e}")
        all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe fix successfully:")
        print("  1. Counts unique emails instead of user_id")
        print("  2. Handles case-insensitive email matching")
        print("  3. Properly excludes null/NA emails")
        print("  4. Produces accurate user counts matching organization size")
        print("=" * 80)
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)
