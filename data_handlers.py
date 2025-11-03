"""
Separate Data Handler for Weekly and Monthly ChatGPT Data
Ensures weekly and monthly data are used in different ways while maintaining consistency
Data Handlers for Weekly and Monthly ChatGPT Data

Provides separate, specialized handlers for analyzing weekly and monthly ChatGPT usage data,
with tools for reconciliation and consistency checking.

Classes:
- WeeklyDataHandler: Analyzes weekly patterns, trends, and peak weeks
- MonthlyDataHandler: Provides monthly projections, quarterly summaries, and seasonality
- DataReconciliationTool: Ensures consistency between weekly and monthly data

Usage:
    from data_handlers import WeeklyDataHandler, MonthlyDataHandler, DataReconciliationTool
    
    # Weekly analysis
    weekly_handler = WeeklyDataHandler()
    weekly_handler.load_data(weekly_files)
    trends = weekly_handler.analyze_trends()
    
    # Monthly analysis
    monthly_handler = MonthlyDataHandler()
    monthly_handler.load_data(monthly_files)
    projections = monthly_handler.project_annual_usage()
    
    # Reconciliation
    reconciler = DataReconciliationTool()
    results = reconciler.reconcile(weekly_handler, monthly_handler)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json


class WeeklyDataHandler:
    """Handler for analyzing weekly ChatGPT usage data."""
    
    def __init__(self):
        """Initialize the weekly data handler."""
        self.data = None
        self.loaded_files = []
        self.message_categories = ['messages', 'gpt_messages', 'tool_messages', 'project_messages']
    
    def load_data(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Load weekly data from CSV files.
        
        Args:
            file_paths: List of paths to weekly CSV files
            
        Returns:
            Combined DataFrame with all weekly data
        """
        dfs = []
        
        for filepath in file_paths:
            try:
                df = pd.read_csv(filepath)
                
                # Verify it's weekly data
                if 'cadence' in df.columns:
                    if not (df['cadence'] == 'Weekly').any():
                        print(f"Warning: {filepath} does not appear to be weekly data")
                
                # Add source file tracking
                df['source_file'] = filepath
                dfs.append(df)
                self.loaded_files.append(filepath)
                
            except Exception as e:
                print(f"Error loading {filepath}: {str(e)}")
        
        if not dfs:
            raise ValueError("No valid weekly data files loaded")
        
        self.data = pd.concat(dfs, ignore_index=True)
        
        # Convert date columns
        if 'period_start' in self.data.columns:
            self.data['period_start'] = pd.to_datetime(self.data['period_start'])
        if 'period_end' in self.data.columns:
            self.data['period_end'] = pd.to_datetime(self.data['period_end'])
        
        # Convert numeric columns
        for col in self.message_categories:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce').fillna(0)
        
        return self.data
    
    def analyze_trends(self) -> Dict[str, Any]:
        """
        Analyze weekly trends in usage.
        
        Returns:
            Dictionary with trend analysis results
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Filter to active users
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        # Group by week
        weekly_stats = active_data.groupby('period_start').agg({
            'email': 'nunique',  # Unique users per week
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum'
        }).reset_index()
        
        weekly_stats.columns = ['week', 'active_users', 'total_messages', 
                               'gpt_messages', 'tool_messages', 'project_messages']
        
        # Calculate week-over-week changes
        weekly_stats['messages_change'] = weekly_stats['total_messages'].diff()
        weekly_stats['messages_change_pct'] = (
            weekly_stats['total_messages'].pct_change() * 100
        ).round(2)
        
        weekly_stats['users_change'] = weekly_stats['active_users'].diff()
        weekly_stats['users_change_pct'] = (
            weekly_stats['active_users'].pct_change() * 100
        ).round(2)
        
        # Calculate average messages per user
        weekly_stats['avg_messages_per_user'] = (
            weekly_stats['total_messages'] / weekly_stats['active_users']
        ).round(2)
        
        return {
            'weekly_statistics': weekly_stats.to_dict('records'),
            'summary': {
                'total_weeks': len(weekly_stats),
                'avg_weekly_messages': int(weekly_stats['total_messages'].mean()),
                'avg_weekly_users': int(weekly_stats['active_users'].mean()),
                'peak_week': {
                    'date': str(weekly_stats.loc[weekly_stats['total_messages'].idxmax(), 'week'].date()),
                    'messages': int(weekly_stats['total_messages'].max()),
                    'users': int(weekly_stats.loc[weekly_stats['total_messages'].idxmax(), 'active_users'])
                },
                'lowest_week': {
                    'date': str(weekly_stats.loc[weekly_stats['total_messages'].idxmin(), 'week'].date()),
                    'messages': int(weekly_stats['total_messages'].min()),
                    'users': int(weekly_stats.loc[weekly_stats['total_messages'].idxmin(), 'active_users'])
                }
            }
        }
    
    def identify_peak_weeks(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identify peak usage weeks.
        
        Args:
            top_n: Number of top weeks to return
            
        Returns:
            List of peak weeks with details
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        weekly_totals = active_data.groupby('period_start').agg({
            'messages': 'sum',
            'email': 'nunique'
        }).reset_index()
        
        weekly_totals.columns = ['week', 'total_messages', 'active_users']
        weekly_totals['avg_messages_per_user'] = (
            weekly_totals['total_messages'] / weekly_totals['active_users']
        ).round(2)
        
        # Sort by total messages
        top_weeks = weekly_totals.nlargest(top_n, 'total_messages')
        
        results = []
        for _, row in top_weeks.iterrows():
            results.append({
                'week_start': str(row['week'].date()),
                'total_messages': int(row['total_messages']),
                'active_users': int(row['active_users']),
                'avg_messages_per_user': float(row['avg_messages_per_user'])
            })
        
        return results
    
    def analyze_user_engagement(self) -> Dict[str, Any]:
        """
        Analyze user engagement patterns in weekly data.
        
        Returns:
            Dictionary with engagement metrics
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        # User-level aggregation
        user_stats = active_data.groupby('email').agg({
            'period_start': 'count',  # Number of active weeks
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum'
        }).reset_index()
        
        user_stats.columns = ['email', 'active_weeks', 'total_messages',
                             'gpt_messages', 'tool_messages', 'project_messages']
        
        # Calculate engagement metrics
        total_weeks = active_data['period_start'].nunique()
        user_stats['engagement_rate'] = (
            (user_stats['active_weeks'] / total_weeks) * 100
        ).round(2)
        
        user_stats['avg_messages_per_week'] = (
            user_stats['total_messages'] / user_stats['active_weeks']
        ).round(2)
        
        # Categorize users
        def categorize_engagement(rate):
            if rate >= 80:
                return 'High'
            elif rate >= 50:
                return 'Medium'
            else:
                return 'Low'
        
        user_stats['engagement_category'] = user_stats['engagement_rate'].apply(categorize_engagement)
        
        # Summary statistics
        engagement_summary = user_stats['engagement_category'].value_counts().to_dict()
        
        return {
            'total_users': len(user_stats),
            'total_weeks_analyzed': total_weeks,
            'engagement_distribution': engagement_summary,
            'avg_engagement_rate': float(user_stats['engagement_rate'].mean().round(2)),
            'avg_active_weeks_per_user': float(user_stats['active_weeks'].mean().round(2)),
            'top_users': user_stats.nlargest(10, 'total_messages')[
                ['email', 'active_weeks', 'total_messages', 'engagement_rate']
            ].to_dict('records')
        }
    
    def get_weekly_summary(self) -> pd.DataFrame:
        """
        Get a summary DataFrame of weekly data.
        
        Returns:
            DataFrame with weekly summaries
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        summary = active_data.groupby('period_start').agg({
            'email': 'nunique',
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum'
        }).reset_index()
        
        summary.columns = ['week', 'active_users', 'messages', 
                          'gpt_messages', 'tool_messages', 'project_messages']
        
        return summary


class MonthlyDataHandler:
    """Handler for analyzing monthly ChatGPT usage data."""
    
    def __init__(self):
        """Initialize the monthly data handler."""
        self.data = None
        self.loaded_files = []
        self.message_categories = ['messages', 'gpt_messages', 'tool_messages', 'project_messages']
    
    def load_data(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Load monthly data from CSV files.
        
        Args:
            file_paths: List of paths to monthly CSV files
            
        Returns:
            Combined DataFrame with all monthly data
        """
        dfs = []
        
        for filepath in file_paths:
            try:
                df = pd.read_csv(filepath)
                
                # Verify it's monthly data
                if 'cadence' in df.columns:
                    if not (df['cadence'] == 'Monthly').any():
                        print(f"Warning: {filepath} does not appear to be monthly data")
                
                # Add source file tracking
                df['source_file'] = filepath
                dfs.append(df)
                self.loaded_files.append(filepath)
                
            except Exception as e:
                print(f"Error loading {filepath}: {str(e)}")
        
        if not dfs:
            raise ValueError("No valid monthly data files loaded")
        
        self.data = pd.concat(dfs, ignore_index=True)
        
        # Convert date columns
        if 'period_start' in self.data.columns:
            self.data['period_start'] = pd.to_datetime(self.data['period_start'])
        if 'period_end' in self.data.columns:
            self.data['period_end'] = pd.to_datetime(self.data['period_end'])
        
        # Convert numeric columns
        for col in self.message_categories:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce').fillna(0)
        
        return self.data
    
    def project_annual_usage(self) -> Dict[str, Any]:
        """
        Project annual usage based on monthly data.
        
        Returns:
            Dictionary with annual projections
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        # Monthly totals
        monthly_totals = active_data.groupby('period_start').agg({
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum',
            'email': 'nunique'
        }).reset_index()
        
        monthly_totals.columns = ['month', 'messages', 'gpt_messages', 
                                 'tool_messages', 'project_messages', 'active_users']
        
        # Calculate monthly averages
        avg_monthly_messages = monthly_totals['messages'].mean()
        avg_monthly_users = monthly_totals['active_users'].mean()
        
        # Calculate growth rate
        if len(monthly_totals) >= 2:
            first_month = monthly_totals.iloc[0]['messages']
            last_month = monthly_totals.iloc[-1]['messages']
            months_diff = len(monthly_totals) - 1
            
            if first_month > 0 and months_diff > 0:
                monthly_growth_rate = ((last_month / first_month) ** (1 / months_diff) - 1) * 100
            else:
                monthly_growth_rate = 0
        else:
            monthly_growth_rate = 0
        
        # Project annual totals
        months_available = len(monthly_totals)
        
        if months_available > 0:
            # Simple projection: average monthly * 12
            simple_projection = avg_monthly_messages * 12
            
            # Growth-adjusted projection
            if monthly_growth_rate > 0:
                growth_adjusted_projection = sum([
                    avg_monthly_messages * (1 + monthly_growth_rate / 100) ** i
                    for i in range(12)
                ])
            else:
                growth_adjusted_projection = simple_projection
        else:
            simple_projection = 0
            growth_adjusted_projection = 0
        
        return {
            'months_analyzed': months_available,
            'avg_monthly_messages': int(avg_monthly_messages),
            'avg_monthly_users': int(avg_monthly_users),
            'monthly_growth_rate': round(monthly_growth_rate, 2),
            'projections': {
                'simple_annual': int(simple_projection),
                'growth_adjusted_annual': int(growth_adjusted_projection)
            },
            'monthly_breakdown': monthly_totals.to_dict('records')
        }
    
    def analyze_quarterly_trends(self) -> Dict[str, Any]:
        """
        Analyze usage by quarter.
        
        Returns:
            Dictionary with quarterly analysis
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        # Add quarter column
        active_data['quarter'] = active_data['period_start'].dt.to_period('Q')
        
        # Quarterly aggregation
        quarterly_stats = active_data.groupby('quarter').agg({
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum',
            'email': 'nunique'
        }).reset_index()
        
        quarterly_stats.columns = ['quarter', 'messages', 'gpt_messages',
                                   'tool_messages', 'project_messages', 'active_users']
        
        # Calculate quarter-over-quarter changes
        quarterly_stats['messages_change'] = quarterly_stats['messages'].diff()
        quarterly_stats['messages_change_pct'] = (
            quarterly_stats['messages'].pct_change() * 100
        ).round(2)
        
        quarterly_stats['users_change'] = quarterly_stats['active_users'].diff()
        quarterly_stats['users_change_pct'] = (
            quarterly_stats['active_users'].pct_change() * 100
        ).round(2)
        
        # Convert quarter to string for JSON serialization
        quarterly_stats['quarter'] = quarterly_stats['quarter'].astype(str)
        
        return {
            'total_quarters': len(quarterly_stats),
            'quarterly_data': quarterly_stats.to_dict('records'),
            'summary': {
                'avg_quarterly_messages': int(quarterly_stats['messages'].mean()),
                'avg_quarterly_users': int(quarterly_stats['active_users'].mean()),
                'best_quarter': {
                    'period': quarterly_stats.loc[quarterly_stats['messages'].idxmax(), 'quarter'],
                    'messages': int(quarterly_stats['messages'].max())
                }
            }
        }
    
    def analyze_seasonality(self) -> Dict[str, Any]:
        """
        Analyze seasonal patterns in monthly data.
        
        Returns:
            Dictionary with seasonality insights
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        # Extract month name
        active_data['month_name'] = active_data['period_start'].dt.month_name()
        active_data['month_num'] = active_data['period_start'].dt.month
        
        # Aggregate by month name
        monthly_patterns = active_data.groupby(['month_num', 'month_name']).agg({
            'messages': 'mean',
            'email': 'nunique'
        }).reset_index().sort_values('month_num')
        
        monthly_patterns.columns = ['month_num', 'month_name', 'avg_messages', 'avg_users']
        
        # Identify peak and low months
        peak_month = monthly_patterns.loc[monthly_patterns['avg_messages'].idxmax()]
        low_month = monthly_patterns.loc[monthly_patterns['avg_messages'].idxmin()]
        
        return {
            'monthly_patterns': monthly_patterns[['month_name', 'avg_messages', 'avg_users']].to_dict('records'),
            'peak_month': {
                'name': peak_month['month_name'],
                'avg_messages': int(peak_month['avg_messages'])
            },
            'low_month': {
                'name': low_month['month_name'],
                'avg_messages': int(low_month['avg_messages'])
            }
        }
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """
        Get a summary DataFrame of monthly data.
        
        Returns:
            DataFrame with monthly summaries
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        active_data = self.data[self.data.get('is_active', 1) == 1].copy()
        
        summary = active_data.groupby('period_start').agg({
            'email': 'nunique',
            'messages': 'sum',
            'gpt_messages': 'sum',
            'tool_messages': 'sum',
            'project_messages': 'sum'
        }).reset_index()
        
        summary.columns = ['month', 'active_users', 'messages',
                          'gpt_messages', 'tool_messages', 'project_messages']
        
        return summary


class DataReconciliationTool:
    """Tool for reconciling weekly and monthly data."""
    
    def __init__(self):
        """Initialize the reconciliation tool."""
        pass
    
    def reconcile(self, weekly_handler: WeeklyDataHandler, 
                 monthly_handler: MonthlyDataHandler,
                 tolerance_pct: float = 1.0) -> Dict[str, Any]:
        """
        Reconcile weekly and monthly data to ensure consistency.
        
        Args:
            weekly_handler: WeeklyDataHandler with loaded data
            monthly_handler: MonthlyDataHandler with loaded data
            tolerance_pct: Acceptable variance percentage
            
        Returns:
            Dictionary with reconciliation results
        """
        if weekly_handler.data is None or monthly_handler.data is None:
            raise ValueError("Both handlers must have data loaded")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tolerance_percentage': tolerance_pct,
            'status': 'PASS',
            'comparisons': []
        }
        
        # Get monthly summary from weekly data
        weekly_summary = weekly_handler.get_weekly_summary()
        monthly_summary = monthly_handler.get_monthly_summary()
        
        # For each month in monthly data, aggregate corresponding weeks
        for _, monthly_row in monthly_summary.iterrows():
            month_start = monthly_row['month']
            
            # Find matching weeks (weeks that start in this month)
            matching_weeks = weekly_summary[
                (weekly_summary['week'].dt.year == month_start.year) &
                (weekly_summary['week'].dt.month == month_start.month)
            ]
            
            if matching_weeks.empty:
                continue
            
            # Aggregate weekly data for this month
            weekly_agg = {
                'messages': matching_weeks['messages'].sum(),
                'gpt_messages': matching_weeks['gpt_messages'].sum(),
                'tool_messages': matching_weeks['tool_messages'].sum(),
                'project_messages': matching_weeks['project_messages'].sum(),
                'active_users': matching_weeks['active_users'].sum()  # Note: This sums users across weeks
            }
            
            comparison = {
                'month': str(month_start.date()),
                'weeks_included': len(matching_weeks),
                'categories': {}
            }
            
            # Compare each category
            for category in ['messages', 'gpt_messages', 'tool_messages', 'project_messages']:
                weekly_val = weekly_agg.get(category, 0)
                monthly_val = monthly_row.get(category, 0)
                
                diff = weekly_val - monthly_val
                
                if monthly_val > 0:
                    diff_pct = abs(diff / monthly_val * 100)
                elif weekly_val > 0:
                    diff_pct = 100.0
                else:
                    diff_pct = 0.0
                
                status = 'MATCH' if diff_pct <= tolerance_pct else 'MISMATCH'
                
                comparison['categories'][category] = {
                    'weekly_total': int(weekly_val),
                    'monthly_total': int(monthly_val),
                    'difference': int(diff),
                    'difference_pct': round(diff_pct, 2),
                    'status': status
                }
                
                if status == 'MISMATCH':
                    results['status'] = 'FAIL'
            
            results['comparisons'].append(comparison)
        
        return results
    
    def generate_reconciliation_report(self, reconciliation_results: Dict[str, Any]) -> str:
        """
        Generate a readable reconciliation report.
        
        Args:
            reconciliation_results: Results from reconcile()
            
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("Data Reconciliation Report")
        lines.append("=" * 80)
        lines.append(f"Generated: {reconciliation_results.get('timestamp', 'N/A')}")
        lines.append(f"Tolerance: {reconciliation_results.get('tolerance_percentage', 0)}%")
        
        status = reconciliation_results.get('status', 'UNKNOWN')
        status_symbol = '✅' if status == 'PASS' else '❌'
        lines.append(f"Overall Status: {status_symbol} {status}")
        lines.append("")
        
        for comparison in reconciliation_results.get('comparisons', []):
            lines.append(f"\nMonth: {comparison['month']}")
            lines.append(f"Weeks Included: {comparison['weeks_included']}")
            lines.append("-" * 60)
            
            for category, cat_data in comparison.get('categories', {}).items():
                cat_status = cat_data['status']
                cat_symbol = '✅' if cat_status == 'MATCH' else '❌'
                
                lines.append(f"\n  {cat_symbol} {category.upper()}")
                lines.append(f"    Weekly Total: {cat_data['weekly_total']:,}")
                lines.append(f"    Monthly Total: {cat_data['monthly_total']:,}")
                lines.append(f"    Difference: {cat_data['difference']:+,} ({cat_data['difference_pct']:+.2f}%)")
        
        lines.append("\n" + "=" * 80)
        
        return '\n'.join(lines)


def main():
    """Example usage of data handlers."""
    
    # Example: Weekly data analysis
    print("=" * 80)
    print("Weekly Data Analysis Example")
    print("=" * 80)
    
    weekly_handler = WeeklyDataHandler()
    weekly_files = ["sample_weekly_data.csv"]
    
    try:
        weekly_handler.load_data(weekly_files)
        print(f"\n✅ Loaded {len(weekly_files)} weekly files")
        
        # Analyze trends
        trends = weekly_handler.analyze_trends()
        print(f"\nWeekly Trends Summary:")
        print(f"  Total Weeks: {trends['summary']['total_weeks']}")
        print(f"  Avg Weekly Messages: {trends['summary']['avg_weekly_messages']:,}")
        print(f"  Avg Weekly Users: {trends['summary']['avg_weekly_users']}")
        
        # Peak weeks
        peak_weeks = weekly_handler.identify_peak_weeks(top_n=3)
        print(f"\nTop 3 Peak Weeks:")
        for i, week in enumerate(peak_weeks, 1):
            print(f"  {i}. {week['week_start']}: {week['total_messages']:,} messages")
        
        # User engagement
        engagement = weekly_handler.analyze_user_engagement()
        print(f"\nUser Engagement:")
        print(f"  Total Users: {engagement['total_users']}")
        print(f"  Avg Engagement Rate: {engagement['avg_engagement_rate']}%")
        print(f"  Engagement Distribution: {engagement['engagement_distribution']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Example: Monthly data analysis
    print("\n" + "=" * 80)
    print("Monthly Data Analysis Example")
    print("=" * 80)
    
    monthly_handler = MonthlyDataHandler()
    monthly_files = ["sample_monthly_data.csv"]
    
    try:
        monthly_handler.load_data(monthly_files)
        print(f"\n✅ Loaded {len(monthly_files)} monthly files")
        
        # Annual projection
        projection = monthly_handler.project_annual_usage()
        print(f"\nAnnual Projections:")
        print(f"  Months Analyzed: {projection['months_analyzed']}")
        print(f"  Avg Monthly Messages: {projection['avg_monthly_messages']:,}")
        print(f"  Simple Annual Projection: {projection['projections']['simple_annual']:,}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Example: Reconciliation
    print("\n" + "=" * 80)
    print("Data Reconciliation Example")
    print("=" * 80)
    
    try:
        reconciler = DataReconciliationTool()
        reconciliation = reconciler.reconcile(weekly_handler, monthly_handler)
        
        report = reconciler.generate_reconciliation_report(reconciliation)
        print(report)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
