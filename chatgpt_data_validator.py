"""
ChatGPT Data Validation Tool
Ensures weekly data aggregates correctly to monthly totals across different categories
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path

class ChatGPTDataValidator:
    """
    Validates that weekly ChatGPT message data sums up correctly to monthly totals
    across different categories (GPT, Project, Tool, General)
    """
    
    def __init__(self):
        self.categories = ['GPT', 'Project', 'Tool', 'General']
        self.validation_results = []
        
    def load_weekly_data(self, file_path: str) -> pd.DataFrame:
        """Load weekly data from CSV or Excel file"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel.")
            
            # Ensure date column is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'week_start' in df.columns:
                df['date'] = pd.to_datetime(df['week_start'])
                
            return df
        except Exception as e:
            print(f"Error loading weekly data: {e}")
            return pd.DataFrame()
    
    def load_monthly_data(self, file_path: str) -> pd.DataFrame:
        """Load monthly data from CSV or Excel file"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Use CSV or Excel.")
            
            # Ensure date column is datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'month' in df.columns:
                df['date'] = pd.to_datetime(df['month'])
                
            return df
        except Exception as e:
            print(f"Error loading monthly data: {e}")
            return pd.DataFrame()
    
    def aggregate_weekly_to_monthly(self, weekly_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate weekly data to monthly level for comparison
        """
        if weekly_df.empty:
            return pd.DataFrame()
        
        # Extract month and year from date
        weekly_df['year_month'] = weekly_df['date'].dt.to_period('M')
        
        # Group by month and category, summing messages
        aggregation_dict = {}
        for category in self.categories:
            if category in weekly_df.columns:
                aggregation_dict[category] = 'sum'
        
        # Add total messages if it exists
        if 'total_messages' in weekly_df.columns:
            aggregation_dict['total_messages'] = 'sum'
        
        monthly_agg = weekly_df.groupby('year_month').agg(aggregation_dict).reset_index()
        
        return monthly_agg
    
    def validate_totals(self, weekly_df: pd.DataFrame, monthly_df: pd.DataFrame) -> Dict:
        """
        Validate that weekly totals match monthly totals for each category
        """
        validation_report = {
            'status': 'PASS',
            'discrepancies': [],
            'summary': {},
            'details': []
        }
        
        # Aggregate weekly data to monthly
        weekly_monthly = self.aggregate_weekly_to_monthly(weekly_df)
        
        if weekly_monthly.empty or monthly_df.empty:
            validation_report['status'] = 'ERROR'
            validation_report['summary']['error'] = 'Empty dataframe(s) provided'
            return validation_report
        
        # Ensure monthly data has year_month column
        if 'year_month' not in monthly_df.columns:
            monthly_df['year_month'] = monthly_df['date'].dt.to_period('M')
        
        # Merge the dataframes for comparison
        comparison = pd.merge(
            weekly_monthly,
            monthly_df,
            on='year_month',
            suffixes=('_weekly_sum', '_monthly'),
            how='outer'
        )
        
        # Validate each category
        for category in self.categories:
            weekly_col = f"{category}_weekly_sum"
            monthly_col = f"{category}_monthly"
            
            if weekly_col in comparison.columns and monthly_col in comparison.columns:
                # Calculate differences
                comparison[f'{category}_diff'] = comparison[monthly_col] - comparison[weekly_col]
                
                # Check for discrepancies
                discrepancies = comparison[comparison[f'{category}_diff'] != 0]
                
                if not discrepancies.empty:
                    validation_report['status'] = 'FAIL'
                    for idx, row in discrepancies.iterrows():
                        validation_report['discrepancies'].append({
                            'month': str(row['year_month']),
                            'category': category,
                            'weekly_sum': row[weekly_col],
                            'monthly_value': row[monthly_col],
                            'difference': row[f'{category}_diff']
                        })
                
                # Add to summary
                validation_report['summary'][category] = {
                    'total_weekly': comparison[weekly_col].sum(),
                    'total_monthly': comparison[monthly_col].sum(),
                    'matches': len(comparison[comparison[f'{category}_diff'] == 0]),
                    'mismatches': len(discrepancies)
                }
        
        # Validate total messages if present
        if 'total_messages_weekly_sum' in comparison.columns and 'total_messages_monthly' in comparison.columns:
            comparison['total_diff'] = comparison['total_messages_monthly'] - comparison['total_messages_weekly_sum']
            total_discrepancies = comparison[comparison['total_diff'] != 0]
            
            if not total_discrepancies.empty:
                validation_report['status'] = 'FAIL'
                for idx, row in total_discrepancies.iterrows():
                    validation_report['discrepancies'].append({
                        'month': str(row['year_month']),
                        'category': 'TOTAL',
                        'weekly_sum': row['total_messages_weekly_sum'],
                        'monthly_value': row['total_messages_monthly'],
                        'difference': row['total_diff']
                    })
        
        validation_report['details'] = comparison.to_dict('records')
        
        return validation_report
    
    def validate_category_breakdown(self, df: pd.DataFrame) -> Dict:
        """
        Validate that category breakdowns sum to total messages
        """
        validation = {
            'status': 'PASS',
            'issues': []
        }
        
        if 'total_messages' not in df.columns:
            return validation
        
        # Calculate sum of categories
        category_sum = df[self.categories].sum(axis=1)
        
        # Check if sums match totals
        df['calculated_total'] = category_sum
        df['total_diff'] = df['total_messages'] - df['calculated_total']
        
        mismatches = df[df['total_diff'] != 0]
        
        if not mismatches.empty:
            validation['status'] = 'FAIL'
            for idx, row in mismatches.iterrows():
                validation['issues'].append({
                    'row_index': idx,
                    'date': str(row.get('date', 'N/A')),
                    'reported_total': row['total_messages'],
                    'calculated_total': row['calculated_total'],
                    'difference': row['total_diff']
                })
        
        return validation
    
    def generate_validation_report(self, 
                                  weekly_file: str, 
                                  monthly_file: str,
                                  output_file: Optional[str] = None) -> Dict:
        """
        Generate comprehensive validation report
        """
        print("Loading data files...")
        weekly_df = self.load_weekly_data(weekly_file)
        monthly_df = self.load_monthly_data(monthly_file)
        
        print("Validating data consistency...")
        report = {
            'timestamp': datetime.now().isoformat(),
            'weekly_file': weekly_file,
            'monthly_file': monthly_file,
            'validations': {}
        }
        
        # Validate weekly vs monthly totals
        print("Validating weekly vs monthly totals...")
        report['validations']['weekly_monthly_reconciliation'] = self.validate_totals(
            weekly_df, monthly_df
        )
        
        # Validate category breakdowns in weekly data
        print("Validating weekly category breakdowns...")
        report['validations']['weekly_category_breakdown'] = self.validate_category_breakdown(
            weekly_df
        )
        
        # Validate category breakdowns in monthly data
        print("Validating monthly category breakdowns...")
        report['validations']['monthly_category_breakdown'] = self.validate_category_breakdown(
            monthly_df
        )
        
        # Overall status
        report['overall_status'] = 'PASS'
        for validation_name, validation_result in report['validations'].items():
            if validation_result.get('status') == 'FAIL':
                report['overall_status'] = 'FAIL'
                break
        
        # Save report if output file specified
        if output_file:
            self.save_report(report, output_file)
        
        return report
    
    def save_report(self, report: Dict, output_file: str):
        """Save validation report to file"""
        try:
            if output_file.endswith('.json'):
                with open(output_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            elif output_file.endswith('.txt'):
                with open(output_file, 'w') as f:
                    f.write(self.format_report_text(report))
            else:
                # Default to JSON
                with open(output_file + '.json', 'w') as f:
                    json.dump(report, f, indent=2, default=str)
            print(f"Report saved to {output_file}")
        except Exception as e:
            print(f"Error saving report: {e}")
    
    def format_report_text(self, report: Dict) -> str:
        """Format report as readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("CHATGPT DATA VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {report['timestamp']}")
        lines.append(f"Weekly File: {report['weekly_file']}")
        lines.append(f"Monthly File: {report['monthly_file']}")
        lines.append(f"Overall Status: {report['overall_status']}")
        lines.append("")
        
        for validation_name, result in report['validations'].items():
            lines.append("-" * 60)
            lines.append(f"Validation: {validation_name.replace('_', ' ').title()}")
            lines.append(f"Status: {result.get('status', 'N/A')}")
            
            if 'discrepancies' in result and result['discrepancies']:
                lines.append(f"Found {len(result['discrepancies'])} discrepancies:")
                for disc in result['discrepancies'][:10]:  # Show first 10
                    lines.append(f"  - {disc['month']}: {disc['category']} "
                               f"(Weekly: {disc['weekly_sum']}, "
                               f"Monthly: {disc['monthly_value']}, "
                               f"Diff: {disc['difference']})")
                if len(result['discrepancies']) > 10:
                    lines.append(f"  ... and {len(result['discrepancies']) - 10} more")
            
            if 'issues' in result and result['issues']:
                lines.append(f"Found {len(result['issues'])} issues:")
                for issue in result['issues'][:10]:  # Show first 10
                    lines.append(f"  - Row {issue['row_index']}: "
                               f"Total mismatch by {issue['difference']}")
                if len(result['issues']) > 10:
                    lines.append(f"  ... and {len(result['issues']) - 10} more")
            
            if 'summary' in result:
                lines.append("Summary by Category:")
                for category, stats in result['summary'].items():
                    lines.append(f"  {category}:")
                    lines.append(f"    Weekly Total: {stats['total_weekly']}")
                    lines.append(f"    Monthly Total: {stats['total_monthly']}")
                    lines.append(f"    Matches: {stats['matches']}")
                    lines.append(f"    Mismatches: {stats['mismatches']}")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def create_sample_data():
    """Create sample weekly and monthly data for testing"""
    
    # Create sample weekly data
    weekly_data = {
        'week_start': [
            '2024-01-01', '2024-01-08', '2024-01-15', '2024-01-22', '2024-01-29',
            '2024-02-05', '2024-02-12', '2024-02-19', '2024-02-26'
        ],
        'GPT': [100, 120, 110, 130, 105, 115, 125, 118, 122],
        'Project': [50, 55, 52, 58, 51, 54, 56, 53, 57],
        'Tool': [75, 80, 78, 82, 76, 79, 81, 77, 83],
        'General': [200, 210, 205, 215, 202, 208, 212, 206, 214],
        'total_messages': [425, 465, 445, 485, 434, 456, 474, 454, 476]
    }
    
    # Create sample monthly data (should match weekly sums)
    monthly_data = {
        'month': ['2024-01-01', '2024-02-01'],
        'GPT': [565, 480],  # Sum of January and February weeks
        'Project': [266, 220],
        'Tool': [391, 320],
        'General': [1032, 840],
        'total_messages': [2254, 1860]
    }
    
    # Save sample data
    pd.DataFrame(weekly_data).to_csv('/home/claude/sample_weekly_data.csv', index=False)
    pd.DataFrame(monthly_data).to_csv('/home/claude/sample_monthly_data.csv', index=False)
    
    print("Sample data files created:")
    print("  - sample_weekly_data.csv")
    print("  - sample_monthly_data.csv")


def main():
    """Main function to run the validator"""
    
    # Create sample data for demonstration
    create_sample_data()
    
    # Initialize validator
    validator = ChatGPTDataValidator()
    
    # Run validation on sample data
    print("\nRunning validation on sample data...")
    report = validator.generate_validation_report(
        weekly_file='/home/claude/sample_weekly_data.csv',
        monthly_file='/home/claude/sample_monthly_data.csv',
        output_file='/home/claude/validation_report.txt'
    )
    
    # Print summary
    print(f"\nValidation Complete!")
    print(f"Overall Status: {report['overall_status']}")
    
    if report['overall_status'] == 'FAIL':
        print("\nIssues found:")
        for validation_name, result in report['validations'].items():
            if result.get('status') == 'FAIL':
                print(f"  - {validation_name.replace('_', ' ').title()}")
                if 'discrepancies' in result:
                    print(f"    Found {len(result['discrepancies'])} discrepancies")
                if 'issues' in result:
                    print(f"    Found {len(result['issues'])} issues")


if __name__ == "__main__":
    main()
