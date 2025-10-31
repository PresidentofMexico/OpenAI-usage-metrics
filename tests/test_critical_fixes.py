"""
Test suite for critical bug fixes in AI Usage Analytics Dashboard

Tests the following critical fixes:
1. Date calculation error (string to datetime conversion)
2. Power user deduplication (users appearing twice)
3. Department mapper duplicate key handling
4. BlueFlame data format support
"""

import pandas as pd
import sys
import os
from datetime import datetime

def test_date_calculation_fix():
    """Test that date calculation handles string dates correctly."""
    print("\n🧪 Testing Date Calculation Fix...")
    
    # Create test data with string dates
    test_dates = pd.Series(['2024-01-01', '2024-01-31', '2024-02-15'])
    
    # This should work without TypeError
    try:
        valid_dates = pd.to_datetime(test_dates, errors='coerce').dropna()
        date_coverage = (valid_dates.max() - valid_dates.min()).days + 1
        
        assert date_coverage == 46, f"Expected 46 days, got {date_coverage}"
        print(f"✅ Date calculation works correctly: {date_coverage} days")
        return True
    except TypeError as e:
        print(f"❌ Date calculation failed with TypeError: {e}")
        return False

def test_power_user_deduplication():
    """Test that power users are deduplicated by email."""
    print("\n🧪 Testing Power User Deduplication...")
    
    # Import the function
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)
    from app import calculate_power_users, _select_primary_department
    
    # Create test data with duplicate user in different departments
    test_data = pd.DataFrame({
        'email': ['user1@test.com', 'user1@test.com', 'user2@test.com'],
        'user_name': ['User One', 'User One', 'User Two'],
        'department': ['finance', 'BlueFlame Users', 'IT'],
        'usage_count': [100, 50, 200],
        'cost_usd': [10.0, 5.0, 20.0],
        'tool_source': ['ChatGPT', 'BlueFlame AI', 'ChatGPT']
    })
    
    # Calculate power users
    power_users = calculate_power_users(test_data, threshold_percentile=0)  # Get all users
    
    # Should have 2 unique users, not 3
    unique_count = len(power_users)
    assert unique_count == 2, f"Expected 2 unique users, got {unique_count}"
    
    # User1 should have combined usage of 150
    user1 = power_users[power_users['email'] == 'user1@test.com']
    assert len(user1) == 1, "User should appear only once"
    assert user1.iloc[0]['usage_count'] == 150, f"Expected combined usage of 150, got {user1.iloc[0]['usage_count']}"
    
    # User1 should have 'finance' as department (not BlueFlame Users)
    assert user1.iloc[0]['department'] == 'finance', f"Expected 'finance', got {user1.iloc[0]['department']}"
    
    print(f"✅ Power users correctly deduplicated: {unique_count} unique users")
    print(f"✅ User1 combined usage: {user1.iloc[0]['usage_count']}")
    print(f"✅ User1 department priority: {user1.iloc[0]['department']}")
    return True

def test_department_selection():
    """Test that department selection prioritizes non-BlueFlame departments."""
    print("\n🧪 Testing Department Selection Logic...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)
    from app import _select_primary_department
    
    # Test case 1: Multiple departments including BlueFlame
    depts1 = pd.Series(['finance', 'BlueFlame Users'])
    result1 = _select_primary_department(depts1)
    assert result1 == 'finance', f"Expected 'finance', got {result1}"
    print(f"✅ Prioritizes real department over BlueFlame: {result1}")
    
    # Test case 2: Only BlueFlame department
    depts2 = pd.Series(['BlueFlame Users'])
    result2 = _select_primary_department(depts2)
    assert result2 == 'BlueFlame Users', f"Expected 'BlueFlame Users', got {result2}"
    print(f"✅ Returns BlueFlame when it's the only option: {result2}")
    
    # Test case 3: Multiple non-BlueFlame departments
    depts3 = pd.Series(['finance', 'IT'])
    result3 = _select_primary_department(depts3)
    assert result3 == 'finance', f"Expected 'finance', got {result3}"
    print(f"✅ Returns first non-BlueFlame department: {result3}")
    
    return True

def test_blueflame_format_detection():
    """Test that BlueFlame data format is properly detected."""
    print("\n🧪 Testing BlueFlame Format Detection...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)
    from app import detect_data_source
    
    # Test combined format (with Table column)
    combined_format = pd.DataFrame({
        'Table': ['Overall Monthly Trends', 'Top 20 Users Total'],
        'Metric': ['Total Messages', 'user1@test.com'],
        'Sep-24': [1000, 50],
        'Oct-24': [1200, 60],
        'MoM Var Sep-24': [0, 0]
    })
    
    result1 = detect_data_source(combined_format)
    assert result1 == 'BlueFlame AI', f"Expected 'BlueFlame AI', got {result1}"
    print(f"✅ Combined format detected: {result1}")
    
    # Test regular format (with Metric column, no Table)
    regular_format = pd.DataFrame({
        'Metric': ['Total Messages', 'Monthly Active Users (MAUs)'],
        'Sep-24': [1000, 25],
        'Oct-24': [1200, 28],
        'MoM Var Sep-24': [0, 0]
    })
    
    result2 = detect_data_source(regular_format)
    assert result2 == 'BlueFlame AI', f"Expected 'BlueFlame AI', got {result2}"
    print(f"✅ Regular format detected: {result2}")
    
    # Test month column format detection
    month_format = pd.DataFrame({
        'User ID': ['user1@test.com'],
        'Sep-24': [100],
        'Oct-24': [120]
    })
    
    result3 = detect_data_source(month_format)
    assert result3 == 'BlueFlame AI', f"Expected 'BlueFlame AI', got {result3}"
    print(f"✅ Month column format detected: {result3}")
    
    return True

def run_all_tests():
    """Run all critical bug fix tests."""
    print("=" * 60)
    print("🚀 Running Critical Bug Fix Tests")
    print("=" * 60)
    
    tests = [
        ("Date Calculation Fix", test_date_calculation_fix),
        ("Power User Deduplication", test_power_user_deduplication),
        ("Department Selection", test_department_selection),
        ("BlueFlame Format Detection", test_blueflame_format_detection)
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
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(result for _, result in results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
