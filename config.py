"""
Configuration settings for AI Usage Metrics Dashboard
Multi-Provider Support: OpenAI, BlueFlame AI, Anthropic, Google AI
"""
import os

# Database settings
DATABASE_PATH = "data/openai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Supported providers
SUPPORTED_PROVIDERS = [
    "OpenAI",
    "BlueFlame AI", 
    "Anthropic",
    "Google AI",
    "Custom"
]

# Provider-specific configurations
PROVIDER_CONFIGS = {
    'OpenAI': {
        'color': '#1f77b4',
        'icon': '🤖',
        'column_mapping': {
            'user_id': ['email', 'user_id', 'user_email'],
            'user_name': ['name', 'user_name', 'display_name'],
            'department': ['department', 'dept', 'team'],
            'date': ['period_start', 'date', 'usage_date'],
            'messages': ['messages'],
            'tool_messages': ['tool_messages'],
            'project_messages': ['project_messages']
        },
        'cost_model': {
            'ChatGPT Messages': 0.02,
            'Tool Messages': 0.01,
            'Project Messages': 0.015
        },
        'sample_format': {
            'email': 'user@company.com',
            'name': 'John Doe',
            'department': 'Engineering',
            'period_start': '2024-01-01',
            'messages': 150,
            'tool_messages': 25,
            'project_messages': 10
        }
    },
    'BlueFlame AI': {
        'color': '#ff7f0e',
        'icon': '🔥',
        'column_mapping': {
            'user_id': ['user_id', 'email'],
            'user_name': ['username', 'user_name', 'name'],
            'department': ['team', 'department', 'dept'],
            'date': ['date', 'usage_date'],
            'queries': ['queries', 'query_count'],
            'api_calls': ['api_calls', 'calls'],
            'tokens_used': ['tokens_used', 'tokens'],
            'cost': ['cost', 'cost_usd']
        },
        'cost_model': {
            'API Calls': 0.001,
            'Queries': 0.01
        },
        'sample_format': {
            'user_id': 'user123',
            'username': 'john.doe',
            'team': 'Engineering',
            'date': '2024-01-01',
            'queries': 75,
            'api_calls': 125,
            'tokens_used': 45000,
            'cost': 12.50
        }
    },
    'Anthropic': {
        'color': '#2ca02c',
        'icon': '🧠',
        'column_mapping': {
            'user_id': ['email', 'user_id'],
            'user_name': ['full_name', 'name', 'user_name'],
            'department': ['department', 'team', 'dept'],
            'date': ['usage_date', 'date'],
            'claude_messages': ['claude_messages', 'messages'],
            'api_requests': ['api_requests', 'requests'],
            'total_cost': ['total_cost', 'cost', 'cost_usd']
        },
        'cost_model': {
            'Claude Messages': 0.015,
            'API Requests': 0.02
        },
        'sample_format': {
            'email': 'user@company.com',
            'full_name': 'John Doe',
            'department': 'Engineering',
            'usage_date': '2024-01-01',
            'claude_messages': 100,
            'api_requests': 50,
            'total_cost': 15.75
        }
    },
    'Google AI': {
        'color': '#d62728',
        'icon': '🔍',
        'column_mapping': {
            'user_id': ['email', 'user_id', 'user_email'],
            'user_name': ['name', 'user_name', 'display_name'],
            'department': ['department', 'team', 'org'],
            'date': ['date', 'usage_date', 'timestamp'],
            'gemini_requests': ['gemini_requests', 'requests'],
            'api_calls': ['api_calls', 'calls'],
            'tokens': ['tokens', 'token_count'],
            'cost': ['cost', 'cost_usd', 'total_cost']
        },
        'cost_model': {
            'Gemini Requests': 0.0125,
            'API Calls': 0.01
        },
        'sample_format': {
            'email': 'user@company.com',
            'name': 'John Doe',
            'department': 'Engineering',
            'date': '2024-01-01',
            'gemini_requests': 80,
            'api_calls': 120,
            'tokens': 50000,
            'cost': 14.25
        }
    },
    'Custom': {
        'color': '#9467bd',
        'icon': '⚙️',
        'column_mapping': {
            'user_id': ['user_id', 'email', 'user_email'],
            'user_name': ['user_name', 'name', 'display_name'],
            'department': ['department', 'dept', 'team'],
            'date': ['date', 'usage_date', 'timestamp'],
            'feature_used': ['feature_used', 'feature', 'service'],
            'usage_count': ['usage_count', 'count', 'interactions'],
            'cost_usd': ['cost_usd', 'cost', 'price']
        },
        'cost_model': {
            'General Usage': 0.01
        },
        'sample_format': {
            'user_id': 'user@company.com',
            'user_name': 'John Doe',
            'department': 'Engineering',
            'date': '2024-01-01',
            'feature_used': 'Custom Feature',
            'usage_count': 100,
            'cost_usd': 10.00
        }
    }
}

# Default values for missing data
DEFAULT_VALUES = {
    'department': 'Unknown',
    'feature_used': 'General',
    'usage_count': 1,
    'cost_usd': 0.0
}