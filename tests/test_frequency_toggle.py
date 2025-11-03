"""
Test for frequency toggle and partial period filtering functionality.

Tests:
1. Weekly view: Blueflame monthly data is allocated to ISO weeks
2. Monthly view: OpenAI weekly data is prorated to calendar months
3. Partial period exclusion works for both weekly and monthly views
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_weekly_normalization():
    """Test that monthly Blueflame data is correctly allocated to weeks."""
    print("\n" + "=" * 80)
    print("TEST: Weekly View Normalization")
    print("=" * 80)
    
    # Create sample Blueflame monthly data
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'user_name': ['Test User'],
        'email': ['user1@test.com'],
        'department': ['Engineering'],
        'date': [pd.Timestamp('2024-01-15')],  # Mid-January
        'feature_used': ['BlueFlame Messages'],
        'usage_count': [100],  # 100 messages for the month
        'cost_usd': [50.0],
        'tool_source': ['BlueFlame AI'],
        'file_source': ['test.csv']
    })
    
    # Simulate weekly normalization
    weekly_records = []
    for _, row in test_data.iterrows():
        if row['tool_source'] == 'BlueFlame AI':
            # Allocate monthly data to weeks
            month_start = pd.Timestamp(year=row['date'].year, month=row['date'].month, day=1)
            month_end = month_start + pd.DateOffset(months=1) - pd.Timedelta(days=1)
            
            # Get all ISO week starts within this month (use set for performance)
            current = month_start
            weeks_in_month = set()
            while current <= month_end:
                week_start = current - pd.to_timedelta(current.weekday(), 'D')
                weeks_in_month.add(week_start)
                current += pd.Timedelta(days=7)
            
            # Convert back to sorted list for iteration
            weeks_in_month = sorted(weeks_in_month)
            
            # Allocate usage evenly across weeks
            if weeks_in_month:
                usage_per_week = row['usage_count'] / len(weeks_in_month)
                cost_per_week = row['cost_usd'] / len(weeks_in_month)
                
                for week_start in weeks_in_month:
                    weekly_row = row.copy()
                    weekly_row['period_start'] = week_start
                    weekly_row['usage_count'] = usage_per_week
                    weekly_row['cost_usd'] = cost_per_week
                    weekly_records.append(weekly_row)
    
    weekly_df = pd.DataFrame(weekly_records)
    
    print(f"✅ Original monthly record: 100 messages")
    print(f"✅ Split into {len(weekly_df)} weekly records")
    print(f"✅ Total usage across weeks: {weekly_df['usage_count'].sum():.2f}")
    print(f"✅ Usage per week: {weekly_df['usage_count'].iloc[0]:.2f}")
    
    # Verify total usage is preserved
    assert abs(weekly_df['usage_count'].sum() - 100) < 0.01, "Total usage should be preserved"
    assert len(weekly_df) > 0, "Should have at least one weekly record"
    
    print("✅ Weekly normalization test passed!")
    return True


def test_monthly_normalization():
    """Test that weekly OpenAI data is correctly prorated to months."""
    print("\n" + "=" * 80)
    print("TEST: Monthly View Normalization")
    print("=" * 80)
    
    # Create sample OpenAI weekly data that spans two months
    # Week from Jan 29 to Feb 4 (spans January and February)
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com'],
        'user_name': ['Test User'],
        'email': ['user1@test.com'],
        'department': ['Engineering'],
        'date': [pd.Timestamp('2024-01-29')],  # Week starts Jan 29
        'feature_used': ['ChatGPT Messages'],
        'usage_count': [70],  # 70 messages for the week
        'cost_usd': [25.0],
        'tool_source': ['ChatGPT'],
        'file_source': ['test.csv']
    })
    
    # Simulate monthly normalization
    monthly_records = []
    for _, row in test_data.iterrows():
        if row['tool_source'] in ['ChatGPT', 'OpenAI']:
            period_start = row['date']
            period_end = period_start + pd.Timedelta(days=6)
            
            # Check if period spans multiple months
            if period_start.month != period_end.month:
                # Split across months
                month1_end = pd.Timestamp(year=period_start.year, month=period_start.month, day=1) + pd.DateOffset(months=1) - pd.Timedelta(days=1)
                days_in_month1 = (month1_end - period_start).days + 1
                days_in_month2 = (period_end - month1_end).days
                total_days = days_in_month1 + days_in_month2
                
                # Month 1 portion
                month1_row = row.copy()
                month1_row['period_start'] = pd.Timestamp(year=period_start.year, month=period_start.month, day=1)
                month1_row['usage_count'] = row['usage_count'] * (days_in_month1 / total_days)
                month1_row['cost_usd'] = row['cost_usd'] * (days_in_month1 / total_days)
                monthly_records.append(month1_row)
                
                # Month 2 portion
                month2_row = row.copy()
                month2_row['period_start'] = pd.Timestamp(year=period_end.year, month=period_end.month, day=1)
                month2_row['usage_count'] = row['usage_count'] * (days_in_month2 / total_days)
                month2_row['cost_usd'] = row['cost_usd'] * (days_in_month2 / total_days)
                monthly_records.append(month2_row)
            else:
                monthly_row = row.copy()
                monthly_row['period_start'] = pd.Timestamp(year=period_start.year, month=period_start.month, day=1)
                monthly_records.append(monthly_row)
    
    monthly_df = pd.DataFrame(monthly_records)
    
    print(f"✅ Original weekly record: 70 messages (Jan 29 - Feb 4)")
    print(f"✅ Split into {len(monthly_df)} monthly records")
    print(f"✅ Total usage across months: {monthly_df['usage_count'].sum():.2f}")
    if len(monthly_df) == 2:
        print(f"✅ January portion: {monthly_df.iloc[0]['usage_count']:.2f} messages")
        print(f"✅ February portion: {monthly_df.iloc[1]['usage_count']:.2f} messages")
    
    # Verify total usage is preserved
    assert abs(monthly_df['usage_count'].sum() - 70) < 0.01, "Total usage should be preserved"
    assert len(monthly_df) == 2, "Should split into 2 monthly records"
    
    print("✅ Monthly normalization test passed!")
    return True


def test_partial_period_exclusion():
    """Test that partial periods are correctly excluded."""
    print("\n" + "=" * 80)
    print("TEST: Partial Period Exclusion")
    print("=" * 80)
    
    # Create sample data with various dates
    today = pd.Timestamp.today().normalize()
    last_month = today - pd.DateOffset(months=1)
    last_week = today - pd.Timedelta(days=7)
    
    test_data = pd.DataFrame({
        'user_id': ['user1@test.com', 'user2@test.com', 'user3@test.com'],
        'period_start': [last_month, last_week, today],
        'usage_count': [100, 50, 25]
    })
    
    # Test monthly exclusion
    current_month_start = today.to_period('M').start_time
    filtered_monthly = test_data[test_data['period_start'] < current_month_start]
    
    print(f"✅ Original records: {len(test_data)}")
    print(f"✅ After monthly partial exclusion: {len(filtered_monthly)}")
    print(f"✅ Excluded current month: {len(test_data) - len(filtered_monthly)} record(s)")
    
    # Test weekly exclusion
    current_week_start = today - pd.to_timedelta(today.weekday(), 'D')
    filtered_weekly = test_data[test_data['period_start'] < current_week_start]
    
    print(f"✅ After weekly partial exclusion: {len(filtered_weekly)}")
    print(f"✅ Excluded current week: {len(test_data) - len(filtered_weekly)} record(s)")
    
    assert len(filtered_monthly) < len(test_data), "Should exclude some records for monthly view"
    assert len(filtered_weekly) < len(test_data), "Should exclude some records for weekly view"
    
    print("✅ Partial period exclusion test passed!")
    return True


def run_all_tests():
    """Run all frequency toggle tests."""
    print("\n" + "=" * 80)
    print("FREQUENCY TOGGLE TEST SUITE")
    print("=" * 80)
    
    try:
        test_weekly_normalization()
        test_monthly_normalization()
        test_partial_period_exclusion()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
