# Duplicate File Processing Prevention

## Overview

The OpenAI Usage Metrics Dashboard now includes **automatic duplicate detection** to prevent the same file from being processed multiple times. This ensures data integrity and accurate analytics when managing multiple CSV exports.

## Problem Addressed

Previously, if you uploaded the same file twice (either manually or through auto-scan), the system would:
- ❌ Insert duplicate records into the database
- ❌ Double-count usage metrics and costs
- ❌ Show inflated user counts and activity
- ❌ Provide no warning that data was already loaded

This made it difficult to verify data integrity, especially when managing 45+ files.

## Solution Implemented

### 1. Database-Level Duplicate Detection

The system now checks if a file has already been processed **before** inserting any data:

```python
# When processing a file, the system automatically checks:
file_check = db.check_file_exists(filename)
if file_check['exists']:
    # Returns details about existing data and prevents re-processing
    return warning_message
```

**What gets checked:**
- Exact filename match (`file_source` column in database)
- Record count, user count, and date range of existing data
- Prevents insertion of duplicate records

### 2. Enhanced User Interface

**File Upload Flow:**
- Shows clear warning when duplicate file is detected
- Displays existing data stats (records, users, date range)
- Provides guidance on how to handle duplicates

**Database Management Tab:**
- Lists all processed files with detailed metadata
- Shows tool source (ChatGPT, BlueFlame AI, etc.)
- Displays record count and user count per file
- Allows selective deletion of files if re-processing is needed

### 3. File Tracking Integration

Works seamlessly with existing file scanner tracking (`file_tracking.json`):
- File scanner prevents auto-processing of already-scanned files
- Database check provides additional safety net
- Two-layer protection ensures no duplicates

## How It Works

### Automatic Protection (Default Behavior)

When you upload a file:

1. **First Upload:** ✅ File processes successfully
   ```
   ✅ Upload Complete!
   - Processed 358 records
   - Source: ChatGPT
   - File: openai_september_2024.csv
   ```

2. **Duplicate Upload:** ⚠️ System detects and prevents
   ```
   ⚠️ File 'openai_september_2024.csv' was already processed!
   Existing data: 358 records, 159 users, date range: 2024-09-01 to 2024-09-30
   Skipping to prevent duplicate data.
   
   💡 If you want to re-process this file, first delete it from 
   the Database Management tab, then upload again.
   ```

### Manual Override (If Needed)

If you need to intentionally re-process a file:

**Option 1: Delete and Re-upload**
1. Go to "Database Management" tab
2. Find the file in "Upload History & File Management"
3. Click the 🗑️ button next to the file
4. Confirm deletion
5. Upload the file again

**Option 2: Programmatic Override**
```python
# For advanced users / API integration
processor.process_monthly_data(df, filename, skip_duplicates=False)
```

## Checking for Existing Duplicates

If you've already uploaded files before this feature was added, use the duplicate detection utility:

```bash
python check_database_duplicates.py
```

**Output Example:**
```
================================================================================
DATABASE DUPLICATE ANALYSIS
================================================================================
Database: openai_metrics.db
Analysis time: 2024-10-29 14:30:00

📊 OVERALL STATISTICS
--------------------------------------------------------------------------------
Total Records: 716
Unique Users: 187
Files Processed: 7

📁 FILES PROCESSED
--------------------------------------------------------------------------------
1. openai_september_2024.csv
   Tool: ChatGPT
   Records: 358
   Users: 159
   Date Range: 2024-09-01 to 2024-09-30

2. blueflame_september_2024.csv
   Tool: BlueFlame AI
   Records: 86
   Users: 28
   Date Range: 2024-09-01 to 2024-09-30

🔍 DUPLICATE DETECTION
--------------------------------------------------------------------------------
✅ No duplicate records detected!
   Your database is clean - each user/date/feature combination appears only once.

💡 RECOMMENDATIONS
--------------------------------------------------------------------------------
✅ Your database looks clean!
   - No duplicate records detected
   - Duplicate prevention is now active for all future uploads
   - You can safely upload your remaining files
```

## Testing

Run the comprehensive test suite to verify duplicate prevention:

```bash
python test_duplicate_prevention.py
```

**Tests Include:**
- ✅ First file upload succeeds
- ✅ Duplicate file upload is prevented
- ✅ File existence check works correctly
- ✅ Different files process successfully
- ✅ Manual override flag works
- ✅ File summary retrieval works

## API Reference

### Database Methods

#### `check_file_exists(file_source)`
Check if a file has already been processed.

**Returns:**
```python
{
    'exists': bool,
    'record_count': int,
    'user_count': int,
    'date_range': (min_date, max_date)
}
```

**Example:**
```python
db = DatabaseManager()
result = db.check_file_exists('openai_oct_2024.csv')

if result['exists']:
    print(f"File already processed: {result['record_count']} records")
else:
    print("File is new, ready to process")
```

#### `get_processed_files_summary()`
Get detailed summary of all processed files.

**Returns:** DataFrame with columns:
- `file_source`: Filename
- `record_count`: Number of records
- `user_count`: Number of unique users
- `tool_source`: AI tool (ChatGPT, BlueFlame AI, etc.)
- `min_date`, `max_date`: Date range coverage
- `created_at`: Upload timestamp

**Example:**
```python
db = DatabaseManager()
files_df = db.get_processed_files_summary()
print(files_df.to_string())
```

### Data Processor Methods

#### `process_monthly_data(df, filename, skip_duplicates=True)`
Process usage data with optional duplicate detection.

**Parameters:**
- `df`: DataFrame with normalized usage data
- `filename`: Source filename for tracking
- `skip_duplicates`: If True (default), check for duplicates before inserting

**Returns:** `(success: bool, message: str)`

**Example:**
```python
processor = DataProcessor(db)

# Automatic duplicate protection (default)
success, message = processor.process_monthly_data(df, 'file.csv')

# Force processing (override duplicate check)
success, message = processor.process_monthly_data(df, 'file.csv', skip_duplicates=False)
```

## FAQ

### Q: What if I need to re-upload a file with updated data?

**A:** Delete the old file first, then upload the new version:
1. Go to Database Management tab
2. Click 🗑️ next to the file
3. Confirm deletion
4. Upload the new file

### Q: Will this affect my existing data?

**A:** No. The duplicate prevention only affects **new** uploads. Your existing data remains unchanged. Use `check_database_duplicates.py` to analyze existing data for duplicates.

### Q: What if I have the same data in files with different names?

**A:** The system only checks filename matches. If you have `openai_sept.csv` and `openai_september.csv` with the same data, both will be processed. You'll need to manually check for this scenario.

### Q: How do I know if a file was already processed?

**A:** Check the "Database Management" tab → "Upload History & File Management" section. It lists all processed files with their statistics.

### Q: Does this work with auto-scan files?

**A:** Yes! Both manual uploads and auto-scanned files benefit from duplicate prevention.

### Q: Can I disable duplicate prevention?

**A:** For manual uploads, no - it's always active for safety. For programmatic access, you can use `skip_duplicates=False` parameter.

## Best Practices

1. **Before Uploading 45 Files:**
   - Run `check_database_duplicates.py` to check current state
   - Review the file list in Database Management tab
   - Clear database if needed (🗑️ Clear All Data button)

2. **Regular Monitoring:**
   - Check Database Management tab periodically
   - Verify file counts match your expectations
   - Use the duplicate checker utility after bulk uploads

3. **File Naming:**
   - Use consistent, descriptive names
   - Include date/period in filename (e.g., `openai_2024_october.csv`)
   - Avoid uploading renamed copies of the same data

4. **Data Validation:**
   - Compare total user counts with your organization size
   - Check date ranges match your expected coverage
   - Verify costs align with your licensing

## Technical Details

### How Duplicate Detection Works

1. **File Identification:** Uses `file_source` column in `usage_metrics` table
2. **Pre-Processing Check:** Queries database before inserting any records
3. **Metadata Retrieval:** Gets existing file stats for user feedback
4. **Graceful Handling:** Returns informative message instead of error

### Database Schema

The `file_source` column tracks origin:
```sql
CREATE TABLE usage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    user_name TEXT,
    email TEXT,
    department TEXT,
    date TEXT NOT NULL,
    feature_used TEXT,
    usage_count INTEGER,
    cost_usd REAL,
    tool_source TEXT DEFAULT 'ChatGPT',
    file_source TEXT,  -- <-- Used for duplicate detection
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### Performance Impact

- ✅ Minimal: Single database query before processing
- ✅ Fast: Uses indexed queries for file lookup
- ✅ Efficient: No impact on existing data retrieval

## Migration Notes

### Upgrading from Previous Version

No migration needed! The feature works immediately:

1. **Existing data:** Remains unchanged
2. **New uploads:** Automatically protected
3. **File tracking:** Integrates with existing `file_tracking.json`

### Checking Existing Database

Run the duplicate checker on your existing database:
```bash
python check_database_duplicates.py
```

If duplicates are found, you can:
1. Clean up by deleting duplicate files individually
2. Or clear database and re-upload all files (now protected)

## Support

**Issues or Questions?**
- Check Database Management tab for file list
- Run `check_database_duplicates.py` for detailed analysis
- Open an issue on GitHub with the output from the duplicate checker

**Related Documentation:**
- [Main README](../README.md)
- [Auto File Detection](AUTO_FILE_DETECTION.md)
- [Database Management](FEATURE_SUMMARY.md)
