#!/usr/bin/env python3
"""
Comprehensive Demo of ChatGPT Data Validation System

This script demonstrates all features of the validation system:
1. Weekly to monthly validation
2. Weekly data analysis
3. Monthly data projections
4. Data reconciliation

Usage:
    python demo_validation_system.py
"""

import os
from chatgpt_data_validator import ChatGPTDataValidator
from data_handlers import WeeklyDataHandler, MonthlyDataHandler, DataReconciliationTool


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_validation():
    """Demonstrate data validation functionality."""
    print_section("1. ChatGPT Data Validation")
    
    # Initialize validator with 1% tolerance
    validator = ChatGPTDataValidator(tolerance_percentage=1.0)
    print("✓ Initialized validator with 1% tolerance")
    
    # Validate sample data
    print("✓ Validating sample data...")
    results = validator.validate_weekly_to_monthly(
        weekly_files=['sample_weekly_data.csv'],
        monthly_file='sample_monthly_data.csv'
    )
    
    # Display results
    print(f"\nValidation Status: {results['overall_status']}")
    print(f"Period: {results.get('period_start')} to {results.get('period_end')}")
    print(f"Total Users: {results['categories']['messages']['total_users']}")
    
    # Show category results
    print("\nCategory Validation Results:")
    for category, data in results['categories'].items():
        status_icon = '✅' if data['status'] == 'PASS' else '❌'
        print(f"  {status_icon} {category.upper()}")
        print(f"     Weekly: {data['weekly_sum']:,} | Monthly: {data['monthly_sum']:,}")
    
    # Generate and save reports
    print("\n✓ Generating validation reports...")
    validator.save_report(results, 'demo_validation_report.txt', output_format='text')
    validator.save_report(results, 'demo_validation_report.json', output_format='json')
    print("  - Saved: demo_validation_report.txt")
    print("  - Saved: demo_validation_report.json")


def demo_weekly_analysis():
    """Demonstrate weekly data analysis."""
    print_section("2. Weekly Data Analysis")
    
    # Load weekly data
    handler = WeeklyDataHandler()
    print("✓ Loading weekly data...")
    handler.load_data(['sample_weekly_data.csv'])
    print(f"  - Loaded {len(handler.data)} weekly records")
    
    # Analyze trends
    print("\n✓ Analyzing weekly trends...")
    trends = handler.analyze_trends()
    
    summary = trends['summary']
    print(f"\nWeekly Trend Summary:")
    print(f"  Total Weeks Analyzed: {summary['total_weeks']}")
    print(f"  Average Weekly Messages: {summary['avg_weekly_messages']:,}")
    print(f"  Average Weekly Active Users: {summary['avg_weekly_users']}")
    
    print(f"\n  Peak Week:")
    print(f"    Date: {summary['peak_week']['date']}")
    print(f"    Messages: {summary['peak_week']['messages']:,}")
    print(f"    Users: {summary['peak_week']['users']}")
    
    print(f"\n  Lowest Week:")
    print(f"    Date: {summary['lowest_week']['date']}")
    print(f"    Messages: {summary['lowest_week']['messages']:,}")
    print(f"    Users: {summary['lowest_week']['users']}")
    
    # Identify peak weeks
    print("\n✓ Identifying peak usage weeks...")
    peak_weeks = handler.identify_peak_weeks(top_n=3)
    
    print("\nTop 3 Peak Weeks:")
    for i, week in enumerate(peak_weeks, 1):
        print(f"  {i}. {week['week_start']}")
        print(f"     Messages: {week['total_messages']:,}")
        print(f"     Users: {week['active_users']}")
        print(f"     Avg per User: {week['avg_messages_per_user']:.1f}")
    
    # Analyze user engagement
    print("\n✓ Analyzing user engagement...")
    engagement = handler.analyze_user_engagement()
    
    print(f"\nUser Engagement Metrics:")
    print(f"  Total Users: {engagement['total_users']}")
    print(f"  Average Engagement Rate: {engagement['avg_engagement_rate']}%")
    print(f"  Average Active Weeks per User: {engagement['avg_active_weeks_per_user']:.1f}")
    
    print(f"\n  Engagement Distribution:")
    for category, count in engagement['engagement_distribution'].items():
        print(f"    {category}: {count} users")


def demo_monthly_analysis():
    """Demonstrate monthly data analysis."""
    print_section("3. Monthly Data Analysis")
    
    # Load monthly data
    handler = MonthlyDataHandler()
    print("✓ Loading monthly data...")
    handler.load_data(['sample_monthly_data.csv'])
    print(f"  - Loaded {len(handler.data)} monthly records")
    
    # Project annual usage
    print("\n✓ Projecting annual usage...")
    projection = handler.project_annual_usage()
    
    print(f"\nAnnual Usage Projections:")
    print(f"  Months Analyzed: {projection['months_analyzed']}")
    print(f"  Average Monthly Messages: {projection['avg_monthly_messages']:,}")
    print(f"  Average Monthly Active Users: {projection['avg_monthly_users']}")
    print(f"  Monthly Growth Rate: {projection['monthly_growth_rate']:.2f}%")
    
    print(f"\n  Projected Annual Totals:")
    print(f"    Simple Projection: {projection['projections']['simple_annual']:,} messages")
    print(f"    Growth-Adjusted: {projection['projections']['growth_adjusted_annual']:,} messages")


def demo_reconciliation():
    """Demonstrate data reconciliation."""
    print_section("4. Data Reconciliation")
    
    # Load both weekly and monthly data
    print("✓ Loading weekly and monthly data...")
    weekly_handler = WeeklyDataHandler()
    weekly_handler.load_data(['sample_weekly_data.csv'])
    
    monthly_handler = MonthlyDataHandler()
    monthly_handler.load_data(['sample_monthly_data.csv'])
    
    # Reconcile data
    print("✓ Reconciling weekly and monthly data...")
    reconciler = DataReconciliationTool()
    results = reconciler.reconcile(weekly_handler, monthly_handler, tolerance_pct=1.0)
    
    print(f"\nReconciliation Status: {results['status']}")
    print(f"Tolerance: {results['tolerance_percentage']}%")
    print(f"Comparisons Made: {len(results['comparisons'])}")
    
    # Show comparison details
    for comparison in results['comparisons']:
        print(f"\nMonth: {comparison['month']}")
        print(f"Weeks Included: {comparison['weeks_included']}")
        
        for category, data in comparison['categories'].items():
            status_icon = '✅' if data['status'] == 'MATCH' else '❌'
            print(f"  {status_icon} {category.upper()}")
            print(f"     Weekly: {data['weekly_total']:,} | Monthly: {data['monthly_total']:,}")
            if data['difference'] != 0:
                print(f"     Difference: {data['difference']:+,} ({data['difference_pct']:+.2f}%)")


def demo_full_workflow():
    """Demonstrate complete validation workflow."""
    print_section("Complete Workflow Demo")
    
    print("This demo shows the full workflow for validating ChatGPT data:")
    print("  1. Validate weekly data against monthly totals")
    print("  2. Analyze weekly usage patterns and trends")
    print("  3. Project annual usage from monthly data")
    print("  4. Reconcile weekly and monthly datasets")
    print("")
    
    try:
        demo_validation()
        demo_weekly_analysis()
        demo_monthly_analysis()
        demo_reconciliation()
        
        print_section("Demo Complete")
        print("✅ All validation and analysis tasks completed successfully!")
        print("\nGenerated Files:")
        print("  - demo_validation_report.txt")
        print("  - demo_validation_report.json")
        print("\nNext Steps:")
        print("  1. Review the validation reports")
        print("  2. Run with your own data files")
        print("  3. Integrate into your Streamlit dashboard")
        print("  4. See DATA_VALIDATION_GUIDE.md for more details")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    import sys
    
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "ChatGPT Data Validation System Demo" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    
    success = demo_full_workflow()
    sys.exit(0 if success else 1)
