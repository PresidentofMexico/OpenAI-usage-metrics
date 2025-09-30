 # Multi-Provider AI Usage Metrics Dashboard

A lightweight Streamlit application for exploring AI usage metrics from multiple providers. Upload monthly CSV exports to generate dashboards that highlight adoption trends, top users, and day-to-day activity across different AI platforms.

## Supported Providers

- **OpenAI** - ChatGPT, Tool Messages, Project Messages
- **BlueFlame AI** - Chat Interactions, API Calls, Token Usage  
- **Anthropic (Claude)** - Claude Messages, Token Usage

## Features

- **Multi-Provider Support** - Switch between different AI providers with a dropdown selector
- **Provider-Specific Data Processing** - Automatic handling of different CSV formats and column mappings
- **Cost Analytics** - Provider-specific cost calculations and breakdowns
- **Interactive Dashboards** - Visualize usage trends, top users, and department analytics
- **Database Management** - Store and manage historical data with SQLite
- **Data Quality Checks** - Automatic validation and quality reporting
- **Flexible Configuration** - Easy to add new providers (see PROVIDER_GUIDE.md)

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

## Usage

1. **Select Provider** - Use the dropdown in the sidebar to choose your AI provider
2. **Upload Data** - Upload the monthly CSV export from your provider
3. **View Analytics** - Explore usage metrics, costs, and trends
4. **Filter Data** - Use date range and filters to drill down into specific segments

The app stores uploaded data in an SQLite database. Data is segregated by provider, allowing you to maintain metrics for multiple AI platforms in one dashboard.

## Adding New Providers

See [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md) for detailed instructions on adding support for additional AI providers.

## Expected Data Formats

### OpenAI Format
```csv
email,name,department,period_start,messages,tool_messages,project_messages
user@company.com,John Doe,["engineering"],2024-01-01,100,50,25
```

### BlueFlame AI Format
```csv
user_id,full_name,team,usage_date,chat_interactions,api_calls,total_tokens
user123,Jane Smith,Marketing,2024-01-01,150,200,50000
```

### Anthropic Format
```csv
user_email,username,org_unit,usage_date,claude_messages,tokens_used
user@company.com,Bob Johnson,Research,2024-01-01,75,30000
```

## Database Management

The dashboard includes a Database Management tab with:
- View database statistics
- Delete specific uploads
- Clear entire database
- Date coverage analysis
- Upload history tracking

## Customizing

### Column Aliases

If your export uses different headings, you can add new providers or modify existing ones in `config.py`. See the `PROVIDERS` configuration for examples.

### Cost Models

Cost per unit is configurable per provider in `config.py`. Adjust the `cost_per_unit` values to match your provider's actual pricing.
