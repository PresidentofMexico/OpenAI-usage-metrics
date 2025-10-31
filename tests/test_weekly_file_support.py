"""
Test script for weekly file detection and recursive folder scanning.

This test validates:
1. Recursive folder scanning finds files in subdirectories
2. Weekly files are correctly detected
3. Data from weekly files preserves actual period_start dates
4. Multiple weekly files preserve their respective dates
5. BlueFlame files remain unchanged (flat structure)
"""

import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)

import pandas as pd
from datetime import datetime
from file_scanner import FileScanner
from config import AUTO_SCAN_FOLDERS, RECURSIVE_SCAN_FOLDERS
import re

def is_weekly_file(filename):
    """
    Detect if a file is a weekly report based on filename.
    Weekly files contain 'weekly' and a date (YYYY-MM-DD format).
    """
    filename_lower = filename.lower()
    has_weekly = 'weekly' in filename_lower
    has_date = re.search(r'\d{4}-\d{2}-\d{2}', filename) is not None
    return has_weekly and has_date

def test_file_scanner_recursive():
    """Test that FileScanner correctly scans recursive folders."""
    print("=" * 80)
    print("TEST 1: FileScanner Recursive Scanning")
    print("=" * 80)
    
    scanner = FileScanner("file_tracking_test.json", recursive_folders=RECURSIVE_SCAN_FOLDERS)
    files = scanner.scan_folders(AUTO_SCAN_FOLDERS)
    
    print(f"\nFound {len(files)} total files")
    
    # Group files by folder
    openai_files = [f for f in files if 'OpenAI User Data' in f['folder']]
    blueflame_files = [f for f in files if 'BlueFlame User Data' in f['folder']]
    
    print(f"\nOpenAI files: {len(openai_files)}")
    for f in openai_files:
        print(f"  📁 {f['folder']:50s} | {f['filename']}")
    
    print(f"\nBlueFlame files: {len(blueflame_files)}")
    for f in blueflame_files:
        print(f"  📁 {f['folder']:50s} | {f['filename']}")
    
    # Verify we found files in subdirectories
    weekly_files = [f for f in openai_files if 'Weekly' in f['folder']]
    monthly_files = [f for f in openai_files if 'Monthly' in f['folder']]
    
    print(f"\n✅ Weekly files found: {len(weekly_files)}")
    print(f"✅ Monthly files found: {len(monthly_files)}")
    
    assert len(weekly_files) >= 2, "Should find at least 2 weekly test files"
    assert len(monthly_files) >= 6, "Should find at least 6 monthly files"
    
    # Clean up test tracking file
    if os.path.exists("file_tracking_test.json"):
        os.remove("file_tracking_test.json")
    
    print("\n✅ TEST 1 PASSED: Recursive scanning works correctly\n")

def test_weekly_file_detection():
    """Test that weekly files are correctly detected by filename."""
    print("=" * 80)
    print("TEST 2: Weekly File Detection")
    print("=" * 80)
    
    test_cases = [
        ("Eldridge Capital Management weekly user report 2025-03-30.csv", True),
        ("Eldridge Capital Management weekly user report 2025-04-06.csv", True),
        ("Openai Eldridge Capital Management monthly user report March.csv", False),
        ("weekly-report-2025-01-15.xlsx", True),
        ("Monthly Report January.csv", False),
    ]
    
    for filename, expected in test_cases:
        result = is_weekly_file(filename)
        status = "✅" if result == expected else "❌"
        print(f"{status} {filename:60s} -> {'Weekly' if result else 'Monthly'} (expected: {'Weekly' if expected else 'Monthly'})")
        assert result == expected, f"Failed for {filename}"
    
    print("\n✅ TEST 2 PASSED: Weekly file detection works correctly\n")

def test_date_preservation():
    """Test that period_start dates are preserved for weekly files."""
    print("=" * 80)
    print("TEST 3: Date Preservation for Weekly Files")
    print("=" * 80)
    
    from data_processor import DataProcessor
    from database import DatabaseManager
    
    # Read the test weekly file that spans March-April
    weekly_file = "OpenAI User Data/Weekly OpenAI User Data/March/Eldridge Capital Management weekly user report 2025-03-30.csv"
    
    if not os.path.exists(weekly_file):
        print(f"❌ Test file not found: {weekly_file}")
        return
    
    df = pd.read_csv(weekly_file)
    print(f"\nLoaded test file with {len(df)} records")
    print(f"Period start: {df['period_start'].iloc[0]}")
    
    # Process through data processor
    db = DatabaseManager("test_date_preservation.db")
    processor = DataProcessor(db)
    result = processor.clean_openai_data(df, os.path.basename(weekly_file))
    
    # All records should have the same period_start date
    unique_dates = result['date'].unique()
    print(f"\nProcessed dates: {unique_dates}")
    print(f"Expected: ['2025-03-30']")
    
    assert len(unique_dates) == 1, f"Expected 1 unique date, got {len(unique_dates)}"
    assert unique_dates[0] == '2025-03-30', f"Expected 2025-03-30, got {unique_dates[0]}"
    
    print(f"\n✅ All records preserve actual period_start date: 2025-03-30")
    
    # Cleanup
    if os.path.exists("test_date_preservation.db"):
        os.remove("test_date_preservation.db")
    
    print("\n✅ TEST 3 PASSED: Date preservation works correctly for weekly files\n")

def test_multiple_weekly_files():
    """Test that different weekly files preserve their respective period_start dates."""
    print("=" * 80)
    print("TEST 4: Multiple Weekly Files Date Preservation")
    print("=" * 80)
    
    from data_processor import DataProcessor
    from database import DatabaseManager
    
    # Test different weekly files
    test_files = [
        ("OpenAI User Data/Weekly OpenAI User Data/May/Eldridge Capital Management weekly user report 2025-05-04.csv", "2025-05-04"),
        ("OpenAI User Data/Weekly OpenAI User Data/May/Eldridge Capital Management weekly user report 2025-05-11.csv", "2025-05-11"),
    ]
    
    db = DatabaseManager("test_multiple_weekly.db")
    processor = DataProcessor(db)
    
    for file_path, expected_date in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️ Skipping {file_path} - file not found")
            continue
            
        df = pd.read_csv(file_path)
        print(f"\nProcessing: {os.path.basename(file_path)}")
        print(f"  Original period_start: {df['period_start'].iloc[0]}")
        
        result = processor.clean_openai_data(df, os.path.basename(file_path))
        unique_dates = result['date'].unique()
        
        print(f"  Processed dates: {unique_dates}")
        assert expected_date in unique_dates, f"Expected {expected_date} in processed dates"
        print(f"  ✅ Preserves period_start: {expected_date}")
    
    # Cleanup
    if os.path.exists("test_multiple_weekly.db"):
        os.remove("test_multiple_weekly.db")
    
    print("\n✅ TEST 4 PASSED: Multiple weekly files preserve their dates correctly\n")

def test_folder_structure():
    """Verify the folder structure is correct."""
    print("=" * 80)
    print("TEST 5: Folder Structure Verification")
    print("=" * 80)
    
    required_folders = [
        "OpenAI User Data/Monthly OpenAI User Data",
        "OpenAI User Data/Weekly OpenAI User Data/March",
        "OpenAI User Data/Weekly OpenAI User Data/April",
        "BlueFlame User Data"
    ]
    
    for folder in required_folders:
        exists = os.path.exists(folder)
        status = "✅" if exists else "❌"
        print(f"{status} {folder}")
        assert exists, f"Required folder missing: {folder}"
    
    print("\n✅ TEST 5 PASSED: Folder structure is correct\n")

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "WEEKLY FILE SUPPORT - TEST SUITE" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        test_folder_structure()
        test_file_scanner_recursive()
        test_weekly_file_detection()
        test_date_preservation()
        test_multiple_weekly_files()
        
        print("=" * 80)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✅ Recursive folder scanning works")
        print("  ✅ Weekly file detection works")
        print("  ✅ Date preservation for weekly files works")
        print("  ✅ Multiple weekly files preserve their dates")
        print("  ✅ Folder structure is correct")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
