# OpenAI Usage Metrics Dashboard - AI Coding Instructions

## Project Overview
This is a Streamlit-based analytics dashboard for processing and visualizing OpenAI Enterprise workspace usage exports. The app transforms monthly CSV reports into interactive dashboards with cost analysis, adoption trends, and user insights.

## Architecture & Data Flow
- **Entry Points**: `app.py` (main dashboard) and `simple_dashboard.py` (lightweight version)
- **Data Layer**: SQLite databases (`openai_metrics.db`, `usage_data.db`) managed by `database.py`
- **Processing**: `data_processor.py` transforms OpenAI CSV exports into normalized usage records
- **Configuration**: `config.py` contains column mappings and default values

### Key Data Transformation Pattern
OpenAI exports contain user-level monthly summaries. The `DataProcessor.clean_openai_data()` method:
1. Extracts usage counts from columns: `messages`, `tool_messages`, `project_messages`
2. Creates separate records per feature type (ChatGPT Messages, Tool Messages, Project Messages)
3. Applies estimated cost calculations (`messages * 0.02`, `tool_messages * 0.01`, etc.)
4. Normalizes department names using `extract_department()` method

## CSV Data Structure
Expected OpenAI export columns:
- `email`, `name`, `department` - User identification
- `period_start` - Month/period identifier
- `messages`, `tool_messages`, `project_messages` - Usage counts
- `is_active`, `user_status` - Filter criteria

## Development Workflows

### Running the Application
```bash
# Main dashboard (recommended)
streamlit run app.py

# Simple dashboard (lightweight alternative)
streamlit run simple_dashboard.py
```

### Data Management
- CSV uploads are processed via Streamlit file uploader
- Database schema auto-initializes on first run
- Multiple dashboard instances share the same SQLite database
- Use database manager methods for safe data operations

### Key Configuration Points
- Column mappings in `config.py` - extend `CSV_COLUMN_MAPPING` for new CSV formats
- Cost estimation logic in `data_processor.py` - modify per-message rates
- Database path in `config.py` - change `DATABASE_PATH` for different environments

## Project-Specific Patterns

### Error Handling
- Database operations wrapped in try/catch with empty DataFrame fallbacks
- CSV processing validates data existence before transformation
- Streamlit caching (`@st.cache_resource`) for database connections

### Cost Calculation Methodology
Fixed per-message rates defined in `DataProcessor.clean_openai_data()`:
- ChatGPT Messages: $0.02 per message
- Tool Messages: $0.01 per message  
- Project Messages: $0.015 per message

### Department Normalization
The `extract_department()` method handles OpenAI's inconsistent department formatting:
- Strips JSON array brackets: `["finance"]` → `finance`
- Defaults unknown/empty departments to "Unknown"
- Capitalizes department names for consistency

### Database Schema
Single table `usage_metrics` with columns:
- User identification: `user_id`, `user_name`, `department`
- Usage data: `date`, `feature_used`, `usage_count`, `cost_usd`
- Metadata: `created_at`, `file_source`

## Critical Dependencies
- **Streamlit**: Dashboard framework, handles file uploads and caching
- **Pandas**: CSV processing and data manipulation
- **Plotly**: All visualizations (bar charts, time series, subplots)
- **SQLite3**: Built-in database, no external database setup required

## Testing & Debugging
- Use sample CSV files in `OpenAI User Data/` directory
- Check database contents via `DatabaseManager.get_all_data()`
- Streamlit debug mode: add `debug=True` to `st.set_page_config()`
- Print statements in `data_processor.py` show processing details in terminal

## File Organization
- `app.py` - Main production dashboard with full analytics
- `simple_dashboard.py` - Minimal viable dashboard for quick analysis
- `app_backup.py` - Previous version backup
- `data/` - Intended database directory (currently databases in root)
- `OpenAI User Data/` - Sample CSV files for testing

When modifying data processing logic, always test with the provided sample CSVs to ensure compatibility with OpenAI's export format.