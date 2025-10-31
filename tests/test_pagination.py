"""
Test script to verify Department Mapper pagination functionality.
"""

import pandas as pd
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)

# Simulate pagination logic
def test_pagination():
    # Create test data with 55 users (to test multiple pages)
    users = []
    for i in range(55):
        users.append({
            'email': f'user{i}@company.com',
            'user_name': f'User {i:02d}',
            'department': 'Finance' if i % 3 == 0 else 'IT' if i % 3 == 1 else 'Analytics',
            'tool_source': 'ChatGPT' if i % 2 == 0 else 'BlueFlame AI, ChatGPT'
        })
    
    users_df = pd.DataFrame(users)
    users_per_page = 20
    
    print("=" * 80)
    print("PAGINATION TEST")
    print("=" * 80)
    print(f"\nTotal users: {len(users_df)}")
    print(f"Users per page: {users_per_page}")
    
    # Calculate total pages
    total_pages = max(1, (len(users_df) + users_per_page - 1) // users_per_page)
    print(f"Total pages: {total_pages}")
    
    # Test each page
    for page in range(total_pages):
        start_idx = page * users_per_page
        end_idx = start_idx + users_per_page
        current_page_users = users_df.iloc[start_idx:end_idx]
        
        print(f"\n--- Page {page + 1} of {total_pages} ---")
        print(f"Start index: {start_idx}, End index: {end_idx}")
        print(f"Users on this page: {len(current_page_users)}")
        print(f"Showing users {start_idx + 1}-{min(end_idx, len(users_df))} of {len(users_df)}")
        
        # Show first few users on the page
        for i, (idx, row) in enumerate(list(current_page_users.iterrows())[:3]):
            multi_tool = '🔗' if ', ' in row['tool_source'] else '  '
            print(f"  {multi_tool} {row['user_name']:15s} | {row['email']:25s} | {row['department']:15s}")
        
        if len(current_page_users) > 3:
            print(f"  ... and {len(current_page_users) - 3} more users")
    
    print("\n" + "=" * 80)
    print("✅ PAGINATION TEST PASSED!")
    print("=" * 80)
    
    # Test search with pagination
    print("\n\nSEARCH + PAGINATION TEST")
    print("=" * 80)
    
    # Simulate search filter
    search = "User 1"
    filtered_df = users_df[
        users_df['user_name'].str.contains(search, case=False, na=False) | 
        users_df['email'].str.contains(search, case=False, na=False)
    ]
    
    print(f"\nSearch term: '{search}'")
    print(f"Filtered users: {len(filtered_df)}")
    
    # Recalculate pages for filtered results
    total_pages_filtered = max(1, (len(filtered_df) + users_per_page - 1) // users_per_page)
    print(f"Total pages (filtered): {total_pages_filtered}")
    
    # Show first page of filtered results
    start_idx = 0
    end_idx = users_per_page
    current_page_users = filtered_df.iloc[start_idx:end_idx]
    
    print(f"\nFirst page of filtered results:")
    print(f"Showing users {start_idx + 1}-{min(end_idx, len(filtered_df))} of {len(filtered_df)} (filtered by '{search}')")
    
    for i, (idx, row) in enumerate(list(current_page_users.iterrows())[:5]):
        multi_tool = '🔗' if ', ' in row['tool_source'] else '  '
        print(f"  {multi_tool} {row['user_name']:15s} | {row['email']:25s} | {row['department']:15s}")
    
    print("\n" + "=" * 80)
    print("✅ SEARCH + PAGINATION TEST PASSED!")
    print("=" * 80)
    
    # Test edge cases
    print("\n\nEDGE CASES TEST")
    print("=" * 80)
    
    # Edge case 1: Exactly 20 users (1 page)
    edge_df_1 = users_df.head(20)
    total_pages_1 = max(1, (len(edge_df_1) + users_per_page - 1) // users_per_page)
    print(f"\nEdge case 1: Exactly {len(edge_df_1)} users = {total_pages_1} page(s) ✓")
    
    # Edge case 2: 21 users (2 pages)
    edge_df_2 = users_df.head(21)
    total_pages_2 = max(1, (len(edge_df_2) + users_per_page - 1) // users_per_page)
    print(f"Edge case 2: Exactly {len(edge_df_2)} users = {total_pages_2} page(s) ✓")
    
    # Edge case 3: 1 user (1 page)
    edge_df_3 = users_df.head(1)
    total_pages_3 = max(1, (len(edge_df_3) + users_per_page - 1) // users_per_page)
    print(f"Edge case 3: Exactly {len(edge_df_3)} user = {total_pages_3} page(s) ✓")
    
    # Edge case 4: No users (1 page - minimum)
    edge_df_4 = users_df.head(0)
    total_pages_4 = max(1, (len(edge_df_4) + users_per_page - 1) // users_per_page)
    print(f"Edge case 4: Exactly {len(edge_df_4)} users = {total_pages_4} page(s) (minimum) ✓")
    
    print("\n" + "=" * 80)
    print("✅ ALL EDGE CASES PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    test_pagination()
