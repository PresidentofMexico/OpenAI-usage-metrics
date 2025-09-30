 # AI Usage Metrics Dashboard

A powerful multi-provider analytics dashboard for tracking and analyzing AI service usage across your organization. Supports OpenAI, BlueFlame AI, Anthropic, Google AI, and custom providers.

## 🎯 Features

### Multi-Provider Support
- **OpenAI** - Track ChatGPT, Tool, and Project messages
- **BlueFlame AI** - Monitor queries and API calls
- **Anthropic** - Analyze Claude messages and API requests
- **Google AI** - Track Gemini requests and API usage
- **Custom** - Flexible format support for any AI provider

### Analytics & Insights
- **Provider Bifurcation** - Filter and analyze data by specific AI provider
- **Usage Trends** - Daily usage and cost visualization
- **User Analysis** - Top users and department breakdowns
- **Cost Tracking** - Provider-specific cost models and transparency
- **Data Quality** - Automated quality checks and validation
- **Growth Metrics** - Month-over-month usage analysis

### Dashboard Features
- Month-over-month summaries of requests, tokens, cost and active user counts
- User-level breakdowns with active day counts per selected month
- Trend analysis that highlights the largest increases or decreases in usage
- Daily/weekly/monthly time-series visualizations
- Export capabilities for filtered data and summary reports

## 🚀 Getting Started

1. Create and activate a Python 3.10+ virtual environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```

## 📊 Supported Data Formats

### OpenAI Format
```csv
email,name,department,period_start,messages,tool_messages,project_messages
user@company.com,John Doe,Engineering,2024-01-01,150,25,10
```

### BlueFlame AI Format
```csv
user_id,username,team,date,queries,api_calls,tokens_used,cost
user123,john.doe,eng,2024-01-01,75,125,45000,12.50
```

### Anthropic Format
```csv
email,full_name,department,usage_date,claude_messages,api_requests,total_cost
user@company.com,John Doe,Engineering,2024-01-01,100,50,15.75
```

### Google AI Format
```csv
email,name,department,date,gemini_requests,api_calls,tokens,cost
user@company.com,John Doe,Engineering,2024-01-01,80,120,50000,14.25
```

See the `sample_data/` directory for example files you can use to test each provider.

## 🔧 Usage

1. **Select Provider** - Choose your AI provider from the dropdown in the sidebar
2. **Upload Data** - Upload your monthly CSV export file
3. **View Analytics** - Explore usage metrics, costs, and trends
4. **Filter Data** - Use date range, user, and department filters
5. **Export Results** - Download filtered data or summary reports

### Switching Providers

The dashboard automatically filters all analytics based on the selected provider:
- Data uploads are tagged with the selected provider
- Analytics show only data for the selected provider
- Use "All Providers" to see combined metrics across all providers

## 📁 Data Storage

The dashboard uses SQLite to store uploaded data with automatic provider tagging:
- Existing OpenAI data is automatically migrated
- New uploads are tagged with the selected provider
- Data persists across sessions
- Manage uploads via the "Database Management" tab

## 🎨 Customization

### Adding a New Provider

1. Update `config.py` with provider configuration:
```python
'Your Provider': {
    'color': '#hexcolor',
    'icon': '🎯',
    'column_mapping': {...},
    'cost_model': {...},
    'sample_format': {...}
}
```

2. Add processor method in `data_processor.py`:
```python
def clean_yourprovider_data(self, df, filename, provider='Your Provider'):
    # Process your provider's CSV format
    ...
```

3. Update the routing in `process_monthly_data()` method

### Column Aliases

If your export uses different column names, you can extend the column mappings in `config.py`:

```python
PROVIDER_CONFIGS['Your Provider']['column_mapping'] = {
    'user_id': ['user_id', 'email', 'userid', 'user_email'],
    'user_name': ['user_name', 'name', 'username', 'display_name'],
    # ... add more aliases
}
```

## 📈 Cost Models

Each provider has configurable cost models defined in `config.py`. Costs are automatically calculated based on usage:

- **OpenAI**: Per-message pricing for different message types
- **BlueFlame AI**: Per-query and per-API-call pricing  
- **Anthropic**: Per-message and per-request pricing
- **Google AI**: Per-request and per-API-call pricing

Update cost models in `config.py` to match your actual pricing.

## 🔐 Data Privacy

- All data is stored locally in SQLite
- No external API calls or data transmission
- Suitable for sensitive enterprise usage data

## 📝 Version History

### v3.0 - Multi-Provider Support
- Added support for multiple AI providers
- Provider-specific data processing and analytics
- Provider selection dropdown
- Database migration for existing data
- Provider-aware cost calculations

### v2.1 - Enhanced Analytics
- Cost transparency and calculations
- Data quality checks
- Database management interface
- Improved analytics

### v1.0 - Initial Release
- OpenAI usage tracking
- Basic analytics dashboard
