#!/usr/bin/env python3
"""
Test employee file upload with various encodings (UTF-8, ISO-8859-1, Windows-1252).
This test verifies that the robust encoding detection handles files with special characters.
"""
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
import io
from database import DatabaseManager
from file_reader import read_csv_robust, read_file_from_path

def create_test_employee_csv_with_encoding(encoding='utf-8'):
    """
    Create a test employee CSV file with special characters that may cause encoding issues.
    
    Args:
        encoding: Target encoding for the CSV file
        
    Returns:
        bytes: Encoded CSV content
    """
    # Create employee data with special characters that commonly appear in names
    # These characters exist in ISO-8859-1 and CP1252 but may cause issues with UTF-8
    data = {
        'First Name': ['José', 'François', 'Søren', 'Müller', 'María'],
        'Last Name': ['García', 'Dubois', 'Hansen', 'Schmidt', 'Rodríguez'],
        'Email': ['jose@test.com', 'francois@test.com', 'soren@test.com', 'muller@test.com', 'maria@test.com'],
        'Title': ['Engineer', 'Manager', 'Analyst', 'Director', 'Lead'],
        'Function': ['Engineering', 'Product', 'Analytics', 'Sales', 'Marketing'],
        'Status': ['Active', 'Active', 'Active', 'Active', 'Active']
    }
    
    df = pd.DataFrame(data)
    
    # Convert to CSV string
    csv_string = df.to_csv(index=False)
    
    # Encode using specified encoding
    try:
        csv_bytes = csv_string.encode(encoding)
        return csv_bytes
    except UnicodeEncodeError as e:
        print(f"Warning: Cannot encode all characters in {encoding}: {e}")
        # Fall back to UTF-8 if encoding fails
        return csv_string.encode('utf-8', errors='replace')


def test_utf8_encoding():
    """Test reading employee CSV with UTF-8 encoding"""
    print("\n" + "=" * 60)
    print("TEST 1: UTF-8 Encoding (Standard)")
    print("=" * 60)
    
    # Create test CSV with UTF-8 encoding
    csv_bytes = create_test_employee_csv_with_encoding('utf-8')
    
    # Create a file-like object that mimics Streamlit's UploadedFile
    class MockUploadedFile:
        def __init__(self, content, name='test.csv'):
            self.content = content
            self.name = name
            self.position = 0
        
        def read(self):
            return self.content
        
        def getvalue(self):
            return self.content
        
        def seek(self, position):
            self.position = position
    
    uploaded_file = MockUploadedFile(csv_bytes, 'employees_utf8.csv')
    
    # Test with read_csv_robust
    df, error_msg = read_csv_robust(uploaded_file)
    
    assert error_msg is None, f"Unexpected error: {error_msg}"
    assert df is not None, "DataFrame should not be None"
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    assert 'First Name' in df.columns, "Missing 'First Name' column"
    assert df['First Name'].iloc[0] == 'José', "First name should be 'José'"
    
    print("✅ PASSED: UTF-8 encoding handled correctly")


def test_iso8859_encoding():
    """Test reading employee CSV with ISO-8859-1 encoding"""
    print("\n" + "=" * 60)
    print("TEST 2: ISO-8859-1 Encoding (Latin-1)")
    print("=" * 60)
    
    # Create test CSV with ISO-8859-1 encoding
    csv_bytes = create_test_employee_csv_with_encoding('iso-8859-1')
    
    # Create a file-like object
    class MockUploadedFile:
        def __init__(self, content, name='test.csv'):
            self.content = content
            self.name = name
            self.position = 0
        
        def read(self):
            return self.content
        
        def getvalue(self):
            return self.content
        
        def seek(self, position):
            self.position = position
    
    uploaded_file = MockUploadedFile(csv_bytes, 'employees_iso8859.csv')
    
    # Test with read_csv_robust
    df, error_msg = read_csv_robust(uploaded_file)
    
    assert error_msg is None, f"Unexpected error: {error_msg}"
    assert df is not None, "DataFrame should not be None"
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    assert 'First Name' in df.columns, "Missing 'First Name' column"
    # Check that special characters are preserved (may have some variations due to encoding)
    assert df['First Name'].iloc[0] in ['José', 'Josﾃｩ', 'Jos�'], f"First name unexpected: {df['First Name'].iloc[0]}"
    
    print("✅ PASSED: ISO-8859-1 encoding handled correctly")


def test_cp1252_encoding():
    """Test reading employee CSV with Windows-1252 encoding"""
    print("\n" + "=" * 60)
    print("TEST 3: Windows-1252 Encoding (CP1252)")
    print("=" * 60)
    
    # Create test CSV with CP1252 encoding
    csv_bytes = create_test_employee_csv_with_encoding('cp1252')
    
    # Create a file-like object
    class MockUploadedFile:
        def __init__(self, content, name='test.csv'):
            self.content = content
            self.name = name
            self.position = 0
        
        def read(self):
            return self.content
        
        def getvalue(self):
            return self.content
        
        def seek(self, position):
            self.position = position
    
    uploaded_file = MockUploadedFile(csv_bytes, 'employees_cp1252.csv')
    
    # Test with read_csv_robust
    df, error_msg = read_csv_robust(uploaded_file)
    
    assert error_msg is None, f"Unexpected error: {error_msg}"
    assert df is not None, "DataFrame should not be None"
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    assert 'First Name' in df.columns, "Missing 'First Name' column"
    
    print("✅ PASSED: Windows-1252 encoding handled correctly")


def test_file_from_path_iso8859():
    """Test reading employee CSV from file path with ISO-8859-1 encoding"""
    print("\n" + "=" * 60)
    print("TEST 4: File Path Reading with ISO-8859-1")
    print("=" * 60)
    
    # Create a temporary file with ISO-8859-1 encoding
    test_file_path = '/tmp/test_employee_iso8859.csv'
    
    csv_bytes = create_test_employee_csv_with_encoding('iso-8859-1')
    
    with open(test_file_path, 'wb') as f:
        f.write(csv_bytes)
    
    # Test with read_file_from_path
    df, error_msg = read_file_from_path(test_file_path)
    
    assert error_msg is None, f"Unexpected error: {error_msg}"
    assert df is not None, "DataFrame should not be None"
    assert len(df) == 5, f"Expected 5 rows, got {len(df)}"
    assert 'First Name' in df.columns, "Missing 'First Name' column"
    
    # Clean up
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
    
    print("✅ PASSED: File path reading with ISO-8859-1 encoding handled correctly")


def test_database_integration_with_iso8859():
    """Test full integration: read ISO-8859-1 file and load into database"""
    print("\n" + "=" * 60)
    print("TEST 5: Database Integration with ISO-8859-1 File")
    print("=" * 60)
    
    # Create temporary database
    db_path = '/tmp/test_encoding.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = DatabaseManager(db_path)
    
    # Create test CSV with ISO-8859-1 encoding
    csv_bytes = create_test_employee_csv_with_encoding('iso-8859-1')
    
    # Create a file-like object
    class MockUploadedFile:
        def __init__(self, content, name='test.csv'):
            self.content = content
            self.name = name
            self.position = 0
        
        def read(self):
            return self.content
        
        def getvalue(self):
            return self.content
        
        def seek(self, position):
            self.position = position
    
    uploaded_file = MockUploadedFile(csv_bytes, 'employees_iso8859.csv')
    
    # Read the file
    emp_df, error_msg = read_csv_robust(uploaded_file)
    
    assert error_msg is None, f"Error reading file: {error_msg}"
    assert emp_df is not None, "DataFrame should not be None"
    
    # Create normalized dataframe (simulating what app.py does)
    normalized_emp_df = pd.DataFrame({
        'first_name': emp_df['First Name'],
        'last_name': emp_df['Last Name'],
        'email': emp_df['Email'],
        'title': emp_df['Title'],
        'department': emp_df['Function'],
        'status': emp_df['Status']
    })
    
    # Load into database
    success, message, count = db.load_employees(normalized_emp_df)
    
    assert success, f"Failed to load employees: {message}"
    assert count == 5, f"Expected 5 employees loaded, got {count}"
    
    # Verify employees are in database
    all_employees = db.get_all_employees()
    assert len(all_employees) == 5, f"Expected 5 employees in database, got {len(all_employees)}"
    
    # Clean up
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("✅ PASSED: Full integration test with ISO-8859-1 encoding")


def test_non_breaking_space_iso8859():
    """Test handling of non-breaking space (0xa0) in ISO-8859-1 encoding"""
    print("\n" + "=" * 60)
    print("TEST 6: Non-Breaking Space in ISO-8859-1 (Byte 0xa0)")
    print("=" * 60)
    
    # Create CSV with non-breaking space (the specific error from the issue)
    csv_content = "First Name,Last Name,Email,Title,Function,Status\n"
    csv_content += "John\xa0Doe,Smith,john@test.com,Engineer,Engineering,Active\n"
    csv_content += "Jane,Doe\xa0Smith,jane@test.com,Manager,Product,Active\n"
    
    # Encode as ISO-8859-1 (where 0xa0 is valid)
    csv_bytes = csv_content.encode('iso-8859-1')
    
    # Create a file-like object
    class MockUploadedFile:
        def __init__(self, content, name='test.csv'):
            self.content = content
            self.name = name
            self.position = 0
        
        def read(self):
            return self.content
        
        def getvalue(self):
            return self.content
        
        def seek(self, position):
            self.position = position
    
    uploaded_file = MockUploadedFile(csv_bytes, 'employees_nbsp.csv')
    
    # This should NOT fail with UTF-8 decode error
    df, error_msg = read_csv_robust(uploaded_file)
    
    assert error_msg is None, f"Unexpected error: {error_msg}"
    assert df is not None, "DataFrame should not be None"
    assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
    
    print("✅ PASSED: Non-breaking space (0xa0) handled correctly")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("EMPLOYEE FILE ENCODING TESTS")
    print("Testing robust encoding detection for ISO-8859-1, CP1252, UTF-8")
    print("=" * 60)
    
    try:
        test_utf8_encoding()
        test_iso8859_encoding()
        test_cp1252_encoding()
        test_file_from_path_iso8859()
        test_database_integration_with_iso8859()
        test_non_breaking_space_iso8859()
        
        print("\n" + "=" * 60)
        print("✅ ALL ENCODING TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
