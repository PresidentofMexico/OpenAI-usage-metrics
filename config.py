"""
Configuration settings for Multi-Provider Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "Multi-Provider Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Provider configurations
PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'icon': '🤖',
        'display_name': 'OpenAI',
        'column_mapping': {
            'user_id': 'email',
            'user_name': 'name',
            'department': 'department',
            'date': 'period_start',
        },
        'usage_columns': {
            'messages': {'feature': 'ChatGPT Messages', 'cost_per_unit': 0.02},
            'tool_messages': {'feature': 'Tool Messages', 'cost_per_unit': 0.01},
            'project_messages': {'feature': 'Project Messages', 'cost_per_unit': 0.015},
        },
        'sample_format': {
            'email': 'user@company.com',
            'name': 'John Doe',
            'department': '["Engineering"]',
            'period_start': '2024-01-01',
            'messages': 100,
            'tool_messages': 50,
            'project_messages': 25
        }
    },
    'blueflame': {
        'name': 'BlueFlame AI',
        'icon': '🔥',
        'display_name': 'BlueFlame AI',
        'column_mapping': {
            'user_id': 'user_id',
            'user_name': 'full_name',
            'department': 'team',
            'date': 'usage_date',
        },
        'usage_columns': {
            'chat_interactions': {'feature': 'Chat Interactions', 'cost_per_unit': 0.025},
            'api_calls': {'feature': 'API Calls', 'cost_per_unit': 0.015},
            'total_tokens': {'feature': 'Total Tokens', 'cost_per_unit': 0.00001},
        },
        'sample_format': {
            'user_id': 'user123',
            'full_name': 'Jane Smith',
            'team': 'Marketing',
            'usage_date': '2024-01-01',
            'chat_interactions': 150,
            'api_calls': 200,
            'total_tokens': 50000
        }
    },
    'anthropic': {
        'name': 'Anthropic',
        'icon': '🧠',
        'display_name': 'Anthropic (Claude)',
        'column_mapping': {
            'user_id': 'user_email',
            'user_name': 'username',
            'department': 'org_unit',
            'date': 'usage_date',
        },
        'usage_columns': {
            'claude_messages': {'feature': 'Claude Messages', 'cost_per_unit': 0.03},
            'tokens_used': {'feature': 'Tokens Used', 'cost_per_unit': 0.00002},
        },
        'sample_format': {
            'user_email': 'user@company.com',
            'username': 'Bob Johnson',
            'org_unit': 'Research',
            'usage_date': '2024-01-01',
            'claude_messages': 75,
            'tokens_used': 30000,
            'cost_estimate': 2.25
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