"""
Test suite for BlueFlame 'All Users' table processing

This test validates the fix for the bug where users appearing in:
- 'All Users Total'
- 'All Increasing Users'
- 'All Decreasing Users'

were being filtered out and not processed, while only users in:
- 'Top 20 Users Total'
- 'Top 10 Increasing Users'
- 'Top 10 Decreasing Users'

were being captured.

This bug caused John Boddiford (and others) to show 0 BlueFlame messages
in the dashboard despite having actual usage data.
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from data_processor import DataProcessor
from cost_calculator import EnterpriseCostCalculator


# Mock database manager for testing
class MockDB:
    pass


def test_all_users_table_processing():
    """
    Test that users in 'All Users Total' tables are processed correctly.
    
    This is a regression test for the bug where John Boddiford's data
    was being filtered out.
    """
    print("\n🧪 Testing 'All Users' Table Processing...")
    
    processor = DataProcessor(MockDB())
    
    # Create test data mimicking the October 2025 CSV structure
    # This includes users in 'All Users Total', 'All Increasing Users', etc.
    test_data = pd.DataFrame({
        'Table': [
            'Overall Monthly Trends', 'Overall Monthly Trends',
            'All Users Total', 'All Users Total', 'All Users Total',
            'All Increasing Users', 'All Increasing Users',
            'All Decreasing Users'
        ],
        'Rank': ['', '', 1, 2, 3, 1, 2, 1],
        'User ID': [
            '', '',
            'john.boddiford@eldridge.com', 'alice.smith@eldridge.com', 'bob.jones@eldridge.com',
            'john.boddiford@eldridge.com', 'alice.smith@eldridge.com',
            'bob.jones@eldridge.com'
        ],
        'Metric': ['Total Messages', 'Monthly Active Users (MAUs)', '', '', '', '', '', ''],
        '25-Aug': ['', '', '', 100, 50, '', 100, 50],
        '25-Sep': [3475, 30, 44, 150, 75, 44, 150, 75],
        '25-Oct': [3872, 62, 858, 200, 100, 858, 200, 100],
        'MoM Var Sep-25': ['', '', '', '', '', '', '', ''],
        'MoM Var Oct-25': ['', '', 814, 50, 25, 814, 50, 25]
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_october.csv')
    
    # Verify we got results
    assert not result_df.empty, "No data was processed from 'All Users' tables!"
    print(f"✅ Processed {len(result_df)} records from 'All Users' tables")
    
    # Verify John Boddiford's data was captured
    john_data = result_df[result_df['user_id'] == 'john.boddiford@eldridge.com']
    assert not john_data.empty, "John Boddiford's data was NOT captured - BUG STILL EXISTS!"
    print(f"✅ John Boddiford data captured: {len(john_data)} months")
    
    # Verify John has September data (44 messages)
    john_sep = john_data[john_data['date'].str.startswith('2025-09')]
    assert not john_sep.empty, "John's September 2025 data missing!"
    assert john_sep.iloc[0]['usage_count'] == 44, f"John's September usage incorrect: expected 44, got {john_sep.iloc[0]['usage_count']}"
    print(f"✅ John's September 2025 usage: {john_sep.iloc[0]['usage_count']} messages")
    
    # Verify John has October data (858 messages)
    john_oct = john_data[john_data['date'].str.startswith('2025-10')]
    assert not john_oct.empty, "John's October 2025 data missing!"
    assert john_oct.iloc[0]['usage_count'] == 858, f"John's October usage incorrect: expected 858, got {john_oct.iloc[0]['usage_count']}"
    print(f"✅ John's October 2025 usage: {john_oct.iloc[0]['usage_count']} messages")
    
    # Verify other users from 'All Users' tables were also captured
    alice_data = result_df[result_df['user_id'] == 'alice.smith@eldridge.com']
    bob_data = result_df[result_df['user_id'] == 'bob.jones@eldridge.com']
    
    assert not alice_data.empty, "Alice's data was not captured from 'All Users' tables!"
    assert not bob_data.empty, "Bob's data was not captured from 'All Users' tables!"
    print(f"✅ Alice's data: {len(alice_data)} months")
    print(f"✅ Bob's data: {len(bob_data)} months")
    
    return True


def test_all_users_vs_top_users_deduplication():
    """
    Test that when a user appears in both 'Top 20' and 'All Users' tables,
    they are properly deduplicated (not double-counted).
    """
    print("\n🧪 Testing Deduplication Across 'Top Users' and 'All Users' Tables...")
    
    processor = DataProcessor(MockDB())
    
    # Create test data where same user appears in multiple tables
    test_data = pd.DataFrame({
        'Table': [
            'Top 20 Users Total', 'Top 20 Users Total',
            'All Users Total', 'All Users Total',
            'All Increasing Users', 'All Increasing Users'
        ],
        'Rank': [1, 2, 1, 2, 1, 2],
        'User ID': [
            'john.boddiford@eldridge.com', 'alice.smith@eldridge.com',
            'john.boddiford@eldridge.com', 'alice.smith@eldridge.com',  # Same users repeated
            'john.boddiford@eldridge.com', 'alice.smith@eldridge.com'   # Same users again
        ],
        'Metric': ['', '', '', '', '', ''],
        '25-Sep': [44, 100, 44, 100, 44, 100],
        '25-Oct': [858, 200, 858, 200, 858, 200],
        'MoM Var Sep-25': ['', '', '', '', '', ''],
        'MoM Var Oct-25': ['', '', '', '', '', '']
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_dedup.csv')
    
    # Count how many records we have for John
    john_data = result_df[result_df['user_id'] == 'john.boddiford@eldridge.com']
    
    # John should have exactly 2 records (Sep and Oct), not 6 (2 months × 3 table appearances)
    # The deduplication should have removed the duplicates
    assert len(john_data) == 2, f"Expected 2 records for John (deduped), got {len(john_data)}"
    print(f"✅ John's records properly deduplicated: {len(john_data)} unique months")
    
    # Verify the counts are correct (not summed)
    john_sep = john_data[john_data['date'].str.startswith('2025-09')]
    john_oct = john_data[john_data['date'].str.startswith('2025-10')]
    
    assert john_sep.iloc[0]['usage_count'] == 44, "September count should be 44, not summed across duplicates"
    assert john_oct.iloc[0]['usage_count'] == 858, "October count should be 858, not summed across duplicates"
    print(f"✅ Usage counts not summed: Sep={john_sep.iloc[0]['usage_count']}, Oct={john_oct.iloc[0]['usage_count']}")
    
    return True


def test_top_users_still_processed():
    """
    Test that the fix doesn't break processing of 'Top 20 Users' tables.
    Ensure backward compatibility is maintained.
    """
    print("\n🧪 Testing 'Top Users' Tables Still Work (Backward Compatibility)...")
    
    processor = DataProcessor(MockDB())
    
    # Create test data with only 'Top' tables (original format)
    test_data = pd.DataFrame({
        'Table': [
            'Top 20 Users Total', 'Top 20 Users Total',
            'Top 10 Increasing Users',
            'Top 10 Decreasing Users'
        ],
        'Rank': [1, 2, 1, 1],
        'User ID': [
            'top.user1@company.com', 'top.user2@company.com',
            'top.user3@company.com',
            'top.user4@company.com'
        ],
        'Metric': ['', '', '', ''],
        '25-Sep': [100, 200, 150, 50],
        '25-Oct': [120, 180, 200, 30],
        'MoM Var Sep-25': ['', '', '', ''],
        'MoM Var Oct-25': ['', '', '', '']
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_top_users.csv')
    
    # Verify all users were captured
    assert not result_df.empty, "No data processed from 'Top Users' tables!"
    assert len(result_df) == 8, f"Expected 8 records (4 users × 2 months), got {len(result_df)}"
    print(f"✅ All 'Top Users' processed: {len(result_df)} records")
    
    # Verify specific users
    for user_id in ['top.user1@company.com', 'top.user2@company.com', 'top.user3@company.com', 'top.user4@company.com']:
        user_data = result_df[result_df['user_id'] == user_id]
        assert not user_data.empty, f"User {user_id} not captured!"
        assert len(user_data) == 2, f"Expected 2 months for {user_id}, got {len(user_data)}"
    
    print("✅ All 'Top Users' have 2 months of data")
    
    return True


def run_all_tests():
    """Run all 'All Users' table tests."""
    print("=" * 70)
    print("🚀 Running BlueFlame 'All Users' Table Tests")
    print("=" * 70)
    
    tests = [
        ("'All Users' Table Processing", test_all_users_table_processing),
        ("Deduplication Across Tables", test_all_users_vs_top_users_deduplication),
        ("'Top Users' Backward Compatibility", test_top_users_still_processed)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
