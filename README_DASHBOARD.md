# OpenAI Usage Metrics Dashboard - Fixed Version

## Overview
This dashboard has been reverted to a simple, working OpenAI-focused implementation. All broken multi-provider code has been removed.

## Running the Dashboard

```bash
streamlit run app.py
```

## Features

### Analytics Dashboard
- **Key Metrics**: Total users, usage events, costs, and per-user averages
- **Usage Trends**: Daily usage and cost charts
- **User Analysis**: Top 10 users by usage, department breakdown
- **Feature Analysis**: Usage distribution across ChatGPT Messages, Tool Messages, and Project Messages
- **Management Insights**: Cost efficiency metrics and usage distribution

### Database Management
- **Overview**: Total records, users, date range, and costs
- **Upload History**: View all imported files with date ranges and record counts
- **Management Actions**:
  - Delete specific uploaded files
  - Clear entire database
- **Data Coverage**: Visual chart of usage over time
- **Raw Data View**: Downloadable CSV export of all data

### Data Quality
- Automatic validation on data load
- Checks for duplicates, missing names, and invalid usage counts
- Visual indicators for data quality issues

## File Upload
Supports OpenAI enterprise monthly export CSV files with columns:
- `email` - User email address
- `name` - User display name
- `department` - Department (supports JSON array format like ["finance"])
- `period_start` - Period date (YYYY-MM-DD)
- `messages` - ChatGPT message count
- `tool_messages` - Tool message count (optional)
- `project_messages` - Project message count (optional)

## Cost Calculation
- ChatGPT Messages: $0.02 per message
- Tool Messages: $0.01 per message
- Project Messages: $0.015 per message

## Database
Uses SQLite database (`openai_metrics.db`) with the following schema:
- `user_id` - User email
- `user_name` - User name
- `department` - Department name
- `date` - Usage date
- `feature_used` - Feature type (ChatGPT Messages, Tool Messages, Project Messages)
- `usage_count` - Number of uses
- `cost_usd` - Calculated cost
- `created_at` - Record creation timestamp
- `file_source` - Source CSV filename

## Filters
- **Date Range**: Select specific date range for analysis
- **Users**: Filter by specific users (multi-select)
- **Departments**: Filter by departments (multi-select)

## Files

### Main Application
- `app.py` - Main dashboard application (OpenAI-focused)
- `database.py` - Database manager (simplified)
- `data_processor.py` - Data processing (OpenAI CSV only)

### Backup/Alternative
- `simple_dashboard.py` - Minimal dashboard alternative
- `app_backup.py` - Previous working version

### Legacy/Reference
- `app_broken_multiprovider.py` - Old multi-provider version (broken)
- `config.py` - Multi-provider configuration (unused)
- `provider_schemas.py` - Provider schemas (unused)

## Troubleshooting

### Database Issues
If you encounter database errors:
1. Stop the dashboard
2. Delete `openai_metrics.db`
3. Restart the dashboard - it will recreate the database
4. Re-upload your CSV files

### File Upload Issues
- Ensure CSV has required columns: `email`, `name`, `department`, `period_start`, `messages`
- Check that department field is properly formatted
- Verify dates are in YYYY-MM-DD format

### Performance
- The dashboard caches database connections for better performance
- Large datasets (>100k records) may take a few seconds to load charts
- Use date range filters to improve performance on large datasets
