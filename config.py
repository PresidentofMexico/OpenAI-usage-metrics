"""
Configuration settings for Multi-Provider Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Provider definitions
PROVIDERS = {
    'OpenAI': {
        'display_name': 'OpenAI',
        'icon': '🤖',
        'columns': {
            'user_id': ['email', 'user_email', 'user_id'],
            'user_name': ['name', 'display_name', 'user_name'],
            'department': ['department', 'dept'],
            'date': ['period_start', 'date', 'usage_date'],
            'messages': ['messages'],
            'tool_messages': ['tool_messages'],
            'project_messages': ['project_messages']
        },
        'features': {
            'messages': {'name': 'ChatGPT Messages', 'cost_per_unit': 0.02},
            'tool_messages': {'name': 'Tool Messages', 'cost_per_unit': 0.01},
            'project_messages': {'name': 'Project Messages', 'cost_per_unit': 0.015}
        },
        'sample_data': {
            'email': 'user@company.com',
            'name': 'John Doe',
            'department': '["engineering"]',
            'period_start': '2025-01-01',
            'messages': 100,
            'tool_messages': 50,
            'project_messages': 25
        }
    },
    'BlueFlame AI': {
        'display_name': 'BlueFlame AI',
        'icon': '🔥',
        'columns': {
            'user_id': ['user_id'],
            'user_name': ['full_name', 'name'],
            'department': ['team', 'department'],
            'date': ['date', 'usage_date'],
            'chat_interactions': ['chat_interactions'],
            'api_calls': ['api_calls'],
            'total_tokens': ['total_tokens']
        },
        'features': {
            'chat_interactions': {'name': 'Chat Interactions', 'cost_per_unit': 0.025},
            'api_calls': {'name': 'API Calls', 'cost_per_unit': 0.015},
            'total_tokens': {'name': 'Total Tokens', 'cost_per_unit': 0.00001}
        },
        'sample_data': {
            'user_id': 'user123',
            'full_name': 'Jane Smith',
            'team': 'Analytics',
            'date': '2025-01-01',
            'chat_interactions': 75,
            'api_calls': 120,
            'total_tokens': 50000
        }
    },
    'Anthropic': {
        'display_name': 'Anthropic',
        'icon': '🎭',
        'columns': {
            'user_id': ['user_email', 'email'],
            'user_name': ['username', 'name'],
            'department': ['org_unit', 'department'],
            'date': ['date', 'usage_date'],
            'claude_messages': ['claude_messages', 'messages'],
            'tokens_used': ['tokens_used'],
            'cost_estimate': ['cost_estimate', 'cost']
        },
        'features': {
            'claude_messages': {'name': 'Claude Messages', 'cost_per_unit': 0.03},
            'tokens_used': {'name': 'Tokens Used', 'cost_per_unit': 0.000015},
        },
        'sample_data': {
            'user_email': 'user@company.com',
            'username': 'Alex Johnson',
            'org_unit': 'Research',
            'date': '2025-01-01',
            'claude_messages': 90,
            'tokens_used': 45000,
            'cost_estimate': 2.7
        }
    }
}

# Expected CSV columns mapping (legacy support)
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