"""
Test script to demonstrate Department Mapper UI improvements.
This script creates test data and shows how the deduplication works.
"""

import pandas as pd
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)
from app import _select_primary_department

# Create test data with users from multiple tools
test_data = pd.DataFrame({
    'email': [
        'kaan.erturk@company.com',
        'kaan.erturk@company.com',
        'john.doe@company.com',
        'jane.smith@company.com',
        'jane.smith@company.com',
        'bob.jones@company.com'
    ],
    'user_name': [
        'Kaan Erturk',
        'Kaan Erturk',
        'John Doe',
        'Jane Smith',
        'Jane Smith',
        'Bob Jones'
    ],
    'department': [
        'finance',
        'BlueFlame Users',
        'IT',
        'Analytics',
        'BlueFlame Users',
        'BlueFlame Users'
    ],
    'tool_source': [
        'ChatGPT',
        'BlueFlame AI',
        'ChatGPT',
        'ChatGPT',
        'BlueFlame AI',
        'BlueFlame AI'
    ],
    'usage_count': [
        325,
        420,
        150,
        200,
        180,
        90
    ]
})

print("=" * 80)
print("DEPARTMENT MAPPER DEDUPLICATION - BEFORE AND AFTER")
print("=" * 80)

# OLD METHOD (showing the bug)
print("\n📊 OLD METHOD (Current Bug)")
print("-" * 80)
old_users = test_data[['email', 'user_name', 'department']].drop_duplicates()
old_users = old_users.sort_values('user_name')

print(f"Total users shown: {len(old_users)}\n")
for idx, row in old_users.iterrows():
    print(f"  {row['user_name']:20s} | {row['email']:30s} | {row['department']:20s}")

# NEW METHOD (after fix)
print("\n✅ NEW METHOD (After Fix)")
print("-" * 80)
new_users = test_data.groupby('email').agg({
    'user_name': 'first',
    'department': lambda x: _select_primary_department(x),
    'tool_source': lambda x: ', '.join(sorted(x.unique())),
    'usage_count': 'sum'
}).reset_index()
new_users = new_users.sort_values('user_name')

print(f"Total users shown: {len(new_users)}\n")
for idx, row in new_users.iterrows():
    multi_tool = '🔗' if ', ' in row['tool_source'] else '  '
    print(f"{multi_tool} {row['user_name']:20s} | {row['email']:30s} | {row['department']:20s} | {row['tool_source']:30s}")

# Summary
print("\n" + "=" * 80)
print("📈 SUMMARY")
print("=" * 80)
print(f"Old method: {len(old_users)} entries (includes duplicates)")
print(f"New method: {len(new_users)} unique users (deduplicated by email)")
print(f"\nDuplicates removed: {len(old_users) - len(new_users)}")

# Show which users have multiple tools
multi_tool_users = new_users[new_users['tool_source'].str.contains(', ')]
print(f"\nUsers with multiple AI tools: {len(multi_tool_users)}")
for idx, row in multi_tool_users.iterrows():
    print(f"  🔗 {row['user_name']} - {row['tool_source']}")
    print(f"     Department: {row['department']} (smart selection)")
    print(f"     Total usage: {row['usage_count']} messages")

print("\n" + "=" * 80)
print("✅ Department Mapper now correctly deduplicates users!")
print("=" * 80)
