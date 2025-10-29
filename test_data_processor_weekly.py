"""
Test data_processor.py weekly file handling
"""

import sys
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

import pandas as pd
from data_processor import DataProcessor
from database import DatabaseManager
import os

def test_data_processor_weekly_file():
    """Test that DataProcessor correctly handles weekly files."""
    print("=" * 80)
    print("TEST: DataProcessor Weekly File Handling")
    print("=" * 80)
    
    # Initialize database and processor
    db = DatabaseManager("test_weekly.db")
    processor = DataProcessor(db)
    
    # Read the test weekly file
    weekly_file = "OpenAI User Data/Weekly OpenAI User Data/March/Eldridge Capital Management weekly user report 2025-03-30.csv"
    
    if not os.path.exists(weekly_file):
        print(f"❌ Test file not found: {weekly_file}")
        return False
    
    print(f"\n📂 Loading: {weekly_file}")
    df = pd.read_csv(weekly_file)
    print(f"✅ Loaded {len(df)} rows")
    
    # Process the data
    print(f"\n🔄 Processing data through clean_openai_data...")
    processed_df = processor.clean_openai_data(df, os.path.basename(weekly_file))
    
    print(f"✅ Processed to {len(processed_df)} records")
    
    # Check the results
    print(f"\n📊 Checking date assignments:")
    
    # Group by user email to see their assigned months
    for email in processed_df['email'].unique():
        user_records = processed_df[processed_df['email'] == email]
        user_name = user_records.iloc[0]['user_name']
        assigned_dates = user_records['date'].unique()
        
        print(f"\n  User: {user_name} ({email})")
        for date in assigned_dates:
            date_obj = pd.to_datetime(date)
            month_name = date_obj.strftime('%B %Y')
            record_count = len(user_records[user_records['date'] == date])
            print(f"    - {month_name}: {record_count} records")
            
            # Verify expected assignments
            if 'User One' in user_name:
                # User One was active April 2-5, should be assigned to April
                assert date_obj.month == 4, f"User One should be assigned to April, got {date_obj.month}"
                print(f"    ✅ Correctly assigned to April")
            elif 'User Two' in user_name:
                # User Two was active March 30-31, should be assigned to March
                assert date_obj.month == 3, f"User Two should be assigned to March, got {date_obj.month}"
                print(f"    ✅ Correctly assigned to March")
    
    # Clean up test database
    if os.path.exists("test_weekly.db"):
        os.remove("test_weekly.db")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED: DataProcessor handles weekly files correctly")
    print("=" * 80)
    
    return True

def test_data_processor_monthly_file():
    """Test that DataProcessor still handles monthly files correctly."""
    print("\n" + "=" * 80)
    print("TEST: DataProcessor Monthly File Handling (Backward Compatibility)")
    print("=" * 80)
    
    # Initialize database and processor
    db = DatabaseManager("test_monthly.db")
    processor = DataProcessor(db)
    
    # Read a monthly file
    monthly_file = "OpenAI User Data/Monthly OpenAI User Data/Openai Eldridge Capital Management monthly user report March.csv"
    
    if not os.path.exists(monthly_file):
        print(f"❌ Test file not found: {monthly_file}")
        return False
    
    print(f"\n📂 Loading: {monthly_file}")
    df = pd.read_csv(monthly_file)
    print(f"✅ Loaded {len(df)} rows")
    
    # Process the data
    print(f"\n🔄 Processing data through clean_openai_data...")
    processed_df = processor.clean_openai_data(df, os.path.basename(monthly_file))
    
    print(f"✅ Processed to {len(processed_df)} records")
    
    # Verify all records are assigned to March
    if len(processed_df) > 0:
        dates = pd.to_datetime(processed_df['date'])
        march_count = (dates.dt.month == 3).sum()
        
        print(f"\n📊 Records assigned to March: {march_count}/{len(processed_df)}")
        
        if march_count == len(processed_df):
            print("✅ All records correctly assigned to March")
        else:
            print(f"❌ Some records not assigned to March!")
            print(processed_df[['user_name', 'date', 'feature_used']])
            return False
    
    # Clean up test database
    if os.path.exists("test_monthly.db"):
        os.remove("test_monthly.db")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED: DataProcessor handles monthly files correctly")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DATA PROCESSOR WEEKLY TEST SUITE" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    try:
        success1 = test_data_processor_weekly_file()
        success2 = test_data_processor_monthly_file()
        
        if success1 and success2:
            print("\n" + "=" * 80)
            print("🎉 ALL DATA PROCESSOR TESTS PASSED! 🎉")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
