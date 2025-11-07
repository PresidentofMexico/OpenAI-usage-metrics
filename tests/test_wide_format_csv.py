#!/usr/bin/env python3
"""
Test suite for wide-format BlueFlame CSV processing

This test validates the new wide-format CSV processing where:
- No 'Table' column exists
- 'User ID' column contains emails
- Month columns are in YY-Mon format (e.g., '25-Oct')
- 'Rank' and 'Metric' columns exist but should be excluded
- Each monthly upload supersedes existing data for those months
"""

import pandas as pd
import sys
import os
import tempfile
from datetime import datetime

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) if 'tests' in script_dir else script_dir
sys.path.insert(0, project_root)

from data_processor import DataProcessor
from database import DatabaseManager


def test_wide_format_detection():
    """
    Test that wide-format CSV is correctly detected and processed.
    """
    print("\n🧪 Testing Wide-Format CSV Detection...")
    
    # Setup test database using tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        db = DatabaseManager(test_db_path)
        processor = DataProcessor(db)
        
        # Create test data mimicking the new wide-format structure
        test_data = pd.DataFrame({
            'Rank': [1, 2, 3],
            'User ID': [
                'ted.divis@eldridge.com',
                'jack.steed@eldridge.com',
                'tyler.mackesy@eldridge.com'
            ],
            'Metric': [None, None, None],  # Empty metric column
            '25-Aug': [233, 252, 610],
            '25-Sep': [758, 90, 337],
            '25-Oct': [601, 187, 163],
            'MoM Var Aug-25': [525, -162, -273],
            'MoM Var Sep-25': [-157, 97, -174],
            'MoM Var Oct-25': [None, None, None]
        })
        
        # Process the data
        result_df = processor.normalize_blueflame_data(test_data, 'test_wide_format.csv')
        
        # Verify we got results
        assert not result_df.empty, "No data was processed from wide-format CSV!"
        print(f"✅ Processed {len(result_df)} records from wide-format CSV")
        
        # Verify the correct number of records (3 users × 3 months)
        expected_records = 3 * 3  # 3 users with data in 3 months
        assert len(result_df) == expected_records, f"Expected {expected_records} records, got {len(result_df)}"
        print(f"✅ Correct number of records: {len(result_df)}")
        
        # Verify specific user data
        ted_data = result_df[result_df['user_id'] == 'ted.divis@eldridge.com']
        assert len(ted_data) == 3, f"Expected 3 months for Ted, got {len(ted_data)}"
        
        # Verify August data for Ted
        ted_aug = ted_data[ted_data['date'].str.startswith('2025-08')]
        assert not ted_aug.empty, "Ted's August data missing!"
        assert ted_aug.iloc[0]['usage_count'] == 233, f"Ted's August usage incorrect: expected 233, got {ted_aug.iloc[0]['usage_count']}"
        print(f"✅ Ted's August 2025 usage: {ted_aug.iloc[0]['usage_count']} messages")
        
        return True
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_month_column_exclusion():
    """
    Test that Rank, Metric, and MoM Var columns are properly excluded.
    """
    print("\n🧪 Testing Month Column Exclusion...")
    
    # Setup test database using tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        db = DatabaseManager(test_db_path)
        processor = DataProcessor(db)
        
        # Create test data with columns that should be excluded
        test_data = pd.DataFrame({
            'Rank': [1, 2],
            'User ID': ['user1@company.com', 'user2@company.com'],
            'Metric': [None, None],
            '25-Oct': [100, 200],
            'MoM Var Oct-25': [50, 100]  # Should be excluded
        })
        
        # Process the data
        result_df = processor.normalize_blueflame_data(test_data, 'test_exclusion.csv')
        
        # Verify only October data exists (not MoM Var)
        assert len(result_df) == 2, f"Expected 2 records (2 users × 1 month), got {len(result_df)}"
        
        # Verify no records have 'MoM Var' in the date
        for _, row in result_df.iterrows():
            assert 'Var' not in str(row['date']), "MoM Var column was incorrectly processed as a month!"
        
        print(f"✅ Column exclusion working correctly: {len(result_df)} records")
        return True
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_empty_cells_handling():
    """
    Test that empty cells and NaN values are properly handled.
    """
    print("\n🧪 Testing Empty Cell Handling...")
    
    # Setup test database using tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        db = DatabaseManager(test_db_path)
        processor = DataProcessor(db)
        
        # Create test data with empty cells
        test_data = pd.DataFrame({
            'Rank': [1, 2, 3],
            'User ID': ['user1@company.com', 'user2@company.com', 'user3@company.com'],
            'Metric': [None, None, None],
            '25-Sep': [100, None, 0],  # user2 has NaN, user3 has 0
            '25-Oct': [None, 200, 150]  # user1 has NaN
        })
        
        # Process the data
        result_df = processor.normalize_blueflame_data(test_data, 'test_empty.csv')
        
        # Verify only non-empty values were processed
        # user1: Sep only (100)
        # user2: Oct only (200)
        # user3: Oct only (150) - Sep was 0 so excluded
        expected_records = 3
        assert len(result_df) == expected_records, f"Expected {expected_records} records, got {len(result_df)}"
        
        # Verify user1 has only September
        user1_data = result_df[result_df['user_id'] == 'user1@company.com']
        assert len(user1_data) == 1, "User1 should have only 1 month"
        assert user1_data.iloc[0]['date'].startswith('2025-09'), "User1 should only have September"
        
        # Verify user2 has only October
        user2_data = result_df[result_df['user_id'] == 'user2@company.com']
        assert len(user2_data) == 1, "User2 should have only 1 month"
        assert user2_data.iloc[0]['date'].startswith('2025-10'), "User2 should only have October"
        
        print(f"✅ Empty cell handling working correctly: {len(result_df)} records")
        return True
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_data_superseding():
    """
    Test that new CSV uploads supersede existing data for covered months.
    """
    print("\n🧪 Testing Data Superseding Logic...")
    
    # Setup test database using tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        db = DatabaseManager(test_db_path)
        processor = DataProcessor(db)
        
        # First upload: October data
        first_data = pd.DataFrame({
            'Rank': [1, 2],
            'User ID': ['user1@company.com', 'user2@company.com'],
            'Metric': [None, None],
            '25-Oct': [100, 200]
        })
        
        first_normalized = processor.normalize_blueflame_data(first_data, 'first_upload.csv')
        success1, msg1 = processor.process_monthly_data(first_normalized, 'first_upload.csv')
        assert success1, f"First upload failed: {msg1}"
        
        # Verify first upload
        all_data = db.get_all_data()
        assert len(all_data) == 2, f"Expected 2 records after first upload, got {len(all_data)}"
        print(f"✅ First upload: {len(all_data)} records")
        
        # Second upload: October data with updated values
        second_data = pd.DataFrame({
            'Rank': [1, 2],
            'User ID': ['user1@company.com', 'user2@company.com'],
            'Metric': [None, None],
            '25-Oct': [150, 250]  # Updated values
        })
        
        second_normalized = processor.normalize_blueflame_data(second_data, 'second_upload.csv')
        success2, msg2 = processor.process_monthly_data(second_normalized, 'second_upload.csv')
        assert success2, f"Second upload failed: {msg2}"
        
        # Verify second upload superseded first
        all_data_after = db.get_all_data()
        assert len(all_data_after) == 2, f"Expected 2 records after second upload (superseded), got {len(all_data_after)}"
        print(f"✅ Second upload: {len(all_data_after)} records (superseded first)")
        
        # Verify updated values
        user1_data = all_data_after[all_data_after['user_id'] == 'user1@company.com']
        assert user1_data.iloc[0]['usage_count'] == 150, f"User1 October count should be 150 (updated), got {user1_data.iloc[0]['usage_count']}"
        print(f"✅ Data superseding works: user1 October updated from 100 to 150")
        
        # Third upload: Add September data (should not affect October)
        third_data = pd.DataFrame({
            'Rank': [1, 2],
            'User ID': ['user1@company.com', 'user2@company.com'],
            'Metric': [None, None],
            '25-Sep': [50, 75]  # New month
        })
        
        third_normalized = processor.normalize_blueflame_data(third_data, 'third_upload.csv')
        success3, msg3 = processor.process_monthly_data(third_normalized, 'third_upload.csv')
        assert success3, f"Third upload failed: {msg3}"
        
        # Verify third upload added to existing data
        all_data_final = db.get_all_data()
        assert len(all_data_final) == 4, f"Expected 4 records (2 Sep + 2 Oct), got {len(all_data_final)}"
        print(f"✅ Third upload: {len(all_data_final)} records (added September without affecting October)")
        
        return True
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_real_csv_processing():
    """
    Test processing the actual October 2025 CSV file.
    """
    print("\n🧪 Testing Real CSV File Processing...")
    
    csv_path = os.path.join(project_root, 'BlueFlame User Data', 'blueflame_usage_combined_October2025_normalized.csv')
    
    if not os.path.exists(csv_path):
        print(f"⚠️  Skipping real CSV test - file not found: {csv_path}")
        return True
    
    # Setup test database using tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        test_db_path = tmp_file.name
    
    try:
        db = DatabaseManager(test_db_path)
        processor = DataProcessor(db)
        
        # Load and process the real CSV
        df = pd.read_csv(csv_path)
        print(f"  Real CSV shape: {df.shape}")
        
        normalized_df = processor.normalize_blueflame_data(df, 'real_october_2025.csv')
        
        assert not normalized_df.empty, "Failed to process real CSV!"
        print(f"✅ Real CSV processed: {len(normalized_df)} records")
        
        # Verify we have multiple months
        unique_months = normalized_df['date'].apply(lambda x: x[:7]).unique()
        print(f"✅ Months in real CSV: {len(unique_months)} ({', '.join(sorted(unique_months))})")
        
        # Verify we have multiple users
        unique_users = normalized_df['user_id'].nunique()
        print(f"✅ Unique users in real CSV: {unique_users}")
        
        return True
    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def run_all_tests():
    """Run all wide-format CSV tests."""
    print("=" * 70)
    print("🚀 Running Wide-Format BlueFlame CSV Tests")
    print("=" * 70)
    
    tests = [
        ("Wide-Format Detection", test_wide_format_detection),
        ("Month Column Exclusion", test_month_column_exclusion),
        ("Empty Cell Handling", test_empty_cells_handling),
        ("Data Superseding", test_data_superseding),
        ("Real CSV Processing", test_real_csv_processing)
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
