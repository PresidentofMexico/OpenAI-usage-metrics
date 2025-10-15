"""
Enterprise Cost Calculator for AI Usage Metrics

Calculates true SaaS costs based on enterprise license pricing,
not per-message usage. Provides cost-per-user metrics for better ROI analysis.
"""
import pandas as pd
from datetime import datetime
from config import ENTERPRISE_PRICING


class EnterpriseCostCalculator:
    """Calculate enterprise SaaS costs based on license pricing."""
    
    def __init__(self):
        self.pricing = ENTERPRISE_PRICING
    
    def calculate_monthly_cost_per_user(self, tool_source, active_users):
        """
        Calculate monthly cost based on enterprise license pricing.
        
        Args:
            tool_source: Name of the AI tool (ChatGPT, BlueFlame AI, etc.)
            active_users: Number of active users in the period
            
        Returns:
            dict: Cost breakdown including total cost and per-user cost
        """
        # Normalize tool source name
        tool_key = self._normalize_tool_name(tool_source)
        
        if tool_key not in self.pricing:
            # Default to ChatGPT pricing if unknown
            tool_key = 'ChatGPT'
        
        pricing_info = self.pricing[tool_key]
        cost_per_user = pricing_info['license_cost_per_user_monthly']
        
        # Calculate total monthly cost
        total_monthly_cost = cost_per_user * active_users
        
        return {
            'cost_per_user_monthly': cost_per_user,
            'total_monthly_cost': total_monthly_cost,
            'active_users': active_users,
            'tool_source': tool_source,
            'pricing_model': 'Enterprise License',
            'notes': pricing_info['notes']
        }
    
    def calculate_annual_cost_projection(self, tool_source, active_users):
        """
        Project annual cost based on current active users.
        
        Args:
            tool_source: Name of the AI tool
            active_users: Number of active users
            
        Returns:
            dict: Annual cost projections
        """
        monthly_calc = self.calculate_monthly_cost_per_user(tool_source, active_users)
        
        annual_total = monthly_calc['total_monthly_cost'] * 12
        annual_per_user = monthly_calc['cost_per_user_monthly'] * 12
        
        return {
            'annual_total_cost': annual_total,
            'annual_cost_per_user': annual_per_user,
            'monthly_cost_per_user': monthly_calc['cost_per_user_monthly'],
            'active_users': active_users,
            'tool_source': tool_source
        }
    
    def enrich_usage_data_with_license_costs(self, usage_df):
        """
        Add enterprise license cost calculations to usage data.
        
        This adds a 'license_cost_usd' column based on per-user pricing,
        while keeping the original 'cost_usd' for reference.
        
        Args:
            usage_df: DataFrame with usage metrics
            
        Returns:
            DataFrame with added cost columns
        """
        if usage_df.empty:
            return usage_df
        
        df = usage_df.copy()
        
        # Group by tool, date, and user to calculate monthly active users
        if 'date' in df.columns:
            df['month'] = pd.to_datetime(df['date'], errors='coerce').dt.to_period('M').astype(str)
        else:
            df['month'] = datetime.now().strftime('%Y-%m')
        
        # Calculate license costs per user per month
        license_costs = []
        
        for idx, row in df.iterrows():
            tool_source = row.get('tool_source', 'ChatGPT')
            tool_key = self._normalize_tool_name(tool_source)
            
            if tool_key in self.pricing:
                # Each active user in a month incurs the full monthly license cost
                cost_per_user = self.pricing[tool_key]['license_cost_per_user_monthly']
            else:
                cost_per_user = self.pricing['ChatGPT']['license_cost_per_user_monthly']
            
            license_costs.append(cost_per_user)
        
        df['license_cost_usd'] = license_costs
        
        return df
    
    def calculate_cost_efficiency_metrics(self, usage_df):
        """
        Calculate cost efficiency metrics for enterprise licenses.
        
        Args:
            usage_df: DataFrame with usage and cost data
            
        Returns:
            dict: Efficiency metrics including cost per message, utilization, etc.
        """
        if usage_df.empty:
            return {}
        
        df = usage_df.copy()
        
        # Add license costs if not present
        if 'license_cost_usd' not in df.columns:
            df = self.enrich_usage_data_with_license_costs(df)
        
        total_users = df['user_id'].nunique()
        total_messages = df['usage_count'].sum()
        total_license_cost = df.groupby(['user_id', 'month'])['license_cost_usd'].first().sum() if 'month' in df.columns else 0
        
        # Calculate efficiency metrics
        metrics = {
            'total_active_users': total_users,
            'total_messages': total_messages,
            'total_license_cost': total_license_cost,
            'messages_per_user': total_messages / max(total_users, 1),
            'cost_per_user': total_license_cost / max(total_users, 1),
            'cost_per_message': total_license_cost / max(total_messages, 1) if total_messages > 0 else 0,
            'license_utilization': 'Active' if total_messages > 0 else 'Inactive'
        }
        
        return metrics
    
    def get_pricing_info(self, tool_source):
        """
        Get pricing information for a specific tool.
        
        Args:
            tool_source: Name of the AI tool
            
        Returns:
            dict: Pricing information
        """
        tool_key = self._normalize_tool_name(tool_source)
        
        if tool_key in self.pricing:
            return self.pricing[tool_key]
        else:
            return self.pricing['ChatGPT']  # Default
    
    def _normalize_tool_name(self, tool_source):
        """Normalize tool source name for pricing lookup."""
        if not tool_source:
            return 'ChatGPT'
        
        tool_lower = str(tool_source).lower()
        
        if 'blueflame' in tool_lower:
            return 'BlueFlame AI'
        elif 'openai' in tool_lower or 'chatgpt' in tool_lower or 'gpt' in tool_lower:
            return 'ChatGPT'
        else:
            return 'ChatGPT'  # Default
