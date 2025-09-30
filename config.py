"""
Configuration settings for Multi-Provider AI Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/ai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "🤖"

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