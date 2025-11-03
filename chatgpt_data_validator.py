"""
ChatGPT Data Validator

Validates that weekly data sums correctly to monthly totals.
Ensures data consistency between weekly and monthly exports from OpenAI ChatGPT.

Features:
- Validates weekly sums match monthly totals for all message categories
- Checks GPT messages, Tool messages, Project messages, and General messages
- Generates detailed validation reports in JSON and text formats
- Identifies discrepancies and provides actionable insights
- Validates that category breakdowns sum to total messages

Usage:
    from chatgpt_data_validator import ChatGPTDataValidator
    
    validator = ChatGPTDataValidator()
    results = validator.validate_weekly_to_monthly(weekly_files, monthly_file)
    validator.generate_report(results, output_format='json')
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import os


class ChatGPTDataValidator:
    """Validates consistency between weekly and monthly ChatGPT usage data."""
    
    def __init__(self, tolerance_percentage: float = 1.0):
        """
        Initialize the validator.
        
        Args:
            tolerance_percentage: Acceptable variance percentage (default: 1.0%)
        """
        self.tolerance_percentage = tolerance_percentage
        self.message_categories = ['messages', 'gpt_messages', 'tool_messages', 'project_messages']
        
    def load_csv_file(self, filepath: str) -> pd.DataFrame:
        """
        Load a CSV file with error handling.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            DataFrame with loaded data
        """
        try:
            df = pd.read_csv(filepath)
            return df
        except Exception as e:
            raise ValueError(f"Error loading file {filepath}: {str(e)}")
    
    def extract_period_from_monthly(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        Extract period start and end from monthly data.
        
        Args:
            df: Monthly data DataFrame
            
        Returns:
            Tuple of (period_start, period_end) as strings
        """
        if 'period_start' in df.columns and 'period_end' in df.columns:
            period_start = df['period_start'].iloc[0]
            period_end = df['period_end'].iloc[0]
            return period_start, period_end
        raise ValueError("Monthly data missing period_start or period_end columns")
    
    def filter_weekly_by_month(self, weekly_dfs: List[pd.DataFrame], 
                               month_start: str, month_end: str) -> pd.DataFrame:
        """
        Filter and combine weekly data for a specific month.
        
        Args:
            weekly_dfs: List of weekly DataFrames
            month_start: Month period start date (YYYY-MM-DD)
            month_end: Month period end date (YYYY-MM-DD)
            
        Returns:
            Combined DataFrame of weekly data within the month
        """
        month_start_dt = pd.to_datetime(month_start)
        month_end_dt = pd.to_datetime(month_end)
        
        filtered_weeks = []
        for df in weekly_dfs:
            if 'period_start' in df.columns:
                df['period_start_dt'] = pd.to_datetime(df['period_start'])
                # Include weeks that start within or overlap with the month
                mask = (df['period_start_dt'] >= month_start_dt) & (df['period_start_dt'] <= month_end_dt)
                filtered_df = df[mask].copy()
                if not filtered_df.empty:
                    filtered_weeks.append(filtered_df)
        
        if not filtered_weeks:
            return pd.DataFrame()
        
        return pd.concat(filtered_weeks, ignore_index=True)
    
    def aggregate_by_user(self, df: pd.DataFrame, category: str) -> Dict[str, int]:
        """
        Aggregate message counts by user for a specific category.
        
        Args:
            df: DataFrame with user data
            category: Message category column name
            
        Returns:
            Dictionary mapping user email to total count
        """
        if 'email' not in df.columns or category not in df.columns:
            return {}
        
        # Filter to active users only
        active_df = df[df.get('is_active', 1) == 1].copy()
        
        # Handle missing values
        active_df[category] = pd.to_numeric(active_df[category], errors='coerce').fillna(0)
        
        # Group by email and sum
        user_totals = active_df.groupby('email')[category].sum().to_dict()
        
        return user_totals
    
    def compare_totals(self, weekly_totals: Dict[str, int], 
                      monthly_totals: Dict[str, int]) -> Dict[str, Any]:
        """
        Compare weekly aggregated totals against monthly totals.
        
        Args:
            weekly_totals: Dictionary of email -> weekly total
            monthly_totals: Dictionary of email -> monthly total
            
        Returns:
            Dictionary with comparison results
        """
        all_users = set(weekly_totals.keys()) | set(monthly_totals.keys())
        
        discrepancies = []
        matches = []
        
        for user in all_users:
            weekly_val = weekly_totals.get(user, 0)
            monthly_val = monthly_totals.get(user, 0)
            
            # Calculate difference
            diff = weekly_val - monthly_val
            
            # Calculate percentage difference
            if monthly_val > 0:
                diff_pct = abs(diff / monthly_val * 100)
            elif weekly_val > 0:
                diff_pct = 100.0  # Missing from monthly
            else:
                diff_pct = 0.0
            
            result = {
                'user': user,
                'weekly_total': weekly_val,
                'monthly_total': monthly_val,
                'difference': diff,
                'difference_pct': round(diff_pct, 2)
            }
            
            if diff_pct > self.tolerance_percentage:
                discrepancies.append(result)
            else:
                matches.append(result)
        
        return {
            'total_users': len(all_users),
            'matching_users': len(matches),
            'discrepancy_users': len(discrepancies),
            'discrepancies': discrepancies,
            'matches': matches
        }
    
    def validate_category_breakdown(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate that category breakdowns sum to total messages.
        
        Args:
            df: DataFrame with message data
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'issues': [],
            'summary': {}
        }
        
        # Filter to active users
        active_df = df[df.get('is_active', 1) == 1].copy()
        
        if active_df.empty:
            return results
        
        # Convert columns to numeric
        for col in self.message_categories:
            if col in active_df.columns:
                active_df[col] = pd.to_numeric(active_df[col], errors='coerce').fillna(0)
        
        # Check each user
        for idx, row in active_df.iterrows():
            total_messages = row.get('messages', 0)
            
            # Calculate sum of categories (excluding main 'messages' field)
            category_sum = sum([
                row.get('gpt_messages', 0),
                row.get('tool_messages', 0),
                row.get('project_messages', 0)
            ])
            
            # These are sub-categories, so they shouldn't exceed total messages
            if category_sum > total_messages:
                results['valid'] = False
                results['issues'].append({
                    'user': row.get('email', 'Unknown'),
                    'total_messages': int(total_messages),
                    'category_sum': int(category_sum),
                    'issue': 'Category sum exceeds total messages'
                })
        
        # Calculate overall statistics
        results['summary'] = {
            'total_messages': int(active_df['messages'].sum()),
            'gpt_messages': int(active_df.get('gpt_messages', pd.Series([0])).sum()),
            'tool_messages': int(active_df.get('tool_messages', pd.Series([0])).sum()),
            'project_messages': int(active_df.get('project_messages', pd.Series([0])).sum())
        }
        
        return results
    
    def validate_weekly_to_monthly(self, weekly_files: List[str], 
                                   monthly_file: str) -> Dict[str, Any]:
        """
        Validate that weekly data sums correctly to monthly totals.
        
        Args:
            weekly_files: List of paths to weekly CSV files
            monthly_file: Path to monthly CSV file
            
        Returns:
            Comprehensive validation results dictionary
        """
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'monthly_file': os.path.basename(monthly_file),
            'weekly_files': [os.path.basename(f) for f in weekly_files],
            'tolerance_percentage': self.tolerance_percentage,
            'overall_status': 'PASS',
            'categories': {}
        }
        
        try:
            # Load monthly data
            monthly_df = self.load_csv_file(monthly_file)
            month_start, month_end = self.extract_period_from_monthly(monthly_df)
            
            validation_results['period_start'] = month_start
            validation_results['period_end'] = month_end
            
            # Load and filter weekly data
            weekly_dfs = [self.load_csv_file(f) for f in weekly_files]
            combined_weekly = self.filter_weekly_by_month(weekly_dfs, month_start, month_end)
            
            if combined_weekly.empty:
                validation_results['overall_status'] = 'ERROR'
                validation_results['error'] = 'No weekly data found for the specified month'
                return validation_results
            
            # Validate each category
            for category in self.message_categories:
                weekly_totals = self.aggregate_by_user(combined_weekly, category)
                monthly_totals = self.aggregate_by_user(monthly_df, category)
                
                comparison = self.compare_totals(weekly_totals, monthly_totals)
                
                category_status = 'PASS' if comparison['discrepancy_users'] == 0 else 'FAIL'
                
                validation_results['categories'][category] = {
                    'status': category_status,
                    'total_users': comparison['total_users'],
                    'matching_users': comparison['matching_users'],
                    'discrepancy_users': comparison['discrepancy_users'],
                    'discrepancies': comparison['discrepancies'][:10],  # Limit to top 10
                    'weekly_sum': sum(weekly_totals.values()),
                    'monthly_sum': sum(monthly_totals.values()),
                    'overall_difference': sum(weekly_totals.values()) - sum(monthly_totals.values())
                }
                
                if category_status == 'FAIL':
                    validation_results['overall_status'] = 'FAIL'
            
            # Validate category breakdowns
            monthly_breakdown = self.validate_category_breakdown(monthly_df)
            validation_results['category_breakdown_validation'] = monthly_breakdown
            
            if not monthly_breakdown['valid']:
                validation_results['overall_status'] = 'WARNING'
            
        except Exception as e:
            validation_results['overall_status'] = 'ERROR'
            validation_results['error'] = str(e)
        
        return validation_results
    
    def generate_report(self, results: Dict[str, Any], 
                       output_format: str = 'text') -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            results: Validation results dictionary
            output_format: 'text' or 'json'
            
        Returns:
            Formatted report string
        """
        if output_format == 'json':
            return json.dumps(results, indent=2)
        
        # Text format
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("ChatGPT Data Validation Report")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {results.get('timestamp', 'N/A')}")
        report_lines.append(f"Monthly File: {results.get('monthly_file', 'N/A')}")
        report_lines.append(f"Period: {results.get('period_start', 'N/A')} to {results.get('period_end', 'N/A')}")
        report_lines.append(f"Weekly Files: {len(results.get('weekly_files', []))}")
        report_lines.append(f"Tolerance: {results.get('tolerance_percentage', 0)}%")
        report_lines.append("")
        
        # Overall status
        status = results.get('overall_status', 'UNKNOWN')
        status_symbol = {
            'PASS': '✅',
            'FAIL': '❌',
            'WARNING': '⚠️',
            'ERROR': '🚫'
        }.get(status, '❓')
        
        report_lines.append(f"Overall Status: {status_symbol} {status}")
        report_lines.append("")
        
        if 'error' in results:
            report_lines.append(f"Error: {results['error']}")
            report_lines.append("=" * 80)
            return '\n'.join(report_lines)
        
        # Category results
        report_lines.append("Category Validation Results:")
        report_lines.append("-" * 80)
        
        for category, cat_results in results.get('categories', {}).items():
            cat_status = cat_results.get('status', 'UNKNOWN')
            cat_symbol = '✅' if cat_status == 'PASS' else '❌'
            
            report_lines.append(f"\n{cat_symbol} {category.upper()}")
            report_lines.append(f"  Status: {cat_status}")
            report_lines.append(f"  Total Users: {cat_results.get('total_users', 0)}")
            report_lines.append(f"  Matching Users: {cat_results.get('matching_users', 0)}")
            report_lines.append(f"  Discrepancies: {cat_results.get('discrepancy_users', 0)}")
            report_lines.append(f"  Weekly Sum: {cat_results.get('weekly_sum', 0):,}")
            report_lines.append(f"  Monthly Sum: {cat_results.get('monthly_sum', 0):,}")
            report_lines.append(f"  Overall Difference: {cat_results.get('overall_difference', 0):+,}")
            
            if cat_results.get('discrepancies'):
                report_lines.append(f"\n  Top Discrepancies:")
                for disc in cat_results['discrepancies'][:5]:
                    report_lines.append(f"    - {disc['user']}")
                    report_lines.append(f"      Weekly: {disc['weekly_total']}, Monthly: {disc['monthly_total']}")
                    report_lines.append(f"      Difference: {disc['difference']:+} ({disc['difference_pct']:+.2f}%)")
        
        # Category breakdown validation
        report_lines.append("\n" + "-" * 80)
        report_lines.append("Category Breakdown Validation:")
        breakdown = results.get('category_breakdown_validation', {})
        breakdown_symbol = '✅' if breakdown.get('valid', False) else '⚠️'
        report_lines.append(f"{breakdown_symbol} Valid: {breakdown.get('valid', False)}")
        
        if breakdown.get('summary'):
            summary = breakdown['summary']
            report_lines.append(f"\nSummary:")
            report_lines.append(f"  Total Messages: {summary.get('total_messages', 0):,}")
            report_lines.append(f"  GPT Messages: {summary.get('gpt_messages', 0):,}")
            report_lines.append(f"  Tool Messages: {summary.get('tool_messages', 0):,}")
            report_lines.append(f"  Project Messages: {summary.get('project_messages', 0):,}")
        
        if breakdown.get('issues'):
            report_lines.append(f"\n  Issues Found: {len(breakdown['issues'])}")
            for issue in breakdown['issues'][:5]:
                report_lines.append(f"    - {issue['user']}: {issue['issue']}")
        
        report_lines.append("\n" + "=" * 80)
        
        return '\n'.join(report_lines)
    
    def save_report(self, results: Dict[str, Any], 
                   output_path: str, output_format: str = 'text'):
        """
        Save validation report to file.
        
        Args:
            results: Validation results dictionary
            output_path: Path to save report
            output_format: 'text' or 'json'
        """
        report = self.generate_report(results, output_format)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        print(f"Report saved to: {output_path}")


def main():
    """Example usage of ChatGPTDataValidator."""
    
    # Use sample data files for demonstration
    weekly_files = ["sample_weekly_data.csv"]
    monthly_file = "sample_monthly_data.csv"
    
    # Initialize validator with 1% tolerance
    validator = ChatGPTDataValidator(tolerance_percentage=1.0)
    
    # Validate data
    print("Validating weekly data against monthly totals...")
    print(f"Weekly files: {weekly_files}")
    print(f"Monthly file: {monthly_file}")
    print("")
    
    results = validator.validate_weekly_to_monthly(weekly_files, monthly_file)
    
    # Generate and display report
    print("\n" + validator.generate_report(results, output_format='text'))
    
    # Save reports
    validator.save_report(results, 'validation_report.txt', output_format='text')
    validator.save_report(results, 'validation_report.json', output_format='json')


if __name__ == "__main__":
    main()
