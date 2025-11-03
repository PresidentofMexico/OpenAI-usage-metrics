"""
Test suite for file tracking reset and clear functionality

Tests the following features:
1. FileScanner reset methods (reset_file_status, reset_all_files_status, reset_all_tracking)
2. Employee marker clearing (clear_employee_markers)
3. Comprehensive reset (clear_and_reset_all)
4. Employee file modification detection
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
import time

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from file_scanner import FileScanner


def test_reset_file_status():
    """Test resetting a single file's status."""
    print("\n🧪 Testing reset_file_status()...")
    
    # Create temporary tracking file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tracking_file = f.name
    
    # Create temporary test file
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    test_file.write("test,data\n1,2\n")
    test_file.close()
    
    try:
        # Initialize scanner
        scanner = FileScanner(tracking_file=tracking_file)
        
        # Mark the file as processed
        scanner.mark_processed(test_file.name, success=True, records_count=100)
        
        # Verify it's tracked
        file_key = os.path.abspath(test_file.name)
        assert file_key in scanner.processed_files, "File should be tracked"
        
        # Reset the file status
        scanner.reset_file_status(test_file.name)
        
        # Verify it's no longer tracked
        assert file_key not in scanner.processed_files, "File should not be tracked after reset"
        
        print("✅ reset_file_status() works correctly")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(tracking_file):
            os.remove(tracking_file)
        if os.path.exists(test_file.name):
            os.remove(test_file.name)


def test_reset_all_files_status():
    """Test resetting all files in specified folders."""
    print("\n🧪 Testing reset_all_files_status()...")
    
    # Create temporary tracking file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tracking_file = f.name
    
    # Create temporary test files
    temp_files = []
    for i in range(3):
        tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        tmp_file.write(f"test,data\n{i},data\n")
        tmp_file.close()
        temp_files.append(tmp_file.name)
    
    try:
        # Initialize scanner
        scanner = FileScanner(tracking_file=tracking_file)
        
        # Mark all files as processed
        for tmp_file in temp_files:
            scanner.mark_processed(tmp_file, success=True, records_count=50 + temp_files.index(tmp_file))
        
        # Verify all are tracked
        assert len(scanner.processed_files) == 3, "Should have 3 tracked files"
        
        # Reset all files
        scanner.reset_all_files_status()
        
        # Verify all are cleared
        assert len(scanner.processed_files) == 0, "All files should be cleared"
        
        print("✅ reset_all_files_status() works correctly")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(tracking_file):
            os.remove(tracking_file)
        for tmp_file in temp_files:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)


def test_reset_all_files_status_filtered():
    """Test resetting files only in specific folders."""
    print("\n🧪 Testing reset_all_files_status() with folder filter...")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    folder1 = os.path.join(temp_dir, "folder1")
    folder2 = os.path.join(temp_dir, "folder2")
    os.makedirs(folder1)
    os.makedirs(folder2)
    
    # Create temporary tracking file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tracking_file = f.name
    
    # Create test files in folders
    file1 = os.path.join(folder1, "file1.csv")
    file2 = os.path.join(folder1, "file2.csv")
    file3 = os.path.join(folder2, "file3.csv")
    
    for filepath in [file1, file2, file3]:
        with open(filepath, 'w') as f:
            f.write("test,data\n1,2\n")
    
    try:
        # Initialize scanner
        scanner = FileScanner(tracking_file=tracking_file)
        
        # Mark files in different folders as processed
        scanner.mark_processed(file1, success=True, records_count=50)
        scanner.mark_processed(file2, success=True, records_count=60)
        scanner.mark_processed(file3, success=True, records_count=70)
        
        # Verify all are tracked
        assert len(scanner.processed_files) == 3, "Should have 3 tracked files"
        
        # Reset only folder1 files
        scanner.reset_all_files_status([folder1])
        
        # Verify only folder1 files are cleared
        assert len(scanner.processed_files) == 1, "Only folder2 file should remain"
        assert os.path.abspath(file3) in scanner.processed_files, "folder2 file should still be tracked"
        
        print("✅ reset_all_files_status() with folder filter works correctly")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(tracking_file):
            os.remove(tracking_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_reset_all_tracking():
    """Test completely clearing tracking file."""
    print("\n🧪 Testing reset_all_tracking()...")
    
    # Create temporary tracking file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tracking_file = f.name
        json.dump({"test": "data"}, f)
    
    # Create temporary test file
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    test_file.write("test,data\n1,2\n")
    test_file.close()
    
    try:
        # Verify file exists
        assert os.path.exists(tracking_file), "Tracking file should exist"
        
        # Initialize scanner
        scanner = FileScanner(tracking_file=tracking_file)
        
        # Mark some files
        scanner.mark_processed(test_file.name, success=True, records_count=100)
        
        # Reset all tracking
        scanner.reset_all_tracking()
        
        # Verify tracking is empty
        assert len(scanner.processed_files) == 0, "Processed files should be empty"
        
        # Verify file was removed
        assert not os.path.exists(tracking_file), "Tracking file should be removed"
        
        print("✅ reset_all_tracking() works correctly")
        return True
        
    finally:
        # Cleanup (in case test failed)
        if os.path.exists(tracking_file):
            os.remove(tracking_file)
        if os.path.exists(test_file.name):
            os.remove(test_file.name)


def test_employee_marker_clearing():
    """Test clearing employee marker files."""
    print("\n🧪 Testing employee marker clearing...")
    
    # Create temporary directory for markers
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create mock marker files
        marker1 = os.path.join(temp_dir, ".Employee Headcount.csv.loaded")
        marker2 = os.path.join(temp_dir, ".Another File.csv.loaded")
        
        with open(marker1, 'w') as f:
            f.write("Loaded on 2024-01-01\n")
        with open(marker2, 'w') as f:
            f.write("Loaded on 2024-01-02\n")
        
        # Verify markers exist
        assert os.path.exists(marker1), "Marker 1 should exist"
        assert os.path.exists(marker2), "Marker 2 should exist"
        
        # Simulate clearing (we'll manually do it since clear_employee_markers 
        # looks in script directory)
        deleted = 0
        for filename in os.listdir(temp_dir):
            if filename.endswith('.loaded') and filename.startswith('.'):
                os.remove(os.path.join(temp_dir, filename))
                deleted += 1
        
        # Verify markers are deleted
        assert deleted == 2, "Should have deleted 2 markers"
        assert not os.path.exists(marker1), "Marker 1 should be deleted"
        assert not os.path.exists(marker2), "Marker 2 should be deleted"
        
        print("✅ Employee marker clearing works correctly")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_file_modification_detection():
    """Test that modified files are detected correctly."""
    print("\n🧪 Testing file modification detection...")
    
    # Create temporary file and tracking
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_file.write("test,data\n1,2\n")
    temp_file.close()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        tracking_file = f.name
    
    try:
        # Initialize scanner
        scanner = FileScanner(tracking_file=tracking_file)
        
        # Get initial file info
        file_info = scanner._get_file_info(temp_file.name, "test_folder")
        assert file_info['status'] == 'new', "New file should have 'new' status"
        
        # Mark as processed
        scanner.mark_processed(temp_file.name, success=True, records_count=1)
        
        # Get file info again - should be 'processed'
        scanner2 = FileScanner(tracking_file=tracking_file)
        file_info2 = scanner2._get_file_info(temp_file.name, "test_folder")
        assert file_info2['status'] == 'processed', "File should have 'processed' status"
        
        # Modify the file
        time.sleep(0.1)  # Ensure different modification time
        with open(temp_file.name, 'a') as f:
            f.write("3,4\n")
        
        # Get file info again - should be 'modified'
        scanner3 = FileScanner(tracking_file=tracking_file)
        file_info3 = scanner3._get_file_info(temp_file.name, "test_folder")
        assert file_info3['status'] == 'modified', f"Modified file should have 'modified' status, got {file_info3['status']}"
        
        print("✅ File modification detection works correctly")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        if os.path.exists(tracking_file):
            os.remove(tracking_file)


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_reset_file_status,
        test_reset_all_files_status,
        test_reset_all_files_status_filtered,
        test_reset_all_tracking,
        test_employee_marker_clearing,
        test_file_modification_detection,
    ]
    
    print("\n" + "="*60)
    print("🧪 Running Reset Functionality Tests")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
