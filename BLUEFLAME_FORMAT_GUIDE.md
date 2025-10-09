# BlueFlame AI Combined Data Format Support

This document describes the BlueFlame AI combined data format support added to the OpenAI Usage Metrics Dashboard.

## Overview

The dashboard now supports importing BlueFlame AI usage data in a combined CSV format that includes both aggregate metrics and user-specific data in a single file.

## Supported Data Formats

### 1. Combined Format (with Table Column)

The combined format includes a `Table` column that distinguishes between different data sections:

```csv
Table,Metric,User ID,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
Overall Monthly Trends,Total Messages,,10000,12000,15000,–
Overall Monthly Trends,Monthly Active Users (MAUs),,50,55,60,–
Top 20 Users Total,,alice@company.com,500,600,700,–
Top 10 Increasing Users,,bob@company.com,100,250,400,–
Top 10 Decreasing Users,,charlie@company.com,800,600,400,–
```

**Supported Table Types:**
- `Overall Monthly Trends` - Aggregate usage metrics
- `Top 20 Users Total` - Top users by total usage
- `Top 10 Increasing Users` - Users with increasing usage
- `Top 10 Decreasing Users` - Users with decreasing usage

### 2. Summary Report Format (with Metric Column)

Aggregate metrics only:

```csv
Metric,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
Total Messages,5000,6000,7000,–
Monthly Active Users (MAUs),25,30,35,–
```

### 3. User Data Format (with User ID Column)

User-specific data:

```csv
User ID,Sep-24,Oct-24,Nov-24,MoM Var Sep-24
john.doe@company.com,200,250,300,–
jane.smith@company.com,150,180,220,–
```

## Data Processing Features

### Automatic Detection

The dashboard automatically detects BlueFlame data by looking for:
- Month columns in format `Mon-YY` (e.g., `Sep-24`, `Oct-24`)
- `Table`, `Metric`, or `User ID` columns
- `MoM Var` (Month-over-Month Variance) columns

### Data Normalization

The system processes the data as follows:

1. **Aggregate Metrics**: Creates summary records for overall trends
   - User ID: `blueflame-aggregate`
   - Department: `All Departments`

2. **Real Users**: Creates individual records for named users
   - Extracts user information from email addresses
   - Default department: `BlueFlame Users`

3. **Synthetic Users**: Creates user-level records from MAU counts
   - User IDs: `blueflame-user-1`, `blueflame-user-2`, etc.
   - Usage distributed evenly based on MAU and total messages
   - Enables accurate per-user averages in dashboard

### Special Value Handling

- **Dashes**: `–`, `-`, `—` are treated as missing/no data
- **N/A**: Treated as missing data
- **Comma-separated numbers**: `10,000` → `10000`
- **Empty values**: Skipped during processing

### Cost Calculation

All BlueFlame messages are costed at **$0.015 per message**.

## Usage

### Uploading Data

1. Navigate to the "📤 Upload Data" tab in the dashboard
2. Select or drag your BlueFlame CSV file
3. The system will automatically detect it as "BlueFlame AI"
4. Click "Process Data" to import

### Dashboard Integration

Once imported, BlueFlame data appears alongside OpenAI data:

- **Overview Metrics**: Total users, usage, and costs
- **Usage Trends**: Monthly trends charts
- **Tool Comparison**: Compare BlueFlame AI vs ChatGPT usage
- **Department Analysis**: Usage by department
- **User Rankings**: Top users across all tools

## Example Data

See `/tmp/test_blueflame_format.py` for example data structures and processing.

## Technical Details

### Database Schema

All data is normalized to the standard schema:

```
user_id         TEXT    - Email or synthetic ID
user_name       TEXT    - Display name
email           TEXT    - User email address
department      TEXT    - Department name
date            TEXT    - Usage date (YYYY-MM-DD)
feature_used    TEXT    - Always "BlueFlame Messages"
usage_count     INTEGER - Number of messages
cost_usd        REAL    - Estimated cost
tool_source     TEXT    - Always "BlueFlame AI"
file_source     TEXT    - Source filename
created_at      TEXT    - Import timestamp
```

### Code Changes

- `app.py`: Updated `detect_data_source()` and `normalize_blueflame_data()`
- `data_processor.py`: Updated `normalize_blueflame_data()` in DataProcessor class

## Testing

Run the test suite to verify functionality:

```bash
# Basic format tests
python /tmp/test_blueflame_format.py

# Database integration test
python /tmp/test_blueflame_db.py

# Visual output test
python /tmp/test_blueflame_visual.py

# OpenAI regression test
python /tmp/test_openai_regression.py
```

## Troubleshooting

### Data not detected

- Ensure month columns follow `Mon-YY` format
- Check that `Table`, `Metric`, or `User ID` columns are present
- Verify file is a valid CSV

### Missing data

- Check for dash placeholders that are being skipped
- Verify date parsing is working (should auto-convert to YYYY-MM-DD)

### Cost calculations seem off

- Default rate is $0.015 per message
- Adjust in code if your pricing differs

## Future Enhancements

- Department mapping from user data
- Support for additional BlueFlame metrics
- Custom cost models per organization
- Historical trend analysis
