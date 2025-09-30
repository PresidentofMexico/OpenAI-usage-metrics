"""
Configuration settings for Multi-Provider Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Provider configurations
PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'icon': '🤖',
        'display_name': 'OpenAI (ChatGPT)',
        'column_mapping': {
            'user_id': 'email',
            'user_name': 'name',
            'department': 'department',
            'date': 'period_start',
            'messages': 'messages',
            'tool_messages': 'tool_messages',
            'project_messages': 'project_messages'
        },
        'features': {
            'messages': {
                'name': 'ChatGPT Messages',
                'cost_per_unit': 0.02
            },
            'tool_messages': {
                'name': 'Tool Messages',
                'cost_per_unit': 0.01
            },
            'project_messages': {
                'name': 'Project Messages',
                'cost_per_unit': 0.015
            }
        },
        'sample_format': {
            'columns': ['email', 'name', 'department', 'period_start', 'messages', 'tool_messages', 'project_messages'],
            'example': 'user@company.com, John Doe, ["engineering"], 2025-01-01, 150, 25, 10'
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
            'date': 'period_start',
            'chat_interactions': 'chat_interactions',
            'api_calls': 'api_calls',
            'total_tokens': 'total_tokens'
        },
        'features': {
            'chat_interactions': {
                'name': 'Chat Interactions',
                'cost_per_unit': 0.018
            },
            'api_calls': {
                'name': 'API Calls',
                'cost_per_unit': 0.012
            },
            'total_tokens': {
                'name': 'Token Usage',
                'cost_per_unit': 0.00001  # Per token
            }
        },
        'sample_format': {
            'columns': ['user_id', 'full_name', 'team', 'period_start', 'chat_interactions', 'api_calls', 'total_tokens'],
            'example': 'user123, Jane Smith, Analytics, 2025-01-01, 200, 50, 150000'
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
            'date': 'period_start',
            'claude_messages': 'claude_messages',
            'tokens_used': 'tokens_used',
            'cost_estimate': 'cost_estimate'
        },
        'features': {
            'claude_messages': {
                'name': 'Claude Messages',
                'cost_per_unit': 0.025
            },
            'tokens_used': {
                'name': 'Tokens Used',
                'cost_per_unit': 0.00001  # Per token
            }
        },
        'sample_format': {
            'columns': ['user_email', 'username', 'org_unit', 'period_start', 'claude_messages', 'tokens_used', 'cost_estimate'],
            'example': 'user@company.com, Alex Johnson, Marketing, 2025-01-01, 180, 120000, 4.50'
        }
    }
}

# Expected CSV columns mapping (legacy - kept for backward compatibility)
CSV_COLUMN_MAPPING = {
    'user_id': ['user_id', 'email', 'user_email'],
    'user_name': ['user_name', 'name', 'display_name', 'full_name', 'username'],
    'department': ['department', 'dept', 'team', 'org_unit'],
    'date': ['date', 'usage_date', 'timestamp', 'period_start'],
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