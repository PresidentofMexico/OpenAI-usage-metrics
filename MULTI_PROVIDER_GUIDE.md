# Multi-Provider Support Guide

## Overview
The AI Usage Metrics Dashboard now supports multiple AI providers with automatic provider detection and provider-specific analytics. This guide explains how to use multi-provider features and how to add support for new providers.

## Supported Providers

Currently supported providers:

1. **OpenAI (ChatGPT)** 🤖
   - ChatGPT Messages, Tool Messages, Project Messages
   - Default provider for existing data

2. **BlueFlame AI** 🔥
   - API Calls, Model Requests
   - Supports actual cost column if provided

3. **Anthropic (Claude)** 🧠
   - Claude Messages, API Usage
   - Supports actual cost column if provided

4. **Google (Gemini)** 🔍
   - Gemini Queries, Bard Interactions
   - Supports actual cost column if provided

## Using Multi-Provider Features

### Uploading Data

1. Upload your AI provider's CSV export using the file uploader
2. The system automatically detects the provider based on column names
3. Data is processed and tagged with the provider name
4. Success message indicates which provider was detected

### Selecting a Provider

1. Use the **AI Provider** dropdown in the sidebar
2. Select which provider's data you want to analyze
3. Dashboard updates to show only data from the selected provider
4. Provider name is displayed in the analytics section

### Provider Context

- The dashboard shows "Currently analyzing: [Provider Name]" to indicate which provider's data is displayed
- All analytics (costs, usage, trends) are filtered to the selected provider
- Different providers may have different feature types and cost models

## Adding a New Provider

To add support for a new AI provider, follow these steps:

### Step 1: Add Provider Configuration

Edit `config.py` and add your provider to the `PROVIDERS` dictionary:

```python
PROVIDERS = {
    # ... existing providers ...
    'your_provider': {
        'name': 'Your Provider Name',
        'icon': '🎯',  # Choose an emoji icon
        'display_name': 'Your Provider (Product)',
        'description': 'Your provider description'
    }
}
```

### Step 2: Define Provider Schema

Add the schema mapping in `PROVIDER_SCHEMAS`:

```python
PROVIDER_SCHEMAS = {
    # ... existing schemas ...
    'your_provider': {
        # Map standard fields to your CSV columns
        'user_id': ['user_email', 'email'],  # First match wins
        'user_name': ['user_name', 'name'],
        'department': ['team', 'dept', 'department'],
        'date': ['usage_date', 'date'],
        
        # Define usage columns and their cost models
        'usage_columns': {
            'api_calls': {
                'feature_name': 'API Calls',
                'cost_per_unit': 0.01  # Cost per call
            },
            'queries': {
                'feature_name': 'Query Requests',
                'cost_per_unit': 0.02
            }
        },
        
        # Optional: If provider supplies actual cost
        'cost_column': 'actual_cost'  # Column name in CSV
    }
}
```

### Step 3: Add Detection Rules

Add signature columns for automatic detection in `PROVIDER_DETECTION`:

```python
PROVIDER_DETECTION = {
    # ... existing rules ...
    'your_provider': ['signature_column1', 'signature_column2']
}
```

Choose 2-3 unique column names that identify this provider's CSV format.

### Step 4: Test Your Provider

1. Create a sample CSV file with your provider's format
2. Upload it through the dashboard
3. Verify automatic detection works
4. Check that data is processed correctly
5. Confirm cost calculations are accurate

## CSV Format Examples

### BlueFlame AI Format
```csv
user_email,user_name,team,date,api_calls,model_requests,total_cost
john@company.com,John Doe,Engineering,2025-09-01,150,45,5.25
```

### Anthropic Format
```csv
user_id,display_name,organization,usage_date,claude_messages,api_usage,spend_usd
user1@company.com,John Doe,Engineering,2025-09-01,100,50,15.50
```

### Google Format
```csv
email,full_name,dept,report_date,gemini_queries,bard_interactions,billing_amount
john@company.com,John Doe,Engineering,2025-09-01,200,50,9.50
```

## Cost Models

### Estimated Costs (Default)
When a provider doesn't supply actual costs, the system estimates based on `cost_per_unit`:
- Cost = usage_count × cost_per_unit

### Actual Costs (Optional)
If your provider supplies actual costs, specify the `cost_column`:
- The system will use the actual cost from the CSV instead of estimating

## Data Isolation

- Each provider's data is stored separately (tagged with provider name)
- Provider selector ensures complete data isolation
- No cross-provider analytics or comparisons
- Each provider has independent user/department lists

## Troubleshooting

### Provider Not Detected
- Check that signature columns in `PROVIDER_DETECTION` match your CSV exactly
- Column names are case-sensitive
- Ensure at least 2-3 unique columns are present

### Incorrect Cost Calculations
- Verify `cost_per_unit` values in schema configuration
- Check if provider supplies actual cost column
- Review processed data in Database Management tab

### Missing Data
- Ensure all required schema fields have valid mappings
- Check that CSV column names match schema alternatives
- Review error messages during upload

## Advanced Customization

### Custom Data Cleaning
For providers requiring special data processing, add a custom cleaning method in `data_processor.py`:

```python
def clean_your_provider_data(self, df, filename, provider='your_provider'):
    """Clean your provider's usage data format."""
    # Custom processing logic here
    # Return DataFrame with standard columns
    pass
```

Then update `process_monthly_data()` to call your custom method.

### Provider-Specific Features
You can extend the dashboard to show provider-specific metrics or visualizations by checking the selected provider in `app.py`.

## Database Schema

The `usage_metrics` table includes a `provider` column:
- All new records are tagged with provider name
- Existing data defaults to 'openai'
- Database automatically migrates when first run

## Best Practices

1. **Consistent Naming**: Use lowercase provider keys without spaces
2. **Icon Selection**: Choose distinctive emoji icons for easy identification
3. **Cost Accuracy**: Verify cost calculations with provider's actual billing
4. **Testing**: Always test with sample data before production use
5. **Documentation**: Update this guide when adding new providers

## Migration Notes

Existing data in the database is automatically tagged as 'openai' provider during the first run after upgrade. No data loss occurs during migration.
