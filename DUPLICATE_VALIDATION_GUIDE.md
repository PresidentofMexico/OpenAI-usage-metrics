# Duplicate Data Validation Guide

## Overview

The Duplicate Data Validation system ensures that user message counts are not inflated by duplicate records caused by overlapping weekly and monthly data imports. This is critical for accurate analytics, executive reporting, and license ROI analysis.

## Problem Statement

When both weekly and monthly ChatGPT usage exports are imported into the dashboard, there's a risk that the same messages are counted multiple times:

- **Scenario**: You import a monthly file for May 2025 (covering the entire month)
- **Scenario**: You also import weekly files for weeks 1-4 of May 2025
- **Result**: Messages from May appear twice in the database - once from the monthly file and once from the weekly files
- **Impact**: User message totals are inflated, leading to inaccurate analytics

### Example: Tyler White

In the Power User Directory, Tyler White shows 7,189 ChatGPT messages. Without validation, it's unclear whether this count represents:
- ✅ 7,189 unique messages (correct)
- ❌ 3,595 unique messages counted twice due to overlapping files (incorrect - 100% duplication)

## Solution: Duplicate Validator

The **Duplicate Validator** detects and reports on duplicate message counts by:

1. **Identifying Duplicate Records**: Finds records where the same user/period/feature combination appears multiple times
2. **Calculating Unique Counts**: Computes the true unique message count by deduplicating overlapping periods
3. **Per-User Validation**: Shows which specific users have duplicates and by how much
4. **Source Tracking**: Identifies which files contributed to the duplicates

## Features

### 1. Duplicate Detection

The validator performs comprehensive duplicate detection at multiple levels:

- **Record-Level**: Identifies exact duplicates (same user, date, feature, tool)
- **User-Level**: Aggregates duplicates per user across all features
- **Feature-Level**: Breaks down duplicates by message type (ChatGPT Messages, Tool Messages, etc.)
- **File-Level**: Shows which source files are causing overlaps

### 2. Validation Reports

Generate detailed validation reports showing:

- Overall validation status (PASS/FAIL)
- Total users checked
- Number of users with duplicates
- Number of duplicate record sets
- Message count summary (total vs. unique)
- Duplication percentage
- Per-user breakdown with status
- Duplicate record details

### 3. User Interface

Access the validation tool via the Streamlit dashboard:

- Navigate to the **"✅ Data Validation"** tab
- Click **"Run Validation"** to analyze the current database
- View results in an interactive table
- Filter by duplicate status
- Export results as CSV or full report

## How to Use

### Via Streamlit Dashboard

1. **Launch the Dashboard**
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Data Validation Tab**
   - Click on the "✅ Data Validation" tab in the main interface

3. **Run Validation**
   - Click the "🚀 Run Validation" button
   - Wait for analysis to complete (usually < 5 seconds)

4. **Review Results**
   - Check the overall status (PASS/DUPLICATES_FOUND/ERROR)
   - Review summary metrics:
     - Users Checked
     - Users with Duplicates
     - Duplicate Records Found
     - Total vs. Unique Messages
   - Examine per-user details in the table

5. **Export Results** (optional)
   - Click "📊 Download CSV" for spreadsheet analysis
   - Click "📄 Download Full Report" for detailed text report

### Via Command Line

Run the validator directly from Python:

```python
from database import DatabaseManager
from duplicate_validator import DuplicateValidator

# Initialize database
db = DatabaseManager()

# Create validator
validator = DuplicateValidator(db)

# Run validation
results = validator.validate_duplicates()

# Generate report
report = validator.generate_report(results, format='text')
print(report)
```

### Using the Demo Script

Test the validator with sample data:

```bash
python demo_duplicate_validation.py
```

This creates a realistic test scenario with:
- Tyler White: 100% duplication (monthly + weekly files)
- Sarah Johnson: ~70% duplication (partial overlap)
- Mike Chen: No duplication (monthly only)

## Understanding Results

### Validation Status

- **✅ PASS**: No duplicates detected - all message counts are accurate
- **⚠️ DUPLICATES_FOUND**: Some users have duplicate records - review details
- **🚫 ERROR**: Validation failed - check error message

### Metrics Explained

**Total Messages in DB**: Sum of all message records in the database (including duplicates)

**Unique Messages**: True count after deduplicating overlapping periods

**Duplicate Messages**: Number of messages counted more than once

**Duplication Rate**: Percentage of duplicate messages (e.g., 43% means nearly half of all messages are duplicates)

**Duplication Factor**: How many times data is duplicated
- 1.0 = No duplicates
- 2.0 = Double-counted (100% duplication)
- 1.5 = 50% of messages are duplicates

### Per-User Validation

Each user receives a validation status:

- **PASS**: User's message counts are accurate (no duplicates)
- **FAIL**: User has duplicate records - counts may be inflated

Example output:
```
❌ Tyler White (tyler.white@example.com)
   Department: Engineering
   Total Messages: 15,378
   Unique Messages: 10,733
   Duplicate Messages: 4,644
   Status: FAIL
   
   Feature Breakdown:
     ⚠️ DUPLICATE ChatGPT Messages:
       - Total: 14,378
       - Unique: 10,033
       - Duplication Factor: 1.43x
```

This indicates:
- Tyler's total in the database is 15,378 messages
- The true unique count is 10,733 messages
- 4,644 messages (30%) are duplicates
- Caused by 1.43x duplication factor (43% duplication)

## Resolving Duplicates

If duplicates are detected, follow these steps:

### Step 1: Identify Overlapping Files

Review the "Duplicate Record Details" section to see which files are causing duplicates:

```
Files: monthly_may_2025.csv, weekly_2025_w18.csv
```

This indicates both files contain the same data for the same period.

### Step 2: Decide Which Files to Keep

Choose one of these strategies:

**Option A: Keep Monthly, Remove Weekly**
- Monthly files provide complete month coverage
- Remove all weekly files for the same period
- Recommended for most use cases

**Option B: Keep Weekly, Remove Monthly**
- Weekly files provide granular week-by-week analysis
- Remove monthly file for the same period
- Recommended for trend analysis

**Option C: Import Only One Type**
- Going forward, import either weekly OR monthly files, not both
- Most reliable way to prevent duplicates

### Step 3: Delete Overlapping Files

1. Navigate to **"🔧 Database Management"** tab
2. Find the duplicate file in the "Data by File" section
3. Click "Delete" to remove that file's records
4. Confirm deletion

### Step 4: Re-Run Validation

After deleting overlapping files:

1. Return to **"✅ Data Validation"** tab
2. Click **"Run Validation"** again
3. Verify status is now **"PASS"**
4. Confirm message counts are accurate

## Technical Details

### How Deduplication Works

The validator uses SQL window functions to identify and deduplicate records:

1. **Group Records**: Group by user, date, feature, and tool
2. **Count Duplicates**: Use COUNT(*) to find groups with > 1 record
3. **Calculate Unique**: For duplicate groups, divide usage_count by record_count
4. **Sum Unique**: Aggregate unique counts per user

Example SQL:
```sql
SELECT 
    email,
    feature_used,
    SUM(CASE 
        WHEN record_count = 1 THEN usage_count
        ELSE CAST(usage_count AS REAL) / record_count
    END) as dedup_messages
FROM (
    SELECT 
        email,
        date,
        feature_used,
        usage_count,
        COUNT(*) OVER (PARTITION BY email, date, feature_used, tool_source) as record_count
    FROM usage_metrics
)
GROUP BY email, feature_used
```

### Data Model

The validator checks the `usage_metrics` table with these key fields:

- `email`: User identifier
- `date`: Period start date (e.g., '2025-05-01')
- `feature_used`: Message type ('ChatGPT Messages', 'Tool Messages', etc.)
- `tool_source`: AI tool ('ChatGPT', 'BlueFlame AI', etc.)
- `usage_count`: Number of messages
- `file_source`: Originating filename

A duplicate is identified when multiple records share the same:
- `email` + `date` + `feature_used` + `tool_source`

### Tolerance and Precision

The validator uses exact matching with no tolerance:
- Any record with `record_count > 1` is flagged as a duplicate
- Duplication factor > 1.01 (1% threshold) marks a user as having duplicates
- This ensures even small duplicates are detected and reported

## API Reference

### DuplicateValidator Class

#### Constructor
```python
DuplicateValidator(db_manager: DatabaseManager)
```

#### Methods

**validate_duplicates()** → Dict[str, Any]
- Runs complete validation analysis
- Returns comprehensive results dictionary

**get_duplicate_details(email: str = None)** → pd.DataFrame
- Returns detailed duplicate records
- Optional: filter by specific user email

**generate_report(results: Dict, format: str = 'text')** → str
- Generates human-readable report
- Formats: 'text' or 'json'

**get_user_validation_status(email: str)** → Dict[str, Any]
- Returns validation status for specific user
- Includes all duplicate details for that user

### Results Structure

```python
{
    'timestamp': '2025-10-30T17:48:51.200969',
    'overall_status': 'DUPLICATES_FOUND',  # or 'PASS', 'ERROR'
    'total_users_checked': 3,
    'users_with_duplicates': 2,
    'duplicate_records_found': 3,
    'users': [
        {
            'email': 'user@example.com',
            'user_name': 'User Name',
            'department': 'Department',
            'total_messages': 15378,
            'unique_messages': 10733,
            'duplicate_messages': 4644,
            'has_duplicates': True,
            'validation_status': 'FAIL',
            'features': [...]
        }
    ],
    'summary': {
        'total_messages_in_db': 22165,
        'unique_messages': 15498,
        'duplicate_messages': 6667,
        'duplication_percentage': 43.02
    }
}
```

## Best Practices

### Prevention

1. **Choose One Data Cadence**: Import either weekly OR monthly files, not both
2. **Track Imports**: Keep a log of which files you've imported
3. **Date Ranges**: Be aware of which periods each file covers
4. **File Naming**: Use consistent naming that includes period (e.g., `monthly_2025_05.csv`)

### Regular Validation

1. **After Every Import**: Run validation after importing new data
2. **Before Reporting**: Validate before generating executive reports
3. **Monthly Check**: Run validation monthly as part of data hygiene
4. **After Bulk Imports**: Always validate after importing multiple files

### Data Quality Workflow

```
1. Import Data → 2. Run Validation → 3. Review Results → 4. Fix Duplicates → 5. Re-validate → 6. Confirm PASS
```

## Troubleshooting

### "No data to validate"

**Cause**: Database is empty or has no ChatGPT message records

**Solution**: 
- Import usage data first via the main dashboard
- Ensure imported files contain ChatGPT message data

### "Validation shows duplicates but files are different"

**Cause**: Different files may cover the same time periods

**Example**: 
- `monthly_may.csv` covers May 1-31
- `weekly_w18.csv` covers May 1-7
- These overlap even though filenames differ

**Solution**:
- Check the `date` field, not just filename
- Review "Duplicate Record Details" to see exact overlapping periods

### "Duplication factor seems incorrect"

**Cause**: Partial period overlaps

**Example**:
- Monthly file: 1,000 messages for May
- Weekly files: 400 messages for first 2 weeks of May only
- Duplication: 1,400 total vs. 1,000 unique = 1.4x factor

**Solution**: This is expected for partial overlaps

### "Validation is slow"

**Cause**: Large database with millions of records

**Solution**:
- Validation typically takes < 5 seconds for < 100K records
- For larger databases (> 1M records), may take 30-60 seconds
- Consider using database indexes (automatically created)

## FAQ

**Q: Will validation modify my data?**
A: No, validation is read-only. It never modifies or deletes data.

**Q: Can I run validation while the dashboard is being used?**
A: Yes, validation is safe to run at any time without impacting other operations.

**Q: What if I want to keep both weekly and monthly data?**
A: The system doesn't prevent this, but you should understand the duplication and use the unique counts for reporting.

**Q: How often should I run validation?**
A: After every data import, and at least once monthly.

**Q: Can validation detect other data quality issues?**
A: Currently, it focuses on duplicates. For other issues, use the existing `chatgpt_data_validator.py` tool.

**Q: What happens if validation finds duplicates?**
A: Nothing automatically - you decide whether to keep or remove duplicates based on your needs.

## Related Documentation

- `chatgpt_data_validator.py` - Validates weekly sums match monthly totals
- `DATA_VALIDATION_GUIDE.md` - General data validation guide
- `database.py` - Database management functions
- `app.py` - Main Streamlit dashboard

## Support

For issues or questions about duplicate validation:

1. Review this guide
2. Run the demo script: `python demo_duplicate_validation.py`
3. Check validation report for specific error messages
4. Review the code in `duplicate_validator.py`

## Version History

- **v1.0** (2025-10-30): Initial release
  - Core duplicate detection
  - Streamlit UI integration
  - Comprehensive reporting
  - Demo script and tests
