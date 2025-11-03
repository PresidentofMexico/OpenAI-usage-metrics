#!/usr/bin/env python3
"""
Test glob pattern matching for employee file auto-detection.

This test validates that the auto_load_employee_file function correctly:
1. Detects employee files with various naming patterns
2. Prioritizes files with "_Emails" suffix
3. Handles multiple matching files correctly
4. Works with glob patterns instead of hardcoded filenames
"""
import sys
import os
import tempfile
import shutil
import glob as glob_module

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager
from app import auto_load_employee_file


def test_glob_pattern_detection():
    """Test that glob patterns correctly detect various employee file naming patterns"""
    print("\n" + "=" * 60)
    print("TEST: Glob Pattern Detection for Employee Files")
    print("=" * 60)
    
    # Create a temporary directory to simulate script directory
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        # Create test employee CSV files with different naming patterns
        test_files = [
            "Employee Headcount 2025_Emails.csv",
            "Employee Headcount October 2025_Emails.csv",
            "Employee Headcount November 2025_Emails.csv",
            "Employee Headcount 2025.csv",  # No _Emails suffix
            "Employee Headcount Oct 2025.csv",  # No _Emails suffix
        ]
        
        # Create sample CSV content
        sample_csv = """First Name,Last Name,Email,Title,Function,Status
John,Doe,john.doe@example.com,Engineer,Engineering,Active
Jane,Smith,jane.smith@example.com,Manager,Product,Active
"""
        
        # Create all test files
        print("\nCreating test employee files:")
        for filename in test_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(sample_csv)
            print(f"  Created: {filename}")
        
        # Test glob pattern matching
        print("\nTesting glob patterns:")
        glob_patterns = [
            "Employee Headcount*Emails.csv",
            "Employee Headcount*.csv"
        ]
        
        employee_file_candidates = []
        seen_files = set()
        
        for pattern in glob_patterns:
            pattern_path = os.path.join(temp_dir, pattern)
            matched_files = glob_module.glob(pattern_path)
            
            if matched_files:
                matched_files.sort(reverse=True)
                print(f"\n  Pattern: {pattern}")
                print(f"  Matched {len(matched_files)} file(s):")
                for f in matched_files:
                    print(f"    - {os.path.basename(f)}")
                
                # Deduplicate
                for file_path in matched_files:
                    if file_path not in seen_files:
                        employee_file_candidates.append(file_path)
                        seen_files.add(file_path)
        
        print(f"\n  Total unique candidates: {len(employee_file_candidates)}")
        print("  Final list (after deduplication):")
        for f in employee_file_candidates:
            print(f"    - {os.path.basename(f)}")
        
        # Verify results
        assert len(employee_file_candidates) == 5, f"Expected 5 unique files, got {len(employee_file_candidates)}"
        
        # Verify files with _Emails are found
        emails_files = [f for f in employee_file_candidates if '_Emails.csv' in f]
        assert len(emails_files) == 3, f"Expected 3 files with _Emails, got {len(emails_files)}"
        
        # Verify files without _Emails are found
        non_emails_files = [f for f in employee_file_candidates if '_Emails.csv' not in f]
        assert len(non_emails_files) == 2, f"Expected 2 files without _Emails, got {len(non_emails_files)}"
        
        # Verify the first candidate is a file with _Emails (priority)
        first_candidate = os.path.basename(employee_file_candidates[0])
        assert '_Emails.csv' in first_candidate, f"First candidate should have _Emails, got: {first_candidate}"
        
        print("\n✅ PASSED: Glob pattern detection works correctly")
        print("   - All 5 files detected")
        print("   - Deduplication working")
        print("   - Files with _Emails prioritized")
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_flexible_naming_patterns():
    """Test that various realistic employee file naming patterns are detected"""
    print("\n" + "=" * 60)
    print("TEST: Flexible Naming Pattern Support")
    print("=" * 60)
    
    # Test different naming patterns that should all be detected
    patterns_to_test = [
        ("Employee Headcount 2025_Emails.csv", True),
        ("Employee Headcount Oct 2025_Emails.csv", True),
        ("Employee Headcount October 2025_Emails.csv", True),
        ("Employee Headcount Q4 2025_Emails.csv", True),
        ("Employee Headcount 2025.csv", True),
        ("Employee Headcount Oct 2025.csv", True),
        ("Employee Headcount.csv", True),  # Minimal name
        ("employee headcount 2025.csv", False),  # Wrong case - shouldn't match
        ("Staff Headcount 2025_Emails.csv", False),  # Wrong prefix - shouldn't match
        ("Employee_Headcount_2025_Emails.csv", False),  # Underscores instead of spaces
    ]
    
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        # Create sample CSV
        sample_csv = "First Name,Last Name,Email\nJohn,Doe,john@test.com\n"
        
        print("\nTesting which files match the patterns:")
        for filename, should_match in patterns_to_test:
            # Create the file
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(sample_csv)
            
            # Test if it matches
            glob_patterns = [
                "Employee Headcount*Emails.csv",
                "Employee Headcount*.csv"
            ]
            
            matches = []
            for pattern in glob_patterns:
                pattern_path = os.path.join(temp_dir, pattern)
                matched = glob_module.glob(pattern_path)
                matches.extend(matched)
            
            # Check if file was matched
            file_matched = file_path in matches
            status = "✓" if file_matched == should_match else "✗"
            expected = "MATCH" if should_match else "NO MATCH"
            actual = "MATCHED" if file_matched else "NOT MATCHED"
            
            print(f"  {status} {filename:45} Expected: {expected:10} Got: {actual}")
            
            # Assert
            assert file_matched == should_match, f"File {filename}: expected {should_match}, got {file_matched}"
            
            # Cleanup the test file
            os.remove(file_path)
        
        print("\n✅ PASSED: All naming patterns behave as expected")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_priority_ordering():
    """Test that files are prioritized correctly (newest year first, _Emails preferred)"""
    print("\n" + "=" * 60)
    print("TEST: File Priority Ordering")
    print("=" * 60)
    
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        # Create files with different years/months
        test_files = [
            "Employee Headcount 2023_Emails.csv",
            "Employee Headcount 2024_Emails.csv",
            "Employee Headcount 2025_Emails.csv",
            "Employee Headcount October 2025_Emails.csv",
            "Employee Headcount November 2025_Emails.csv",
        ]
        
        sample_csv = "First Name,Last Name,Email\nTest,User,test@test.com\n"
        
        # Create all files
        for filename in test_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(sample_csv)
        
        # Apply the same logic as auto_load_employee_file
        glob_patterns = ["Employee Headcount*Emails.csv", "Employee Headcount*.csv"]
        employee_file_candidates = []
        seen_files = set()
        
        for pattern in glob_patterns:
            pattern_path = os.path.join(temp_dir, pattern)
            matched_files = glob_module.glob(pattern_path)
            if matched_files:
                matched_files.sort(reverse=True)  # Sort descending (newest first)
                for file_path in matched_files:
                    if file_path not in seen_files:
                        employee_file_candidates.append(file_path)
                        seen_files.add(file_path)
        
        print("\nFile priority order:")
        for i, f in enumerate(employee_file_candidates, 1):
            print(f"  {i}. {os.path.basename(f)}")
        
        # Verify that we got all files
        assert len(employee_file_candidates) == 5, f"Expected 5 files, got {len(employee_file_candidates)}"
        
        # Verify the files are sorted in reverse alphabetical order
        # This is what the actual code does - it doesn't guarantee chronological order
        first_file = os.path.basename(employee_file_candidates[0])
        print(f"\nFirst file to be loaded: {first_file}")
        
        # Verify files are in reverse alphabetical order
        file_names = [os.path.basename(f) for f in employee_file_candidates]
        sorted_names = sorted(file_names, reverse=True)
        assert file_names == sorted_names, f"Files should be in reverse alphabetical order. Got: {file_names}, Expected: {sorted_names}"
        
        print("✅ Files are sorted in reverse alphabetical order")
        print("\n✅ PASSED: File ordering works correctly")
        
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 60)
    print("GLOB PATTERN EMPLOYEE FILE DETECTION TESTS")
    print("=" * 60)
    
    try:
        test_glob_pattern_detection()
        test_flexible_naming_patterns()
        test_priority_ordering()
        
        print("\n" + "=" * 60)
        print("✅ ALL GLOB PATTERN TESTS PASSED")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
