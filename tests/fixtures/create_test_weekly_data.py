"""
Create test weekly data files to test the weekly file detection and date parsing logic.
This creates weekly files that span two months to test edge cases.
"""

import pandas as pd
import os
from datetime import datetime, timedelta

# Create sample weekly data that spans March-April boundary
# Week starting March 30, 2025 (Sunday) - ends April 5, 2025 (Saturday)

def create_weekly_report_spanning_months():
    """Create a weekly report that spans March and April 2025."""
    
    # Week: March 30 - April 5, 2025
    # Days in March: March 30, 31 (2 days)
    # Days in April: April 1, 2, 3, 4, 5 (5 days)
    # Should be assigned to April since most days are in April
    
    data = [
        {
            'cadence': 'Weekly',
            'period_start': '2025-03-30',
            'period_end': '2025-04-05',
            'account_id': '8692590815c34cfca1333ff09b53ee58',
            'public_id': 'user-test1',
            'name': 'Test User One',
            'email': 'test.user1@eldridge.com',
            'role': '',
            'user_role': 'standard-user',
            'department': '',
            'groups': '',
            'user_status': 'enabled',
            'created_or_invited_date': '2025-03-01',
            'is_active': 1,
            'first_day_active_in_period': '2025-04-02',  # First activity in April
            'last_day_active_in_period': '2025-04-05',   # Last activity in April
            'messages': 25,
            'messages_rank': '',
            'model_to_messages': "{'gpt-4o': 25}",
            'gpt_messages': 5,
            'gpts_messaged': 1,
            'gpt_to_messages': '',
            'tool_messages': 3,
            'tools_messaged': 1,
            'tool_to_messages': '',
            'project_messages': 2,
            'projects_messaged': 1,
            'project_to_messages': '',
            'projects_created': 0,
            'last_day_active': '2025-04-05'
        },
        {
            'cadence': 'Weekly',
            'period_start': '2025-03-30',
            'period_end': '2025-04-05',
            'account_id': '8692590815c34cfca1333ff09b53ee58',
            'public_id': 'user-test2',
            'name': 'Test User Two',
            'email': 'test.user2@eldridge.com',
            'role': '',
            'user_role': 'standard-user',
            'department': '',
            'groups': '',
            'user_status': 'enabled',
            'created_or_invited_date': '2025-03-01',
            'is_active': 1,
            'first_day_active_in_period': '2025-03-30',  # First activity in March
            'last_day_active_in_period': '2025-03-31',   # Last activity in March
            'messages': 10,
            'messages_rank': '',
            'model_to_messages': "{'gpt-4o': 10}",
            'gpt_messages': 2,
            'gpts_messaged': 1,
            'gpt_to_messages': '',
            'tool_messages': 1,
            'tools_messaged': 1,
            'tool_to_messages': '',
            'project_messages': 0,
            'projects_messaged': 0,
            'project_to_messages': '',
            'projects_created': 0,
            'last_day_active': '2025-03-31'
        }
    ]
    
    df = pd.DataFrame(data)
    
    # Save to appropriate folder
    output_dir = "OpenAI User Data/Weekly OpenAI User Data/March"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = "Eldridge Capital Management weekly user report 2025-03-30.csv"
    filepath = os.path.join(output_dir, filename)
    
    df.to_csv(filepath, index=False)
    print(f"✅ Created test weekly file: {filepath}")
    print(f"   Period: March 30 - April 5, 2025")
    print(f"   User 1: Activity in April (should assign to April)")
    print(f"   User 2: Activity in March (should assign to March)")
    
    return filepath

def create_weekly_report_all_same_month():
    """Create a weekly report entirely within one month (April)."""
    
    data = [
        {
            'cadence': 'Weekly',
            'period_start': '2025-04-06',
            'period_end': '2025-04-12',
            'account_id': '8692590815c34cfca1333ff09b53ee58',
            'public_id': 'user-test3',
            'name': 'Test User Three',
            'email': 'test.user3@eldridge.com',
            'role': '',
            'user_role': 'standard-user',
            'department': '',
            'groups': '',
            'user_status': 'enabled',
            'created_or_invited_date': '2025-03-01',
            'is_active': 1,
            'first_day_active_in_period': '2025-04-07',
            'last_day_active_in_period': '2025-04-11',
            'messages': 30,
            'messages_rank': '',
            'model_to_messages': "{'gpt-4o': 30}",
            'gpt_messages': 8,
            'gpts_messaged': 2,
            'gpt_to_messages': '',
            'tool_messages': 5,
            'tools_messaged': 1,
            'tool_to_messages': '',
            'project_messages': 3,
            'projects_messaged': 1,
            'project_to_messages': '',
            'projects_created': 0,
            'last_day_active': '2025-04-11'
        }
    ]
    
    df = pd.DataFrame(data)
    
    # Save to appropriate folder
    output_dir = "OpenAI User Data/Weekly OpenAI User Data/April"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = "Eldridge Capital Management weekly user report 2025-04-06.csv"
    filepath = os.path.join(output_dir, filename)
    
    df.to_csv(filepath, index=False)
    print(f"✅ Created test weekly file: {filepath}")
    print(f"   Period: April 6 - April 12, 2025")
    print(f"   All activity in April (should assign to April)")
    
    return filepath

if __name__ == "__main__":
    print("Creating test weekly data files...")
    print("=" * 80)
    
    file1 = create_weekly_report_spanning_months()
    print()
    file2 = create_weekly_report_all_same_month()
    
    print()
    print("=" * 80)
    print("✅ Test data creation complete!")
    print()
    print("Files created:")
    print(f"  1. {file1}")
    print(f"  2. {file2}")
    print()
    print("These files test:")
    print("  - Weekly files spanning two months")
    print("  - Date-based assignment to correct month")
    print("  - Weekly file detection based on filename")
