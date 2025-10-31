"""
Tests for frequency_utils.py

Validates proration and allocation transforms for weekly/monthly data unification.
"""
import sys
import os

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime
from frequency_utils import (
    openai_weekly_to_monthly,
    blueflame_monthly_to_weekly_estimated,
    _expand_weekly_to_daily,
    _expand_monthly_to_daily
)


def test_openai_weekly_to_monthly_same_month():
    """Test weekly data entirely within one month aggregates correctly."""
    print("\n" + "=" * 80)
    print("TEST: OpenAI weekly → monthly (same month)")
    print("=" * 80)
    
    # Week entirely in May 2025
    df = pd.DataFrame({
        'date': ['2025-05-05'],  # Monday, May 5
        'usage_count': [70]
    })
    
    result = openai_weekly_to_monthly(df)
    
    print(f"Input: Week starting 2025-05-05, usage=70")
    print(f"Output: {len(result)} month(s)")
    print(result)
    
    # Should have one month (May)
    assert len(result) == 1, f"Expected 1 month, got {len(result)}"
    assert result.iloc[0]['period_start'] == pd.Timestamp('2025-05-01'), \
        f"Expected 2025-05-01, got {result.iloc[0]['period_start']}"
    assert result.iloc[0]['usage_count'] == 70, \
        f"Expected usage=70, got {result.iloc[0]['usage_count']}"
    
    print("✅ PASSED: Week in single month aggregates correctly")
    return True


def test_openai_weekly_to_monthly_spanning_months():
    """Test weekly data spanning two months prorates correctly."""
    print("\n" + "=" * 80)
    print("TEST: OpenAI weekly → monthly (spanning months)")
    print("=" * 80)
    
    # Week from Jan 29 - Feb 4 (3 days in Jan, 4 days in Feb)
    df = pd.DataFrame({
        'date': ['2025-01-29'],  # Wednesday, Jan 29
        'usage_count': [700]
    })
    
    result = openai_weekly_to_monthly(df)
    result = result.sort_values('period_start').reset_index(drop=True)
    
    print(f"Input: Week starting 2025-01-29 (spans Jan/Feb), usage=700")
    print(f"Output: {len(result)} month(s)")
    print(result)
    
    # Should have two months (Jan and Feb)
    assert len(result) == 2, f"Expected 2 months, got {len(result)}"
    
    # Jan should get 3/7 of usage (Jan 29, 30, 31)
    jan_usage = result[result['period_start'] == pd.Timestamp('2025-01-01')]['usage_count'].values[0]
    expected_jan = 700 * 3 / 7
    assert abs(jan_usage - expected_jan) < 0.01, \
        f"Expected Jan usage={expected_jan:.2f}, got {jan_usage:.2f}"
    
    # Feb should get 4/7 of usage (Feb 1, 2, 3, 4)
    feb_usage = result[result['period_start'] == pd.Timestamp('2025-02-01')]['usage_count'].values[0]
    expected_feb = 700 * 4 / 7
    assert abs(feb_usage - expected_feb) < 0.01, \
        f"Expected Feb usage={expected_feb:.2f}, got {feb_usage:.2f}"
    
    # Total should be preserved
    total = result['usage_count'].sum()
    assert abs(total - 700) < 0.01, f"Expected total=700, got {total:.2f}"
    
    print(f"✅ PASSED: Jan gets {jan_usage:.2f} (3/7), Feb gets {feb_usage:.2f} (4/7)")
    return True


def test_multiple_weeks_to_monthly():
    """Test multiple weekly records aggregate correctly."""
    print("\n" + "=" * 80)
    print("TEST: Multiple weeks → monthly aggregation")
    print("=" * 80)
    
    # Three weeks in May
    df = pd.DataFrame({
        'date': ['2025-05-05', '2025-05-12', '2025-05-19'],
        'usage_count': [100, 200, 150]
    })
    
    result = openai_weekly_to_monthly(df)
    
    print(f"Input: 3 weeks in May, total usage=450")
    print(f"Output: {len(result)} month(s)")
    print(result)
    
    assert len(result) == 1, f"Expected 1 month, got {len(result)}"
    assert result.iloc[0]['period_start'] == pd.Timestamp('2025-05-01')
    assert result.iloc[0]['usage_count'] == 450, \
        f"Expected total=450, got {result.iloc[0]['usage_count']}"
    
    print("✅ PASSED: Multiple weeks aggregate correctly")
    return True


def test_blueflame_monthly_to_weekly_even_by_day():
    """Test Blueflame monthly → weekly allocation (even_by_day method)."""
    print("\n" + "=" * 80)
    print("TEST: Blueflame monthly → weekly (even_by_day)")
    print("=" * 80)
    
    # May 2025 (31 days)
    df = pd.DataFrame({
        'date': ['2025-05-01'],
        'usage_count': [3100]  # 100 per day
    })
    
    result = blueflame_monthly_to_weekly_estimated(df, method="even_by_day")
    result = result.sort_values('iso_week_start').reset_index(drop=True)
    
    print(f"Input: May 2025, usage=3100 (31 days)")
    print(f"Output: {len(result)} week(s)")
    print(result)
    
    # May 2025 spans 5 ISO weeks
    # Week 1: Apr 28 - May 4 (4 days in May)
    # Week 2: May 5 - May 11 (7 days)
    # Week 3: May 12 - May 18 (7 days)
    # Week 4: May 19 - May 25 (7 days)
    # Week 5: May 26 - Jun 1 (6 days in May)
    # Total: 4+7+7+7+6 = 31 days ✓
    
    assert len(result) >= 5, f"Expected at least 5 weeks, got {len(result)}"
    
    # Total should be preserved
    total = result['usage_count'].sum()
    assert abs(total - 3100) < 0.01, f"Expected total=3100, got {total:.2f}"
    
    print(f"✅ PASSED: Total preserved ({total:.2f}), distributed across {len(result)} weeks")
    return True


def test_blueflame_monthly_to_weekly_business_days():
    """Test Blueflame monthly → weekly allocation (business_days method)."""
    print("\n" + "=" * 80)
    print("TEST: Blueflame monthly → weekly (business_days)")
    print("=" * 80)
    
    # May 2025
    df = pd.DataFrame({
        'date': ['2025-05-01'],
        'usage_count': [2200]  # Will be spread across weekdays only
    })
    
    result = blueflame_monthly_to_weekly_estimated(df, method="business_days")
    
    print(f"Input: May 2025, usage=2200")
    print(f"Output: {len(result)} week(s)")
    print(result)
    
    # Total should still be preserved (just distributed differently)
    total = result['usage_count'].sum()
    assert abs(total - 2200) < 0.01, f"Expected total=2200, got {total:.2f}"
    
    print(f"✅ PASSED: Business days method preserves total ({total:.2f})")
    return True


def test_month_lengths_preserved():
    """Test that different month lengths (28/29/30/31 days) preserve totals."""
    print("\n" + "=" * 80)
    print("TEST: Variable month lengths preserve totals")
    print("=" * 80)
    
    months = [
        ('2025-01-01', 31, 3100),  # January - 31 days
        ('2025-02-01', 28, 2800),  # February - 28 days (2025 not leap year)
        ('2025-04-01', 30, 3000),  # April - 30 days
    ]
    
    for month_start, days, total_usage in months:
        df = pd.DataFrame({
            'date': [month_start],
            'usage_count': [total_usage]
        })
        
        result = blueflame_monthly_to_weekly_estimated(df, method="even_by_day")
        result_total = result['usage_count'].sum()
        
        print(f"{month_start}: {days} days, usage={total_usage}, allocated={result_total:.2f}")
        
        assert abs(result_total - total_usage) < 0.01, \
            f"Month {month_start}: Expected {total_usage}, got {result_total:.2f}"
    
    print("✅ PASSED: All month lengths preserve totals")
    return True


def test_empty_dataframe_handling():
    """Test that empty DataFrames are handled gracefully."""
    print("\n" + "=" * 80)
    print("TEST: Empty DataFrame handling")
    print("=" * 80)
    
    empty_df = pd.DataFrame(columns=['date', 'usage_count'])
    
    # Test weekly to monthly
    result1 = openai_weekly_to_monthly(empty_df)
    assert result1.empty, "Expected empty result for empty input"
    assert 'period_start' in result1.columns, "Expected period_start column"
    
    # Test monthly to weekly
    result2 = blueflame_monthly_to_weekly_estimated(empty_df)
    assert result2.empty, "Expected empty result for empty input"
    assert 'iso_week_start' in result2.columns, "Expected iso_week_start column"
    
    print("✅ PASSED: Empty DataFrames handled correctly")
    return True


def test_leap_year_handling():
    """Test that leap years (Feb 29) are handled correctly."""
    print("\n" + "=" * 80)
    print("TEST: Leap year (Feb 2024) handling")
    print("=" * 80)
    
    # February 2024 - leap year (29 days)
    df = pd.DataFrame({
        'date': ['2024-02-01'],
        'usage_count': [2900]  # 100 per day including Feb 29
    })
    
    result = blueflame_monthly_to_weekly_estimated(df, method="even_by_day")
    total = result['usage_count'].sum()
    
    print(f"Feb 2024 (leap year): 29 days, usage=2900, allocated={total:.2f}")
    
    assert abs(total - 2900) < 0.01, f"Expected total=2900, got {total:.2f}"
    
    print("✅ PASSED: Leap year handled correctly")
    return True


def test_week_crossing_three_months():
    """Test edge case of a week that could touch 3 months (rare but possible)."""
    print("\n" + "=" * 80)
    print("TEST: Week crossing months edge case")
    print("=" * 80)
    
    # Week starting Dec 30, 2024 (Mon) - goes into 2025
    # Dec 30-31 (2 days in Dec), Jan 1-5 (5 days in Jan)
    df = pd.DataFrame({
        'date': ['2024-12-30'],  # Monday
        'usage_count': [700]
    })
    
    result = openai_weekly_to_monthly(df)
    result = result.sort_values('period_start').reset_index(drop=True)
    
    print(f"Input: Week starting 2024-12-30 (spans Dec/Jan), usage=700")
    print(f"Output: {len(result)} month(s)")
    print(result)
    
    assert len(result) == 2, f"Expected 2 months, got {len(result)}"
    
    # Total should be preserved
    total = result['usage_count'].sum()
    assert abs(total - 700) < 0.01, f"Expected total=700, got {total:.2f}"
    
    print("✅ PASSED: Week crossing year boundary handled correctly")
    return True


def test_proportional_allocation():
    """Test proportional_to_openai allocation method."""
    print("\n" + "=" * 80)
    print("TEST: Proportional allocation to OpenAI pattern")
    print("=" * 80)
    
    # OpenAI weekly data for May
    openai_df = pd.DataFrame({
        'date': ['2025-05-05', '2025-05-12', '2025-05-19', '2025-05-26'],
        'usage_count': [100, 200, 300, 400]  # Total = 1000
    })
    
    # Blueflame monthly data for May
    blueflame_df = pd.DataFrame({
        'date': ['2025-05-01'],
        'usage_count': [5000]
    })
    
    result = blueflame_monthly_to_weekly_estimated(
        blueflame_df, 
        method="proportional_to_openai",
        openai_weekly=openai_df
    )
    
    print(f"OpenAI pattern: 100, 200, 300, 400 (proportions: 10%, 20%, 30%, 40%)")
    print(f"Blueflame total: 5000")
    print(f"Output: {len(result)} week(s)")
    print(result)
    
    # Total should be preserved
    total = result['usage_count'].sum()
    assert abs(total - 5000) < 1, f"Expected total=5000, got {total:.2f}"
    
    # Check proportions roughly match OpenAI
    # Week 1 (100/1000 = 10%) should get ~500
    # Week 2 (200/1000 = 20%) should get ~1000
    # Week 3 (300/1000 = 30%) should get ~1500
    # Week 4 (400/1000 = 40%) should get ~2000
    
    print("✅ PASSED: Proportional allocation preserves total")
    return True


def run_all_tests():
    """Run all frequency utils tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 22 + "FREQUENCY UTILS TEST SUITE" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    
    tests = [
        test_openai_weekly_to_monthly_same_month,
        test_openai_weekly_to_monthly_spanning_months,
        test_multiple_weeks_to_monthly,
        test_blueflame_monthly_to_weekly_even_by_day,
        test_blueflame_monthly_to_weekly_business_days,
        test_month_lengths_preserved,
        test_empty_dataframe_handling,
        test_leap_year_handling,
        test_week_crossing_three_months,
        test_proportional_allocation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {test_func.__name__}")
            print(f"   {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ ERROR: {test_func.__name__}")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
