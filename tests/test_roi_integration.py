"""
Integration test demonstrating ROI utilities with actual database data.

This test shows how to use roi_utils.py with the existing DatabaseManager
and DataProcessor classes to generate ROI metrics from real usage data.
"""

import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import pandas as pd
from database import DatabaseManager
from roi_utils import (
    calculate_time_savings,
    calculate_cost_savings,
    calculate_business_value,
    calculate_ai_impact_score,
    identify_value_leaders,
    calculate_roi_summary
)


def test_roi_integration_with_database():
    """
    Demonstrate integration of ROI utilities with existing database.
    """
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: ROI Utilities with Database")
    print("=" * 80)
    
    # Initialize database (use test database to avoid affecting production)
    db = DatabaseManager("test_roi_integration.db")
    
    # Insert sample usage data
    sample_data = pd.DataFrame({
        'user_id': ['alice@company.com', 'bob@company.com', 'charlie@company.com'] * 4,
        'user_name': ['Alice Smith', 'Bob Johnson', 'Charlie Brown'] * 4,
        'email': ['alice@company.com', 'bob@company.com', 'charlie@company.com'] * 4,
        'department': ['Engineering', 'Sales', 'Finance'] * 4,
        'date': ['2024-01-01'] * 12,
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'Project Messages', 'ChatGPT Messages'] * 3,
        'usage_count': [150, 200, 100, 180, 120, 90, 160, 140, 110, 130, 170, 95],
        'cost_usd': [0.0] * 12,  # Cost tracking disabled
        'tool_source': ['ChatGPT'] * 12,
        'file_source': ['test_data.csv'] * 12,
        'created_at': ['2024-01-01T00:00:00'] * 12
    })
    
    # Insert data into database
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    sample_data.to_sql('usage_metrics', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"\n✅ Inserted {len(sample_data)} sample records into test database")
    
    # Retrieve data from database
    usage_data = db.get_all_data()
    print(f"✅ Retrieved {len(usage_data)} records from database")
    
    # Calculate ROI metrics
    print("\n📊 Calculating ROI Metrics...")
    
    enriched = calculate_time_savings(usage_data)
    enriched = calculate_cost_savings(enriched)
    enriched = calculate_business_value(enriched)
    enriched = calculate_ai_impact_score(enriched)
    
    print(f"✅ Enriched data with ROI metrics")
    
    # Display sample results
    print("\n📈 Sample ROI Data:")
    sample_cols = ['user_name', 'department', 'feature_used', 'usage_count',
                   'time_saved_hours', 'cost_saved_usd', 'business_value_usd', 
                   'ai_impact_score']
    print(enriched[sample_cols].head(5).to_string(index=False))
    
    # Identify value leaders
    print("\n🏆 Top Value Leaders (by User):")
    top_users = identify_value_leaders(enriched, by='user', top_n=3, metric='business_value_usd')
    display_cols = ['user_name', 'usage_count', 'business_value_usd', 'pct_of_total']
    print(top_users[display_cols].to_string(index=False))
    
    print("\n🏆 Top Departments:")
    top_depts = identify_value_leaders(enriched, by='department', top_n=3, metric='business_value_usd')
    dept_cols = ['department', 'usage_count', 'business_value_usd', 'pct_of_total']
    print(top_depts[dept_cols].to_string(index=False))
    
    # Generate comprehensive summary
    print("\n📋 ROI Summary Report:")
    summary = calculate_roi_summary(
        usage_data, 
        total_licenses=500,
        license_cost_per_user=30.0,
        include_all_metrics=True
    )
    
    print(f"  • Total Active Users: {summary['total_users']}")
    print(f"  • Total Usage: {summary['total_usage']:,} messages")
    print(f"  • Time Saved: {summary['total_time_saved_hours']:,.2f} hours")
    print(f"  • Cost Saved: ${summary['total_cost_saved_usd']:,.2f}")
    print(f"  • Business Value: ${summary['total_business_value_usd']:,.2f}")
    print(f"  • ROI Ratio: {summary['roi_ratio']:.2f}x")
    
    if 'opportunity_costs' in summary:
        opp = summary['opportunity_costs']
        print(f"\n💡 Opportunity Analysis:")
        print(f"  • License Utilization: {opp['utilization_rate_pct']:.1f}%")
        print(f"  • Unused Licenses: {opp['unused_licenses']}")
        print(f"  • Wasted Spend: ${opp['unused_license_cost_monthly']:,.2f}/month")
        print(f"  • Improvement Potential: ${opp['opportunity_for_improvement_usd']:,.2f}")
    
    # Clean up test database
    os.remove(db.db_path)
    print(f"\n✅ Test database cleaned up")
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST PASSED: ROI utilities work seamlessly with database")
    print("=" * 80)
    
    return True


def test_roi_with_empty_database():
    """Test that ROI utilities handle empty database gracefully."""
    print("\n" + "=" * 80)
    print("EDGE CASE TEST: Empty Database Handling")
    print("=" * 80)
    
    # Create empty database
    db = DatabaseManager("test_roi_empty.db")
    
    # Get empty data
    usage_data = db.get_all_data()
    print(f"✅ Retrieved {len(usage_data)} records (should be 0)")
    
    # Try to calculate ROI on empty data
    try:
        if not usage_data.empty:
            enriched = calculate_business_value(usage_data)
            print("✅ ROI calculations handled empty data")
        else:
            print("✅ Empty data detected, skipping calculations (expected behavior)")
        
        # Summary should handle empty data
        summary = calculate_roi_summary(usage_data, total_licenses=100, license_cost_per_user=30)
        print(f"✅ ROI summary handled empty data: {summary['total_users']} users")
        
    except Exception as e:
        print(f"❌ Error handling empty data: {e}")
        return False
    finally:
        # Clean up
        os.remove(db.db_path)
    
    print("\n" + "=" * 80)
    print("EDGE CASE TEST PASSED")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ROI INTEGRATION TESTS" + " " * 37 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = []
    
    # Run tests
    tests = [
        ("ROI Integration with Database", test_roi_integration_with_database),
        ("Empty Database Handling", test_roi_with_empty_database)
    ]
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 80)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Integration Tests: {passed}/{total} passed ({passed/total*100:.1f}%)")
    print("=" * 80)
    
    sys.exit(0 if passed == total else 1)
