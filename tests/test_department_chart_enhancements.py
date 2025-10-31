"""
Test suite for Department Usage Comparison Chart Enhancements

Tests the following enhancements:
1. Message type breakdown in department statistics
2. Department user drilldown data aggregation
3. Stacked bar chart data structure
"""

import pandas as pd
import sys
import os
from datetime import datetime

def test_dept_message_type_breakdown():
    """Test that department statistics include message type breakdown."""
    print("\n🧪 Testing Department Message Type Breakdown...")
    
    # Create test data with multiple message types
    test_data = pd.DataFrame({
        'department': ['Finance', 'Finance', 'IT', 'IT'],
        'user_id': ['user1', 'user2', 'user3', 'user4'],
        'email': ['user1@test.com', 'user2@test.com', 'user3@test.com', 'user4@test.com'],
        'user_name': ['User 1', 'User 2', 'User 3', 'User 4'],
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages', 'BlueFlame Messages'],
        'usage_count': [100, 50, 200, 75],
        'date': ['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-01']
    })
    
    # Calculate department statistics with message type breakdown
    dept_stats = test_data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage']
    
    # Calculate message type breakdown for each department
    dept_message_breakdown = test_data.groupby(['department', 'feature_used'])['usage_count'].sum().reset_index()
    dept_message_pivot = dept_message_breakdown.pivot(index='department', columns='feature_used', values='usage_count').fillna(0)
    
    # Merge message type breakdown with dept_stats
    for col in dept_message_pivot.columns:
        dept_stats = dept_stats.merge(
            dept_message_pivot[[col]].reset_index().rename(columns={'department': 'Department', col: col}),
            on='Department',
            how='left'
        )
        dept_stats[col] = dept_stats[col].fillna(0)
    
    # Verify Finance department has correct breakdown
    finance_row = dept_stats[dept_stats['Department'] == 'Finance'].iloc[0]
    assert finance_row['ChatGPT Messages'] == 100, f"Expected 100 ChatGPT messages, got {finance_row['ChatGPT Messages']}"
    assert finance_row['Tool Messages'] == 50, f"Expected 50 Tool messages, got {finance_row['Tool Messages']}"
    assert finance_row['Total Usage'] == 150, f"Expected 150 total messages, got {finance_row['Total Usage']}"
    
    # Verify IT department has correct breakdown
    it_row = dept_stats[dept_stats['Department'] == 'IT'].iloc[0]
    assert it_row['ChatGPT Messages'] == 200, f"Expected 200 ChatGPT messages, got {it_row['ChatGPT Messages']}"
    assert it_row.get('BlueFlame Messages', 0) == 75, f"Expected 75 BlueFlame messages, got {it_row.get('BlueFlame Messages', 0)}"
    
    print(f"✅ Message type breakdown calculated correctly")
    print(f"   Finance: ChatGPT={finance_row['ChatGPT Messages']}, Tool={finance_row['Tool Messages']}")
    print(f"   IT: ChatGPT={it_row['ChatGPT Messages']}, BlueFlame={it_row.get('BlueFlame Messages', 0)}")
    return True

def test_department_user_drilldown():
    """Test that user-level statistics can be aggregated for a department."""
    print("\n🧪 Testing Department User Drilldown...")
    
    # Create test data for department drilldown
    test_data = pd.DataFrame({
        'department': ['Finance', 'Finance', 'Finance', 'IT'],
        'email': ['user1@test.com', 'user1@test.com', 'user2@test.com', 'user3@test.com'],
        'user_name': ['User 1', 'User 1', 'User 2', 'User 3'],
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages', 'ChatGPT Messages'],
        'usage_count': [100, 50, 200, 75],
        'date': ['2024-01-01', '2024-01-15', '2024-01-10', '2024-01-05']
    })
    
    # Get users for Finance department
    dept_users = test_data[test_data['department'] == 'Finance'].copy()
    
    # Aggregate by user
    user_stats = dept_users.groupby(['email', 'user_name']).agg({
        'usage_count': 'sum',
        'date': ['min', 'max']
    }).reset_index()
    
    # Flatten multi-level columns
    user_stats.columns = ['email', 'user_name', 'total_messages', 'first_active', 'last_active']
    
    # Get message type breakdown for each user
    message_types = dept_users['feature_used'].unique()
    for msg_type in message_types:
        user_msg_type = dept_users[dept_users['feature_used'] == msg_type].groupby('email')['usage_count'].sum()
        user_stats[msg_type] = user_stats['email'].map(user_msg_type).fillna(0).astype(int)
    
    # Verify user1 has correct aggregation
    user1 = user_stats[user_stats['email'] == 'user1@test.com'].iloc[0]
    assert user1['total_messages'] == 150, f"Expected 150 total messages, got {user1['total_messages']}"
    assert user1['ChatGPT Messages'] == 100, f"Expected 100 ChatGPT messages, got {user1['ChatGPT Messages']}"
    assert user1['Tool Messages'] == 50, f"Expected 50 Tool messages, got {user1['Tool Messages']}"
    
    # Verify user2 has correct aggregation
    user2 = user_stats[user_stats['email'] == 'user2@test.com'].iloc[0]
    assert user2['total_messages'] == 200, f"Expected 200 total messages, got {user2['total_messages']}"
    
    print(f"✅ User drilldown aggregation works correctly")
    print(f"   User 1: {user1['total_messages']} total (ChatGPT={user1['ChatGPT Messages']}, Tool={user1['Tool Messages']})")
    print(f"   User 2: {user2['total_messages']} total")
    return True

def test_stacked_bar_data_structure():
    """Test that data structure supports stacked bar chart."""
    print("\n🧪 Testing Stacked Bar Data Structure...")
    
    # Create test data
    test_data = pd.DataFrame({
        'department': ['Finance', 'Finance', 'IT', 'IT'],
        'user_id': ['user1', 'user2', 'user3', 'user4'],
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages', 'Project Messages'],
        'usage_count': [100, 50, 200, 75]
    })
    
    # Create department stats with message breakdown
    dept_stats = test_data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage']
    
    # Calculate message type breakdown
    dept_message_breakdown = test_data.groupby(['department', 'feature_used'])['usage_count'].sum().reset_index()
    dept_message_pivot = dept_message_breakdown.pivot(index='department', columns='feature_used', values='usage_count').fillna(0)
    
    # Merge message type breakdown
    for col in dept_message_pivot.columns:
        dept_stats = dept_stats.merge(
            dept_message_pivot[[col]].reset_index().rename(columns={'department': 'Department', col: col}),
            on='Department',
            how='left'
        )
        dept_stats[col] = dept_stats[col].fillna(0)
    
    # Get message type columns for stacking
    message_type_cols = [col for col in dept_stats.columns 
                       if col not in ['Department', 'Active Users', 'Total Usage']]
    
    # Verify we have the expected message types
    assert len(message_type_cols) > 0, "No message type columns found"
    assert 'ChatGPT Messages' in message_type_cols, "ChatGPT Messages not in message type columns"
    
    # Verify that sum of message types equals total usage
    for _, row in dept_stats.iterrows():
        msg_sum = sum(row[col] for col in message_type_cols)
        assert abs(msg_sum - row['Total Usage']) < 0.01, f"Message type sum {msg_sum} != Total Usage {row['Total Usage']}"
    
    print(f"✅ Stacked bar data structure is valid")
    print(f"   Message types found: {message_type_cols}")
    print(f"   Verification: Sum of message types equals Total Usage")
    return True

def run_all_tests():
    """Run all department chart enhancement tests."""
    print("\n" + "=" * 60)
    print("🧪 Department Chart Enhancement Test Suite")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Message Type Breakdown", test_dept_message_type_breakdown()))
    except Exception as e:
        print(f"❌ Message Type Breakdown test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Message Type Breakdown", False))
    
    try:
        results.append(("Department User Drilldown", test_department_user_drilldown()))
    except Exception as e:
        print(f"❌ Department User Drilldown test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Department User Drilldown", False))
    
    try:
        results.append(("Stacked Bar Data Structure", test_stacked_bar_data_structure()))
    except Exception as e:
        print(f"❌ Stacked Bar Data Structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Stacked Bar Data Structure", False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
