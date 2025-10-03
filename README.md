 # OpenAI usage metrics
Automatically pull and update user metrics

A lightweight Streamlit application for exploring OpenAI Enterprise workspace exports. Upload the monthly CSV metrics provided in the Workspace Settings panel to generate dashboards that highlight adoption trends, top users, and day-to-day activity.

## ✨ New Feature: Automatic File Detection

The dashboard now supports **automatic file detection**! Simply place your CSV files in the `OpenAI User Data/` folder and the dashboard will automatically detect and process them - no manual uploads required.

**Quick Start:**
1. Drop CSV files into `OpenAI User Data/` or `BlueFlame User Data/`
2. Open the dashboard: `streamlit run app.py`
3. Click "⚡ Process All" in the sidebar

See [AUTO_FILE_DETECTION.md](AUTO_FILE_DETECTION.md) for full documentation.

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

## Usage Options

### Option 1: Automatic File Detection (Recommended)
- Place CSV files in `OpenAI User Data/`, `BlueFlame User Data/`, or `data/uploads/`
- Dashboard automatically detects new files
- Click "Process All" or process files individually
- Files are tracked to prevent duplicate imports

### Option 2: Manual Upload
- Select tool type in sidebar
- Upload file through file uploader
- Click "Process Upload"
- Works exactly as before

The app stores uploaded data in SQLite database (`openai_metrics.db`). Both automatic and manual methods store data in the same database.

## Features

- **🔄 Automatic File Detection** - Scan folders for CSV files automatically
- **📊 Multi-Platform Support** - OpenAI ChatGPT, BlueFlame AI, and more
- **📈 Executive Overview** - Key metrics, trends, and data quality indicators
- **👥 Power Users Analysis** - Identify and track top users
- **🏢 Department Mapping** - Custom department assignments
- **💾 Database Management** - Export, backup, and manage data
- Automatic normalisation of CSV exports with flexible column-name matching
- Month-over-month summaries of requests, tokens, cost and active user counts
- User-level breakdowns with active day counts per selected month
- Trend analysis that highlights the largest increases or decreases in usage
- Daily/weekly/monthly time-series visualisations with optional rolling averages

# Customising column aliases

If your export uses different headings, you can provide additional aliases by editing `config.py` and extending the `PROVIDER_COLUMN_MAPPING` dictionary.
