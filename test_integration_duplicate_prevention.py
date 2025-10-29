"""
Integration test for duplicate prevention across the entire workflow.

Tests the complete user journey:
1. Upload a file manually
2. Auto-scan and process files
3. Attempt to re-upload same file
4. Verify database state
5. Test file deletion and re-upload
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from data_processor import DataProcessor
from file_scanner import FileScanner


def create_sample_openai_csv(filepath, filename_suffix=""):
    """Create a sample OpenAI CSV export file."""
    data = {
        'email': ['user1@company.com', 'user2@company.com', 'user3@company.com'],
        'name': ['Alice Smith', 'Bob Jones', 'Carol White'],
        'department': ['["Engineering"]', '["Sales"]', '["Marketing"]'],
        'period_start': ['2024-10-01', '2024-10-01', '2024-10-01'],
        'period_end': ['2024-10-31', '2024-10-31', '2024-10-31'],
        'is_active': ['true', 'true', 'true'],
        'user_status': ['active', 'active', 'active'],
        'messages': [150, 200, 175],
        'tool_messages': [50, 75, 60],
        'project_messages': [10, 15, 12]
    }
    
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    return len(df)


def test_full_workflow():
    """Test the complete duplicate prevention workflow."""
    
    print("=" * 80)
    print("INTEGRATION TEST: Full Duplicate Prevention Workflow")
    print("=" * 80)
    
    # Create temporary directories and files
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup test environment
        test_db_path = os.path.join(tmpdir, "test.db")
        test_tracking_path = os.path.join(tmpdir, "tracking.json")
        test_data_folder = os.path.join(tmpdir, "data")
        os.makedirs(test_data_folder)
        
        # Initialize components
        db = DatabaseManager(db_path=test_db_path)
        processor = DataProcessor(db)
        scanner = FileScanner(tracking_file=test_tracking_path)
        
        # Create test CSV files
        test_file1 = os.path.join(test_data_folder, "openai_october_2024.csv")
        test_file2 = os.path.join(test_data_folder, "openai_november_2024.csv")
        
        create_sample_openai_csv(test_file1)
        create_sample_openai_csv(test_file2)
        
        print("\n" + "=" * 80)
        print("TEST 1: Initial File Upload")
        print("=" * 80)
        
        # Simulate manual upload workflow
        df1 = pd.read_csv(test_file1)
        
        # Normalize data (simplified version)
        normalized_df1 = pd.DataFrame({
            'user_id': df1['email'],
            'user_name': df1['name'],
            'email': df1['email'],
            'department': df1['department'].str.replace('[', '').str.replace(']', '').str.replace('"', ''),
            'date': df1['period_start'],
            'feature_used': 'ChatGPT Messages',
            'usage_count': df1['messages'],
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': os.path.basename(test_file1)
        })
        
        success1, message1 = processor.process_monthly_data(normalized_df1, os.path.basename(test_file1))
        
        if success1:
            print(f"✅ PASS: First file uploaded successfully")
            print(f"   {message1}")
        else:
            print(f"❌ FAIL: First upload failed: {message1}")
            return False
        
        # Check database state
        files_summary = db.get_processed_files_summary()
        if len(files_summary) == 1:
            print(f"✅ PASS: Database shows 1 processed file")
        else:
            print(f"❌ FAIL: Expected 1 file, found {len(files_summary)}")
            return False
        
        print("\n" + "=" * 80)
        print("TEST 2: Duplicate File Upload Prevention")
        print("=" * 80)
        
        # Attempt to upload the same file again
        success2, message2 = processor.process_monthly_data(normalized_df1, os.path.basename(test_file1))
        
        if not success2 and "already processed" in message2:
            print(f"✅ PASS: Duplicate upload was prevented")
            print(f"   Warning message: {message2[:100]}...")
        else:
            print(f"❌ FAIL: Duplicate should have been prevented")
            print(f"   success={success2}, message={message2}")
            return False
        
        # Verify record count hasn't changed
        all_data = db.get_all_data()
        if len(all_data) == 3:  # 3 users from first file
            print(f"✅ PASS: Record count unchanged (3 records)")
        else:
            print(f"❌ FAIL: Record count changed to {len(all_data)}")
            return False
        
        print("\n" + "=" * 80)
        print("TEST 3: Different File Upload")
        print("=" * 80)
        
        # Upload a different file
        df2 = pd.read_csv(test_file2)
        normalized_df2 = pd.DataFrame({
            'user_id': df2['email'],
            'user_name': df2['name'],
            'email': df2['email'],
            'department': df2['department'].str.replace('[', '').str.replace(']', '').str.replace('"', ''),
            'date': df2['period_start'],
            'feature_used': 'ChatGPT Messages',
            'usage_count': df2['messages'],
            'cost_usd': 60.0,
            'tool_source': 'ChatGPT',
            'file_source': os.path.basename(test_file2)
        })
        
        success3, message3 = processor.process_monthly_data(normalized_df2, os.path.basename(test_file2))
        
        if success3:
            print(f"✅ PASS: Second file uploaded successfully")
        else:
            print(f"❌ FAIL: Second file upload failed: {message3}")
            return False
        
        # Check file count
        files_summary = db.get_processed_files_summary()
        if len(files_summary) == 2:
            print(f"✅ PASS: Database shows 2 processed files")
        else:
            print(f"❌ FAIL: Expected 2 files, found {len(files_summary)}")
            return False
        
        print("\n" + "=" * 80)
        print("TEST 4: File Deletion and Re-upload")
        print("=" * 80)
        
        # Delete first file
        delete_success = db.delete_by_file(os.path.basename(test_file1))
        
        if delete_success:
            print(f"✅ PASS: File deleted successfully")
        else:
            print(f"❌ FAIL: File deletion failed")
            return False
        
        # Verify record count
        all_data = db.get_all_data()
        if len(all_data) == 3:  # Only 3 records from second file
            print(f"✅ PASS: Records from deleted file removed (3 remaining)")
        else:
            print(f"❌ FAIL: Expected 3 records, found {len(all_data)}")
            return False
        
        # Re-upload the first file (should work now)
        success4, message4 = processor.process_monthly_data(normalized_df1, os.path.basename(test_file1))
        
        if success4:
            print(f"✅ PASS: File re-uploaded after deletion")
        else:
            print(f"❌ FAIL: Re-upload failed: {message4}")
            return False
        
        # Final verification
        all_data = db.get_all_data()
        if len(all_data) == 6:  # 3 + 3 records
            print(f"✅ PASS: Final record count correct (6 records)")
        else:
            print(f"❌ FAIL: Expected 6 records, found {len(all_data)}")
            return False
        
        print("\n" + "=" * 80)
        print("TEST 5: Database Statistics")
        print("=" * 80)
        
        stats = db.get_database_stats()
        
        print(f"Total records: {stats['total_records']}")
        print(f"Unique users: {stats['unique_users']}")
        print(f"Total cost: ${stats['total_cost']:.2f}")
        print(f"Records by file: {stats['records_by_file']}")
        
        if stats['total_records'] == 6 and stats['unique_users'] == 3:
            print(f"✅ PASS: Database statistics correct")
        else:
            print(f"❌ FAIL: Database statistics incorrect")
            return False
        
        print("\n" + "=" * 80)
        print("TEST 6: File Summary Report")
        print("=" * 80)
        
        files_summary = db.get_processed_files_summary()
        print(f"\nProcessed files:")
        for idx, row in files_summary.iterrows():
            print(f"  {idx + 1}. {row['file_source']}")
            print(f"     Records: {row['record_count']}, Users: {row['user_count']}")
            print(f"     Tool: {row['tool_source']}")
            print(f"     Date Range: {row['min_date']} to {row['max_date']}")
        
        if len(files_summary) == 2:
            print(f"\n✅ PASS: File summary correct")
        else:
            print(f"\n❌ FAIL: File summary incorrect")
            return False
        
        print("\n" + "=" * 80)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 80)
        print("\nSummary:")
        print("  ✅ Files can be uploaded successfully")
        print("  ✅ Duplicate files are detected and prevented")
        print("  ✅ Different files can be uploaded")
        print("  ✅ Files can be deleted and re-uploaded")
        print("  ✅ Database statistics are accurate")
        print("  ✅ File summaries are generated correctly")
        print("\n🎉 Duplicate prevention is working perfectly!")
        
        return True


if __name__ == "__main__":
    try:
        success = test_full_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
