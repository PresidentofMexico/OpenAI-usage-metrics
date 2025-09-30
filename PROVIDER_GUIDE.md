# Multi-Provider Analytics Dashboard

## Adding New Providers

This guide explains how to add support for a new AI provider to the analytics dashboard.

### Overview

The dashboard supports multiple AI providers through a flexible configuration system. Currently supported providers:
- **OpenAI** - ChatGPT, Tool Messages, Project Messages
- **BlueFlame AI** - Chat Interactions, API Calls, Token Usage
- **Anthropic** - Claude Messages, Token Usage

### Steps to Add a New Provider

#### 1. Update Configuration (`config.py`)

Add a new entry to the `PROVIDERS` dictionary:

```python
PROVIDERS = {
    # ... existing providers ...
    'your_provider_id': {
        'name': 'ProviderName',
        'icon': '🔮',  # Choose an emoji icon
        'display_name': 'Provider Display Name',
        'column_mapping': {
            'user_id': 'csv_column_for_user_id',
            'user_name': 'csv_column_for_user_name',
            'department': 'csv_column_for_department',
            'date': 'csv_column_for_date',
        },
        'usage_columns': {
            'csv_usage_column_1': {
                'feature': 'Feature Display Name',
                'cost_per_unit': 0.02  # Cost calculation per unit
            },
            'csv_usage_column_2': {
                'feature': 'Another Feature',
                'cost_per_unit': 0.01
            },
        },
        'sample_format': {
            'csv_column_1': 'sample_value_1',
            'csv_column_2': 'sample_value_2',
            # ... all expected columns with sample values
        }
    }
}
```

**Key Fields Explained:**
- `name`: Internal identifier
- `icon`: Emoji shown in UI
- `display_name`: User-facing name
- `column_mapping`: Maps standard fields to CSV column names
- `usage_columns`: Defines which columns contain usage metrics and their cost models
- `sample_format`: Example CSV format shown to users

#### 2. Implement Data Processor (`data_processor.py`)

Add a new cleaning method in the `DataProcessor` class:

```python
def clean_your_provider_data(self, df, filename):
    """Clean YourProvider usage data format."""
    try:
        provider_config = config.PROVIDERS['your_provider_id']
        processed_data = []
        
        for _, row in df.iterrows():
            # Extract basic info using provider column mapping
            user_id = row.get(provider_config['column_mapping']['user_id'], 'unknown')
            user_name = row.get(provider_config['column_mapping']['user_name'], 'Unknown User')
            department = row.get(provider_config['column_mapping']['department'], 'Unknown')
            date = row.get(provider_config['column_mapping']['date'], datetime.now().strftime('%Y-%m-%d'))
            
            # Process each usage column
            for col_name, col_config in provider_config['usage_columns'].items():
                usage_value = row.get(col_name, 0)
                if pd.notna(usage_value) and usage_value > 0:
                    processed_data.append({
                        'user_id': str(user_id),
                        'user_name': str(user_name),
                        'department': str(department),
                        'date': str(date),
                        'feature_used': col_config['feature'],
                        'usage_count': int(usage_value),
                        'cost_usd': float(usage_value) * col_config['cost_per_unit'],
                        'created_at': datetime.now().isoformat(),
                        'file_source': filename
                    })
        
        return pd.DataFrame(processed_data)
        
    except Exception as e:
        print(f"Error in clean_your_provider_data: {str(e)}")
        return pd.DataFrame()
```

#### 3. Register Provider in Process Method

Update the `process_monthly_data` method to handle the new provider:

```python
def process_monthly_data(self, df, filename, provider='openai'):
    """Process uploaded monthly data for specified provider."""
    try:
        # ... existing code ...
        
        # Clean the data based on provider format
        if provider == 'openai':
            processed_df = self.clean_openai_data(df, filename)
        elif provider == 'blueflame':
            processed_df = self.clean_blueflame_data(df, filename)
        elif provider == 'anthropic':
            processed_df = self.clean_anthropic_data(df, filename)
        elif provider == 'your_provider_id':  # Add this
            processed_df = self.clean_your_provider_data(df, filename)
        else:
            return False, f"Unsupported provider: {provider}"
        
        # ... rest of the code ...
```

### Testing Your Provider

1. **Create test data** matching your provider's CSV format:
```python
test_data = pd.DataFrame([{
    'csv_column_1': 'value1',
    'csv_column_2': 'value2',
    # ... all required columns
}])
```

2. **Test data processing**:
```python
from data_processor import DataProcessor
from database import DatabaseManager

db = DatabaseManager()
processor = DataProcessor(db)

success, message = processor.process_monthly_data(
    test_data, 
    'test.csv', 
    provider='your_provider_id'
)
print(f"Success: {success}, Message: {message}")
```

3. **Verify in database**:
```python
data = db.get_all_data(provider='your_provider_id')
print(f"Records: {len(data)}")
print(data.head())
```

### Provider-Specific Best Practices

1. **Column Mapping**: Use exact column names from the provider's export format
2. **Cost Calculation**: Verify cost per unit with provider's pricing documentation
3. **Data Validation**: Handle missing or null values gracefully
4. **Date Format**: Ensure dates are in 'YYYY-MM-DD' format
5. **Department Field**: Handle various department formats (arrays, strings, etc.)

### Example: Complete Provider Configuration

Here's a complete example for a fictional "AI Cloud" provider:

```python
'aicloud': {
    'name': 'AI Cloud',
    'icon': '☁️',
    'display_name': 'AI Cloud Services',
    'column_mapping': {
        'user_id': 'employee_email',
        'user_name': 'employee_name',
        'department': 'division',
        'date': 'report_date',
    },
    'usage_columns': {
        'llm_queries': {'feature': 'LLM Queries', 'cost_per_unit': 0.025},
        'embeddings_count': {'feature': 'Embeddings', 'cost_per_unit': 0.0001},
        'fine_tuning_hours': {'feature': 'Fine Tuning', 'cost_per_unit': 5.00},
    },
    'sample_format': {
        'employee_email': 'user@company.com',
        'employee_name': 'John Doe',
        'division': 'Engineering',
        'report_date': '2024-01-01',
        'llm_queries': 500,
        'embeddings_count': 10000,
        'fine_tuning_hours': 2
    }
}
```

### Troubleshooting

**Issue**: Provider doesn't appear in dropdown
- **Solution**: Check that provider ID is added to `PROVIDERS` in `config.py`

**Issue**: Data not processing correctly
- **Solution**: Verify column names match exactly in `column_mapping`

**Issue**: Cost calculations are wrong
- **Solution**: Review `cost_per_unit` values in `usage_columns`

**Issue**: Provider shows no data
- **Solution**: Ensure `provider` parameter is passed correctly and database has records with matching provider value

### Database Schema

All provider data is stored in the same `usage_metrics` table with a `provider` column:

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
    provider TEXT DEFAULT 'openai'
)
```

The dashboard automatically filters data by provider when displaying analytics.
