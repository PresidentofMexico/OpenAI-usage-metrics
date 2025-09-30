 # AI Usage Metrics Dashboard
Multi-provider analytics dashboard for AI platform usage metrics

A lightweight Streamlit application for analyzing usage metrics from multiple AI providers including OpenAI, BlueFlame AI, Anthropic, and Google. Upload monthly CSV exports to generate comprehensive dashboards with cost analysis, adoption trends, and user insights.

## 🚀 Features

- **Multi-Provider Support**: Analyze data from OpenAI, BlueFlame AI, Anthropic, Google, and more
- **Automatic Provider Detection**: System automatically identifies provider from CSV format
- **Provider-Specific Analytics**: Tailored cost models and feature categories for each provider
- **Interactive Dashboards**: Month-over-month trends, user analytics, and department breakdowns
- **Cost Transparency**: Detailed cost calculations with provider-specific pricing models
- **Data Quality Checks**: Built-in validation and quality metrics
- **Database Management**: Track uploads, manage data, and monitor system health

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

## Supported Providers

- **OpenAI (ChatGPT)** 🤖 - ChatGPT Messages, Tool Messages, Project Messages
- **BlueFlame AI** 🔥 - API Calls, Model Requests
- **Anthropic (Claude)** 🧠 - Claude Messages, API Usage
- **Google (Gemini)** 🔍 - Gemini Queries, Bard Interactions

See [MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md) for details on adding new providers.

## Usage

1. **Upload Data**: Use the sidebar to upload CSV exports from your AI provider
2. **Select Provider**: Choose which provider's data to analyze from the dropdown
3. **Analyze**: View interactive dashboards with usage trends, costs, and insights
4. **Filter**: Refine analysis by date range, users, or departments
5. **Export**: Download filtered data and summary reports

The app stores data in a SQLite database for persistent analytics across sessions.

## Advanced Features

### Multi-Provider Analytics
- Automatic provider detection from CSV format
- Provider-specific cost models and feature categories
- Isolated analytics per provider
- Easy addition of new providers via configuration

### Data Quality Dashboard
- Completeness metrics and duplicate detection
- Data validation and anomaly alerts
- Active user tracking

### Management Insights
- Usage growth analysis
- Cost efficiency metrics
- Top users and departments
- Feature usage distribution

## Configuration

Provider configurations are defined in `config.py`:
- Column mappings for each provider
- Cost models (per-unit pricing)
- Provider detection rules
- Display settings (icons, names)

## Database

Data is stored in SQLite (`data/openai_metrics.db` by default):
- Persistent storage across sessions
- Multi-provider data isolation
- Automatic schema migration
- Database management UI included

## Features

- Automatic normalisation of CSV exports with flexible column-name matching.
- Month-over-month summaries of requests, tokens, cost and active user counts.
- User-level breakdowns with active day counts per selected month.
- Trend analysis that highlights the largest increases or decreases in usage.
- Daily/weekly/monthly time-series visualisations with optional rolling averages.

# Customising column aliases

If your export uses different headings, you can provide additional aliases by editing `usage_metrics/data_ingestion.py` and extending the `DEFAULT_COLUMN_ALIASES` mapping.
