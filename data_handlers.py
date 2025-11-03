"""
Separate Data Handler for Weekly and Monthly ChatGPT Data
Ensures weekly and monthly data are used in different ways while maintaining consistency
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class WeeklyDataHandler:
    """
    Handles weekly ChatGPT data with specific analysis methods
    """
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load weekly data"""
        if self.data_path.endswith('.csv'):
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.endswith(('.xlsx', '.xls')):
            self.df = pd.read_excel(self.data_path)
        
        # Convert date columns
        if 'week_start' in self.df.columns:
            self.df['week_start'] = pd.to_datetime(self.df['week_start'])
            self.df['week_num'] = self.df['week_start'].dt.isocalendar().week
            self.df['year'] = self.df['week_start'].dt.year
    
    def calculate_weekly_trends(self) -> pd.DataFrame:
        """Calculate week-over-week trends"""
        trends = self.df.copy()
        
        # Calculate week-over-week changes for each category
        for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if col in trends.columns:
                trends[f'{col}_wow_change'] = trends[col].diff()
                trends[f'{col}_wow_pct'] = trends[col].pct_change() * 100
        
        return trends
    
    def get_weekly_averages(self) -> Dict:
        """Calculate weekly averages by category"""
        averages = {}
        for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if col in self.df.columns:
                averages[col] = {
                    'mean': self.df[col].mean(),
                    'median': self.df[col].median(),
                    'std': self.df[col].std(),
                    'min': self.df[col].min(),
                    'max': self.df[col].max()
                }
        return averages
    
    def identify_peak_weeks(self, category: str = 'total_messages') -> pd.DataFrame:
        """Identify peak usage weeks"""
        if category not in self.df.columns:
            return pd.DataFrame()
        
        # Find weeks above 90th percentile
        threshold = self.df[category].quantile(0.9)
        peak_weeks = self.df[self.df[category] > threshold].copy()
        peak_weeks['peak_indicator'] = 'Peak'
        
        return peak_weeks[['week_start', category, 'peak_indicator']]
    
    def get_category_distribution(self) -> pd.DataFrame:
        """Get distribution of messages across categories for each week"""
        dist_df = self.df.copy()
        
        categories = ['GPT', 'Project', 'Tool', 'General']
        for cat in categories:
            if cat in dist_df.columns and 'total_messages' in dist_df.columns:
                dist_df[f'{cat}_pct'] = (dist_df[cat] / dist_df['total_messages']) * 100
        
        return dist_df


class MonthlyDataHandler:
    """
    Handles monthly ChatGPT data with specific analysis methods
    """
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load monthly data"""
        if self.data_path.endswith('.csv'):
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.endswith(('.xlsx', '.xls')):
            self.df = pd.read_excel(self.data_path)
        
        # Convert date columns
        if 'month' in self.df.columns:
            self.df['month'] = pd.to_datetime(self.df['month'])
            self.df['month_name'] = self.df['month'].dt.strftime('%B %Y')
    
    def calculate_monthly_trends(self) -> pd.DataFrame:
        """Calculate month-over-month trends"""
        trends = self.df.copy()
        
        # Calculate month-over-month changes
        for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if col in trends.columns:
                trends[f'{col}_mom_change'] = trends[col].diff()
                trends[f'{col}_mom_pct'] = trends[col].pct_change() * 100
        
        return trends
    
    def project_next_month(self) -> Dict:
        """Project next month's values based on trends"""
        projections = {}
        
        for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if col in self.df.columns:
                # Simple linear projection based on last 3 months
                if len(self.df) >= 3:
                    recent = self.df[col].tail(3)
                    trend = recent.diff().mean()
                    last_value = recent.iloc[-1]
                    projection = last_value + trend
                    
                    projections[col] = {
                        'last_value': last_value,
                        'trend': trend,
                        'projection': projection,
                        'confidence': 'Medium' if abs(trend/last_value) < 0.1 else 'Low'
                    }
        
        return projections
    
    def get_quarterly_summary(self) -> pd.DataFrame:
        """Aggregate monthly data to quarterly level"""
        quarterly = self.df.copy()
        quarterly['quarter'] = quarterly['month'].dt.to_period('Q')
        
        # Group by quarter
        agg_dict = {}
        for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if col in quarterly.columns:
                agg_dict[col] = 'sum'
        
        return quarterly.groupby('quarter').agg(agg_dict).reset_index()
    
    def calculate_seasonality(self) -> Dict:
        """Identify seasonal patterns in monthly data"""
        seasonality = {}
        
        if len(self.df) >= 12:  # Need at least a year of data
            self.df['month_of_year'] = self.df['month'].dt.month
            
            for col in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
                if col in self.df.columns:
                    monthly_avg = self.df.groupby('month_of_year')[col].mean()
                    seasonality[col] = {
                        'highest_month': monthly_avg.idxmax(),
                        'lowest_month': monthly_avg.idxmin(),
                        'seasonal_range': monthly_avg.max() - monthly_avg.min(),
                        'monthly_averages': monthly_avg.to_dict()
                    }
        
        return seasonality


class DataReconciliationTool:
    """
    Tool to reconcile and validate weekly vs monthly data
    """
    
    def __init__(self, weekly_handler: WeeklyDataHandler, monthly_handler: MonthlyDataHandler):
        self.weekly = weekly_handler
        self.monthly = monthly_handler
    
    def reconcile_period(self, year: int, month: int) -> Dict:
        """Reconcile data for a specific month"""
        # Filter weekly data for the month
        month_start = pd.Timestamp(year=year, month=month, day=1)
        month_end = month_start + pd.offsets.MonthEnd(0)
        
        weekly_in_month = self.weekly.df[
            (self.weekly.df['week_start'] >= month_start) & 
            (self.weekly.df['week_start'] <= month_end)
        ]
        
        # Get monthly data for the same period
        monthly_record = self.monthly.df[
            self.monthly.df['month'] == month_start
        ]
        
        reconciliation = {
            'period': f"{year}-{month:02d}",
            'status': 'RECONCILED',
            'discrepancies': []
        }
        
        # Compare totals for each category
        for category in ['GPT', 'Project', 'Tool', 'General', 'total_messages']:
            if category in weekly_in_month.columns and category in monthly_record.columns:
                weekly_sum = weekly_in_month[category].sum()
                monthly_val = monthly_record[category].iloc[0] if not monthly_record.empty else 0
                
                if weekly_sum != monthly_val:
                    reconciliation['status'] = 'DISCREPANCY'
                    reconciliation['discrepancies'].append({
                        'category': category,
                        'weekly_sum': weekly_sum,
                        'monthly_value': monthly_val,
                        'difference': monthly_val - weekly_sum
                    })
        
        return reconciliation
    
    def create_reconciliation_report(self) -> List[Dict]:
        """Create full reconciliation report for all periods"""
        reports = []
        
        # Get unique year-month combinations from monthly data
        for _, row in self.monthly.df.iterrows():
            year = row['month'].year
            month = row['month'].month
            report = self.reconcile_period(year, month)
            reports.append(report)
        
        return reports
    
    def visualize_discrepancies(self, save_path: Optional[str] = None):
        """Create visualization of discrepancies"""
        reports = self.create_reconciliation_report()
        
        # Prepare data for visualization
        discrepancy_data = []
        for report in reports:
            for disc in report.get('discrepancies', []):
                discrepancy_data.append({
                    'period': report['period'],
                    'category': disc['category'],
                    'difference': disc['difference']
                })
        
        if not discrepancy_data:
            print("No discrepancies found to visualize!")
            return
        
        # Create visualization
        disc_df = pd.DataFrame(discrepancy_data)
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 8))
        
        # Plot 1: Discrepancies by period
        pivot_period = disc_df.pivot(index='period', columns='category', values='difference')
        pivot_period.plot(kind='bar', ax=axes[0])
        axes[0].set_title('Discrepancies by Period and Category')
        axes[0].set_xlabel('Period')
        axes[0].set_ylabel('Difference (Monthly - Weekly Sum)')
        axes[0].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        axes[0].legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Plot 2: Total discrepancies by category
        total_disc = disc_df.groupby('category')['difference'].sum()
        total_disc.plot(kind='bar', ax=axes[1], color='coral')
        axes[1].set_title('Total Discrepancies by Category')
        axes[1].set_xlabel('Category')
        axes[1].set_ylabel('Total Difference')
        axes[1].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            print(f"Visualization saved to {save_path}")
        else:
            plt.show()


def example_usage():
    """Example of how to use the separate data handlers"""
    
    print("=" * 80)
    print("EXAMPLE: Using Separate Weekly and Monthly Data Handlers")
    print("=" * 80)
    
    # Initialize handlers (using the sample data created earlier)
    weekly_handler = WeeklyDataHandler('/home/claude/sample_weekly_data.csv')
    monthly_handler = MonthlyDataHandler('/home/claude/sample_monthly_data.csv')
    
    print("\n1. WEEKLY DATA ANALYSIS")
    print("-" * 40)
    
    # Get weekly trends
    weekly_trends = weekly_handler.calculate_weekly_trends()
    print("Weekly Trends (last 3 weeks):")
    print(weekly_trends[['week_start', 'total_messages', 'total_messages_wow_pct']].tail(3))
    
    # Get weekly averages
    weekly_avg = weekly_handler.get_weekly_averages()
    print("\nWeekly Averages:")
    for category, stats in weekly_avg.items():
        print(f"  {category}: Mean={stats['mean']:.1f}, Std={stats['std']:.1f}")
    
    # Identify peak weeks
    peak_weeks = weekly_handler.identify_peak_weeks()
    print(f"\nPeak Weeks (>90th percentile): {len(peak_weeks)} weeks")
    
    print("\n2. MONTHLY DATA ANALYSIS")
    print("-" * 40)
    
    # Get monthly trends
    monthly_trends = monthly_handler.calculate_monthly_trends()
    print("Monthly Trends:")
    print(monthly_trends[['month_name', 'total_messages', 'total_messages_mom_pct']])
    
    # Project next month
    projections = monthly_handler.project_next_month()
    print("\nProjections for Next Month:")
    for category, proj in projections.items():
        print(f"  {category}: {proj['projection']:.0f} (confidence: {proj['confidence']})")
    
    print("\n3. DATA RECONCILIATION")
    print("-" * 40)
    
    # Initialize reconciliation tool
    recon_tool = DataReconciliationTool(weekly_handler, monthly_handler)
    
    # Create reconciliation report
    recon_reports = recon_tool.create_reconciliation_report()
    
    print("Reconciliation Results:")
    for report in recon_reports:
        print(f"  {report['period']}: {report['status']}")
        if report['discrepancies']:
            for disc in report['discrepancies']:
                print(f"    - {disc['category']}: Difference = {disc['difference']}")
    
    print("\n" + "=" * 80)
    print("Data handlers keep weekly and monthly data separate while ensuring consistency!")
    print("=" * 80)


if __name__ == "__main__":
    example_usage()
