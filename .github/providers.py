"""
Provider-specific configurations for different AI platforms
"""

PROVIDER_CONFIGS = {
    "OpenAI": {
        "name": "OpenAI",
        "icon": "🤖",
        "color": "#10A37F",
        "column_mapping": {
            'user_id': ['user_id', 'email', 'user_email'],
            'user_name': ['user_name', 'name', 'display_name'],
            'department': ['department', 'dept', 'team'],
            'date': ['date', 'usage_date', 'timestamp', 'period_start'],
            'feature_used': ['feature_used', 'feature', 'service'],
            'usage_count': ['usage_count', 'count', 'interactions', 'messages'],
            'cost_usd': ['cost_usd', 'cost', 'price']
        },
        "cost_model": {
            "ChatGPT Messages": 0.02,
            "Tool Messages": 0.01,
            "Project Messages": 0.015,
            "API Calls": 0.025
        }
    },
    "BlueFlame AI": {
        "name": "BlueFlame AI",
        "icon": "🔥",
        "color": "#FF6B35",
        "column_mapping": {
            'user_id': ['user_email', 'email', 'user_id'],
            'user_name': ['full_name', 'user_name', 'name'],
            'department': ['department', 'division', 'team'],
            'date': ['activity_date', 'date', 'timestamp'],
            'feature_used': ['service_type', 'feature', 'product'],
            'usage_count': ['requests', 'usage_count', 'interactions'],
            'cost_usd': ['total_cost', 'cost_usd', 'billing_amount']
        },
        "cost_model": {
            "AI Assistant": 0.03,
            "Document Analysis": 0.05,
            "Data Processing": 0.04,
            "Custom Models": 0.08
        }
    },
    "Anthropic": {
        "name": "Anthropic",
        "icon": "🧠",
        "color": "#FF9500", 
        "column_mapping": {
            'user_id': ['user_id', 'email'],
            'user_name': ['user_name', 'name'],
            'department': ['department', 'org_unit'],
            'date': ['date', 'usage_date'],
            'feature_used': ['model', 'service'],
            'usage_count': ['requests', 'calls'],
            'cost_usd': ['cost', 'amount']
        },
        "cost_model": {
            "Claude": 0.025,
            "Claude Instant": 0.015
        }
    }
}

def get_provider_list():
    """Get list of available providers"""
    return list(PROVIDER_CONFIGS.keys())

def get_provider_config(provider_name):
    """Get configuration for specific provider"""
    return PROVIDER_CONFIGS.get(provider_name, PROVIDER_CONFIGS["OpenAI"])