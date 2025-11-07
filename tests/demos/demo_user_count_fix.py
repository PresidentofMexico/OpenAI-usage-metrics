"""
Demo script showing the before/after impact of the user counting fix.

This script creates a sample dataset that mimics the real-world problem:
- Users have multiple records across different features/time periods
- Old method (user_id.nunique()) over-counts users
- New method (email.nunique()) provides accurate counts
"""

import pandas as pd
import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)


def create_sample_data():
    """
    Create sample data that demonstrates the over-counting issue.
    
    Scenario: 5 actual users, but each has multiple records due to:
    - Different features used (ChatGPT, Tool Messages, Project Messages)
    - Multiple time periods
    - Different user_id values in different contexts
    """
    data = []
    
    # User 1: Alice - heavy user with 4 different user_id entries
    data.extend([
        {'user_id': 'alice_chat', 'email': 'alice@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-01-01', 'usage': 50},
        {'user_id': 'alice_tool', 'email': 'alice@company.com', 'feature': 'Tool Messages', 'date': '2024-01-15', 'usage': 30},
        {'user_id': 'alice_proj', 'email': 'alice@company.com', 'feature': 'Project Messages', 'date': '2024-02-01', 'usage': 20},
        {'user_id': 'alice_jan', 'email': 'alice@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-01-20', 'usage': 40},
    ])
    
    # User 2: Bob - moderate user with 3 different user_id entries
    data.extend([
        {'user_id': 'bob_001', 'email': 'bob@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-01-05', 'usage': 25},
        {'user_id': 'bob_002', 'email': 'bob@company.com', 'feature': 'Tool Messages', 'date': '2024-01-18', 'usage': 15},
        {'user_id': 'bob_003', 'email': 'bob@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-02-03', 'usage': 30},
    ])
    
    # User 3: Charlie - light user with 2 entries
    data.extend([
        {'user_id': 'charlie_v1', 'email': 'charlie@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-01-10', 'usage': 10},
        {'user_id': 'charlie_v2', 'email': 'charlie@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-02-05', 'usage': 12},
    ])
    
    # User 4: Diana - occasional user with 2 entries
    data.extend([
        {'user_id': 'diana_main', 'email': 'diana@company.com', 'feature': 'Tool Messages', 'date': '2024-01-12', 'usage': 8},
        {'user_id': 'diana_alt', 'email': 'diana@company.com', 'feature': 'Project Messages', 'date': '2024-02-08', 'usage': 5},
    ])
    
    # User 5: Eve - new user with 1 entry
    data.append(
        {'user_id': 'eve_new', 'email': 'eve@company.com', 'feature': 'ChatGPT Messages', 'date': '2024-02-10', 'usage': 15}
    )
    
    return pd.DataFrame(data)


def demonstrate_fix():
    """Show the before/after impact of the fix."""
    
    print("\n" + "=" * 80)
    print("DEMONSTRATION: User Counting Fix Impact")
    print("=" * 80)
    
    # Create sample data
    df = create_sample_data()
    
    print(f"\n📊 Sample Dataset Overview:")
    print(f"   Total records in database: {len(df)}")
    print(f"   Actual users in organization: 5 (Alice, Bob, Charlie, Diana, Eve)")
    print()
    
    # Show sample records
    print("Sample Records:")
    print(df[['user_id', 'email', 'feature', 'usage']].head(6))
    print("   ...")
    print()
    
    # OLD METHOD - Count unique user_id (THE BUG)
    old_count = df['user_id'].nunique()
    print("=" * 80)
    print("❌ OLD METHOD - Counting unique user_id values (INCORRECT)")
    print("=" * 80)
    print(f"Code: data['user_id'].nunique()")
    print(f"Result: {old_count} users")
    print(f"\n⚠️  PROBLEM: This over-counts by {old_count - 5} users!")
    print(f"   Each person is counted multiple times due to multiple user_id values")
    print()
    
    # Show breakdown
    print("User ID Breakdown:")
    user_id_counts = df.groupby('email')['user_id'].nunique().sort_values(ascending=False)
    for email, count in user_id_counts.items():
        name = email.split('@')[0].title()
        print(f"   {name}: {count} different user_id values")
    print()
    
    # NEW METHOD - Count unique emails (THE FIX)
    new_count = df['email'].dropna().str.lower().nunique()
    print("=" * 80)
    print("✅ NEW METHOD - Counting unique emails (CORRECT)")
    print("=" * 80)
    print(f"Code: data['email'].dropna().str.lower().nunique()")
    print(f"Result: {new_count} users")
    print(f"\n✅ CORRECT: Accurately reflects the actual user count!")
    print(f"   Each person is counted exactly once, regardless of record count")
    print()
    
    # Impact summary
    print("=" * 80)
    print("📊 IMPACT SUMMARY")
    print("=" * 80)
    print(f"Old count (user_id):  {old_count} users  ❌ INFLATED")
    print(f"New count (email):    {new_count} users  ✅ ACCURATE")
    print(f"Over-count removed:   {old_count - new_count} phantom users")
    print(f"Accuracy improvement: {((old_count - new_count) / old_count * 100):.1f}% reduction in error")
    print()
    
    # Show per-user metrics impact
    print("=" * 80)
    print("📈 IMPACT ON PER-USER METRICS")
    print("=" * 80)
    
    total_usage = df['usage'].sum()
    
    old_avg = total_usage / old_count
    new_avg = total_usage / new_count
    
    print(f"Total usage: {total_usage} messages")
    print()
    print(f"OLD avg messages/user: {old_avg:.1f} (based on {old_count} users)")
    print(f"NEW avg messages/user: {new_avg:.1f} (based on {new_count} users)")
    print()
    print(f"Difference: {new_avg - old_avg:.1f} messages/user")
    print(f"   The NEW metric is {((new_avg / old_avg - 1) * 100):.1f}% higher (more accurate)")
    print()
    
    # Real-world extrapolation
    print("=" * 80)
    print("🏢 REAL-WORLD SCENARIO (Mentioned in Issue)")
    print("=" * 80)
    print(f"Problem reported: Dashboard showing 365+ users")
    print(f"Actual users: <250 users")
    print(f"Over-count: ~115+ phantom users (46% error)")
    print()
    print(f"Our fix in this demo:")
    print(f"  • Eliminated {old_count - new_count} phantom users")
    print(f"  • From {old_count} down to {new_count} (actual count)")
    print(f"  • Error reduction: {((old_count - new_count) / old_count * 100):.1f}%")
    print()
    print("✅ Fix successfully resolves the over-counting issue!")
    print("=" * 80)


if __name__ == '__main__':
    demonstrate_fix()
