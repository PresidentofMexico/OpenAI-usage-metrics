"""
Configuration settings for AI Usage Metrics Dashboard
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Expected CSV columns mapping (legacy - kept for backward compatibility)
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

# ============================================================================
# MULTI-PROVIDER CONFIGURATION
# ============================================================================

# Provider definitions with display information
PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'icon': '🤖',
        'display_name': 'OpenAI (ChatGPT)',
        'description': 'OpenAI ChatGPT and API usage'
    },
    'blueflame': {
        'name': 'BlueFlame AI',
        'icon': '🔥',
        'display_name': 'BlueFlame AI',
        'description': 'BlueFlame AI platform usage'
    },
    'anthropic': {
        'name': 'Anthropic',
        'icon': '🧠',
        'display_name': 'Anthropic (Claude)',
        'description': 'Anthropic Claude usage'
    },
    'google': {
        'name': 'Google',
        'icon': '🔍',
        'display_name': 'Google (Gemini)',
        'description': 'Google Gemini/Bard usage'
    }
}

# Provider-specific schema mappings
PROVIDER_SCHEMAS = {
    'openai': {
        'user_id': ['email'],
        'user_name': ['name'],
        'department': ['department'],
        'date': ['period_start'],
        'usage_columns': {
            'messages': {
                'feature_name': 'ChatGPT Messages',
                'cost_per_unit': 0.02
            },
            'tool_messages': {
                'feature_name': 'Tool Messages',
                'cost_per_unit': 0.01
            },
            'project_messages': {
                'feature_name': 'Project Messages',
                'cost_per_unit': 0.015
            }
        }
    },
    'blueflame': {
        'user_id': ['user_email', 'email'],
        'user_name': ['user_name', 'name'],
        'department': ['team', 'department'],
        'date': ['date', 'usage_date'],
        'usage_columns': {
            'api_calls': {
                'feature_name': 'API Calls',
                'cost_per_unit': 0.01
            },
            'model_requests': {
                'feature_name': 'Model Requests',
                'cost_per_unit': 0.025
            }
        },
        'cost_column': 'total_cost'  # If provider supplies actual cost
    },
    'anthropic': {
        'user_id': ['user_id', 'email'],
        'user_name': ['display_name', 'name'],
        'department': ['organization', 'dept'],
        'date': ['usage_date', 'date'],
        'usage_columns': {
            'claude_messages': {
                'feature_name': 'Claude Messages',
                'cost_per_unit': 0.03
            },
            'api_usage': {
                'feature_name': 'API Usage',
                'cost_per_unit': 0.015
            }
        },
        'cost_column': 'spend_usd'  # If provider supplies actual cost
    },
    'google': {
        'user_id': ['email'],
        'user_name': ['full_name', 'name'],
        'department': ['dept', 'department'],
        'date': ['report_date', 'date'],
        'usage_columns': {
            'gemini_queries': {
                'feature_name': 'Gemini Queries',
                'cost_per_unit': 0.02
            },
            'bard_interactions': {
                'feature_name': 'Bard Interactions',
                'cost_per_unit': 0.015
            }
        },
        'cost_column': 'billing_amount'  # If provider supplies actual cost
    }
}

# Provider detection rules (checks for signature columns)
PROVIDER_DETECTION = {
    'openai': ['messages', 'period_start', 'email'],
    'blueflame': ['api_calls', 'model_requests'],
    'anthropic': ['claude_messages', 'user_id'],
    'google': ['gemini_queries', 'report_date']
}