"""
Test suite for Department Mapper deduplication fix.

Tests that users with records from multiple AI tools (OpenAI and BlueFlame)
appear only once in the Department Mapper UI, with smart department selection.
"""

import pandas as pd
import sys

def test_department_mapper_deduplication():
    """Test that department mapper deduplicates users by email only."""
    print("\n🧪 Testing Department Mapper Deduplication...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    sys.path.insert(0, project_root)
    from app import _select_primary_department
    
    # Simulate data from database with duplicate user across different tools/departments
    test_data = pd.DataFrame({
        'email': ['kaan@test.com', 'kaan@test.com', 'john@test.com'],
        'user_name': ['Kaan Erturk', 'Kaan Erturk', 'John Doe'],
        'department': ['finance', 'BlueFlame Users', 'IT'],
        'tool_source': ['ChatGPT', 'BlueFlame AI', 'ChatGPT']
    })
    
    # OLD METHOD (current bug): drop_duplicates on email, user_name, department
    old_method_df = test_data[['email', 'user_name', 'department']].drop_duplicates()
    old_count = len(old_method_df)
    
    # NEW METHOD: Group by email and select primary department
    new_method_df = test_data.groupby('email').agg({
        'user_name': 'first',
        'department': lambda x: _select_primary_department(x),
        'tool_source': lambda x: ', '.join(sorted(x.unique()))
    }).reset_index()
    new_count = len(new_method_df)
    
    print(f"  Old method (bug): {old_count} users shown")
    print(f"  New method (fixed): {new_count} users shown")
    
    # Verify deduplication
    assert old_count == 3, f"Old method should show 3 users (bug), got {old_count}"
    assert new_count == 2, f"New method should show 2 unique users, got {new_count}"
    
    # Verify Kaan Erturk appears only once with 'finance' department
    kaan = new_method_df[new_method_df['email'] == 'kaan@test.com']
    assert len(kaan) == 1, "Kaan should appear only once"
    assert kaan.iloc[0]['department'] == 'finance', f"Kaan should have 'finance' dept, got {kaan.iloc[0]['department']}"
    assert kaan.iloc[0]['tool_source'] == 'BlueFlame AI, ChatGPT', f"Kaan should show both tools, got {kaan.iloc[0]['tool_source']}"
    
    print(f"✅ Kaan Erturk correctly deduplicated:")
    print(f"   - Department: {kaan.iloc[0]['department']}")
    print(f"   - Tools: {kaan.iloc[0]['tool_source']}")
    
    return True

def run_test():
    """Run the department mapper deduplication test."""
    print("=" * 60)
    print("🚀 Testing Department Mapper Deduplication Fix")
    print("=" * 60)
    
    try:
        result = test_department_mapper_deduplication()
        print("\n" + "=" * 60)
        if result:
            print("✅ PASS: Department Mapper Deduplication Test")
        else:
            print("❌ FAIL: Department Mapper Deduplication Test")
        print("=" * 60)
        return result
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
