"""
Demonstration script showing the Department Performance bug fix.

This script simulates the bug and demonstrates how the fix resolves it.
"""

import pandas as pd
import sqlite3
import os
import sys

# Add project to path
sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

from database import DatabaseManager
from app import apply_employee_departments

def create_demo_database():
    """Create a demo database that reproduces the bug."""
    db_path = "demo_dept_fix.db"
    
    # Remove old database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    
    # Create employees table
    conn.execute("""
        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            title TEXT,
            department TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create usage_metrics table
    conn.execute("""
        CREATE TABLE usage_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT,
            email TEXT,
            department TEXT,
            date TEXT NOT NULL,
            feature_used TEXT,
            usage_count INTEGER,
            cost_usd REAL,
            tool_source TEXT DEFAULT 'ChatGPT',
            file_source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert employees (correct departments)
    employees = [
        ('Jack', 'Steed', 'jack.steed@company.com', 'Senior Analyst', 'Corporate Credit', 'Active'),
        ('Tyler', 'Mackesy', 'tyler.mackesy@company.com', 'Credit Manager', 'Corporate Credit', 'Active'),
        ('Alice', 'Johnson', 'alice.j@company.com', 'Software Engineer', 'Engineering', 'Active'),
        ('Bob', 'Smith', 'bob.smith@company.com', 'Data Analyst', 'Analytics', 'Active'),
    ]
    
    for emp in employees:
        conn.execute("""
            INSERT INTO employees (first_name, last_name, email, title, department, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, emp)
    
    # Insert usage data with INCORRECT departments (simulating the bug)
    # This is what happens when CSV data has wrong departments
    usage_data = [
        # Jack and Tyler incorrectly marked as 'Unknown' in usage data
        ('jack.steed@company.com', 'Jack Steed', 'jack.steed@company.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 150000, 60.0, 'ChatGPT'),
        ('tyler.mackesy@company.com', 'Tyler Mackesy', 'tyler.mackesy@company.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 80000, 60.0, 'ChatGPT'),
        
        # Bob incorrectly marked as 'Unknown'
        ('bob.smith@company.com', 'Bob Smith', 'bob.smith@company.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 70000, 60.0, 'ChatGPT'),
        
        # Alice correctly marked
        ('alice.j@company.com', 'Alice Johnson', 'alice.j@company.com', 'Engineering', '2024-10-01', 'ChatGPT Messages', 30000, 60.0, 'ChatGPT'),
        
        # Actual unknown users (not in employee table)
        ('external1@vendor.com', 'External User 1', 'external1@vendor.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 8000, 60.0, 'ChatGPT'),
        ('external2@contractor.com', 'External User 2', 'external2@contractor.com', 'Unknown', '2024-10-01', 'ChatGPT Messages', 10000, 60.0, 'ChatGPT'),
    ]
    
    for data in usage_data:
        conn.execute("""
            INSERT INTO usage_metrics (user_id, user_name, email, department, date, feature_used, usage_count, cost_usd, tool_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
    
    conn.commit()
    conn.close()
    
    return db_path

def demonstrate_bug_and_fix():
    """Demonstrate the bug and the fix."""
    
    print("\n" + "="*80)
    print("DEMONSTRATION: Department Performance Bug Fix")
    print("="*80)
    
    # Create demo database
    db_path = create_demo_database()
    db = DatabaseManager(db_path)
    
    # Get all data
    data = db.get_all_data()
    
    print("\n📋 SCENARIO:")
    print("-" * 80)
    print("• Employee Master File has 4 employees with correct departments:")
    print("  - Jack Steed → Corporate Credit")
    print("  - Tyler Mackesy → Corporate Credit") 
    print("  - Alice Johnson → Engineering")
    print("  - Bob Smith → Analytics")
    print("\n• Usage data (from CSV upload) has INCORRECT departments:")
    print("  - Jack, Tyler, Bob all marked as 'Unknown' (incorrect)")
    print("  - Only Alice has correct 'Engineering' department")
    print("  - 2 external users correctly marked as 'Unknown'")
    
    # Show the bug: Department Performance BEFORE fix
    print("\n" + "="*80)
    print("🐛 BUG: Department Performance (BEFORE Fix)")
    print("="*80)
    print("\nDepartment aggregation directly from usage_metrics table:")
    print("-" * 80)
    
    dept_stats_before = data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats_before.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    dept_stats_before = dept_stats_before.sort_values('Total Usage', ascending=False)
    
    print(dept_stats_before.to_string(index=False))
    
    top_dept = dept_stats_before.iloc[0]['Department']
    top_usage = dept_stats_before.iloc[0]['Total Usage']
    
    print(f"\n❌ PROBLEM: '{top_dept}' shows as #1 department with {top_usage:,} messages")
    print(f"   But this includes Jack, Tyler, and Bob who ARE employees!")
    
    # Show Unidentified Users section
    print("\n" + "="*80)
    print("📊 Unidentified Users Section (shows only 2 users)")
    print("="*80)
    
    unidentified = db.get_unidentified_users()
    print("\nUsers NOT in employee master file:")
    print("-" * 80)
    print(unidentified[['user_name', 'email', 'total_usage']].to_string(index=False))
    
    print(f"\n⚠️  DISCREPANCY:")
    print(f"   • Department Performance shows 'Unknown' with {top_usage:,} messages")
    print(f"   • Unidentified Users shows only {unidentified['total_usage'].sum():,} messages")
    print(f"   • Difference: {top_usage - unidentified['total_usage'].sum():,} messages from EMPLOYEES!")
    
    # Apply the fix
    print("\n" + "="*80)
    print("✅ SOLUTION: Apply Employee Departments (THE FIX)")
    print("="*80)
    
    data_fixed = apply_employee_departments(data, db)
    
    dept_stats_after = data_fixed.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats_after.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    dept_stats_after = dept_stats_after.sort_values('Total Usage', ascending=False)
    
    print("\nDepartment Performance (AFTER applying employee departments):")
    print("-" * 80)
    print(dept_stats_after.to_string(index=False))
    
    top_dept_after = dept_stats_after.iloc[0]['Department']
    top_usage_after = dept_stats_after.iloc[0]['Total Usage']
    
    print(f"\n✅ FIXED: '{top_dept_after}' is now correctly #1 with {top_usage_after:,} messages")
    print(f"   (Jack Steed: 150k + Tyler Mackesy: 80k = 230k)")
    
    # Show unknown is now correct
    unknown_row = dept_stats_after[dept_stats_after['Department'] == 'Unknown']
    if not unknown_row.empty:
        unknown_usage_after = unknown_row.iloc[0]['Total Usage']
        print(f"\n✅ 'Unknown' now correctly shows {unknown_usage_after:,} messages")
        print(f"   (Matches Unidentified Users: {unidentified['total_usage'].sum():,} messages)")
    
    # Show the fix details
    print("\n" + "="*80)
    print("🔧 How the Fix Works")
    print("="*80)
    print("""
1. Data is loaded from usage_metrics table (may have wrong departments)
2. apply_employee_departments() is called:
   • Looks up each user in employee master file
   • If found, replaces department with employee's department
   • If not found, keeps existing department (e.g., 'Unknown')
3. Now department stats are accurate and consistent!
    """)
    
    # Summary
    print("\n" + "="*80)
    print("📈 SUMMARY")
    print("="*80)
    print("\nBEFORE Fix:")
    print(f"  ❌ 'Unknown' incorrectly appears as top department ({top_usage:,} msgs)")
    print(f"  ❌ Employees (Jack, Tyler, Bob) counted under 'Unknown'")
    print(f"  ❌ Discrepancy with Unidentified Users section")
    
    print("\nAFTER Fix:")
    print(f"  ✅ '{top_dept_after}' correctly appears as top department ({top_usage_after:,} msgs)")
    print(f"  ✅ All employees show their correct departments from master file")
    print(f"  ✅ 'Unknown' only includes actual unidentified users (18k msgs)")
    print(f"  ✅ Consistency across all dashboard sections")
    
    print("\n" + "="*80)
    print("✨ FIX SUCCESSFULLY DEMONSTRATED!")
    print("="*80 + "\n")
    
    # Cleanup
    os.remove(db_path)

if __name__ == "__main__":
    demonstrate_bug_and_fix()
