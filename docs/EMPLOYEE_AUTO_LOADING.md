# Employee Auto-Loading Feature

## Overview
The dashboard now automatically loads employee master data from CSV files in the repository on app startup. This eliminates the need for manual employee file uploads through the UI.

## How It Works

### Automatic Detection
When the Streamlit app initializes, it automatically scans for employee CSV files in the repository root directory using flexible glob patterns:
- `Employee Headcount*Emails.csv` (preferred - e.g., "Employee Headcount 2025_Emails.csv")
- `Employee Headcount*.csv` (fallback - e.g., "Employee Headcount 2025.csv")

**Supported file naming patterns:**
- `Employee Headcount 2025_Emails.csv` ✅
- `Employee Headcount October 2025_Emails.csv` ✅
- `Employee Headcount Nov 2025_Emails.csv` ✅
- `Employee Headcount Q4 2025_Emails.csv` ✅
- `Employee Headcount 2025.csv` ✅
- `Employee Headcount October 2025.csv` ✅
- Any file matching the pattern `Employee Headcount*.csv` ✅

### Loading Process
1. **File Detection**: Uses glob patterns to find employee CSV files in the repository:
   - Pattern 1: `Employee Headcount*Emails.csv` (preferred)
   - Pattern 2: `Employee Headcount*.csv` (fallback)
   - Files are sorted in reverse alphabetical order (newest dates typically come first)
   - Duplicate matches are automatically deduplicated
2. **Column Mapping**: Automatically maps CSV columns to database schema:
   - `First Name` → `first_name`
   - `Last Name` → `last_name`
   - `Email` → `email`
   - `Title` → `title`
   - `Function` → `department`
   - `Status` → `status`
3. **Database Loading**: Loads employees into the `employees` table
4. **Marker Creation**: Creates a `.{filename}.loaded` marker file to prevent reloading

### Smart Caching
- Uses marker files to avoid reloading employees on every app restart
- Only loads when:
  - No marker file exists
  - Employee count in database is 0
- Marker files are excluded from git via `.gitignore`

## Benefits

### For Users
- ✅ **Zero Configuration**: No manual file uploads required
- ✅ **Instant Availability**: Employee data ready on first app start
- ✅ **Always Current**: Update the CSV in repo to refresh employee data
- ✅ **Department Mapping**: Automatic department assignment for AI usage

### For Developers
- ✅ **Version Controlled**: Employee master file tracked in git
- ✅ **Consistent Data**: Same employee data across all deployments
- ✅ **Easy Updates**: Simply replace CSV file and restart app

## File Format

### Expected CSV Structure
```csv
Last Name,First Name,Title,Function,Status,Email
Abbot,Sebastian,Senior Director,Product Development,ECMS,sebastian.abbot@eldridge.com
Ahern,Corinne,Associate,Corporate Credit - Manufacturing,ECMS,corinne.ahern@eldridge.com
```

### Column Descriptions
- **Last Name**: Employee last name (required)
- **First Name**: Employee first name (required)
- **Title**: Job title (optional)
- **Function**: Department/functional area (maps to department field)
- **Status**: Employment status (optional)
- **Email**: Employee email address (optional but recommended)

## Features Enabled

When employee data is loaded, the following features become available:

1. **Department Analytics**
   - Usage breakdown by department
   - Cost allocation per department
   - Power users by department

2. **Employee Identification**
   - Distinguish employees from external users
   - Track unidentified users (not in employee roster)

3. **Accurate Department Mapping**
   - AI usage automatically mapped to correct departments
   - Employee master file is authoritative source for departments

4. **Power User Detection**
   - Identify top users within departments
   - Track engagement by employee role

## Updating Employee Data

### Option 1: Replace CSV File
1. Update or create a new CSV file in repository (ensure it matches the naming pattern)
2. Delete marker file: `rm .Employee\ Headcount*.loaded` (or the specific marker file)
3. Restart the app

### Option 2: Manual Upload
1. Use the "Employee Master File" section in the UI
2. Upload updated CSV through file uploader
3. Data will be merged with existing records

## Naming Flexibility

The auto-load feature now supports flexible file naming! Any of these patterns will work:
- `Employee Headcount YYYY_Emails.csv` (year only)
- `Employee Headcount Month YYYY_Emails.csv` (month and year)
- `Employee Headcount QX YYYY_Emails.csv` (quarter and year)
- Same patterns without `_Emails` suffix

The system will automatically:
- Find all matching files
- Sort them (typically newest first based on filename)
- Load the first valid file found
- Create a marker to prevent reloading

## Technical Details

### Implementation Location
- **File**: `app.py`
- **Function**: `auto_load_employee_file(db_manager)`
- **Called From**: `init_app()` (cached with `@st.cache_resource`)

### Database Schema
```sql
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    title TEXT,
    department TEXT,
    status TEXT,
    created_at TEXT,
    updated_at TEXT
)
```

### Marker File Format
```
Loaded on 2025-10-22T03:10:45.123456
Records: 283
```

## Troubleshooting

### Employees Not Loading
1. **Check file name pattern**: File must match `Employee Headcount*.csv` pattern
   - Good: `Employee Headcount 2025_Emails.csv`
   - Good: `Employee Headcount October 2025.csv`
   - Bad: `employee headcount 2025.csv` (lowercase)
   - Bad: `Staff Headcount 2025.csv` (wrong prefix)
2. Verify column names match expected format
3. Check app logs for `[auto_load_employee_file]` messages
4. Delete marker files and restart app: `rm .Employee\ Headcount*.loaded`
5. Ensure file is in repository root (same directory as `app.py`)

### Duplicate Employees
- Employees are matched by email or name
- Existing records are updated, not duplicated
- Check database directly: `SELECT * FROM employees`

### Performance
- Loading ~300 employees takes < 1 second
- Marker file prevents reloading on subsequent starts
- No performance impact on normal app usage

## Example Usage

```python
# In app.py initialization
@st.cache_resource
def init_app():
    db = DatabaseManager()
    processor = DataProcessor(db)
    scanner = FileScanner(FILE_TRACKING_PATH)
    
    # Auto-load employee file if it exists
    auto_load_employee_file(db)
    
    return db, processor, scanner
```

## Future Enhancements

Possible improvements:
- Support multiple employee file formats
- Automatic refresh on file change detection
- Employee sync from HR systems
- Historical employee data tracking
- Department hierarchy support
