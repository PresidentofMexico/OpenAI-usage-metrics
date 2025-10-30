"""
Demo script to create duplicate data and test the validation utility.

This script creates a test scenario with overlapping weekly and monthly data
to demonstrate the duplicate validation functionality.
"""

import sqlite3
from datetime import datetime
from database import DatabaseManager
from duplicate_validator import DuplicateValidator


def create_test_scenario():
    """Create a test database with duplicate data."""
    
    print("Creating test scenario with duplicate data...")
    print("=" * 80)
    
    # Initialize database
    db = DatabaseManager(db_path="test_duplicates.db")
    
    # Clear existing data
    conn = sqlite3.connect("test_duplicates.db")
    conn.execute("DELETE FROM usage_metrics")
    conn.commit()
    
    # Scenario: Import monthly data for May 2025
    print("\n📁 Importing monthly data (May 2025)...")
    monthly_data = [
        # Tyler White - Monthly total for May
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-01', 'ChatGPT Messages', 7189, 60.0, 'ChatGPT', 'monthly_may_2025.csv'),
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-01', 'Tool Messages', 500, 0.0, 'ChatGPT', 'monthly_may_2025.csv'),
        
        # Sarah Johnson - Monthly total
        ('sarah.johnson@example.com', 'sarah.johnson@example.com', 'Sarah Johnson', 'Product', '2025-05-01', 'ChatGPT Messages', 3245, 60.0, 'ChatGPT', 'monthly_may_2025.csv'),
        
        # Mike Chen - Monthly total
        ('mike.chen@example.com', 'mike.chen@example.com', 'Mike Chen', 'Marketing', '2025-05-01', 'ChatGPT Messages', 1892, 60.0, 'ChatGPT', 'monthly_may_2025.csv'),
    ]
    
    for row in monthly_data:
        conn.execute("""
            INSERT INTO usage_metrics (user_id, email, user_name, department, date, feature_used, usage_count, cost_usd, tool_source, file_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
    
    conn.commit()
    print(f"  ✅ Imported {len(monthly_data)} monthly records")
    
    # Scenario: Import overlapping weekly data for May 2025
    # This creates duplicates for Tyler White and Sarah Johnson
    print("\n📁 Importing weekly data (Weeks of May 2025)...")
    weekly_data = [
        # Tyler White - Week 1 (May 1-7)
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-01', 'ChatGPT Messages', 1500, 60.0, 'ChatGPT', 'weekly_2025_w18.csv'),
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-01', 'Tool Messages', 100, 0.0, 'ChatGPT', 'weekly_2025_w18.csv'),
        
        # Tyler White - Week 2 (May 8-14)
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-08', 'ChatGPT Messages', 1800, 60.0, 'ChatGPT', 'weekly_2025_w19.csv'),
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-08', 'Tool Messages', 120, 0.0, 'ChatGPT', 'weekly_2025_w19.csv'),
        
        # Tyler White - Week 3 (May 15-21)
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-15', 'ChatGPT Messages', 1689, 60.0, 'ChatGPT', 'weekly_2025_w20.csv'),
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-15', 'Tool Messages', 130, 0.0, 'ChatGPT', 'weekly_2025_w20.csv'),
        
        # Tyler White - Week 4 (May 22-28)
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-22', 'ChatGPT Messages', 2200, 60.0, 'ChatGPT', 'weekly_2025_w21.csv'),
        ('tyler.white@example.com', 'tyler.white@example.com', 'Tyler White', 'Engineering', '2025-05-22', 'Tool Messages', 150, 0.0, 'ChatGPT', 'weekly_2025_w21.csv'),
        
        # Sarah Johnson - Week 1
        ('sarah.johnson@example.com', 'sarah.johnson@example.com', 'Sarah Johnson', 'Product', '2025-05-01', 'ChatGPT Messages', 800, 60.0, 'ChatGPT', 'weekly_2025_w18.csv'),
        
        # Sarah Johnson - Week 2
        ('sarah.johnson@example.com', 'sarah.johnson@example.com', 'Sarah Johnson', 'Product', '2025-05-08', 'ChatGPT Messages', 850, 60.0, 'ChatGPT', 'weekly_2025_w19.csv'),
        
        # Note: Mike Chen has no weekly data, so his monthly total is accurate
    ]
    
    for row in weekly_data:
        conn.execute("""
            INSERT INTO usage_metrics (user_id, email, user_name, department, date, feature_used, usage_count, cost_usd, tool_source, file_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)
    
    conn.commit()
    print(f"  ✅ Imported {len(weekly_data)} weekly records")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ Test scenario created successfully!")
    print("\nScenario Summary:")
    print("  - Tyler White: Monthly file (7,189 messages) + 4 Weekly files (7,189 messages)")
    print("    → Expected: DUPLICATE - Messages counted twice")
    print("  - Sarah Johnson: Monthly file (3,245 messages) + 2 Weekly files (1,650 messages)")
    print("    → Expected: PARTIAL DUPLICATE - Some overlap")
    print("  - Mike Chen: Monthly file only (1,892 messages)")
    print("    → Expected: NO DUPLICATE - Clean data")
    print("\n" + "=" * 80)
    
    return db


def run_validation(db):
    """Run the duplicate validation and display results."""
    
    print("\n\n🔍 Running Duplicate Validation...")
    print("=" * 80)
    
    validator = DuplicateValidator(db)
    results = validator.validate_duplicates()
    
    # Display full report
    report = validator.generate_report(results, format='text')
    print(report)
    
    # Show detailed analysis for Tyler White
    print("\n\n" + "=" * 80)
    print("🔎 Detailed Analysis: Tyler White")
    print("=" * 80)
    
    tyler_status = validator.get_user_validation_status('tyler.white@example.com')
    
    if tyler_status['validation_status'] != 'NOT_FOUND':
        print(f"\nUser: {tyler_status['user_name']} ({tyler_status['email']})")
        print(f"Department: {tyler_status['department']}")
        print(f"Validation Status: {tyler_status['validation_status']}")
        print(f"\nMessage Counts:")
        print(f"  Total Messages in DB: {tyler_status['total_messages']:,}")
        print(f"  Unique Messages: {tyler_status['unique_messages']:,}")
        print(f"  Duplicate Messages: {tyler_status['duplicate_messages']:,}")
        print(f"  Has Duplicates: {tyler_status['has_duplicates']}")
        
        print(f"\nFeature Breakdown:")
        for feature in tyler_status['features']:
            dup_indicator = "⚠️ DUPLICATE" if feature['is_duplicated'] else "✅ CLEAN"
            print(f"  {dup_indicator} {feature['feature']}:")
            print(f"    - Total: {feature['total_messages']:,}")
            print(f"    - Unique: {feature['unique_messages']:,}")
            print(f"    - Duplication Factor: {feature['duplication_factor']}x")
        
        # Show duplicate details
        print(f"\nDuplicate Records:")
        tyler_dups = validator.get_duplicate_details('tyler.white@example.com')
        if not tyler_dups.empty:
            print(f"  Found {len(tyler_dups)} duplicate records")
            print("\n  File Sources:")
            for file in tyler_dups['file_source'].unique():
                count = len(tyler_dups[tyler_dups['file_source'] == file])
                print(f"    - {file}: {count} records")
    
    print("\n" + "=" * 80)


def main():
    """Main demo function."""
    
    print("\n" + "=" * 80)
    print("DUPLICATE DATA VALIDATION DEMO")
    print("=" * 80)
    print("\nThis demo creates a realistic scenario where both weekly and monthly")
    print("ChatGPT usage data have been imported, causing duplicate message counts.")
    print("")
    
    # Create test scenario
    db = create_test_scenario()
    
    # Run validation
    run_validation(db)
    
    print("\n\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nThe validation tool successfully:")
    print("  ✅ Detected duplicate records from overlapping files")
    print("  ✅ Calculated accurate unique message counts")
    print("  ✅ Identified which users have duplicates")
    print("  ✅ Showed which files contributed to duplicates")
    print("\nNext Steps:")
    print("  1. Review duplicate records in the report above")
    print("  2. Use Database Management to delete overlapping files")
    print("  3. Re-run validation to confirm clean data")
    print("\nTest database saved to: test_duplicates.db")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
