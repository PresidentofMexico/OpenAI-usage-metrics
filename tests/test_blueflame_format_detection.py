"""
Test suite for BlueFlame format detection fix

Tests that the detect_data_source() function in app.py correctly identifies
BlueFlame data files with the new YY-Mon format (e.g., '25-Apr', '25-Oct')
in addition to the original Mon-YY format (e.g., 'Sep-24', 'Oct-24').

This addresses the bug where files with YY-Mon format columns were incorrectly
detected as "Unknown" format, causing data upload failures.
"""

import pandas as pd
import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)


def detect_data_source(df):
    """
    Copy of the detect_data_source function from app.py for testing.
    This is the updated version with YY-Mon format support.
    """
    columns = df.columns.tolist()
    
    # OpenAI ChatGPT detection
    if 'gpt_messages' in columns or 'tool_messages' in columns:
        return 'ChatGPT'
    
    # BlueFlame AI detection - updated for all formats
    # Check for month columns in both formats:
    # - Mon-YY format (e.g., 'Sep-24', 'Oct-25')
    # - YY-Mon format (e.g., '25-Apr', '25-Sep')
    month_abbrevs = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    has_month_cols = any(
        col for col in columns 
        if len(col.split('-')) == 2 and (
            col.split('-')[0] in month_abbrevs or  # Mon-YY format
            col.split('-')[1] in month_abbrevs     # YY-Mon format
        )
    )
    
    if ('Metric' in columns and any(col.startswith('MoM Var') for col in columns)) or \
       ('Total Messages' in df.values if not df.empty else False) or \
       ('User ID' in columns and has_month_cols) or \
       ('Table' in columns and has_month_cols):
        return 'BlueFlame AI'
    
    # Default or ask user
    return 'Unknown'


def test_detect_yy_mon_format():
    """Test detection of new YY-Mon format (e.g., 25-Apr, 25-Sep)."""
    print("\n🧪 Testing YY-Mon Format Detection (New Format)...")
    
    # Create test data with YY-Mon format columns (the problematic format)
    df = pd.DataFrame({
        'Rank': [1, 2, 3],
        'User ID': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
        'Metric': ['', '', ''],
        '25-Apr': [100, 150, 200],
        '25-May': [120, 160, 210],
        '25-Jun': [130, 170, 220],
        '25-Jul': [140, 180, 230],
        '25-Aug': [150, 190, 240],
        '25-Sep': [160, 200, 250],
        '25-Oct': [170, 210, 260],
        'Total': [970, 1060, 1410]
    })
    
    detected = detect_data_source(df)
    assert detected == 'BlueFlame AI', f"Expected 'BlueFlame AI', got '{detected}'"
    print(f"✅ YY-Mon format correctly detected as: {detected}")
    
    return True


def test_detect_mon_yy_format():
    """Test detection of original Mon-YY format (e.g., Sep-24, Oct-24)."""
    print("\n🧪 Testing Mon-YY Format Detection (Original Format)...")
    
    # Create test data with Mon-YY format columns (backward compatibility)
    df = pd.DataFrame({
        'Table': ['Overall Monthly Trends', 'Overall Monthly Trends'],
        'Metric': ['Total Messages', 'Monthly Active Users (MAUs)'],
        'Sep-24': [1000, 25],
        'Oct-24': [1200, 28],
        'Nov-24': [1500, 32],
        'MoM Var Sep-24': [0, 0]
    })
    
    detected = detect_data_source(df)
    assert detected == 'BlueFlame AI', f"Expected 'BlueFlame AI', got '{detected}'"
    print(f"✅ Mon-YY format correctly detected as: {detected}")
    
    return True


def test_detect_mixed_formats():
    """Test detection with files that might have both formats (edge case)."""
    print("\n🧪 Testing Mixed Format Detection...")
    
    # Create test data with both formats (unlikely but test for robustness)
    df = pd.DataFrame({
        'User ID': ['user@test.com'],
        'Metric': [''],
        'Sep-24': [100],
        '25-Oct': [150]
    })
    
    detected = detect_data_source(df)
    assert detected == 'BlueFlame AI', f"Expected 'BlueFlame AI', got '{detected}'"
    print(f"✅ Mixed format correctly detected as: {detected}")
    
    return True


def test_detect_openai_format():
    """Test that OpenAI format detection still works (regression test)."""
    print("\n🧪 Testing OpenAI Format Detection (Regression Test)...")
    
    # Create test data with OpenAI format
    df = pd.DataFrame({
        'email': ['user@test.com'],
        'name': ['Test User'],
        'messages': [150],
        'gpt_messages': [50],
        'tool_messages': [25]
    })
    
    detected = detect_data_source(df)
    assert detected == 'ChatGPT', f"Expected 'ChatGPT', got '{detected}'"
    print(f"✅ OpenAI format correctly detected as: {detected}")
    
    return True


def test_detect_unknown_format():
    """Test that truly unknown formats are detected as 'Unknown'."""
    print("\n🧪 Testing Unknown Format Detection...")
    
    # Create test data with unrecognizable format
    df = pd.DataFrame({
        'RandomColumn1': [1, 2, 3],
        'RandomColumn2': ['a', 'b', 'c'],
        'SomeData': [100, 200, 300]
    })
    
    detected = detect_data_source(df)
    assert detected == 'Unknown', f"Expected 'Unknown', got '{detected}'"
    print(f"✅ Unknown format correctly detected as: {detected}")
    
    return True


def test_actual_file():
    """Test with the actual problematic file if it exists."""
    print("\n🧪 Testing with Actual Blueflame File...")
    
    file_path = os.path.join(project_root, 'BlueFlame User Data', 
                             'blueflame_usage_combined_October2025_normalized.csv')
    
    if not os.path.exists(file_path):
        print("⚠️  Actual file not found, skipping this test")
        return True
    
    try:
        df = pd.read_csv(file_path)
        detected = detect_data_source(df)
        
        assert detected == 'BlueFlame AI', f"Expected 'BlueFlame AI', got '{detected}'"
        print(f"✅ Actual file correctly detected as: {detected}")
        print(f"   File has {len(df)} rows with columns: {list(df.columns)[:5]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error testing actual file: {e}")
        return False


def run_all_tests():
    """Run all format detection tests."""
    print("=" * 70)
    print("🚀 Running BlueFlame Format Detection Tests")
    print("=" * 70)
    
    tests = [
        ("YY-Mon Format Detection", test_detect_yy_mon_format),
        ("Mon-YY Format Detection", test_detect_mon_yy_format),
        ("Mixed Format Detection", test_detect_mixed_formats),
        ("OpenAI Format Detection", test_detect_openai_format),
        ("Unknown Format Detection", test_detect_unknown_format),
        ("Actual File Detection", test_actual_file)
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
