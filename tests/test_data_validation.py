"""
Test Suite for ChatGPT Data Validation and Handler Tools

Tests the following components:
1. ChatGPTDataValidator - Weekly to monthly validation
2. WeeklyDataHandler - Weekly data analysis
3. MonthlyDataHandler - Monthly data analysis
4. DataReconciliationTool - Consistency checking

Usage:
    python test_data_validation.py
"""

import pandas as pd
import sys
import os
from datetime import datetime

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from chatgpt_data_validator import ChatGPTDataValidator
from data_handlers import WeeklyDataHandler, MonthlyDataHandler, DataReconciliationTool


def test_validator_initialization():
    """Test that validator initializes correctly."""
    print("\n🧪 Testing Validator Initialization...")
    
    try:
        validator = ChatGPTDataValidator(tolerance_percentage=1.0)
        
        assert validator.tolerance_percentage == 1.0, "Tolerance not set correctly"
        assert len(validator.message_categories) == 4, "Wrong number of message categories"
        
        print("✅ Validator initialized correctly")
        return True
    except Exception as e:
        print(f"❌ Validator initialization failed: {e}")
        return False


def test_load_sample_data():
    """Test loading sample CSV files."""
    print("\n🧪 Testing Sample Data Loading...")
    
    try:
        validator = ChatGPTDataValidator()
        
        # Test monthly file
        monthly_df = validator.load_csv_file('sample_monthly_data.csv')
        assert not monthly_df.empty, "Monthly data is empty"
        assert 'messages' in monthly_df.columns, "Missing messages column"
        
        # Test weekly file
        weekly_df = validator.load_csv_file('sample_weekly_data.csv')
        assert not weekly_df.empty, "Weekly data is empty"
        assert 'cadence' in weekly_df.columns, "Missing cadence column"
        
        print(f"✅ Successfully loaded monthly data: {len(monthly_df)} rows")
        print(f"✅ Successfully loaded weekly data: {len(weekly_df)} rows")
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weekly_to_monthly_validation():
    """Test that weekly data sums correctly to monthly totals."""
    print("\n🧪 Testing Weekly to Monthly Validation...")
    
    try:
        validator = ChatGPTDataValidator(tolerance_percentage=1.0)
        
        results = validator.validate_weekly_to_monthly(
            weekly_files=['sample_weekly_data.csv'],
            monthly_file='sample_monthly_data.csv'
        )
        
        # Check overall status
        assert results['overall_status'] == 'PASS', f"Validation failed: {results.get('error', 'Unknown error')}"
        
        # Check each category
        for category in ['messages', 'gpt_messages', 'tool_messages', 'project_messages']:
            cat_result = results['categories'][category]
            assert cat_result['status'] == 'PASS', f"Category {category} failed validation"
            assert cat_result['discrepancy_users'] == 0, f"Found discrepancies in {category}"
        
        print("✅ Weekly data sums correctly to monthly totals")
        print(f"   Categories validated: {len(results['categories'])}")
        print(f"   Total users checked: {results['categories']['messages']['total_users']}")
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_category_breakdown_validation():
    """Test that category breakdowns sum correctly."""
    print("\n🧪 Testing Category Breakdown Validation...")
    
    try:
        validator = ChatGPTDataValidator()
        monthly_df = validator.load_csv_file('sample_monthly_data.csv')
        
        breakdown = validator.validate_category_breakdown(monthly_df)
        
        assert breakdown['valid'] == True, "Category breakdown validation failed"
        assert 'summary' in breakdown, "Missing summary in breakdown"
        assert breakdown['summary']['total_messages'] > 0, "No messages in summary"
        
        print("✅ Category breakdowns validated successfully")
        print(f"   Total Messages: {breakdown['summary']['total_messages']}")
        print(f"   GPT Messages: {breakdown['summary']['gpt_messages']}")
        print(f"   Tool Messages: {breakdown['summary']['tool_messages']}")
        print(f"   Project Messages: {breakdown['summary']['project_messages']}")
        return True
        
    except Exception as e:
        print(f"❌ Category breakdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_generation():
    """Test report generation in both text and JSON formats."""
    print("\n🧪 Testing Report Generation...")
    
    try:
        validator = ChatGPTDataValidator()
        
        results = validator.validate_weekly_to_monthly(
            weekly_files=['sample_weekly_data.csv'],
            monthly_file='sample_monthly_data.csv'
        )
        
        # Test text report
        text_report = validator.generate_report(results, output_format='text')
        assert len(text_report) > 0, "Text report is empty"
        assert 'ChatGPT Data Validation Report' in text_report, "Missing report header"
        
        # Test JSON report
        json_report = validator.generate_report(results, output_format='json')
        assert len(json_report) > 0, "JSON report is empty"
        assert '"overall_status"' in json_report, "Missing status in JSON"
        
        print("✅ Report generation successful")
        print(f"   Text report length: {len(text_report)} chars")
        print(f"   JSON report length: {len(json_report)} chars")
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_weekly_handler():
    """Test WeeklyDataHandler functionality."""
    print("\n🧪 Testing WeeklyDataHandler...")
    
    try:
        handler = WeeklyDataHandler()
        handler.load_data(['sample_weekly_data.csv'])
        
        assert handler.data is not None, "Data not loaded"
        assert len(handler.data) > 0, "No data rows loaded"
        
        # Test trends analysis
        trends = handler.analyze_trends()
        assert 'weekly_statistics' in trends, "Missing weekly statistics"
        assert 'summary' in trends, "Missing summary"
        assert trends['summary']['total_weeks'] > 0, "No weeks found"
        
        # Test peak weeks
        peak_weeks = handler.identify_peak_weeks(top_n=3)
        assert len(peak_weeks) > 0, "No peak weeks identified"
        assert 'total_messages' in peak_weeks[0], "Missing total_messages in peak week"
        
        # Test user engagement
        engagement = handler.analyze_user_engagement()
        assert engagement['total_users'] > 0, "No users found"
        assert 'engagement_distribution' in engagement, "Missing engagement distribution"
        
        print("✅ WeeklyDataHandler working correctly")
        print(f"   Total weeks: {trends['summary']['total_weeks']}")
        print(f"   Total users: {engagement['total_users']}")
        print(f"   Peak week messages: {peak_weeks[0]['total_messages']}")
        return True
        
    except Exception as e:
        print(f"❌ WeeklyDataHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monthly_handler():
    """Test MonthlyDataHandler functionality."""
    print("\n🧪 Testing MonthlyDataHandler...")
    
    try:
        handler = MonthlyDataHandler()
        handler.load_data(['sample_monthly_data.csv'])
        
        assert handler.data is not None, "Data not loaded"
        assert len(handler.data) > 0, "No data rows loaded"
        
        # Test annual projection
        projection = handler.project_annual_usage()
        assert 'months_analyzed' in projection, "Missing months_analyzed"
        assert projection['months_analyzed'] > 0, "No months found"
        assert 'projections' in projection, "Missing projections"
        assert projection['projections']['simple_annual'] > 0, "Invalid annual projection"
        
        print("✅ MonthlyDataHandler working correctly")
        print(f"   Months analyzed: {projection['months_analyzed']}")
        print(f"   Avg monthly messages: {projection['avg_monthly_messages']}")
        print(f"   Annual projection: {projection['projections']['simple_annual']}")
        return True
        
    except Exception as e:
        print(f"❌ MonthlyDataHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reconciliation_tool():
    """Test DataReconciliationTool functionality."""
    print("\n🧪 Testing DataReconciliationTool...")
    
    try:
        weekly_handler = WeeklyDataHandler()
        weekly_handler.load_data(['sample_weekly_data.csv'])
        
        monthly_handler = MonthlyDataHandler()
        monthly_handler.load_data(['sample_monthly_data.csv'])
        
        reconciler = DataReconciliationTool()
        results = reconciler.reconcile(weekly_handler, monthly_handler, tolerance_pct=1.0)
        
        assert 'status' in results, "Missing status in results"
        assert results['status'] == 'PASS', f"Reconciliation failed: {results.get('status')}"
        assert 'comparisons' in results, "Missing comparisons"
        assert len(results['comparisons']) > 0, "No comparisons made"
        
        # Test report generation
        report = reconciler.generate_reconciliation_report(results)
        assert len(report) > 0, "Empty reconciliation report"
        assert 'Data Reconciliation Report' in report, "Missing report header"
        
        print("✅ DataReconciliationTool working correctly")
        print(f"   Status: {results['status']}")
        print(f"   Comparisons made: {len(results['comparisons'])}")
        return True
        
    except Exception as e:
        print(f"❌ DataReconciliationTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_discrepancy_detection():
    """Test that discrepancies are properly detected."""
    print("\n🧪 Testing Discrepancy Detection...")
    
    try:
        # Create test data with intentional discrepancy
        validator = ChatGPTDataValidator(tolerance_percentage=1.0)
        
        # Mock data with mismatches
        weekly_totals = {'user1@test.com': 100, 'user2@test.com': 200}
        monthly_totals = {'user1@test.com': 100, 'user2@test.com': 250}  # 50 message difference
        
        comparison = validator.compare_totals(weekly_totals, monthly_totals)
        
        assert comparison['discrepancy_users'] > 0, "Failed to detect discrepancy"
        assert len(comparison['discrepancies']) > 0, "No discrepancies reported"
        
        # Check that user2 is flagged
        user2_discrepancy = [d for d in comparison['discrepancies'] if d['user'] == 'user2@test.com']
        assert len(user2_discrepancy) > 0, "Specific discrepancy not detected"
        
        print("✅ Discrepancy detection working correctly")
        print(f"   Discrepancies found: {comparison['discrepancy_users']}")
        return True
        
    except Exception as e:
        print(f"❌ Discrepancy detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation and handler tests."""
    print("=" * 80)
    print("🚀 Running Data Validation & Handler Tests")
    print("=" * 80)
    
    tests = [
        ("Validator Initialization", test_validator_initialization),
        ("Sample Data Loading", test_load_sample_data),
        ("Weekly to Monthly Validation", test_weekly_to_monthly_validation),
        ("Category Breakdown Validation", test_category_breakdown_validation),
        ("Report Generation", test_report_generation),
        ("WeeklyDataHandler", test_weekly_handler),
        ("MonthlyDataHandler", test_monthly_handler),
        ("DataReconciliationTool", test_reconciliation_tool),
        ("Discrepancy Detection", test_discrepancy_detection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed successfully!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    print("=" * 80)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
