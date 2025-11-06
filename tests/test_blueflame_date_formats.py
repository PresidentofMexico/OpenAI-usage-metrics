"""
Test suite for BlueFlame date format parsing

Tests that the BlueFlame data processor correctly handles both:
1. Mon-YY format (e.g., 'Sep-24', 'Oct-24')
2. YY-Mon format (e.g., '25-Sep', '25-Oct')

This addresses the critical bug where YY-Mon format columns were silently skipped.
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
from database import DatabaseManager


def test_parse_blueflame_month_column():
    """Test the helper function that parses both date formats."""
    print("\n🧪 Testing parse_blueflame_month_column Helper Function...")
    
    # Create a mock database manager (we don't need real DB for this test)
    class MockDB:
        pass
    
    processor = DataProcessor(MockDB())
    
    # Test Mon-YY format (original format)
    test_cases_mon_yy = [
        ('Sep-24', datetime(2024, 9, 1)),
        ('Oct-24', datetime(2024, 10, 1)),
        ('Jan-25', datetime(2025, 1, 1)),
        ('Dec-23', datetime(2023, 12, 1))
    ]
    
    for col_name, expected_date in test_cases_mon_yy:
        result = processor.parse_blueflame_month_column(col_name)
        assert not pd.isna(result), f"Failed to parse Mon-YY format: {col_name}"
        assert result.year == expected_date.year, f"Year mismatch for {col_name}"
        assert result.month == expected_date.month, f"Month mismatch for {col_name}"
        print(f"✅ Mon-YY format '{col_name}' parsed correctly: {result.strftime('%Y-%m')}")
    
    # Test YY-Mon format (new format)
    test_cases_yy_mon = [
        ('25-Apr', datetime(2025, 4, 1)),
        ('25-May', datetime(2025, 5, 1)),
        ('25-Sep', datetime(2025, 9, 1)),
        ('25-Oct', datetime(2025, 10, 1)),
        ('24-Dec', datetime(2024, 12, 1))
    ]
    
    for col_name, expected_date in test_cases_yy_mon:
        result = processor.parse_blueflame_month_column(col_name)
        assert not pd.isna(result), f"Failed to parse YY-Mon format: {col_name}"
        assert result.year == expected_date.year, f"Year mismatch for {col_name}: expected {expected_date.year}, got {result.year}"
        assert result.month == expected_date.month, f"Month mismatch for {col_name}: expected {expected_date.month}, got {result.month}"
        print(f"✅ YY-Mon format '{col_name}' parsed correctly: {result.strftime('%Y-%m')}")
    
    # Test invalid formats (should return NaT)
    invalid_cases = ['Invalid', '2024-09', 'Sep 24', '25/Sep']
    for col_name in invalid_cases:
        result = processor.parse_blueflame_month_column(col_name)
        assert pd.isna(result), f"Should have failed to parse invalid format: {col_name}"
        print(f"✅ Invalid format '{col_name}' correctly returned NaT")
    
    return True


def test_normalize_blueflame_data_with_yy_mon_format():
    """Test that normalize_blueflame_data correctly processes YY-Mon format."""
    print("\n🧪 Testing normalize_blueflame_data with YY-Mon Format...")
    
    # Create a mock database manager
    class MockDB:
        pass
    
    processor = DataProcessor(MockDB())
    
    # Create test data with YY-Mon format columns (like the actual CSV)
    test_data = pd.DataFrame({
        'Table': ['Overall Monthly Trends', 'Overall Monthly Trends', 'Overall Monthly Trends', 'Overall Monthly Trends'],
        'Rank': ['', '', '', ''],
        'User ID': ['', '', '', ''],
        'Metric': ['Total Messages', 'MoM Growth %', 'Monthly Active Users (MAUs)', 'Avg. Messages per MAU'],
        '25-Apr': ['', '', '', ''],
        '25-May': ['', '', '', ''],
        '25-Jun': ['', '', '', ''],
        '25-Jul': ['', '', '', ''],
        '25-Aug': [1318, '', 11, 119],
        '25-Sep': [3475, '', 30, 115],
        '25-Oct': [3872, '', 62, 62],
        'MoM Var Jul-25': [9431, '', 19, -4],
        'MoM Var Aug-25': [2157, '', 32, -53],
        'MoM Var Sep-25': [397, '', 74, 7],
        'MoM Var Oct-25': [5559, '', '', '']
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_file.csv')
    
    # Verify we got results
    assert not result_df.empty, "No data was processed - columns were likely skipped!"
    print(f"✅ Processed {len(result_df)} records from YY-Mon format data")
    
    # Verify we have data for the expected months
    dates = pd.to_datetime(result_df['date'])
    unique_months = dates.dt.to_period('M').unique()
    print(f"✅ Found data for {len(unique_months)} unique months: {sorted([str(m) for m in unique_months])}")
    
    # Verify August 2025 data exists (25-Aug column)
    aug_2025_data = result_df[result_df['date'].str.startswith('2025-08')]
    assert not aug_2025_data.empty, "No data found for August 2025 (25-Aug column)"
    print(f"✅ August 2025 data found: {len(aug_2025_data)} records")
    
    # Verify September 2025 data exists (25-Sep column)
    sep_2025_data = result_df[result_df['date'].str.startswith('2025-09')]
    assert not sep_2025_data.empty, "No data found for September 2025 (25-Sep column)"
    print(f"✅ September 2025 data found: {len(sep_2025_data)} records")
    
    # Verify October 2025 data exists (25-Oct column)
    oct_2025_data = result_df[result_df['date'].str.startswith('2025-10')]
    assert not oct_2025_data.empty, "No data found for October 2025 (25-Oct column)"
    print(f"✅ October 2025 data found: {len(oct_2025_data)} records")
    
    return True


def test_normalize_blueflame_data_with_mon_yy_format():
    """Test that normalize_blueflame_data still works with Mon-YY format (backward compatibility)."""
    print("\n🧪 Testing normalize_blueflame_data with Mon-YY Format (Backward Compatibility)...")
    
    # Create a mock database manager
    class MockDB:
        pass
    
    processor = DataProcessor(MockDB())
    
    # Create test data with Mon-YY format columns (original format)
    test_data = pd.DataFrame({
        'Table': ['Overall Monthly Trends', 'Overall Monthly Trends', 'Overall Monthly Trends'],
        'Metric': ['Total Messages', 'Monthly Active Users (MAUs)', 'Avg. Messages per MAU'],
        'Sep-24': [1000, 25, 40],
        'Oct-24': [1200, 28, 42],
        'Nov-24': [1500, 32, 46],
        'MoM Var Sep-24': [0, 0, 0]
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_file.csv')
    
    # Verify we got results
    assert not result_df.empty, "No data was processed - backward compatibility broken!"
    print(f"✅ Processed {len(result_df)} records from Mon-YY format data")
    
    # Verify we have data for the expected months
    dates = pd.to_datetime(result_df['date'])
    unique_months = dates.dt.to_period('M').unique()
    print(f"✅ Found data for {len(unique_months)} unique months: {sorted([str(m) for m in unique_months])}")
    
    # Verify September 2024 data exists
    sep_2024_data = result_df[result_df['date'].str.startswith('2024-09')]
    assert not sep_2024_data.empty, "No data found for September 2024"
    print(f"✅ September 2024 data found: {len(sep_2024_data)} records")
    
    return True


def test_user_level_data_with_yy_mon_format():
    """Test user-level data processing with YY-Mon format."""
    print("\n🧪 Testing User-Level Data with YY-Mon Format...")
    
    # Create a mock database manager
    class MockDB:
        pass
    
    processor = DataProcessor(MockDB())
    
    # Create test data with user-level format and YY-Mon columns
    test_data = pd.DataFrame({
        'Table': ['Top 20 Users Total', 'Top 20 Users Total'],
        'Rank': [1, 2],
        'User ID': ['john.boddiford@company.com', 'jane.doe@company.com'],
        'Metric': ['', ''],
        '25-Aug': [150, 75],
        '25-Sep': [200, 100],
        '25-Oct': [180, 90],
        'MoM Var Aug-25': [50, 25],
        'MoM Var Sep-25': [-20, -10]
    })
    
    # Process the data
    result_df = processor.normalize_blueflame_data(test_data, 'test_file.csv')
    
    # Verify we got results
    assert not result_df.empty, "No user data was processed!"
    print(f"✅ Processed {len(result_df)} user records from YY-Mon format data")
    
    # Verify John Boddiford's data was captured
    john_data = result_df[result_df['user_id'] == 'john.boddiford@company.com']
    assert not john_data.empty, "John Boddiford's data was not captured!"
    print(f"✅ John Boddiford data captured: {len(john_data)} months")
    
    # Verify we have data for all three months
    john_dates = sorted(john_data['date'].tolist())
    print(f"✅ John Boddiford months: {john_dates}")
    assert len(john_dates) == 3, f"Expected 3 months of data, got {len(john_dates)}"
    
    # Verify October 2025 data for John
    john_oct = john_data[john_data['date'].str.startswith('2025-10')]
    assert not john_oct.empty, "John's October 2025 data missing!"
    assert john_oct.iloc[0]['usage_count'] == 180, "John's October usage count incorrect"
    print(f"✅ John's October 2025 usage: {john_oct.iloc[0]['usage_count']} messages")
    
    return True


def run_all_tests():
    """Run all BlueFlame date format tests."""
    print("=" * 70)
    print("🚀 Running BlueFlame Date Format Tests")
    print("=" * 70)
    
    tests = [
        ("Parse Month Column Helper", test_parse_blueflame_month_column),
        ("YY-Mon Format Processing", test_normalize_blueflame_data_with_yy_mon_format),
        ("Mon-YY Format Backward Compatibility", test_normalize_blueflame_data_with_mon_yy_format),
        ("User-Level YY-Mon Format", test_user_level_data_with_yy_mon_format)
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
