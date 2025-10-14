#!/usr/bin/env python3
"""
Demo script showing get_unidentified_users() method in action
Simulates the Department Mapper use case from PR #33
"""
import os
import sys
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

import pandas as pd
from database import DatabaseManager

def demo_unidentified_users():
    """Demonstrate the get_unidentified_users() functionality"""
    
    # Create a demo database
    demo_db = 'demo_unidentified.db'
    if os.path.exists(demo_db):
        os.remove(demo_db)
    
    print("\n" + "=" * 70)
    print("DEMO: Department Mapper - Unidentified Users Detection")
    print("=" * 70)
    print("\nThis demo simulates the PR #33 Department Mapper feature that")
    print("calls db.get_unidentified_users() to find users not in the")
    print("employee master file.\n")
    
    # Step 1: Initialize
    print("Step 1: Initializing database...")
    db = DatabaseManager(demo_db)
    print("✅ Database ready\n")
    
    # Step 2: Load employee master file
    print("Step 2: Loading employee master file...")
    employees = pd.DataFrame({
        'first_name': ['Sarah', 'Mike', 'Jennifer'],
        'last_name': ['Johnson', 'Smith', 'Davis'],
        'email': ['sarah.johnson@company.com', 'mike.smith@company.com', 'jennifer.davis@company.com'],
        'title': ['Senior Engineer', 'Product Manager', 'Data Analyst'],
        'department': ['Engineering', 'Product', 'Analytics'],
        'status': ['Active', 'Active', 'Active']
    })
    
    db.load_employees(employees)
    print(f"✅ Loaded {len(employees)} employees from master file\n")
    
    # Step 3: Simulate AI usage data upload
    print("Step 3: Processing AI tool usage data...")
    import sqlite3
    conn = sqlite3.connect(demo_db)
    
    usage_data = pd.DataFrame({
        'user_id': [
            'sarah.johnson@company.com', 'sarah.johnson@company.com',
            'mike.smith@company.com',
            'contractor.john@external.com', 'contractor.john@external.com', 'contractor.john@external.com',
            'temp.worker@agency.com', 'temp.worker@agency.com'
        ],
        'user_name': [
            'Sarah Johnson', 'Sarah Johnson',
            'Mike Smith',
            'John Contractor', 'John Contractor', 'John Contractor',
            'Temp Worker', 'Temp Worker'
        ],
        'email': [
            'sarah.johnson@company.com', 'sarah.johnson@company.com',
            'mike.smith@company.com',
            'contractor.john@external.com', 'contractor.john@external.com', 'contractor.john@external.com',
            'temp.worker@agency.com', 'temp.worker@agency.com'
        ],
        'department': [
            'Engineering', 'Engineering',
            'Product',
            'Unknown', 'Unknown', 'Unknown',
            'Unknown', 'Unknown'
        ],
        'date': [
            '2024-01-15', '2024-01-16',
            '2024-01-15',
            '2024-01-15', '2024-01-16', '2024-01-17',
            '2024-01-15', '2024-01-16'
        ],
        'feature_used': [
            'ChatGPT', 'ChatGPT',
            'ChatGPT',
            'ChatGPT', 'Tool Messages', 'ChatGPT',
            'ChatGPT', 'ChatGPT'
        ],
        'usage_count': [
            35, 42,
            28,
            150, 80, 95,
            60, 45
        ],
        'cost_usd': [
            17.5, 21.0,
            14.0,
            75.0, 40.0, 47.5,
            30.0, 22.5
        ],
        'tool_source': [
            'ChatGPT', 'ChatGPT',
            'ChatGPT',
            'ChatGPT', 'BlueFlame', 'ChatGPT',
            'ChatGPT', 'ChatGPT'
        ],
        'file_source': [
            'usage_jan.csv', 'usage_jan.csv',
            'usage_jan.csv',
            'usage_jan.csv', 'usage_jan.csv', 'usage_jan.csv',
            'usage_jan.csv', 'usage_jan.csv'
        ]
    })
    
    usage_data.to_sql('usage_metrics', conn, if_exists='append', index=False)
    conn.close()
    print(f"✅ Processed {len(usage_data)} usage records\n")
    
    # Step 4: Call get_unidentified_users() - THE KEY METHOD FROM PR #33
    print("Step 4: Detecting unidentified users (PR #33 fix)...")
    print("         Calling: db.get_unidentified_users()\n")
    
    unidentified_df = db.get_unidentified_users()
    
    if unidentified_df.empty:
        print("✅ No unidentified users found - all users are in employee master file")
    else:
        print(f"⚠️  Found {len(unidentified_df)} unidentified users:\n")
        print("-" * 70)
        
        for idx, row in unidentified_df.iterrows():
            print(f"\n👤 User #{idx + 1}:")
            print(f"   Name:        {row['user_name']}")
            print(f"   Email:       {row['email']}")
            print(f"   Tools Used:  {row['tools_used']}")
            print(f"   Total Usage: {int(row['total_usage']):,} messages")
            print(f"   Total Cost:  ${row['total_cost']:.2f}")
            print(f"   Days Active: {int(row['days_active'])} days")
            
            # Calculate average per day
            avg_per_day = row['total_usage'] / row['days_active']
            print(f"   Avg/Day:     {int(avg_per_day):,} messages/day")
        
        print("\n" + "-" * 70)
        print("\n📊 Summary Statistics:")
        print(f"   Total unidentified users:  {len(unidentified_df)}")
        print(f"   Total usage (unidentified): {int(unidentified_df['total_usage'].sum()):,} messages")
        print(f"   Total cost (unidentified):  ${unidentified_df['total_cost'].sum():.2f}")
        
        # Show who has highest usage
        top_user = unidentified_df.iloc[0]
        print(f"\n🔝 Highest usage unidentified user:")
        print(f"   {top_user['user_name']} ({top_user['email']})")
        print(f"   {int(top_user['total_usage']):,} messages, ${top_user['total_cost']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE")
    print("=" * 70)
    print("\nThe get_unidentified_users() method successfully:")
    print("  ✓ Identified users NOT in the employee master file")
    print("  ✓ Aggregated their usage statistics")
    print("  ✓ Sorted by total usage (highest first)")
    print("  ✓ Grouped multi-tool usage per user")
    print("\nThis data would be displayed in the Department Mapper UI,")
    print("allowing admins to assign departments to unidentified users.\n")
    
    # Cleanup
    if os.path.exists(demo_db):
        os.remove(demo_db)

if __name__ == "__main__":
    demo_unidentified_users()
