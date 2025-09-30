 # AI Usage Metrics Dashboard (Multi-Provider)

A lightweight Streamlit application for exploring usage metrics from multiple AI providers. Upload monthly CSV metrics to generate dashboards that highlight adoption trends, top users, and day-to-day activity.

## Supported Providers

- **🤖 OpenAI (ChatGPT)** - Enterprise workspace exports
- **🔥 BlueFlame AI** - Usage analytics
- **🧠 Anthropic (Claude)** - Enterprise usage data

## Getting started

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
3. Launch the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```

The app stores uploaded data in a local SQLite database. Upload monthly exports for any supported provider to track usage over time. Data from different providers is segregated and can be viewed independently using the provider selector in the sidebar.

## Features

- **Multi-Provider Support**: Switch between different AI providers using the dropdown selector
- **Provider-Specific Data Processing**: Each provider has its own data format and cost model
- **Automatic Data Normalization**: Flexible column-name matching for CSV exports
- **Month-over-Month Summaries**: Track requests, tokens, costs, and active user counts
- **User-Level Breakdowns**: Detailed usage metrics per user with activity tracking
- **Trend Analysis**: Identify the largest increases or decreases in usage
- **Time-Series Visualizations**: Daily/weekly/monthly charts with optional rolling averages
- **Cost Calculation**: Provider-specific pricing models with detailed breakdowns
- **Database Management**: Upload history, data cleanup, and backup functionality

## Adding a New Provider

To add support for a new AI provider, follow these steps:

### 1. Update `config.py`

Add a new provider configuration to the `PROVIDERS` dictionary:

```python
'your_provider': {
    'name': 'Your Provider',
    'icon': '🎯',  # Choose an emoji icon
    'display_name': 'Your Provider Name',
    'column_mapping': {
        'user_id': 'email_column_name',
        'user_name': 'name_column_name',
        'department': 'team_column_name',
        'date': 'date_column_name',
        # Add other field mappings as needed
    },
    'features': {
        'feature_1': {
            'name': 'Feature Display Name',
            'cost_per_unit': 0.02  # Cost per usage unit
        },
        # Add more features as needed
    },
    'sample_format': {
        'columns': ['col1', 'col2', 'col3'],
        'example': 'sample,data,row'
    }
}
```

### 2. Update `data_processor.py`

Add a new cleaning method for your provider:

```python
def clean_your_provider_data(self, df, filename):
    """Clean Your Provider usage data format."""
    try:
        provider_config = config.PROVIDERS['your_provider']
        processed_data = []
        
        for _, row in df.iterrows():
            # Extract data based on your provider's format
            # Create records for each feature
            records.append({
                'user_id': ...,
                'user_name': ...,
                'department': ...,
                'date': ...,
                'feature_used': ...,
                'usage_count': ...,
                'cost_usd': ...,
                'created_at': datetime.now().isoformat(),
                'file_source': filename,
                'provider': 'your_provider'
            })
            processed_data.extend(records)
        
        return pd.DataFrame(processed_data)
    except Exception as e:
        print(f"Error in clean_your_provider_data: {str(e)}")
        return pd.DataFrame()
```

### 3. Update the `process_monthly_data` method

Add your provider to the processing logic:

```python
elif provider == 'your_provider':
    processed_df = self.clean_your_provider_data(df, filename)
```

That's it! Your new provider will now appear in the dropdown selector and work with the full analytics dashboard.

## Data Format Examples

### OpenAI Format
```csv
email,name,department,period_start,messages,tool_messages,project_messages
user@company.com,John Doe,["engineering"],2025-01-01,150,25,10
```

### BlueFlame AI Format
```csv
user_id,full_name,team,period_start,chat_interactions,api_calls,total_tokens
user123,Jane Smith,Analytics,2025-01-01,200,50,150000
```

### Anthropic Format
```csv
user_email,username,org_unit,period_start,claude_messages,tokens_used,cost_estimate
user@company.com,Alex Johnson,Marketing,2025-01-01,180,120000,4.50
```
