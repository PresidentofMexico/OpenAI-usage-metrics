"""
Comprehensive test suite for ROI utilities and metrics.

Tests all major ROI calculation functions including:
- Mapping usage events to estimated hours/value
- Edge cases (zero usage, unknown department, future/invalid dates)
- Per-user ROI metrics
- Per-department ROI metrics
- Composite ROI calculations
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from roi_utils import (
    estimate_hours_saved,
    calculate_monetary_value,
    calculate_roi_per_user,
    calculate_roi_per_department,
    calculate_composite_roi,
    validate_date_field,
    DEFAULT_ROI_CONFIG
)


def test_estimate_hours_saved_basic():
    """Test basic hours saved calculation for standard messages."""
    print("\n🧪 Testing estimate_hours_saved - Basic Calculation")
    
    # Test standard ChatGPT messages (5 min per message)
    hours = estimate_hours_saved(60, 'ChatGPT Messages')
    expected = 5.0  # 60 messages * 5 min / 60 = 5 hours
    assert hours == expected, f"Expected {expected} hours, got {hours}"
    print(f"✅ Standard messages: 60 messages = {hours} hours")
    
    # Test tool messages (10 min per message)
    hours = estimate_hours_saved(30, 'Tool Messages')
    expected = 5.0  # 30 messages * 10 min / 60 = 5 hours
    assert hours == expected, f"Expected {expected} hours, got {hours}"
    print(f"✅ Tool messages: 30 messages = {hours} hours")
    
    # Test project messages (15 min per message)
    hours = estimate_hours_saved(20, 'Project Messages')
    expected = 5.0  # 20 messages * 15 min / 60 = 5 hours
    assert hours == expected, f"Expected {expected} hours, got {hours}"
    print(f"✅ Project messages: 20 messages = {hours} hours")
    
    return True


def test_estimate_hours_saved_edge_cases():
    """Test hours saved calculation with edge cases."""
    print("\n🧪 Testing estimate_hours_saved - Edge Cases")
    
    # Test zero usage
    hours = estimate_hours_saved(0, 'ChatGPT Messages')
    assert hours == 0.0, f"Expected 0.0 for zero usage, got {hours}"
    print(f"✅ Zero usage: {hours} hours")
    
    # Test negative usage (should return 0)
    hours = estimate_hours_saved(-10, 'ChatGPT Messages')
    assert hours == 0.0, f"Expected 0.0 for negative usage, got {hours}"
    print(f"✅ Negative usage: {hours} hours")
    
    # Test None usage
    hours = estimate_hours_saved(None, 'ChatGPT Messages')
    assert hours == 0.0, f"Expected 0.0 for None usage, got {hours}"
    print(f"✅ None usage: {hours} hours")
    
    # Test NaN usage
    hours = estimate_hours_saved(np.nan, 'ChatGPT Messages')
    assert hours == 0.0, f"Expected 0.0 for NaN usage, got {hours}"
    print(f"✅ NaN usage: {hours} hours")
    
    # Test float usage
    hours = estimate_hours_saved(12.5, 'ChatGPT Messages')
    expected = 1.04  # 12.5 * 5 / 60 = 1.041666...
    assert abs(hours - expected) < 0.01, f"Expected ~{expected} hours, got {hours}"
    print(f"✅ Float usage: 12.5 messages = {hours} hours")
    
    return True


def test_estimate_hours_saved_custom_config():
    """Test hours saved calculation with custom configuration."""
    print("\n🧪 Testing estimate_hours_saved - Custom Configuration")
    
    # Custom config with different time estimates
    custom_config = {
        'minutes_saved_per_message': 10,  # Double the default
        'minutes_saved_per_tool_message': 20,
        'minutes_saved_per_project_message': 30
    }
    
    hours = estimate_hours_saved(30, 'ChatGPT Messages', config=custom_config)
    expected = 5.0  # 30 messages * 10 min / 60 = 5 hours
    assert hours == expected, f"Expected {expected} hours, got {hours}"
    print(f"✅ Custom config (10 min/msg): 30 messages = {hours} hours")
    
    return True


def test_calculate_monetary_value_basic():
    """Test basic monetary value calculation."""
    print("\n🧪 Testing calculate_monetary_value - Basic Calculation")
    
    # Test Engineering department
    value = calculate_monetary_value(10, 'Engineering')
    expected = 750.0  # 10 hours * $75/hour
    assert value == expected, f"Expected ${expected}, got ${value}"
    print(f"✅ Engineering: 10 hours = ${value}")
    
    # Test Finance department
    value = calculate_monetary_value(10, 'Finance')
    expected = 700.0  # 10 hours * $70/hour
    assert value == expected, f"Expected ${expected}, got ${value}"
    print(f"✅ Finance: 10 hours = ${value}")
    
    # Test Unknown department (default rate)
    value = calculate_monetary_value(10, 'Unknown')
    expected = 500.0  # 10 hours * $50/hour
    assert value == expected, f"Expected ${expected}, got ${value}"
    print(f"✅ Unknown department: 10 hours = ${value}")
    
    return True


def test_calculate_monetary_value_edge_cases():
    """Test monetary value calculation with edge cases."""
    print("\n🧪 Testing calculate_monetary_value - Edge Cases")
    
    # Test zero hours
    value = calculate_monetary_value(0, 'Engineering')
    assert value == 0.0, f"Expected $0.0 for zero hours, got ${value}"
    print(f"✅ Zero hours: ${value}")
    
    # Test negative hours (should return 0)
    value = calculate_monetary_value(-5, 'Engineering')
    assert value == 0.0, f"Expected $0.0 for negative hours, got ${value}"
    print(f"✅ Negative hours: ${value}")
    
    # Test None hours
    value = calculate_monetary_value(None, 'Engineering')
    assert value == 0.0, f"Expected $0.0 for None hours, got ${value}"
    print(f"✅ None hours: ${value}")
    
    # Test NaN hours
    value = calculate_monetary_value(np.nan, 'Engineering')
    assert value == 0.0, f"Expected $0.0 for NaN hours, got ${value}"
    print(f"✅ NaN hours: ${value}")
    
    # Test unknown department (should use default)
    value = calculate_monetary_value(10, 'NonExistentDept')
    expected = 500.0  # 10 hours * $50/hour (default)
    assert value == expected, f"Expected ${expected}, got ${value}"
    print(f"✅ Unknown dept with fallback: ${value}")
    
    # Test custom hourly rate override
    value = calculate_monetary_value(10, 'Engineering', hourly_rate=100)
    expected = 1000.0  # 10 hours * $100/hour (override)
    assert value == expected, f"Expected ${expected}, got ${value}"
    print(f"✅ Custom hourly rate override: ${value}")
    
    return True


def test_calculate_roi_per_user():
    """Test per-user ROI calculation."""
    print("\n🧪 Testing calculate_roi_per_user")
    
    # Create test data with multiple users
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user1@test.com', 'user2@test.com', 'user2@test.com'],
        'user_name': ['Alice', 'Alice', 'Bob', 'Bob'],
        'department': ['Engineering', 'Engineering', 'Finance', 'Finance'],
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages', 'ChatGPT Messages'],
        'usage_count': [60, 30, 120, 0]  # Alice: 60+30, Bob: 120+0
    })
    
    result = calculate_roi_per_user(test_data)
    
    # Validate structure
    assert len(result) == 2, f"Expected 2 users, got {len(result)}"
    assert 'user_id' in result.columns, "Missing user_id column"
    assert 'hours_saved' in result.columns, "Missing hours_saved column"
    assert 'monetary_value_usd' in result.columns, "Missing monetary_value_usd column"
    print(f"✅ Result has correct structure with {len(result)} users")
    
    # Validate Alice's metrics
    alice = result[result['user_id'] == 'user1@test.com'].iloc[0]
    # Alice: 60 msgs * 5 min + 30 msgs * 10 min = 300 + 300 = 600 min = 10 hours
    assert alice['hours_saved'] == 10.0, f"Alice hours: expected 10.0, got {alice['hours_saved']}"
    # Alice: 10 hours * $75 (Engineering) = $750
    assert alice['monetary_value_usd'] == 750.0, f"Alice value: expected $750, got ${alice['monetary_value_usd']}"
    print(f"✅ Alice metrics: {alice['hours_saved']} hours, ${alice['monetary_value_usd']}")
    
    # Validate Bob's metrics
    bob = result[result['user_id'] == 'user2@test.com'].iloc[0]
    # Bob: 120 msgs * 5 min = 600 min = 10 hours
    assert bob['hours_saved'] == 10.0, f"Bob hours: expected 10.0, got {bob['hours_saved']}"
    # Bob: 10 hours * $70 (Finance) = $700
    assert bob['monetary_value_usd'] == 700.0, f"Bob value: expected $700, got ${bob['monetary_value_usd']}"
    print(f"✅ Bob metrics: {bob['hours_saved']} hours, ${bob['monetary_value_usd']}")
    
    return True


def test_calculate_roi_per_user_edge_cases():
    """Test per-user ROI calculation with edge cases."""
    print("\n🧪 Testing calculate_roi_per_user - Edge Cases")
    
    # Test empty dataframe
    empty_df = pd.DataFrame()
    result = calculate_roi_per_user(empty_df)
    assert result.empty, "Expected empty result for empty input"
    print("✅ Empty dataframe handled correctly")
    
    # Test missing required columns
    bad_df = pd.DataFrame({'name': ['Alice'], 'count': [100]})
    try:
        result = calculate_roi_per_user(bad_df)
        assert False, "Should have raised ValueError for missing columns"
    except ValueError as e:
        assert 'Missing required columns' in str(e), f"Unexpected error message: {e}"
        print("✅ Missing columns detected correctly")
    
    # Test user with zero usage
    zero_usage_df = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'user_name': ['Alice'],
        'department': ['Engineering'],
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [0]
    })
    result = calculate_roi_per_user(zero_usage_df)
    assert len(result) == 1, "Should have one user"
    assert result.iloc[0]['hours_saved'] == 0.0, "Zero usage should give zero hours"
    assert result.iloc[0]['monetary_value_usd'] == 0.0, "Zero usage should give zero value"
    print("✅ Zero usage user handled correctly")
    
    # Test user with unknown department
    unknown_dept_df = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'user_name': ['Alice'],
        'department': ['SomethingNew'],
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [60]
    })
    result = calculate_roi_per_user(unknown_dept_df)
    assert len(result) == 1, "Should have one user"
    # 60 msgs * 5 min / 60 = 5 hours
    assert result.iloc[0]['hours_saved'] == 5.0, f"Expected 5.0 hours, got {result.iloc[0]['hours_saved']}"
    # 5 hours * $50 (default) = $250
    assert result.iloc[0]['monetary_value_usd'] == 250.0, f"Expected $250, got {result.iloc[0]['monetary_value_usd']}"
    print("✅ Unknown department uses default rate")
    
    return True


def test_calculate_roi_per_department():
    """Test per-department ROI calculation."""
    print("\n🧪 Testing calculate_roi_per_department")
    
    # Create test data with multiple departments
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com', 'user4@test.com'],
        'department': ['Engineering', 'Engineering', 'Finance', 'Finance'],
        'feature_used': ['ChatGPT Messages', 'ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages'],
        'usage_count': [60, 120, 30, 60]
    })
    
    result = calculate_roi_per_department(test_data)
    
    # Validate structure
    assert len(result) == 2, f"Expected 2 departments, got {len(result)}"
    assert 'department' in result.columns, "Missing department column"
    assert 'hours_saved' in result.columns, "Missing hours_saved column"
    assert 'monetary_value_usd' in result.columns, "Missing monetary_value_usd column"
    assert 'active_users' in result.columns, "Missing active_users column"
    assert 'avg_value_per_user' in result.columns, "Missing avg_value_per_user column"
    print(f"✅ Result has correct structure with {len(result)} departments")
    
    # Validate Engineering metrics
    eng = result[result['department'] == 'Engineering'].iloc[0]
    assert eng['active_users'] == 2, f"Engineering users: expected 2, got {eng['active_users']}"
    # Engineering: (60 + 120) * 5 min / 60 = 15 hours
    assert eng['hours_saved'] == 15.0, f"Engineering hours: expected 15.0, got {eng['hours_saved']}"
    # Engineering: 15 hours * $75 = $1125
    assert eng['monetary_value_usd'] == 1125.0, f"Engineering value: expected $1125, got ${eng['monetary_value_usd']}"
    # Avg per user: $1125 / 2 = $562.50
    assert eng['avg_value_per_user'] == 562.5, f"Engineering avg: expected $562.5, got ${eng['avg_value_per_user']}"
    print(f"✅ Engineering: {eng['active_users']} users, {eng['hours_saved']} hours, ${eng['monetary_value_usd']}")
    
    # Validate Finance metrics
    fin = result[result['department'] == 'Finance'].iloc[0]
    assert fin['active_users'] == 2, f"Finance users: expected 2, got {fin['active_users']}"
    # Finance: 30 tool msgs * 10 min + 60 msgs * 5 min = 300 + 300 = 600 min = 10 hours
    assert fin['hours_saved'] == 10.0, f"Finance hours: expected 10.0, got {fin['hours_saved']}"
    # Finance: 10 hours * $70 = $700
    assert fin['monetary_value_usd'] == 700.0, f"Finance value: expected $700, got ${fin['monetary_value_usd']}"
    print(f"✅ Finance: {fin['active_users']} users, {fin['hours_saved']} hours, ${fin['monetary_value_usd']}")
    
    return True


def test_calculate_roi_per_department_edge_cases():
    """Test per-department ROI calculation with edge cases."""
    print("\n🧪 Testing calculate_roi_per_department - Edge Cases")
    
    # Test empty dataframe
    empty_df = pd.DataFrame()
    result = calculate_roi_per_department(empty_df)
    assert result.empty, "Expected empty result for empty input"
    print("✅ Empty dataframe handled correctly")
    
    # Test missing department column (should default to 'Unknown')
    no_dept_df = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [60]
    })
    result = calculate_roi_per_department(no_dept_df)
    assert len(result) == 1, "Should have one department"
    assert result.iloc[0]['department'] == 'Unknown', f"Expected 'Unknown', got {result.iloc[0]['department']}"
    print("✅ Missing department defaults to 'Unknown'")
    
    # Test department with zero total usage
    zero_usage_df = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com'],
        'department': ['Marketing', 'Marketing'],
        'feature_used': ['ChatGPT Messages', 'ChatGPT Messages'],
        'usage_count': [0, 0]
    })
    result = calculate_roi_per_department(zero_usage_df)
    marketing = result[result['department'] == 'Marketing'].iloc[0]
    assert marketing['hours_saved'] == 0.0, "Zero usage should give zero hours"
    assert marketing['monetary_value_usd'] == 0.0, "Zero usage should give zero value"
    print("✅ Department with zero usage handled correctly")
    
    return True


def test_calculate_composite_roi():
    """Test composite ROI calculation across all data."""
    print("\n🧪 Testing calculate_composite_roi")
    
    # Create comprehensive test data
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
        'department': ['Engineering', 'Finance', 'Engineering'],
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'ChatGPT Messages'],
        'usage_count': [60, 30, 120],
        'date': ['2024-01-01', '2024-01-15', '2024-02-01']
    })
    
    result = calculate_composite_roi(test_data)
    
    # Validate structure
    assert 'total_hours_saved' in result, "Missing total_hours_saved"
    assert 'total_monetary_value_usd' in result, "Missing total_monetary_value_usd"
    assert 'total_users' in result, "Missing total_users"
    assert 'total_usage_events' in result, "Missing total_usage_events"
    assert 'avg_hours_per_user' in result, "Missing avg_hours_per_user"
    assert 'avg_value_per_user' in result, "Missing avg_value_per_user"
    assert 'date_range' in result, "Missing date_range"
    assert 'monthly_average_value' in result, "Missing monthly_average_value"
    print("✅ Result has all required fields")
    
    # Validate total users
    assert result['total_users'] == 3, f"Expected 3 users, got {result['total_users']}"
    print(f"✅ Total users: {result['total_users']}")
    
    # Validate total usage
    assert result['total_usage_events'] == 210, f"Expected 210 events, got {result['total_usage_events']}"
    print(f"✅ Total usage: {result['total_usage_events']}")
    
    # Validate total hours
    # user1: 60 * 5 min = 300 min = 5 hours (Engineering)
    # user2: 30 * 10 min = 300 min = 5 hours (Finance, tool msgs)
    # user3: 120 * 5 min = 600 min = 10 hours (Engineering)
    # Total: 20 hours
    assert result['total_hours_saved'] == 20.0, f"Expected 20.0 hours, got {result['total_hours_saved']}"
    print(f"✅ Total hours saved: {result['total_hours_saved']}")
    
    # Validate total value
    # user1: 5 hours * $75 = $375
    # user2: 5 hours * $70 = $350
    # user3: 10 hours * $75 = $750
    # Total: $1475
    assert result['total_monetary_value_usd'] == 1475.0, f"Expected $1475, got ${result['total_monetary_value_usd']}"
    print(f"✅ Total value: ${result['total_monetary_value_usd']}")
    
    # Validate averages
    expected_avg_hours = 20.0 / 3  # 6.67 hours
    assert abs(result['avg_hours_per_user'] - expected_avg_hours) < 0.01, f"Expected ~{expected_avg_hours} avg hours, got {result['avg_hours_per_user']}"
    
    expected_avg_value = 1475.0 / 3  # 491.67
    assert abs(result['avg_value_per_user'] - expected_avg_value) < 0.01, f"Expected ~{expected_avg_value} avg value, got {result['avg_value_per_user']}"
    print(f"✅ Averages: {result['avg_hours_per_user']} hours/user, ${result['avg_value_per_user']}/user")
    
    # Validate date range
    assert result['date_range'] is not None, "Date range should not be None"
    assert '2024-01-01' in result['date_range'], "Date range should include start date"
    assert '2024-02-01' in result['date_range'], "Date range should include end date"
    print(f"✅ Date range: {result['date_range']}")
    
    # Validate monthly average is calculated
    assert result['monthly_average_value'] > 0, f"Monthly average should be > 0, got {result['monthly_average_value']}"
    print(f"✅ Monthly average: ${result['monthly_average_value']}")
    
    return True


def test_calculate_composite_roi_edge_cases():
    """Test composite ROI calculation with edge cases."""
    print("\n🧪 Testing calculate_composite_roi - Edge Cases")
    
    # Test empty dataframe
    empty_df = pd.DataFrame()
    result = calculate_composite_roi(empty_df)
    assert result['total_hours_saved'] == 0.0, "Empty data should give zero hours"
    assert result['total_monetary_value_usd'] == 0.0, "Empty data should give zero value"
    assert result['total_users'] == 0, "Empty data should have zero users"
    print("✅ Empty dataframe handled correctly")
    
    # Test with invalid dates
    invalid_dates_df = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'department': ['Engineering'],
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [60],
        'date': ['invalid-date']
    })
    result = calculate_composite_roi(invalid_dates_df)
    # Should still calculate hours and value, but date_range might be None
    assert result['total_hours_saved'] == 5.0, f"Expected 5.0 hours despite invalid date, got {result['total_hours_saved']}"
    print("✅ Invalid dates handled gracefully")
    
    # Test with future dates (should still calculate, validation is separate)
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    future_dates_df = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'department': ['Engineering'],
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [60],
        'date': [future_date]
    })
    result = calculate_composite_roi(future_dates_df)
    assert result['total_hours_saved'] == 5.0, f"Expected 5.0 hours, got {result['total_hours_saved']}"
    print("✅ Future dates processed (validation is separate)")
    
    return True


def test_validate_date_field():
    """Test date field validation."""
    print("\n🧪 Testing validate_date_field")
    
    # Test valid past date (string)
    assert validate_date_field('2024-01-01') == True, "Valid past date should return True"
    print("✅ Valid past date (string): True")
    
    # Test valid past date (datetime)
    past_date = datetime(2024, 1, 1)
    assert validate_date_field(past_date) == True, "Valid past date (datetime) should return True"
    print("✅ Valid past date (datetime): True")
    
    # Test today (should be valid)
    today = datetime.now().date()
    assert validate_date_field(today) == True, "Today should be valid"
    print("✅ Today: True")
    
    # Test future date (should be invalid)
    future_date = datetime.now() + timedelta(days=30)
    assert validate_date_field(future_date) == False, "Future date should return False"
    print("✅ Future date: False")
    
    # Test invalid string
    assert validate_date_field('not-a-date') == False, "Invalid date string should return False"
    print("✅ Invalid date string: False")
    
    # Test None
    assert validate_date_field(None) == False, "None should return False"
    print("✅ None: False")
    
    # Test NaN
    assert validate_date_field(np.nan) == False, "NaN should return False"
    print("✅ NaN: False")
    
    # Test empty string
    assert validate_date_field('') == False, "Empty string should return False"
    print("✅ Empty string: False")
    
    return True


def test_with_sample_csv():
    """Test ROI calculations with actual sample CSV data from the repository."""
    print("\n🧪 Testing with Sample CSV Data")
    
    # Try to load sample CSV from repository
    sample_files = [
        'sample_monthly_data.csv',
        'sample_weekly_data.csv',
        'OpenAI User Data/sample.csv'
    ]
    
    sample_loaded = False
    for sample_file in sample_files:
        full_path = os.path.join(project_root, sample_file)
        if os.path.exists(full_path):
            try:
                df = pd.read_csv(full_path)
                print(f"📂 Loaded sample file: {sample_file}")
                print(f"   Rows: {len(df)}, Columns: {list(df.columns)[:5]}...")
                
                # Try to process if it has the right structure
                if 'email' in df.columns or 'user_email' in df.columns:
                    # Normalize to expected format
                    test_df = pd.DataFrame()
                    test_df['user_id'] = df.get('email', df.get('user_email', []))
                    test_df['user_name'] = df.get('name', df.get('user_name', ['User'] * len(df)))
                    test_df['department'] = df.get('department', ['Unknown'] * len(df))
                    test_df['feature_used'] = 'ChatGPT Messages'
                    test_df['usage_count'] = df.get('messages', df.get('usage_count', [10] * len(df)))
                    
                    # Calculate ROI metrics
                    if not test_df.empty and test_df['user_id'].notna().any():
                        composite = calculate_composite_roi(test_df)
                        print(f"   Total hours saved: {composite['total_hours_saved']}")
                        print(f"   Total value: ${composite['total_monetary_value_usd']}")
                        print(f"   Total users: {composite['total_users']}")
                        sample_loaded = True
                        break
            except Exception as e:
                print(f"   ⚠️  Could not process {sample_file}: {e}")
    
    if sample_loaded:
        print("✅ Successfully tested with sample CSV data")
    else:
        print("ℹ️  No suitable sample CSV found - creating synthetic data")
        # Create synthetic data for testing
        synthetic_df = pd.DataFrame({
            'user_id': [f'user{i}@test.com' for i in range(1, 11)],
            'user_name': [f'User {i}' for i in range(1, 11)],
            'department': ['Engineering'] * 3 + ['Finance'] * 3 + ['Marketing'] * 4,
            'feature_used': ['ChatGPT Messages'] * 10,
            'usage_count': [100, 80, 60, 50, 40, 30, 25, 20, 15, 10]
        })
        composite = calculate_composite_roi(synthetic_df)
        print(f"   Total hours saved: {composite['total_hours_saved']}")
        print(f"   Total value: ${composite['total_monetary_value_usd']}")
        print(f"   Total users: {composite['total_users']}")
        print("✅ Successfully tested with synthetic data")
    
    return True


def run_all_tests():
    """Run all test functions and report results."""
    print("=" * 80)
    print("ROI UTILITIES TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Hours Saved - Basic", test_estimate_hours_saved_basic),
        ("Hours Saved - Edge Cases", test_estimate_hours_saved_edge_cases),
        ("Hours Saved - Custom Config", test_estimate_hours_saved_custom_config),
        ("Monetary Value - Basic", test_calculate_monetary_value_basic),
        ("Monetary Value - Edge Cases", test_calculate_monetary_value_edge_cases),
        ("ROI Per User", test_calculate_roi_per_user),
        ("ROI Per User - Edge Cases", test_calculate_roi_per_user_edge_cases),
        ("ROI Per Department", test_calculate_roi_per_department),
        ("ROI Per Department - Edge Cases", test_calculate_roi_per_department_edge_cases),
        ("Composite ROI", test_calculate_composite_roi),
        ("Composite ROI - Edge Cases", test_calculate_composite_roi_edge_cases),
        ("Date Validation", test_validate_date_field),
        ("Sample CSV Integration", test_with_sample_csv),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ PASSED: {test_name}")
            else:
                failed += 1
                print(f"\n❌ FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"\n❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 80)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
