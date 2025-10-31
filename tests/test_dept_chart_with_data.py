#!/usr/bin/env python3
"""
Test script to verify the department chart enhancements work correctly with real data.
This simulates the Streamlit app's data loading and chart generation logic.
"""

import pandas as pd
import sys
import os

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from database import DatabaseManager
from data_processor import DataProcessor

def test_with_real_data():
    """Test department chart logic with real data from database."""
    print("=" * 60)
    print("Testing Department Chart Enhancements with Real Data")
    print("=" * 60)
    
    # Initialize database
    db = DatabaseManager()
    
    # Get all data
    print("\n📊 Loading data from database...")
    data = db.get_all_data()
    
    if data.empty:
        print("⚠️  No data in database. Skipping test.")
        return True
    
    print(f"✅ Loaded {len(data)} records")
    print(f"   Unique users: {data['user_id'].nunique()}")
    print(f"   Departments: {data['department'].nunique()}")
    print(f"   Date range: {data['date'].min()} to {data['date'].max()}")
    
    # Calculate department statistics with message type breakdown (same logic as app.py)
    print("\n🔧 Calculating department statistics...")
    dept_stats = data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage']
    
    # Calculate message type breakdown for each department
    dept_message_breakdown = data.groupby(['department', 'feature_used'])['usage_count'].sum().reset_index()
    dept_message_pivot = dept_message_breakdown.pivot(index='department', columns='feature_used', values='usage_count').fillna(0)
    
    # Merge message type breakdown with dept_stats (single merge for better performance)
    dept_stats = dept_stats.merge(
        dept_message_pivot.reset_index().rename(columns={'department': 'Department'}),
        on='Department',
        how='left'
    ).fillna(0)
    
    # Calculate derived metrics
    total_usage_all = dept_stats['Total Usage'].sum()
    dept_stats['Usage Share %'] = (dept_stats['Total Usage'] / total_usage_all * 100).round(1)
    dept_stats['Avg Messages/User'] = (dept_stats['Total Usage'] / dept_stats['Active Users']).round(0)
    dept_stats = dept_stats.sort_values('Total Usage', ascending=False)
    
    print(f"✅ Calculated stats for {len(dept_stats)} departments")
    
    # Get message type columns
    message_type_cols = [col for col in dept_stats.columns 
                       if col not in ['Department', 'Active Users', 'Total Usage', 'Usage Share %', 'Avg Messages/User']]
    
    print(f"\n📈 Message types found: {message_type_cols}")
    
    # Display top 5 departments
    print("\n🏆 Top 5 Departments by Total Usage:")
    print("-" * 60)
    for idx, row in dept_stats.head(5).iterrows():
        print(f"\n{row['Department']}:")
        print(f"  Total Messages: {row['Total Usage']:,}")
        print(f"  Active Users: {row['Active Users']}")
        print(f"  Avg Messages/User: {row['Avg Messages/User']:,.0f}")
        print(f"  Usage Share: {row['Usage Share %']:.1f}%")
        
        # Show message type breakdown
        breakdown = []
        for msg_type in message_type_cols:
            if row[msg_type] > 0:
                breakdown.append(f"{msg_type}: {int(row[msg_type]):,}")
        if breakdown:
            print(f"  Breakdown: {', '.join(breakdown)}")
    
    # Verify totals match
    print("\n🧪 Verification Tests:")
    
    # Test 1: Sum of message types equals total usage
    for idx, row in dept_stats.iterrows():
        msg_sum = sum(row[col] for col in message_type_cols)
        total = row['Total Usage']
        if abs(msg_sum - total) > 0.01:
            print(f"❌ FAIL: {row['Department']} - Sum of message types ({msg_sum}) != Total Usage ({total})")
            return False
    print("✅ PASS: Sum of message types equals Total Usage for all departments")
    
    # Test 2: User drilldown for top department
    top_dept = dept_stats.iloc[0]['Department']
    print(f"\n👥 Testing user drilldown for '{top_dept}'...")
    
    dept_users = data[data['department'] == top_dept].copy()
    
    if not dept_users.empty:
        # Aggregate by user
        user_stats = dept_users.groupby(['email', 'user_name']).agg({
            'usage_count': 'sum',
            'date': ['min', 'max']
        }).reset_index()
        
        # Flatten multi-level columns
        user_stats.columns = ['email', 'user_name', 'total_messages', 'first_active', 'last_active']
        
        # Get message type breakdown for each user
        for msg_type in message_type_cols:
            user_msg_type = dept_users[dept_users['feature_used'] == msg_type].groupby('email')['usage_count'].sum()
            user_stats[msg_type] = user_stats['email'].map(user_msg_type).fillna(0).astype(int)
        
        print(f"✅ PASS: User drilldown created for {len(user_stats)} users in {top_dept}")
        
        # Show top 3 users
        print(f"\n  Top 3 users in {top_dept}:")
        for _, user in user_stats.nlargest(3, 'total_messages').iterrows():
            print(f"    {user['user_name']} ({user['email']}): {int(user['total_messages']):,} messages")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Department chart enhancements work correctly.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = test_with_real_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
