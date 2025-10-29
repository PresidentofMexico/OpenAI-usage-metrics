"""
Test suite for duplicate file processing prevention.

This test validates that:
1. Files can be processed successfully on first upload
2. Duplicate files are detected and prevented from being re-processed
3. File tracking correctly identifies already-processed files
4. Database maintains data integrity by preventing duplicate records
"""

import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from data_processor import DataProcessor


def test_duplicate_detection():
    """Test that duplicate file processing is properly prevented."""
    
    print("=" * 80)
    print("TEST: Duplicate File Processing Prevention")
    print("=" * 80)
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp_db:
        test_db_path = tmp_db.name
    
    try:
        # Initialize database and processor
        db = DatabaseManager(db_path=test_db_path)
        processor = DataProcessor(db)
        
        # Create sample normalized data
        sample_data = pd.DataFrame({
            'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
            'user_name': ['User One', 'User Two', 'User Three'],
            'email': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
            'department': ['Engineering', 'Sales', 'Marketing'],
            'date': ['2024-10-01', '2024-10-01', '2024-10-01'],
            'feature_used': ['ChatGPT Messages', 'ChatGPT Messages', 'ChatGPT Messages'],
            'usage_count': [100, 200, 150],
            'cost_usd': [60.0, 60.0, 60.0],
            'tool_source': ['ChatGPT', 'ChatGPT', 'ChatGPT'],
            'file_source': ['test_file.csv', 'test_file.csv', 'test_file.csv']
        })
        
        # Test 1: First processing should succeed
        print("\n[TEST 1] Processing file for the first time...")
        success1, message1 = processor.process_monthly_data(sample_data, 'test_file.csv', skip_duplicates=True)
        
        if success1:
            print(f"✅ PASS: First processing succeeded")
            print(f"   Message: {message1}")
        else:
            print(f"❌ FAIL: First processing should succeed but got: {message1}")
            return False
        
        # Verify data was inserted
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE file_source = 'test_file.csv'")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 3:
            print(f"✅ PASS: Correct number of records inserted ({count})")
        else:
            print(f"❌ FAIL: Expected 3 records but found {count}")
            return False
        
        # Test 2: Second processing should be prevented
        print("\n[TEST 2] Attempting to process the same file again...")
        success2, message2 = processor.process_monthly_data(sample_data, 'test_file.csv', skip_duplicates=True)
        
        if not success2 and "already processed" in message2:
            print(f"✅ PASS: Duplicate detected and prevented")
            print(f"   Message: {message2}")
        else:
            print(f"❌ FAIL: Duplicate should be prevented but got: success={success2}, message={message2}")
            return False
        
        # Verify record count hasn't changed
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE file_source = 'test_file.csv'")
        count_after = cursor.fetchone()[0]
        conn.close()
        
        if count_after == 3:
            print(f"✅ PASS: Record count unchanged ({count_after})")
        else:
            print(f"❌ FAIL: Record count changed from 3 to {count_after} - duplicates were inserted!")
            return False
        
        # Test 3: Check file_exists method
        print("\n[TEST 3] Testing check_file_exists method...")
        file_check = db.check_file_exists('test_file.csv')
        
        if file_check['exists']:
            print(f"✅ PASS: File correctly identified as existing")
            print(f"   Record count: {file_check['record_count']}")
            print(f"   User count: {file_check['user_count']}")
            print(f"   Date range: {file_check['date_range']}")
        else:
            print(f"❌ FAIL: File should be identified as existing")
            return False
        
        if file_check['record_count'] == 3 and file_check['user_count'] == 3:
            print(f"✅ PASS: File statistics are correct")
        else:
            print(f"❌ FAIL: File statistics incorrect - records={file_check['record_count']}, users={file_check['user_count']}")
            return False
        
        # Test 4: Different file should be processed successfully
        print("\n[TEST 4] Processing a different file...")
        sample_data2 = sample_data.copy()
        sample_data2['file_source'] = 'different_file.csv'
        
        success3, message3 = processor.process_monthly_data(sample_data2, 'different_file.csv', skip_duplicates=True)
        
        if success3:
            print(f"✅ PASS: Different file processed successfully")
        else:
            print(f"❌ FAIL: Different file should be processed: {message3}")
            return False
        
        # Verify total record count
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_metrics")
        total_count = cursor.fetchone()[0]
        conn.close()
        
        if total_count == 6:  # 3 from first file + 3 from second file
            print(f"✅ PASS: Total record count is correct ({total_count})")
        else:
            print(f"❌ FAIL: Expected 6 total records but found {total_count}")
            return False
        
        # Test 5: Processing with skip_duplicates=False should work
        print("\n[TEST 5] Testing skip_duplicates=False option...")
        success4, message4 = processor.process_monthly_data(sample_data, 'test_file.csv', skip_duplicates=False)
        
        if success4:
            print(f"✅ PASS: File processed when skip_duplicates=False")
        else:
            print(f"❌ FAIL: Should process when skip_duplicates=False: {message4}")
            return False
        
        # Verify duplicates were added
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_metrics WHERE file_source = 'test_file.csv'")
        count_with_dups = cursor.fetchone()[0]
        conn.close()
        
        if count_with_dups == 6:  # Original 3 + duplicate 3
            print(f"✅ PASS: Duplicates added when skip_duplicates=False ({count_with_dups})")
        else:
            print(f"❌ FAIL: Expected 6 records for test_file.csv but found {count_with_dups}")
            return False
        
        # Test 6: Test get_processed_files_summary
        print("\n[TEST 6] Testing get_processed_files_summary method...")
        files_summary = db.get_processed_files_summary()
        
        if not files_summary.empty:
            print(f"✅ PASS: Files summary retrieved")
            print(f"   Files found: {len(files_summary)}")
            print(files_summary[['file_source', 'record_count', 'user_count', 'tool_source']].to_string(index=False))
        else:
            print(f"❌ FAIL: Files summary should not be empty")
            return False
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED - Duplicate prevention working correctly!")
        print("=" * 80)
        return True
        
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print(f"\n🧹 Cleaned up test database: {test_db_path}")


if __name__ == "__main__":
    try:
        success = test_duplicate_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
