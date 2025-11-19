import os

# Database settings
DATABASE_PATH = "ai_metrics.db"

# Dashboard settings
DASHBOARD_TITLE = "AI Usage Metrics Dashboard"
DASHBOARD_ICON = "📊"

# Folder settings
AUTO_SCAN_FOLDERS = [
    "OpenAI User Data",
    "BlueFlame User Data",
    "data/uploads"
]

RECURSIVE_SCAN_FOLDERS = [
    "OpenAI User Data"
]

FILE_TRACKING_PATH = "file_tracking.json"

# ROI Settings
ROI_HOURLY_VALUE = 50  # USD per hour saved
ROI_MONTHLY_WORK_HOURS = 160

# Provider configurations
PROVIDERS = {
    'OpenAI': {
        'name': 'OpenAI',
        'color': '#00A67E',
        'features': ['ChatGPT Messages', 'Tool Messages', 'Project Messages']
    },
    'BlueFlame AI': {
        'name': 'BlueFlame AI',
        'color': '#FF6B35',
        'features': ['BlueFlame Queries', 'API Calls']
    }
}

# Pricing Model
ENTERPRISE_PRICING = {
    'ChatGPT': {
        'license_cost_per_user_monthly': 60.00,
        'currency': 'USD'
    },
    'BlueFlame AI': {
        'license_cost_per_user_monthly': 125.00,
        'currency': 'USD'
    },
    'OpenAI': { 
        'license_cost_per_user_monthly': 60.00,
        'currency': 'USD'
    }
}

# UI Colors for Styles
THEME = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#065f46',
    'warning': '#92400e',
    'error': '#991b1b',
    'bg_light': '#ffffff',
    'bg_dark': '#1e293b'
}
