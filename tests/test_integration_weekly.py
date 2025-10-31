"""
End-to-end integration test for weekly file support.

This test validates the complete flow:
1. FileScanner finds files in recursive folders
2. Files are correctly identified as weekly/monthly
3. Data is normalized with correct date assignments
4. Data can be processed and stored in database
"""

import sys
import os

# Use relative path from the script location
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from file_scanner import FileScanner
from data_processor import DataProcessor
from database import DatabaseManager
from config import AUTO_SCAN_FOLDERS, RECURSIVE_SCAN_FOLDERS
from file_reader import read_file_from_path

def test_end_to_end_integration():
    """Complete end-to-end test of weekly file support."""
    print("=" * 80)
    print("END-TO-END INTEGRATION TEST")
    print("=" * 80)
    
    # Step 1: Initialize components
    print("\n📦 Step 1: Initializing components...")
    db = DatabaseManager("test_integration.db")
    processor = DataProcessor(db)
    scanner = FileScanner("test_file_tracking.json", recursive_folders=RECURSIVE_SCAN_FOLDERS)
    print("✅ Components initialized")
    
    # Step 2: Scan folders
    print("\n📂 Step 2: Scanning folders...")
    all_files = scanner.scan_folders(AUTO_SCAN_FOLDERS)
    print(f"✅ Found {len(all_files)} total files")
    
    # Filter for OpenAI files
    openai_files = [f for f in all_files if 'OpenAI User Data' in f['folder']]
    weekly_files = [f for f in openai_files if 'Weekly' in f['folder']]
    monthly_files = [f for f in openai_files if 'Monthly' in f['folder']]
    
    print(f"   - OpenAI files: {len(openai_files)}")
    print(f"   - Weekly files: {len(weekly_files)}")
    print(f"   - Monthly files: {len(monthly_files)}")
    
    assert len(weekly_files) >= 2, "Should find weekly test files"
    assert len(monthly_files) >= 7, "Should find monthly files"
    
    # Step 3: Process a weekly file
    print("\n🔄 Step 3: Processing weekly file...")
    weekly_test_files = [f for f in weekly_files if '2025-03-30' in f['filename']]
    assert len(weekly_test_files) > 0, "Could not find weekly test file with date 2025-03-30"
    weekly_test_file = weekly_test_files[0]
    print(f"   Processing: {weekly_test_file['filename']}")
    
    # Read the file
    df, error = read_file_from_path(weekly_test_file['path'])
    assert error is None, f"Error reading file: {error}"
    print(f"   ✅ Read {len(df)} rows from file")
    
    # Process through data processor
    processed_df = processor.clean_openai_data(df, weekly_test_file['filename'])
    print(f"   ✅ Processed to {len(processed_df)} records")
    
    # Verify date preservation
    print("\n📊 Step 4: Verifying date preservation...")
    unique_dates = processed_df['date'].unique()
    
    print(f"   - Unique dates: {unique_dates}")
    print(f"   - Expected: ['2025-03-30']")
    
    # All records should have the same period_start date
    assert len(unique_dates) == 1, f"Expected 1 unique date, got {len(unique_dates)}"
    assert unique_dates[0] == '2025-03-30', f"Expected 2025-03-30, got {unique_dates[0]}"
    
    print("   ✅ All records preserve period_start date: 2025-03-30")
    
    # Step 5: Store in database
    print("\n💾 Step 5: Storing in database...")
    success, message = processor.process_monthly_data(processed_df, weekly_test_file['filename'])
    assert success, f"Failed to store data: {message}"
    print(f"   ✅ {message}")
    
    # Step 6: Verify data in database
    print("\n🔍 Step 6: Verifying data in database...")
    all_data = db.get_all_data()
    print(f"   Total records in DB: {len(all_data)}")
    
    # Check that we have the expected records with the preserved date
    db_march = all_data[pd.to_datetime(all_data['date']).dt.month == 3]
    db_dates = all_data['date'].unique()
    
    print(f"   - Unique dates in DB: {db_dates}")
    
    assert '2025-03-30' in db_dates, "Database should have 2025-03-30 records"
    
    print("   ✅ Database contains correct data with preserved dates")
    
    # Step 7: Test monthly file for backward compatibility
    print("\n🔄 Step 7: Testing monthly file (backward compatibility)...")
    monthly_test_files = [f for f in monthly_files if 'March' in f['filename']]
    assert len(monthly_test_files) > 0, "Could not find monthly test file for March"
    monthly_test_file = monthly_test_files[0]
    print(f"   Processing: {monthly_test_file['filename']}")
    
    df_monthly, error = read_file_from_path(monthly_test_file['path'])
    assert error is None, f"Error reading monthly file: {error}"
    
    processed_monthly = processor.clean_openai_data(df_monthly, monthly_test_file['filename'])
    print(f"   ✅ Processed {len(processed_monthly)} records from monthly file")
    
    # All should be March
    monthly_months = pd.to_datetime(processed_monthly['date']).dt.month.unique()
    assert len(monthly_months) == 1 and monthly_months[0] == 3, "All monthly records should be March"
    print("   ✅ Monthly file backward compatibility confirmed")
    
    # Cleanup
    print("\n🧹 Cleaning up test files...")
    if os.path.exists("test_integration.db"):
        os.remove("test_integration.db")
    if os.path.exists("test_file_tracking.json"):
        os.remove("test_file_tracking.json")
    print("   ✅ Cleanup complete")
    
    print("\n" + "=" * 80)
    print("✅ END-TO-END INTEGRATION TEST PASSED")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✅ File scanning works with recursive folders")
    print("  ✅ Weekly files detected and read correctly")
    print("  ✅ Weekly files preserve actual period_start dates")
    print("  ✅ Data stored successfully in database")
    print("  ✅ Database queries work correctly")
    print("  ✅ Monthly files still work (backward compatibility)")
    print()

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "END-TO-END INTEGRATION TEST" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        test_end_to_end_integration()
        print("🎉 SUCCESS! The complete weekly file support feature is working correctly! 🎉")
        print()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
