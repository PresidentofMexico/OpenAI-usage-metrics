"""
Sample data schemas for different AI providers
"""

PROVIDER_SCHEMAS = {
    'OpenAI': {
        'description': 'OpenAI Enterprise workspace export format',
        'sample_columns': [
            'email',           # User email address
            'name',            # User display name  
            'department',      # User department (JSON array format)
            'period_start',    # Usage period start date
            'messages',        # Number of ChatGPT messages
            'tool_messages',   # Number of tool-assisted messages
            'project_messages' # Number of project-specific messages
        ],
        'sample_data': {
            'email': 'john.doe@company.com',
            'name': 'John Doe',
            'department': '["engineering"]',
            'period_start': '2024-01-01',
            'messages': 150,
            'tool_messages': 25,
            'project_messages': 10
        }
    },
    
    'BlueFlame AI': {
        'description': 'BlueFlame AI usage export format',
        'sample_columns': [
            'user_email',      # User email address
            'full_name',       # User full name
            'team',           # User team/department  
            'usage_date',     # Date of usage
            'total_queries',  # Total queries made
            'api_calls'       # API calls made
        ],
        'sample_data': {
            'user_email': 'jane.smith@company.com',
            'full_name': 'Jane Smith',
            'team': 'Marketing',
            'usage_date': '2024-01-15',
            'total_queries': 75,
            'api_calls': 12
        }
    },
    
    'Anthropic': {
        'description': 'Anthropic Claude usage export format',
        'sample_columns': [
            'email',          # User email
            'user_name',      # User name
            'department',     # Department
            'date',          # Usage date
            'messages_sent', # Messages sent to Claude
            'tokens_used'    # Total tokens consumed
        ],
        'sample_data': {
            'email': 'bob.wilson@company.com',
            'user_name': 'Bob Wilson',
            'department': 'Research',
            'date': '2024-01-20',
            'messages_sent': 45,
            'tokens_used': 12500
        }
    },
    
    'Google': {
        'description': 'Google AI/Bard usage export format (example)',
        'sample_columns': [
            'user_id',        # User identifier
            'display_name',   # User display name
            'org_unit',      # Organizational unit
            'activity_date', # Date of activity
            'conversations', # Number of conversations
            'api_requests'   # API requests made
        ],
        'sample_data': {
            'user_id': 'alice.brown@company.com',
            'display_name': 'Alice Brown',
            'org_unit': 'Sales', 
            'activity_date': '2024-01-25',
            'conversations': 30,
            'api_requests': 8
        }
    }
}

def get_schema_info(provider):
    """Get schema information for a specific provider."""
    return PROVIDER_SCHEMAS.get(provider, {})

def get_sample_csv_content(provider):
    """Generate sample CSV content for a provider."""
    schema = PROVIDER_SCHEMAS.get(provider, {})
    if not schema:
        return None
    
    columns = schema.get('sample_columns', [])
    sample_data = schema.get('sample_data', {})
    
    # Create CSV header
    csv_content = ','.join(columns) + '\n'
    
    # Create sample row
    sample_row = [str(sample_data.get(col, '')) for col in columns]
    csv_content += ','.join(sample_row) + '\n'
    
    return csv_content