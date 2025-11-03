"""
Unit Tests for ROI Utilities Module

Tests all core ROI calculation functions to ensure accuracy and reliability.
"""

import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from roi_utils import (
    calculate_time_savings,
    calculate_cost_savings,
    calculate_business_value,
    calculate_ai_impact_score,
    identify_value_leaders,
    calculate_opportunity_cost,
    calculate_roi_summary,
    update_time_savings_benchmark,
    update_labor_cost,
    update_department_multiplier,
    get_current_benchmarks,
    TIME_SAVINGS_PER_FEATURE,
    LABOR_COST_PER_HOUR,
    DEPARTMENT_IMPACT_MULTIPLIER
)


def test_calculate_time_savings():
    """Test time savings calculation with known values."""
    print("\n" + "=" * 80)
    print("TEST: Calculate Time Savings")
    print("=" * 80)
    
    # Create test data
    test_data = pd.DataFrame({
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'General'],
        'usage_count': [100, 50, 20]
    })
    
    # Calculate time savings
    result = calculate_time_savings(test_data)
    
    # Verify columns exist
    assert 'time_saved_minutes' in result.columns, "Missing time_saved_minutes column"
    assert 'time_saved_hours' in result.columns, "Missing time_saved_hours column"
    
    # Verify calculations
    # ChatGPT Messages: 100 * 12 = 1200 minutes = 20 hours
    assert result.iloc[0]['time_saved_minutes'] == 1200, \
        f"Expected 1200 minutes, got {result.iloc[0]['time_saved_minutes']}"
    assert result.iloc[0]['time_saved_hours'] == 20.0, \
        f"Expected 20 hours, got {result.iloc[0]['time_saved_hours']}"
    
    # Tool Messages: 50 * 25 = 1250 minutes = 20.833 hours
    assert abs(result.iloc[1]['time_saved_hours'] - 20.833) < 0.01, \
        f"Expected ~20.833 hours, got {result.iloc[1]['time_saved_hours']}"
    
    # General: 20 * 10 = 200 minutes
    assert result.iloc[2]['time_saved_minutes'] == 200, \
        f"Expected 200 minutes, got {result.iloc[2]['time_saved_minutes']}"
    
    print("✅ Time savings calculated correctly")
    print(f"   Total hours saved: {result['time_saved_hours'].sum():.2f}")
    return True


def test_calculate_cost_savings():
    """Test cost savings calculation with department-specific rates."""
    print("\n" + "=" * 80)
    print("TEST: Calculate Cost Savings")
    print("=" * 80)
    
    # Create test data with time savings already calculated
    test_data = pd.DataFrame({
        'feature_used': ['ChatGPT Messages', 'Tool Messages'],
        'usage_count': [100, 50],
        'department': ['Engineering', 'Sales'],
        'time_saved_hours': [20.0, 20.833]
    })
    
    # Calculate cost savings
    result = calculate_cost_savings(test_data)
    
    # Verify columns exist
    assert 'cost_saved_usd' in result.columns, "Missing cost_saved_usd column"
    assert 'labor_cost_per_hour' in result.columns, "Missing labor_cost_per_hour column"
    
    # Verify calculations
    # Engineering: 20 hours * $85/hour = $1700
    expected_eng_cost = 20.0 * LABOR_COST_PER_HOUR['Engineering']
    assert abs(result.iloc[0]['cost_saved_usd'] - expected_eng_cost) < 0.01, \
        f"Expected ${expected_eng_cost}, got ${result.iloc[0]['cost_saved_usd']}"
    
    # Sales: 20.833 hours * $65/hour
    expected_sales_cost = 20.833 * LABOR_COST_PER_HOUR['Sales']
    assert abs(result.iloc[1]['cost_saved_usd'] - expected_sales_cost) < 1.0, \
        f"Expected ~${expected_sales_cost}, got ${result.iloc[1]['cost_saved_usd']}"
    
    print("✅ Cost savings calculated correctly")
    print(f"   Total cost saved: ${result['cost_saved_usd'].sum():,.2f}")
    return True


def test_calculate_business_value():
    """Test business value calculation with impact multipliers."""
    print("\n" + "=" * 80)
    print("TEST: Calculate Business Value")
    print("=" * 80)
    
    # Create test data with cost savings
    test_data = pd.DataFrame({
        'feature_used': ['ChatGPT Messages', 'Tool Messages'],
        'usage_count': [100, 50],
        'department': ['Engineering', 'Finance'],
        'time_saved_hours': [20.0, 20.0],
        'cost_saved_usd': [1700.0, 1400.0]
    })
    
    # Calculate business value
    result = calculate_business_value(test_data)
    
    # Verify columns exist
    assert 'business_value_usd' in result.columns, "Missing business_value_usd column"
    assert 'impact_multiplier' in result.columns, "Missing impact_multiplier column"
    
    # Verify multipliers are applied
    # Engineering: 1700 * 1.3 = 2210
    expected_eng_value = 1700.0 * DEPARTMENT_IMPACT_MULTIPLIER['Engineering']
    assert abs(result.iloc[0]['business_value_usd'] - expected_eng_value) < 0.01, \
        f"Expected ${expected_eng_value}, got ${result.iloc[0]['business_value_usd']}"
    
    # Finance: 1400 * 1.15 = 1610
    expected_fin_value = 1400.0 * DEPARTMENT_IMPACT_MULTIPLIER['Finance']
    assert abs(result.iloc[1]['business_value_usd'] - expected_fin_value) < 0.01, \
        f"Expected ${expected_fin_value}, got ${result.iloc[1]['business_value_usd']}"
    
    print("✅ Business value calculated correctly")
    print(f"   Total business value: ${result['business_value_usd'].sum():,.2f}")
    return True


def test_calculate_ai_impact_score():
    """Test AI impact score calculation."""
    print("\n" + "=" * 80)
    print("TEST: Calculate AI Impact Score")
    print("=" * 80)
    
    # Create test data
    test_data = pd.DataFrame({
        'feature_used': ['Tool Messages', 'ChatGPT Messages', 'General'] * 2,
        'usage_count': [200, 100, 50, 180, 120, 40],
        'department': ['Engineering', 'Sales', 'Finance'] * 2,
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'] * 2
    })
    
    # Calculate impact scores
    result = calculate_ai_impact_score(test_data)
    
    # Verify columns exist
    assert 'ai_impact_score' in result.columns, "Missing ai_impact_score column"
    assert 'score_category' in result.columns, "Missing score_category column"
    
    # Verify scores are in 0-100 range
    assert result['ai_impact_score'].min() >= 0, "Score below 0"
    assert result['ai_impact_score'].max() <= 100, "Score above 100"
    
    # Verify categories are assigned
    assert result['score_category'].isin(['Low', 'Medium', 'High']).all(), \
        "Invalid score categories"
    
    # Higher usage should generally produce higher scores
    high_usage_score = result[result['usage_count'] == 200]['ai_impact_score'].iloc[0]
    low_usage_score = result[result['usage_count'] == 40]['ai_impact_score'].iloc[0]
    assert high_usage_score > low_usage_score, \
        f"Higher usage should have higher score: {high_usage_score} vs {low_usage_score}"
    
    print("✅ AI impact scores calculated correctly")
    print(f"   Score range: {result['ai_impact_score'].min():.1f} - {result['ai_impact_score'].max():.1f}")
    print(f"   Category distribution: {result['score_category'].value_counts().to_dict()}")
    return True


def test_identify_value_leaders():
    """Test value leader identification."""
    print("\n" + "=" * 80)
    print("TEST: Identify Value Leaders")
    print("=" * 80)
    
    # Create test data with known values
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'] * 3,
        'user_name': ['Alice', 'Bob', 'Charlie'] * 3,
        'department': ['Engineering', 'Sales', 'Finance'] * 3,
        'feature_used': ['ChatGPT Messages'] * 9,
        'usage_count': [100, 200, 50, 150, 180, 60, 120, 220, 70],
        'business_value_usd': [1000, 2000, 500, 1500, 1800, 600, 1200, 2200, 700]
    })
    
    # Test user leaders
    user_leaders = identify_value_leaders(test_data, by='user', top_n=3, metric='business_value_usd')
    
    # Verify structure
    assert len(user_leaders) <= 3, f"Expected max 3 leaders, got {len(user_leaders)}"
    assert 'user_id' in user_leaders.columns, "Missing user_id column"
    assert 'business_value_usd' in user_leaders.columns, "Missing business_value_usd column"
    assert 'pct_of_total' in user_leaders.columns, "Missing pct_of_total column"
    
    # Verify sorting (descending by value)
    assert user_leaders['business_value_usd'].is_monotonic_decreasing or \
           (user_leaders['business_value_usd'].iloc[0] >= user_leaders['business_value_usd'].iloc[-1]), \
           "Leaders not sorted by value"
    
    # Test department leaders
    dept_leaders = identify_value_leaders(test_data, by='department', top_n=3, metric='business_value_usd')
    
    assert len(dept_leaders) <= 3, f"Expected max 3 departments, got {len(dept_leaders)}"
    assert 'department' in dept_leaders.columns, "Missing department column"
    
    print("✅ Value leaders identified correctly")
    print(f"   Top user value: ${user_leaders['business_value_usd'].iloc[0]:,.2f}")
    print(f"   Top department: {dept_leaders['department'].iloc[0]}")
    return True


def test_calculate_opportunity_cost():
    """Test opportunity cost calculations."""
    print("\n" + "=" * 80)
    print("TEST: Calculate Opportunity Cost")
    print("=" * 80)
    
    # Create test data with varied usage
    test_data = pd.DataFrame({
        'user_id': [f'user{i}@test.com' for i in range(1, 11)],
        'usage_count': [200, 180, 150, 120, 100, 80, 60, 40, 20, 10],
        'feature_used': ['ChatGPT Messages'] * 10,
        'department': ['Engineering'] * 10,
        'business_value_usd': [2000, 1800, 1500, 1200, 1000, 800, 600, 400, 200, 100]
    })
    
    # Calculate opportunity costs
    result = calculate_opportunity_cost(
        test_data,
        total_licenses=20,
        license_cost_per_user=30.0
    )
    
    # Verify structure
    assert 'total_licenses' in result, "Missing total_licenses"
    assert 'active_users' in result, "Missing active_users"
    assert 'unused_licenses' in result, "Missing unused_licenses"
    assert 'utilization_rate_pct' in result, "Missing utilization_rate_pct"
    assert 'opportunity_for_improvement_usd' in result, "Missing opportunity_for_improvement_usd"
    
    # Verify calculations
    assert result['total_licenses'] == 20, "Incorrect total licenses"
    assert result['active_users'] == 10, f"Expected 10 active users, got {result['active_users']}"
    assert result['unused_licenses'] == 10, f"Expected 10 unused licenses, got {result['unused_licenses']}"
    
    # Utilization should be 50% (10/20)
    assert abs(result['utilization_rate_pct'] - 50.0) < 0.1, \
        f"Expected 50% utilization, got {result['utilization_rate_pct']:.1f}%"
    
    # Unused license cost should be 10 * $30 = $300
    assert result['unused_license_cost_monthly'] == 300.0, \
        f"Expected $300 unused cost, got ${result['unused_license_cost_monthly']}"
    
    print("✅ Opportunity costs calculated correctly")
    print(f"   Utilization rate: {result['utilization_rate_pct']:.1f}%")
    print(f"   Unused licenses: {result['unused_licenses']}")
    print(f"   Unused cost/month: ${result['unused_license_cost_monthly']:,.2f}")
    return True


def test_calculate_roi_summary():
    """Test comprehensive ROI summary generation."""
    print("\n" + "=" * 80)
    print("TEST: Calculate ROI Summary")
    print("=" * 80)
    
    # Create comprehensive test data
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'] * 3,
        'user_name': ['Alice', 'Bob', 'Charlie'] * 3,
        'department': ['Engineering', 'Sales', 'Finance'] * 3,
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'Project Messages'] * 3,
        'usage_count': [150, 200, 100, 80, 120, 90, 50, 180, 110]
    })
    
    # Calculate ROI summary
    summary = calculate_roi_summary(
        test_data,
        total_licenses=500,
        license_cost_per_user=30.0,
        include_all_metrics=True
    )
    
    # Verify key metrics exist
    assert 'total_users' in summary, "Missing total_users"
    assert 'total_usage' in summary, "Missing total_usage"
    assert 'total_time_saved_hours' in summary, "Missing total_time_saved_hours"
    assert 'total_cost_saved_usd' in summary, "Missing total_cost_saved_usd"
    assert 'total_business_value_usd' in summary, "Missing total_business_value_usd"
    assert 'top_users' in summary, "Missing top_users"
    assert 'top_departments' in summary, "Missing top_departments"
    assert 'opportunity_costs' in summary, "Missing opportunity_costs"
    assert 'roi_ratio' in summary, "Missing roi_ratio"
    
    # Verify values are reasonable
    assert summary['total_users'] == 3, f"Expected 3 users, got {summary['total_users']}"
    assert summary['total_usage'] > 0, "Total usage should be positive"
    assert summary['total_time_saved_hours'] > 0, "Time saved should be positive"
    assert summary['total_business_value_usd'] > 0, "Business value should be positive"
    
    # ROI ratio should be positive
    assert summary['roi_ratio'] > 0, "ROI ratio should be positive"
    
    print("✅ ROI summary generated correctly")
    print(f"   Total users: {summary['total_users']}")
    print(f"   Total value: ${summary['total_business_value_usd']:,.2f}")
    print(f"   ROI ratio: {summary['roi_ratio']:.2f}x")
    return True


def test_benchmark_customization():
    """Test ability to customize benchmarks."""
    print("\n" + "=" * 80)
    print("TEST: Benchmark Customization")
    print("=" * 80)
    
    # Get original benchmarks
    original = get_current_benchmarks()
    original_time_savings = original['time_savings']['ChatGPT Messages']
    original_labor_cost = original['labor_costs']['Engineering']
    original_multiplier = original['department_multipliers']['Engineering']
    
    # Update benchmarks
    update_time_savings_benchmark('ChatGPT Messages', 15.0)
    update_labor_cost('Engineering', 100.0)
    update_department_multiplier('Engineering', 1.5)
    
    # Verify updates
    updated = get_current_benchmarks()
    assert updated['time_savings']['ChatGPT Messages'] == 15.0, "Time savings not updated"
    assert updated['labor_costs']['Engineering'] == 100.0, "Labor cost not updated"
    assert updated['department_multipliers']['Engineering'] == 1.5, "Multiplier not updated"
    
    # Restore originals
    update_time_savings_benchmark('ChatGPT Messages', original_time_savings)
    update_labor_cost('Engineering', original_labor_cost)
    update_department_multiplier('Engineering', original_multiplier)
    
    print("✅ Benchmark customization works correctly")
    print(f"   Updated and restored benchmarks successfully")
    return True


def test_integration_full_pipeline():
    """Test the complete ROI calculation pipeline end-to-end."""
    print("\n" + "=" * 80)
    print("TEST: Full ROI Pipeline Integration")
    print("=" * 80)
    
    # Create realistic usage data
    np.random.seed(42)
    users = [f'user{i}@company.com' for i in range(1, 21)]
    departments = ['Engineering', 'Sales', 'Finance', 'Marketing', 'Operations']
    features = ['ChatGPT Messages', 'Tool Messages', 'Project Messages']
    
    rows = []
    for user in users:
        dept = np.random.choice(departments)
        for feature in features:
            usage = int(np.random.uniform(10, 200))
            rows.append({
                'user_id': user,
                'user_name': user.split('@')[0].title(),
                'department': dept,
                'feature_used': feature,
                'usage_count': usage
            })
    
    test_data = pd.DataFrame(rows)
    
    # Run full pipeline
    enriched = calculate_time_savings(test_data)
    enriched = calculate_cost_savings(enriched)
    enriched = calculate_business_value(enriched)
    enriched = calculate_ai_impact_score(enriched)
    
    # Verify all columns were added
    expected_cols = [
        'time_saved_minutes', 'time_saved_hours',
        'cost_saved_usd', 'business_value_usd',
        'ai_impact_score', 'score_category'
    ]
    for col in expected_cols:
        assert col in enriched.columns, f"Missing column: {col}"
    
    # Verify no NaN values in key metrics
    assert not enriched['time_saved_hours'].isna().any(), "NaN in time_saved_hours"
    assert not enriched['cost_saved_usd'].isna().any(), "NaN in cost_saved_usd"
    assert not enriched['business_value_usd'].isna().any(), "NaN in business_value_usd"
    
    # Generate summary
    summary = calculate_roi_summary(enriched, total_licenses=100, license_cost_per_user=30)
    
    # Verify summary completeness
    assert summary['total_users'] == 20, "User count mismatch"
    assert summary['total_usage'] > 0, "No usage recorded"
    assert summary['total_business_value_usd'] > 0, "No value calculated"
    
    print("✅ Full pipeline integration successful")
    print(f"   Processed {len(enriched)} records for {summary['total_users']} users")
    print(f"   Total business value: ${summary['total_business_value_usd']:,.2f}")
    print(f"   Average value/user: ${summary['avg_business_value_per_user_usd']:,.2f}")
    return True


def run_all_tests():
    """Run all ROI utilities tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ROI UTILITIES TEST SUITE" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    
    tests = [
        ("Time Savings Calculation", test_calculate_time_savings),
        ("Cost Savings Calculation", test_calculate_cost_savings),
        ("Business Value Calculation", test_calculate_business_value),
        ("AI Impact Score Calculation", test_calculate_ai_impact_score),
        ("Value Leader Identification", test_identify_value_leaders),
        ("Opportunity Cost Calculation", test_calculate_opportunity_cost),
        ("ROI Summary Generation", test_calculate_roi_summary),
        ("Benchmark Customization", test_benchmark_customization),
        ("Full Pipeline Integration", test_integration_full_pipeline)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            print(f"❌ {name} FAILED with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False, str(e)))
    
    # Print summary
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "TEST SUMMARY" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {name}")
        if error:
            print(f"           Error: {error}")
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
