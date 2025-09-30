# Adding New Providers to Multi-Provider Analytics Dashboard

This guide explains how to add support for a new AI provider to the dashboard.

## Overview

The dashboard supports multiple AI providers through a configuration-based approach. Adding a new provider requires updating the configuration file only - no code changes needed!

## Steps to Add a New Provider

### 1. Update `config.py`

Add a new entry to the `PROVIDERS` dictionary in `config.py`:

```python
PROVIDERS = {
    # ... existing providers ...
    
    'Your Provider Name': {
        'display_name': 'Your Provider Name',
        'icon': '🚀',  # Choose an appropriate emoji
        'columns': {
            # Map your CSV columns to internal field names
            'user_id': ['user_id_column', 'email_column'],  # List possible column names
            'user_name': ['name_column', 'full_name_column'],
            'department': ['dept_column', 'team_column'],
            'date': ['date_column', 'usage_date'],
            # Add your provider-specific feature columns
            'feature1': ['feature1_column'],
            'feature2': ['feature2_column'],
        },
        'features': {
            # Define each feature with display name and cost per unit
            'feature1': {'name': 'Feature 1 Display Name', 'cost_per_unit': 0.02},
            'feature2': {'name': 'Feature 2 Display Name', 'cost_per_unit': 0.01},
        },
        'sample_data': {
            # Provide a sample row for the "Expected Data Format" display
            'user_id_column': 'user@example.com',
            'name_column': 'John Doe',
            'dept_column': 'Engineering',
            'date_column': '2025-01-01',
            'feature1_column': 100,
            'feature2_column': 50,
        }
    }
}
```

### 2. Create a Data Processor Method

Add a new method to the `DataProcessor` class in `data_processor.py`:

```python
def clean_yourprovider_data(self, df, filename, provider='Your Provider Name'):
    """Clean Your Provider usage data format."""
    try:
        processed_data = []
        
        for _, row in df.iterrows():
            # Extract basic info using the column mappings from config
            user_id = row.get('user_id_column', 'unknown')
            user_name = row.get('name_column', 'Unknown User')
            department = row.get('dept_column', 'Unknown')
            date = row.get('date_column', '2025-01-01')
            
            records = []
            
            # Process Feature 1
            feature1 = row.get('feature1_column', 0)
            if pd.notna(feature1) and feature1 > 0:
                records.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'department': department,
                    'date': date,
                    'feature_used': 'Feature 1 Display Name',
                    'usage_count': int(feature1),
                    'cost_usd': float(feature1) * 0.02,  # Use cost from config
                    'created_at': datetime.now().isoformat(),
                    'file_source': filename,
                    'provider': provider
                })
            
            # Process Feature 2
            feature2 = row.get('feature2_column', 0)
            if pd.notna(feature2) and feature2 > 0:
                records.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'department': department,
                    'date': date,
                    'feature_used': 'Feature 2 Display Name',
                    'usage_count': int(feature2),
                    'cost_usd': float(feature2) * 0.01,  # Use cost from config
                    'created_at': datetime.now().isoformat(),
                    'file_source': filename,
                    'provider': provider
                })
            
            processed_data.extend(records)
        
        return pd.DataFrame(processed_data)
        
    except Exception as e:
        print(f"Error in clean_yourprovider_data: {str(e)}")
        return pd.DataFrame()
```

### 3. Update the Process Method

Add your provider to the `process_monthly_data` method in `data_processor.py`:

```python
def process_monthly_data(self, df, filename, provider='OpenAI'):
    """Process uploaded monthly data for any provider."""
    try:
        # ... existing code ...
        
        # Add your provider here
        if provider == 'OpenAI':
            processed_df = self.clean_openai_data(df, filename, provider)
        elif provider == 'BlueFlame AI':
            processed_df = self.clean_blueflame_data(df, filename, provider)
        elif provider == 'Anthropic':
            processed_df = self.clean_anthropic_data(df, filename, provider)
        elif provider == 'Your Provider Name':
            processed_df = self.clean_yourprovider_data(df, filename, provider)
        else:
            return False, f"Unsupported provider: {provider}"
        
        # ... rest of the method ...
```

## Configuration Details

### Column Mappings

The `columns` section maps your CSV column names to internal field names. The system will look for any of the column names in the list (from left to right) in the uploaded CSV.

**Required fields:**
- `user_id`: User identifier (email, username, etc.)
- `user_name`: Display name for the user
- `department`: Department or team name
- `date`: Usage date

**Optional fields:**
- Any provider-specific feature columns

### Features Configuration

Each feature should specify:
- `name`: Display name shown in charts and reports
- `cost_per_unit`: Cost multiplier per usage unit

### Sample Data

Provide a representative sample row that matches your CSV format. This will be displayed to users in the "Expected Data Format" section.

## Testing Your Provider

1. **Create test data**: Create a CSV file with your provider's format
2. **Upload via UI**: Use the provider dropdown to select your provider
3. **Upload test file**: Upload your test CSV and verify processing
4. **Check dashboard**: Ensure metrics and charts display correctly
5. **Verify database**: Check that data is properly tagged with your provider name

## Example: Adding Google AI

```python
'Google AI': {
    'display_name': 'Google AI',
    'icon': '🔵',
    'columns': {
        'user_id': ['email', 'user_email'],
        'user_name': ['display_name', 'name'],
        'department': ['organization', 'dept'],
        'date': ['timestamp', 'date'],
        'gemini_requests': ['gemini_requests'],
        'palm_requests': ['palm_requests'],
        'total_tokens': ['tokens_consumed'],
    },
    'features': {
        'gemini_requests': {'name': 'Gemini Requests', 'cost_per_unit': 0.025},
        'palm_requests': {'name': 'PaLM Requests', 'cost_per_unit': 0.020},
        'total_tokens': {'name': 'Total Tokens', 'cost_per_unit': 0.00002},
    },
    'sample_data': {
        'email': 'user@company.com',
        'display_name': 'Jane Doe',
        'organization': 'Research',
        'timestamp': '2025-01-15',
        'gemini_requests': 200,
        'palm_requests': 100,
        'tokens_consumed': 50000,
    }
}
```

## Best Practices

1. **Use descriptive icons**: Choose emoji that represents your provider
2. **Flexible column mappings**: Provide multiple possible column names for flexibility
3. **Accurate cost models**: Use realistic cost-per-unit values
4. **Representative samples**: Ensure sample data shows typical usage patterns
5. **Test thoroughly**: Upload real data to verify all features work correctly

## Database Schema

All provider data is stored in the same `usage_metrics` table with the following schema:

```sql
CREATE TABLE usage_metrics (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    user_name TEXT,
    department TEXT,
    date TEXT,
    feature_used TEXT,
    usage_count INTEGER,
    cost_usd REAL,
    created_at TEXT,
    file_source TEXT,
    provider TEXT DEFAULT 'OpenAI'
);
```

The `provider` column ensures data from different providers is kept separate while using the same storage structure.

## Troubleshooting

**Issue**: Provider doesn't appear in dropdown
- **Solution**: Verify provider is added to `PROVIDERS` dict in `config.py`

**Issue**: Upload fails with "Unsupported provider"
- **Solution**: Check that provider name in `process_monthly_data` matches exactly

**Issue**: No data shows after upload
- **Solution**: Verify column mappings match your CSV column names

**Issue**: Incorrect costs calculated
- **Solution**: Review `cost_per_unit` values in features configuration

## Support

For questions or issues adding new providers, please open an issue on GitHub.
