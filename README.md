 # OpenAI Usage Metrics Dashboard

> An enterprise-grade analytics dashboard for OpenAI ChatGPT and BlueFlame AI usage tracking, cost analysis, and ROI optimization.

A Streamlit-based application that transforms monthly CSV exports from OpenAI Enterprise and BlueFlame AI into interactive dashboards with comprehensive adoption trends, cost analysis, and user insights. Designed for IT administrators, finance teams, and executives managing enterprise AI tool deployments.

**Current Status:** Production-ready ✅ | Actively maintained

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Features](#-features)
- [Data Validation System](#-data-validation-system)
- [Data Formats & Processing](#-data-formats--processing)
- [Usage & Examples](#-usage--examples)
- [Testing & Performance](#-testing--performance)
- [Changelog & Fixes](#-changelog--fixes)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License & Support](#-license--support)

---

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PresidentofMexico/OpenAI-usage-metrics.git
   cd OpenAI-usage-metrics
   ```

2. **Create and activate a Python 3.10+ virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the dashboard**
   ```bash
   streamlit run app.py
   ```

### Quick Start (3 Steps - Recommended)

The dashboard now features **automatic file detection**, reducing setup from 7 steps to just 3:

1. **Drop CSV files** into the designated folders:
   - `OpenAI User Data/` - For OpenAI ChatGPT exports
   - `BlueFlame User Data/` - For BlueFlame AI exports
   - `data/uploads/` - For general uploads

2. **Open the dashboard**
   ```bash
   streamlit run app.py
   ```

3. **Click "⚡ Process All"** in the sidebar to batch import all new files

The dashboard automatically:
- ✅ Scans folders on startup
- ✅ Detects CSV and Excel files
- ✅ Tracks processed files to prevent duplicates
- ✅ Shows file status (New/Processed/Modified/Error)

**Alternative:** Use the manual upload feature in the sidebar for individual file uploads.

📖 **See [Automatic File Detection Documentation](docs/AUTO_FILE_DETECTION.md) for detailed setup and troubleshooting.**

---

## ✨ Features

### 🔄 Automatic File Detection

The dashboard's **automatic file detection** feature eliminates manual uploads by scanning designated folders for CSV/Excel files.

**Key Benefits:**
- **Smart Tracking** - Prevents duplicate imports with automatic file tracking
- **Batch Processing** - Process multiple files with one click
- **Status Display** - Clear indicators for New, Processed, Modified, and Error states
- **Flexible Setup** - Works alongside manual uploads seamlessly

**Quick Overview:**
- Scans folders: `OpenAI User Data/`, `BlueFlame User Data/`, `data/uploads/`
- Detects file types: `.csv`, `.xlsx`, `.xls`
- Tracking file: `file_tracking.json` stores processing metadata
- Refresh capability: Click "🔄 Refresh Files" to rescan

**Processing Options:**
- **Individual:** Click "▶️ Process" button next to any file
- **Batch:** Click "⚡ Process All X New Files" to import everything at once

📖 **Full documentation:** [docs/AUTO_FILE_DETECTION.md](docs/AUTO_FILE_DETECTION.md)

---

### 🤖 BlueFlame AI Support

Complete integration with BlueFlame AI usage data, supporting three CSV format types:

**Supported Table Types:**
1. **Combined Format** - Single CSV with `Table` column containing:
   - Overall Monthly Trends (aggregate metrics)
   - Top 20 Users Total
   - Top 10 Increasing Users
   - Top 10 Decreasing Users

2. **Summary Report Format** - Aggregate metrics only with `Metric` column
3. **User Data Format** - User-specific data with `User ID` column

**Data Normalization:**
The system intelligently processes BlueFlame data:
- ✅ Extracts **real users** from Top 20/Top 10 tables (e.g., 28 users, 86 records)
- ✅ Creates **aggregate records** for overall trends (`blueflame-aggregate` user)
- ✅ Handles special values: dashes (`–`, `-`, `—`), N/A, comma-separated numbers
- ✅ Converts dates from multiple formats (`Sep-24`, `25-Sep`, `YY-Mon`)
- ✅ Applies **$0.015 per message** cost model

**Processing Improvements:**
- Fixed logic that previously showed only 1 synthetic user instead of 28+ real users
- Added provider-toggle radio button in sidebar: "All Tools / ChatGPT / BlueFlame AI"
- Proper validation and column detection for all format types

**Example Results:**
```
BlueFlame September 2025: 28 users, 86 records
OpenAI September 2025: 159 users, 358 records
Combined database: 187 unique users, 444 records
```

📖 **Full format guide:** [docs/BLUEFLAME_FORMAT_GUIDE.md](docs/BLUEFLAME_FORMAT_GUIDE.md)  
📖 **Implementation details:** [docs/BLUEFLAME_FIX_SUMMARY.md](docs/BLUEFLAME_FIX_SUMMARY.md)

---

### 📊 Message Type Analytics & Feature Breakdown

**NEW!** Detailed message type breakdowns across all dashboard sections to understand feature adoption and usage patterns.

**Key Capabilities:**
- **Organization-Wide Analytics** - See which AI features are most popular (ChatGPT Messages, GPT Messages, Tool Messages, Project Messages)
- **Department Breakdowns** - Expandable feature usage details for each department with interactive charts
- **Feature Adoption Tracking** - Dedicated analytics tab with trends, heatmaps, and insights
- **Power User Analysis** - Already-existing feature showing message type composition for top users

**What You'll See:**

1. **Executive Summary**
   - Pie chart showing organization-wide feature distribution
   - Detailed statistics for each message type with percentages
   - Feature descriptions with expandable help text

2. **Department Performance**
   - Click any department to expand and see feature-specific breakdown
   - Bar charts showing message type distribution per department
   - Department-specific statistics (active users, messages/user, total cost)

3. **Message Type Analytics Tab**
   - Feature usage trends over time (line chart)
   - Current distribution visualization (donut chart)
   - Department vs Feature heatmap showing adoption patterns
   - Key insights: most popular feature, adoption rate, most diverse usage

**Message Types Tracked:**
- **ChatGPT Messages** - Standard conversational AI interactions
- **GPT Messages** - Custom GPT usage (specialized assistants)
- **Tool Messages** - Code Interpreter, web browsing, data analysis
- **Project Messages** - ChatGPT Projects (organized workspaces)
- **BlueFlame Messages** - BlueFlame AI platform interactions

**Example Insights:**
```
Tool Messages: 62,970 (74.1% of total)
ChatGPT Messages: 18,732 (22.0%)
Project Messages: 2,613 (3.1%)
GPT Messages: 640 (0.8%)
```

**Screenshots:**

![Executive Summary - Feature Adoption Analytics](https://github.com/user-attachments/assets/aba9e9d0-76bf-4d43-a327-2b26f3a6dfdb)

![Message Type Analytics Tab](https://github.com/user-attachments/assets/3896f061-918e-41da-ba9c-af72af24fb92)

![Department Feature Breakdown](https://github.com/user-attachments/assets/469ae88e-5eb4-4c4f-9681-6049fe60a821)

---

### 💰 Cost Model & Enterprise Pricing

The dashboard uses **enterprise license-based pricing**, not per-message costs, reflecting how organizations actually pay for AI tools.

**Enterprise Pricing Model:**

| Provider | Cost per User | Annual Cost | What's Included |
|----------|--------------|-------------|-----------------|
| **ChatGPT Enterprise** | $60/month | $720/year | All messages, custom GPTs, tools, projects |
| **BlueFlame AI** | $125/month | $1,500/year | All messages and features |

**Why This Matters:**

❌ **Old Per-Message Model (Incorrect):**
```
159 users × 114,247 messages × $0.02 = $2,285/month
Problem: Vastly underestimates true cost
```

✅ **New Enterprise License Model (Accurate):**
```
159 users × $60/user = $9,540/month = $114,480/year
Benefit: Reflects actual enterprise license costs
```

**Key Metric Changes:**

| Metric | Before | After | Reason |
|--------|--------|-------|---------|
| Primary Cost Metric | Cost per message | **Cost per user** | Enterprise licenses are per-user |
| ChatGPT Message Cost | $0.02/message | **$60/user/month** | Real enterprise license cost |
| Tool Messages Cost | $0.01/message | **$0 (included)** | Included in base license |
| Project Messages Cost | $0.015/message | **$0 (included)** | Included in base license |
| Focus Metric | Message volume | **Cost per user + Engagement** | Better ROI analysis |

**Dashboard Insights:**
- **YTD Spending** with provider breakdown
- **Projected Annual Cost** with accurate methodology
- **Avg Monthly Cost per User** - Primary financial metric
- **Messages per User** - Engagement indicator
- **License Utilization & ROI Analysis** - Identifies underutilized licenses

**Real-World Impact:**
```
Budget Planning: "We have 159 ChatGPT licenses at $9,540/month = $114,480/year"
ROI Justification: "Each user costs $720/year and averages 719 messages/month"
License Optimization: "23 users with <10 messages/month - potential $16,560/year savings"
```

📖 **Detailed comparison:** [docs/COST_MODEL_COMPARISON.md](docs/COST_MODEL_COMPARISON.md)  
📖 **Implementation summary:** [docs/ENTERPRISE_PRICING_UPDATE.md](docs/ENTERPRISE_PRICING_UPDATE.md)

---

### 💾 Database & File Management

Comprehensive data management features with quality checks and error handling:

**Core Features:**
- **Individual File Deletion** - Remove specific uploads with safety confirmations
- **Batch Deletion** - Clear multiple files at once
- **Error Handling** - Graceful fallbacks for cache issues and stale objects
- **Data Quality Checks** - Automatic validation, duplicate detection, missing data alerts
- **Export Options** - Raw data export, PDF reports, Excel workbooks

**File Management:**
- Track all uploaded files with metadata (filename, date, record count)
- Delete files individually or in bulk from database
- View upload history and file sources
- Export data to CSV for external analysis

**Cache Error Handling:**
When Streamlit's cached `DatabaseManager` becomes stale:
- ✅ Automatic error detection with user-friendly messages
- ✅ One-click "Clear Cache & Reload" button
- ✅ Manual restart instructions as alternative
- ✅ Prevents app crashes from outdated cache

**Pagination Improvements:**
- Fixed tab switching issue where pagination buttons caused app to return to first tab
- Previous/Next buttons now work correctly while preserving active tab
- Enhanced user experience with stable navigation

📖 **Cache fix details:** [docs/CACHE_ERROR_FIX.md](docs/CACHE_ERROR_FIX.md)  
📖 **Pagination fix:** [docs/PAGINATION_BUTTON_FIX.md](docs/PAGINATION_BUTTON_FIX.md)

---

### 📊 Additional Features

- **👥 Employee Master File Integration** - Load employee roster for automatic department assignment ([Guide](docs/EMPLOYEE_INTEGRATION_GUIDE.md))
- **📈 Executive Overview** - YTD spending, projections, top departments, cost efficiency
- **👥 Power Users Analysis** - Identify and track top users with deduplication fixes
- **🏢 Department Mapping** - Custom department assignments with name matching
- **📱 Mobile Responsive** - Works on tablets and phones
- **🎨 Dark Mode** - Professional dark theme with improved readability
- **❓ Help Tooltips** - Comprehensive metric explanations throughout
- **📄 Export Options** - PDF reports (HTML format) and multi-sheet Excel workbooks

---

## 📊 Data Validation System

**NEW!** Comprehensive tools for validating and analyzing weekly and monthly ChatGPT data.

### Overview

The data validation system ensures data quality and consistency between weekly and monthly OpenAI exports. It provides three key components:

#### 1. ChatGPT Data Validator (`chatgpt_data_validator.py`)

Validates that weekly data sums correctly to monthly totals across all message categories.

**Key Features:**
- ✅ Validates all categories (GPT, Tool, Project, General messages)
- ✅ Generates detailed validation reports (text and JSON)
- ✅ Identifies discrepancies with configurable tolerance
- ✅ Validates category breakdowns

**Quick Start:**
```bash
python chatgpt_data_validator.py
```

#### 2. Data Handlers (`data_handlers.py`)

Separate handlers for weekly and monthly data analysis.

**WeeklyDataHandler:**
- Weekly patterns and trends analysis
- Peak week identification
- User engagement tracking
- Week-over-week comparisons

**MonthlyDataHandler:**
- Annual usage projections
- Quarterly summaries
- Seasonality analysis
- Growth rate calculations

**DataReconciliationTool:**
- Ensures consistency between weekly and monthly data
- Category-level validation
- Detailed reconciliation reports

**Quick Start:**
```bash
python data_handlers.py
```

#### 3. Sample Data Files

Included example files demonstrate successful validation:
- `sample_weekly_data.csv` - 4 weeks of usage data (5 users)
- `sample_monthly_data.csv` - Corresponding monthly totals
- **Validation Result:** ✅ All data reconciles correctly

### Usage Example

```python
from chatgpt_data_validator import ChatGPTDataValidator
from data_handlers import WeeklyDataHandler, MonthlyDataHandler

# Validate weekly against monthly
validator = ChatGPTDataValidator(tolerance_percentage=1.0)
results = validator.validate_weekly_to_monthly(
    weekly_files=['week1.csv', 'week2.csv', 'week3.csv'],
    monthly_file='monthly_report.csv'
)

print(validator.generate_report(results, output_format='text'))

# Analyze weekly trends
weekly = WeeklyDataHandler()
weekly.load_data(['week1.csv', 'week2.csv', 'week3.csv'])
trends = weekly.analyze_trends()
print(f"Peak week: {trends['summary']['peak_week']}")

# Project annual usage
monthly = MonthlyDataHandler()
monthly.load_data(['jan.csv', 'feb.csv', 'mar.csv'])
projection = monthly.project_annual_usage()
print(f"Annual projection: {projection['projections']['simple_annual']:,}")
```

### Testing

Run the comprehensive test suite:
```bash
python test_data_validation.py
```

**Expected Output:**
```
📈 Total: 9/9 tests passed
🎉 All tests passed successfully!
```

### Documentation

📖 **Complete guide:** [DATA_VALIDATION_GUIDE.md](DATA_VALIDATION_GUIDE.md)

**Key Topics:**
- Component documentation and API reference
- Expected CSV format specifications
- Validation report formats (text and JSON)
- Integration with existing dashboard
- Best practices and troubleshooting
- Performance benchmarks

---

## 📁 Data Formats & Processing

### Supported CSV Structures

#### OpenAI ChatGPT Export Format

Expected columns:
```
email, name, department, period_start, is_active, user_status
messages, tool_messages, project_messages
```

**Processing:**
- Extracts usage counts from message columns
- Creates separate records per feature type (ChatGPT Messages, Tool Messages, Project Messages)
- Applies enterprise license costs: $60/user/month for primary messages, $0 for additional features
- Normalizes department names from JSON arrays: `["finance"]` → `finance`

#### BlueFlame AI Export Formats

**1. Combined Format (with Table Column):**
```csv
Table,Metric,User ID,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
Overall Monthly Trends,Total Messages,,10000,12000,15000,–
Top 20 Users Total,,alice@company.com,500,600,700,–
```

**2. Summary Report Format (with Metric Column):**
```csv
Metric,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
Total Messages,5000,6000,7000,–
Monthly Active Users (MAUs),25,30,35,–
```

**3. User Data Format (with User ID Column):**
```csv
User ID,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
john.doe@company.com,200,250,300,–
jane.smith@company.com,150,180,220,–
```

### Data Normalization Details

**Special Value Handling:**
- Dashes (`–`, `-`, `—`) → treated as null/missing data
- `N/A` → treated as missing data
- Comma-separated numbers: `10,000` → `10000`
- Empty values → skipped during processing

**Department Normalization:**
```python
# Input: ["finance"] or ["sales", "marketing"]
# Output: "finance" or "sales, marketing"
# Default: "Unknown" for missing/invalid departments
```

**Date Conversion:**
- Input formats: `Sep-24`, `25-Sep`, `YY-Mon`, `Mon-YY`
- Output format: `YYYY-MM-DD` for database storage

**Cost Calculations:**
- BlueFlame: $0.015 per message (used during data import)
- OpenAI: $60/user/month for ChatGPT Messages, $0 for included features

### Database Schema

Single table `usage_metrics`:
```sql
user_id       TEXT    -- Email or synthetic ID
user_name     TEXT    -- Display name
email         TEXT    -- User email address
department    TEXT    -- Department name
date          TEXT    -- Usage date (YYYY-MM-DD)
feature_used  TEXT    -- Feature name (e.g., "ChatGPT Messages", "BlueFlame Messages")
usage_count   INTEGER -- Number of messages/interactions
cost_usd      REAL    -- Calculated cost (enterprise license model)
tool_source   TEXT    -- Provider name ("ChatGPT", "BlueFlame AI")
file_source   TEXT    -- Source filename for tracking
created_at    TEXT    -- Import timestamp
```

📖 **BlueFlame format guide:** [docs/BLUEFLAME_FORMAT_GUIDE.md](docs/BLUEFLAME_FORMAT_GUIDE.md)  
📖 **Auto-detection details:** [docs/AUTO_FILE_DETECTION.md](docs/AUTO_FILE_DETECTION.md)

---

## 📖 Usage & Examples

### Basic Workflow

**1. Upload Data**

Option A - Automatic (Recommended):
```bash
# Place files in designated folders
cp my_openai_export.csv "OpenAI User Data/"
cp my_blueflame_export.csv "BlueFlame User Data/"

# Start dashboard
streamlit run app.py

# Click "⚡ Process All" in sidebar
```

Option B - Manual Upload:
```
1. Navigate to "📤 Upload Data" tab
2. Select or drag your CSV file
3. System auto-detects format (OpenAI/BlueFlame)
4. Click "Process Data" to import
```

**2. Process Files**

Batch Processing:
```
Sidebar → Auto-Detect Files → "⚡ Process All X New Files"
```

Individual Processing:
```
Sidebar → Auto-Detect Files → Click "▶️ Process" next to specific file
```

**3. Toggle Providers**

```
Sidebar → Radio Button Selector:
- All Tools (combined view)
- ChatGPT (OpenAI only)
- BlueFlame AI (BlueFlame only)
```

**4. View Analytics**

Navigate through tabs:
- **📊 Executive Overview** - High-level metrics and trends
- **👥 Power Users** - Top users ranked by usage
- **🏢 Department Mapping** - Custom department assignments
- **💾 Database Management** - File management and data export

**5. Export Reports**

```
Executive Overview tab → Click export buttons:
- 📄 Export PDF Report (HTML format - print to PDF from browser)
- 📊 Export to Excel (Multi-sheet workbook with pivot tables)
```

**6. Delete Files**

```
Database Management tab → Upload History → Click 🗑️ button per file
Or: Click "Clear All Data" with confirmation prompt
```

### Code Examples

**Provider Toggle Implementation:**
```python
# In sidebar
selected_tool = st.radio(
    "Provider",
    options=['All Tools'] + available_tools,
    help="📊 Filter dashboard to show data from specific AI platform"
)

# Apply filter
if selected_tool != 'All Tools':
    filtered_data = data[data['tool_source'] == selected_tool]
```

**Run Dashboard:**
```bash
streamlit run app.py
```

**Access Dashboard:**
```
http://localhost:8501
```

📖 **Employee integration guide:** [docs/EMPLOYEE_INTEGRATION_GUIDE.md](docs/EMPLOYEE_INTEGRATION_GUIDE.md)

---

## 🧪 Testing & Performance

### Test Coverage

**Automated Test Suite:**
```bash
# Run critical fixes test
python test_critical_fixes.py
```

Expected output:
```
✅ PASS: Date Calculation Fix
✅ PASS: Power User Deduplication
✅ PASS: Department Selection
✅ PASS: BlueFlame Format Detection
📈 Total: 4/4 tests passed
```

**Test Categories:**
- Unit tests for file scanning and detection
- Integration tests for BlueFlame format processing
- Data quality and validation tests
- Department mapper functionality
- Pagination and UI component tests

### Performance Metrics

**File Scanning:**
- Scan time: <1 second for 100 files
- Memory overhead: Minimal (files processed one at a time)

**File Processing:**
- Small files (<1MB): ~2-3 seconds per file
- Large files (>50MB): 10-30 seconds per file
- Batch processing: Sequential with progress tracking

**Real-World Testing:**
- 7 files processed: All successful
- 187 unique users imported
- 444 usage records created
- Combined OpenAI + BlueFlame data

**Database Operations:**
- SQLite database: Fast read/write operations
- Same performance as manual upload method
- No external database setup required

### Sample Data Generation

```bash
# Generate sample data for testing
python generate_sample_data.py
```

📖 **Quick start guide:** [docs/QUICK_START.md](docs/QUICK_START.md)  
📖 **Feature summary:** [docs/FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md)

---

## 📝 Changelog & Fixes

### Recent Highlights

**Major Features:**
- ✅ **Automatic File Detection** - Reduced setup from 7 steps to 3
- ✅ **BlueFlame AI Support** - All 3 format types supported, 28+ real users processed
- ✅ **Enterprise Pricing Model** - $60/user/month for ChatGPT, $125/user/month for BlueFlame
- ✅ **Provider Toggle** - Radio button selector in sidebar
- ✅ **Individual File Deletion** - Remove specific files with safety confirmations

**Critical Bug Fixes:**
- ✅ **Date Calculation TypeError** - Fixed string date subtraction with `pd.to_datetime()`
- ✅ **Power User Deduplication** - Users now appear once with combined usage
- ✅ **Cache Error Handling** - One-click "Clear Cache & Reload" button
- ✅ **Pagination Tab Switching** - Buttons now preserve active tab
- ✅ **BlueFlame Processing** - Fixed to extract 28 real users instead of 1 synthetic user

**UI/UX Improvements:**
- ✅ Mobile responsive design
- ✅ Loading spinners during operations
- ✅ Comprehensive help tooltips
- ✅ Dark mode improvements
- ✅ Professional visual polish

### Full Changelog

📖 **Complete change history:** [docs/CHANGES.md](docs/CHANGES.md)  
📖 **Fix summaries directory:** [docs/](docs/)

Key fix documentation:
- [Cache Error Fix](docs/CACHE_ERROR_FIX.md)
- [Pagination Button Fix](docs/PAGINATION_BUTTON_FIX.md)
- [BlueFlame Fix Summary](docs/BLUEFLAME_FIX_SUMMARY.md)
- [Power User Fix](docs/POWER_USER_FIX_SUMMARY.md)
- [Department Mapper Fixes](docs/DEPARTMENT_MAPPER_FIX_SUMMARY.md)

---

## 🔮 Future Enhancements

### Proposed Features

**Automatic Processing:**
- Scheduled auto-processing with cron jobs
- Real-time file watching for instant imports
- Webhook integration for automated uploads

**Cost Model Extensions:**
- Support for different license tiers (Team, Business, Enterprise)
- Custom pricing overrides per organization
- Seat allocation tracking (purchased vs. utilized licenses)
- License utilization trend analysis

**Department Mapping:**
- Advanced name matching algorithms
- Bulk import from HR systems
- Department hierarchy support
- Auto-mapping based on email domains

**Analytics Enhancements:**
- Predictive usage forecasting
- Anomaly detection for unusual usage patterns
- Custom metric definitions
- Advanced filtering and segmentation

**Integration & Export:**
- API endpoints for programmatic access
- Power BI / Tableau connectors
- Automated email reports
- Slack/Teams notifications for key events

### Contributing

We welcome contributions! To get started:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with tests
4. **Run the test suite** (`python test_critical_fixes.py`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

**Contribution Guidelines:**
- Follow existing code style and patterns
- Add tests for new features
- Update documentation for user-facing changes
- Keep commits focused and atomic

**Areas for Contribution:**
- New data source integrations
- Enhanced visualizations
- Performance optimizations
- Documentation improvements
- Bug fixes and issue resolution

📖 **Feature summary for reference:** [docs/FEATURE_SUMMARY.md](docs/FEATURE_SUMMARY.md)

---

## 📄 License & Support

### Support

**For questions and bug reports:**
- Open an issue on [GitHub Issues](https://github.com/PresidentofMexico/OpenAI-usage-metrics/issues)
- Include relevant error messages and log output
- Provide sample data (anonymized) if possible

**Troubleshooting:**

*Dashboard won't load:*
```bash
pip install -r requirements.txt
streamlit run app.py
```

*Files not appearing in auto-detect:*
1. Verify files are in correct folder (`OpenAI User Data/` or `BlueFlame User Data/`)
2. Check file extensions (`.csv`, `.xlsx`, `.xls`)
3. Click "🔄 Refresh Files" button
4. Check console for folder warnings

*Processing failures:*
- Save CSV as UTF-8 encoding
- Verify CSV structure matches expected format
- Check for corrupted files
- Re-export from source system

*Cache errors:*
- Click "Clear Cache & Reload" button in error message
- Or restart Streamlit manually

**Documentation:**
- [Full documentation directory](docs/)
- [Automatic File Detection Guide](docs/AUTO_FILE_DETECTION.md)
- [BlueFlame Format Guide](docs/BLUEFLAME_FORMAT_GUIDE.md)
- [Employee Integration Guide](docs/EMPLOYEE_INTEGRATION_GUIDE.md)

### Customization

**Column Mapping:**

If your CSV export uses different column names, edit `config.py`:

```python
PROVIDER_COLUMN_MAPPING = {
    'openai': {
        'email': ['email', 'user_email', 'username'],
        'name': ['name', 'display_name', 'full_name'],
        # Add your custom mappings here
    }
}
```

---

## 🌟 Acknowledgments

Built with [Streamlit](https://streamlit.io/), [Pandas](https://pandas.pydata.org/), and [Plotly](https://plotly.com/).

**Status: Production Ready ✅**  
**Last Updated:** 2025-10-22
