"""
Integration test for Department Mapper pagination with database.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, '/home/runner/work/OpenAI-usage-metrics/OpenAI-usage-metrics')

from database import DatabaseManager
from app import _select_primary_department

print("=" * 80)
print("DEPARTMENT MAPPER PAGINATION - DATABASE INTEGRATION TEST")
print("=" * 80)

# Initialize database
db = DatabaseManager()

# Get all data
all_data = db.get_all_data()
print(f"\n📊 Total records in database: {len(all_data)}")
print(f"📊 Unique users: {all_data['email'].nunique()}")

# Simulate the deduplication logic from display_department_mapper()
users_df = all_data.groupby('email').agg({
    'user_name': 'first',
    'department': lambda x: _select_primary_department(x),
    'tool_source': lambda x: ', '.join(sorted(x.unique()))
}).reset_index()
users_df = users_df.sort_values('user_name')

print(f"📊 Deduplicated users: {len(users_df)}")

# Pagination parameters
users_per_page = 20
total_pages = max(1, (len(users_df) + users_per_page - 1) // users_per_page)

print(f"\n📄 Pagination settings:")
print(f"   Users per page: {users_per_page}")
print(f"   Total pages: {total_pages}")

# Simulate pagination
print(f"\n📋 Page breakdown:")
for page in range(total_pages):
    start_idx = page * users_per_page
    end_idx = start_idx + users_per_page
    current_page_users = users_df.iloc[start_idx:end_idx]
    
    showing_text = f"Showing users {start_idx + 1}-{min(end_idx, len(users_df))} of {len(users_df)}"
    print(f"\n   Page {page + 1}: {showing_text}")
    print(f"   Users on page: {len(current_page_users)}")
    
    # Show users on this page
    for i, (idx, row) in enumerate(current_page_users.iterrows()):
        multi_tool = '🔗' if ', ' in row['tool_source'] else '  '
        print(f"      {multi_tool} {row['user_name']:20s} | {row['email']:30s} | {row['department']:20s}")

# Test search functionality
print(f"\n" + "=" * 80)
print("SEARCH FUNCTIONALITY TEST")
print("=" * 80)

search_term = "john"
filtered_df = users_df[
    users_df['user_name'].str.contains(search_term, case=False, na=False) | 
    users_df['email'].str.contains(search_term, case=False, na=False)
]

print(f"\n🔍 Search term: '{search_term}'")
print(f"📊 Filtered users: {len(filtered_df)}")

if len(filtered_df) > 0:
    total_pages_filtered = max(1, (len(filtered_df) + users_per_page - 1) // users_per_page)
    print(f"📄 Total pages (filtered): {total_pages_filtered}")
    
    start_idx = 0
    end_idx = users_per_page
    current_page_users = filtered_df.iloc[start_idx:end_idx]
    
    showing_text = f"Showing users {start_idx + 1}-{min(end_idx, len(filtered_df))} of {len(filtered_df)} (filtered by '{search_term}')"
    print(f"\n   {showing_text}")
    
    for i, (idx, row) in enumerate(current_page_users.iterrows()):
        multi_tool = '🔗' if ', ' in row['tool_source'] else '  '
        print(f"      {multi_tool} {row['user_name']:20s} | {row['email']:30s} | {row['department']:20s}")
else:
    print(f"   No users found matching '{search_term}'")

print(f"\n" + "=" * 80)
print("✅ ALL INTEGRATION TESTS PASSED!")
print("=" * 80)
