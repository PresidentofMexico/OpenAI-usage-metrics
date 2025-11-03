"""
Configuration settings for Multi-Provider AI Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/ai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "🤖"

# Auto-scan folder settings
AUTO_SCAN_FOLDERS = [
    "OpenAI User Data",
    "BlueFlame User Data",
    "data/uploads"  # Optional user upload folder
]

# Folders that should be scanned recursively (for subfolders like Monthly/Weekly)
RECURSIVE_SCAN_FOLDERS = [
    "OpenAI User Data"
]

# File tracking settings
FILE_TRACKING_PATH = "file_tracking.json"

# Provider configurations
PROVIDERS = {
    'OpenAI': {
        'name': 'OpenAI',
        'icon': '🤖',
        'color': '#00A67E',
        'features': ['ChatGPT Messages', 'Tool Messages', 'Project Messages']
    },
    'BlueFlame AI': {
        'name': 'BlueFlame AI',
        'icon': '🔥',
        'color': '#FF6B35',
        'features': ['BlueFlame Queries', 'API Calls']
    },
    'Anthropic': {
        'name': 'Anthropic',
        'icon': '🏛️',
        'color': '#D2691E',
        'features': ['Claude Messages', 'Token Usage']
    },
    'Google': {
        'name': 'Google AI',
        'icon': '🔍',
        'color': '#4285F4',
        'features': ['Bard Conversations', 'API Requests']
    }
}

# Expected CSV columns mapping for each provider
PROVIDER_COLUMN_MAPPING = {
    'OpenAI': {
        'user_id': ['email', 'user_email'],
        'user_name': ['name', 'display_name'],
        'department': ['department', 'dept'],
        'date': ['period_start', 'date'],
        'usage_metrics': ['messages', 'tool_messages', 'project_messages']
    },
    'BlueFlame AI': {
        'user_id': ['user_email', 'email'],
        'user_name': ['full_name', 'name'],
        'department': ['team', 'department'],
        'date': ['usage_date', 'date'],
        'usage_metrics': ['total_queries', 'api_calls']
    },
    'Anthropic': {
        'user_id': ['email', 'user_email'],
        'user_name': ['user_name', 'name'],
        'department': ['department', 'team'],
        'date': ['date', 'usage_date'],
        'usage_metrics': ['messages_sent', 'tokens_used']
    }
}

# Default values for missing data
DEFAULT_VALUES = {
    'department': 'Unknown',
    'feature_used': 'General',
    'usage_count': 1,
    'cost_usd': 0.0,
    'provider': 'OpenAI'
}

# Enterprise SaaS License Pricing (per user per month)
# NOTE: Cost tracking has been disabled. All costs are set to $0.00
# This dashboard focuses on usage analytics, not financial tracking
ENTERPRISE_PRICING = {
    'ChatGPT': {
        'license_cost_per_user_monthly': 0.00,  # Cost tracking disabled
        'description': 'ChatGPT Enterprise License',
        'notes': 'Cost tracking disabled - focus on usage analytics',
        'min_seats': 150,
        'annual_cost_per_user': 0.00
    },
    'BlueFlame AI': {
        'license_cost_per_user_monthly': 0.00,  # Cost tracking disabled
        'description': 'BlueFlame AI Enterprise License',
        'notes': 'Cost tracking disabled - focus on usage analytics',
        'min_seats': 1,
        'annual_cost_per_user': 0.00
    },
    'OpenAI': {  # Alias for ChatGPT
        'license_cost_per_user_monthly': 0.00,  # Cost tracking disabled
        'description': 'OpenAI Enterprise License',
        'notes': 'Cost tracking disabled - focus on usage analytics',
        'min_seats': 150,
        'annual_cost_per_user': 0.00
    }
}

# Legacy per-message pricing (kept for reference/comparison)
# NOTE: Cost tracking has been disabled. All costs are set to $0.00
LEGACY_MESSAGE_PRICING = {
    'ChatGPT Messages': 0.00,
    'GPT Messages': 0.00,
    'Tool Messages': 0.00,
    'Project Messages': 0.00,
    'BlueFlame Messages': 0.00
}