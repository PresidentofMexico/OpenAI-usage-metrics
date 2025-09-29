"""
Configuration settings for OpenAI Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "OpenAI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Expected CSV columns mapping
CSV_COLUMN_MAPPING = {
    'user_id': ['user_id', 'email', 'user_email'],
    'user_name': ['user_name', 'name', 'display_name'],
    'department': ['department', 'dept', 'team'],
    'date': ['date', 'usage_date', 'timestamp'],
    'feature_used': ['feature_used', 'feature', 'service'],
    'usage_count': ['usage_count', 'count', 'interactions'],
    'cost_usd': ['cost_usd', 'cost', 'price']
}

# Default values for missing data
DEFAULT_VALUES = {
    'department': 'Unknown',
    'feature_used': 'General',
    'usage_count': 1,
    'cost_usd': 0.0
}