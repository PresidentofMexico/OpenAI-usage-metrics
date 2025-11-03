# Employee Master File Integration

## Overview

The dashboard now supports integration of a master employee file to serve as the single source of truth for user data and department assignments. This ensures data consistency, allows for the identification of non-employee tool usage, and streamlines department mapping.

## Features

### 1. Automatic Employee File Loading (New!)
- **Auto-loads employee file on app startup** if it exists in the repository
- **Flexible file naming** using glob patterns:
  - Primary: `Employee Headcount*Emails.csv` (e.g., "Employee Headcount 2025_Emails.csv")
  - Fallback: `Employee Headcount*.csv` (e.g., "Employee Headcount 2025.csv")
- **Supported naming patterns:**
  - `Employee Headcount 2025_Emails.csv` ✅
  - `Employee Headcount October 2025_Emails.csv` ✅
  - `Employee Headcount Nov 2025_Emails.csv` ✅
  - `Employee Headcount Q4 2025.csv` ✅
  - Any variation matching `Employee Headcount*.csv` ✅
- **Smart caching** with marker files prevents duplicate loads
- **Works in any deployment environment** - uses script directory, not working directory
- **Zero configuration required** - just place the employee file in the repository root

### 2. Employee Data Store
- **New `employees` table** in the database stores the master list of full-time employees
- Schema includes:
  - `employee_id` (Primary Key)
  - `first_name`, `last_name` (TEXT)
  - `email` (TEXT, UNIQUE)
  - `title` (TEXT)
  - `department` (TEXT) - Sourced from the 'Function' column in employee file
  - `status` (TEXT) - From the 'Status' column
  - `created_at`, `updated_at` (Timestamps)

### 2. Employee File Upload
- **File uploader in Database Management tab** for uploading employee roster
- Supports **CSV and Excel** formats
- **Column mapping interface** to map your file's columns to the required fields
- **Automatic deduplication** - Updates existing employees based on email

### 3. Automatic Department Assignment
- When processing AI tool usage files, the system:
  - Looks up each user's email in the employee table
  - **For employees**: Uses department from employee table (overrides tool export data)
  - **For non-employees**: Flags with 'Unidentified User' department

### 4. Enhanced Department Mapper
- **Dynamically populated departments** from employee table
- **Read-only departments** for employees (sourced from master file)
- **Editable mapping** for unidentified users only
- **Filter options**: View all users, employees only, or unidentified only
- **Visual indicators**: ✅ for employees, ⚠️ for unidentified users

### 5. Unidentified Users Tracking
- **Dedicated section** in Department Mapper shows all users not in employee roster
- Displays:
  - User name and email
  - Tools used
  - Total usage and cost
  - Days active

## Employee File Format

### Required Columns
Your employee file should contain these columns (exact names can be mapped during upload):

| Column | Description | Example |
|--------|-------------|---------|
| First Name | Employee's first name | John |
| Last Name | Employee's last name | Doe |
| Email | Employee's email address (unique) | john.doe@company.com |
| Title | Job title or position | Senior Engineer |
| Function | Department/Function | Engineering |
| Status | Employment status | Active |

### Sample CSV Format
```csv
First Name,Last Name,Email,Title,Function,Status
John,Doe,john.doe@company.com,Senior Engineer,Engineering,Active
Jane,Smith,jane.smith@company.com,Product Manager,Product,Active
Bob,Johnson,bob.johnson@company.com,Data Analyst,Analytics,Active
```

### Sample Excel Format
The same structure works for Excel files (.xlsx). The uploader will read the first sheet.

## Usage Instructions

### Quick Start (Automatic Loading)
If you have an employee file matching the supported pattern in your repository root:
- `Employee Headcount*Emails.csv` (any variation with month/year/quarter)
- `Employee Headcount*.csv` (any variation)

**The app will automatically load it on startup!** No manual upload needed.

Examples of files that will auto-load:
- `Employee Headcount 2025_Emails.csv` ✅
- `Employee Headcount October 2025_Emails.csv` ✅
- `Employee Headcount Q4 2025.csv` ✅
- `Employee Headcount Nov 2025_Emails.csv` ✅

### Manual Upload (Alternative Method)

### Step 1: Upload Employee Master File
1. Navigate to the **"🔧 Database Management"** tab
2. Find the **"👥 Employee Master File"** section
3. Click **"Upload Employee Master File"** button
4. Select your CSV or Excel file
5. Map your file's columns to the required fields:
   - Map "Function" column to "Department Column (Function)"
   - Map other columns as appropriate
6. Click **"📥 Load Employees"**

### Step 2: Upload AI Tool Usage Data
1. Upload your OpenAI or BlueFlame usage exports as usual
2. The system will automatically:
   - Look up each user in the employee table
   - Assign departments from employee data for known users
   - Flag unidentified users

### Step 3: Review Unidentified Users
1. Go to the **"🏢 Department Mapper"** tab
2. Review the **"⚠️ Unidentified Users"** section
3. These are users who used AI tools but aren't in your employee roster:
   - Could be contractors, external users, or recently departed employees
   - Can be manually assigned departments if needed

### Step 4: Manage Department Mappings
1. Use the **"All Users"** table in Department Mapper
2. **Employee departments are read-only** (🔒 icon) - they come from the master file
3. **Unidentified users can be mapped** to appropriate departments
4. Use filters to focus on specific user types
5. Click **"💾 Save All Department Mappings"** to persist changes

## Benefits

### Data Consistency
- Single source of truth for employee data
- Prevents department mismatches between tools
- Ensures accurate reporting by department

### Non-Employee Detection
- Identify contractor and external tool usage
- Track usage by recently departed employees
- Audit tool access across organization

### Simplified Management
- No need to manually map every user's department
- Automatic department updates when employee file is re-uploaded
- Clear separation between employee and non-employee usage

## Technical Notes

### Database Schema
The employee table is created automatically when the application initializes:
```sql
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE NOT NULL,
    title TEXT,
    department TEXT,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### Employee Lookup Process
1. When normalizing usage data, each user email is looked up in the employees table
2. If found: department and name are taken from employee record
3. If not found: department is set to 'Unidentified User'

### Updates and Maintenance
- Re-upload employee file anytime to update employee data
- Existing employee records are updated based on email (UNIQUE constraint)
- New employees are added automatically
- Historical usage data is not retroactively updated

## Troubleshooting

### Auto-load not working
- **Check file name pattern**: Must match `Employee Headcount*.csv`
  - ✅ Good: `Employee Headcount 2025_Emails.csv`
  - ✅ Good: `Employee Headcount October 2025.csv`
  - ❌ Bad: `employee headcount 2025.csv` (lowercase 'e')
  - ❌ Bad: `Staff Headcount 2025.csv` (wrong prefix)
  - ❌ Bad: `Employee_Headcount_2025.csv` (underscores instead of spaces)
- File must be in the repository root (same directory as `app.py`)
- Check application logs for `[auto_load_employee_file]` messages
- Marker files (`.*.loaded`) prevent duplicate loads - delete them to force reload:
  ```bash
  rm .Employee\ Headcount*.loaded
  ```

### "No employees loaded yet"
- Upload an employee master file first in the Database Management tab

### "Unidentified User" appearing for known employees
- Verify the email address in your employee file matches exactly (case-insensitive)
- Re-upload employee file if recently updated
- Check that employee has 'Active' status

### Department not updating for employee
- Employee departments are read-only and come from the master file
- Update the employee file and re-upload to change departments
- Manual department mappings only apply to unidentified users

## API Reference

### Database Methods

```python
# Load employees from DataFrame
success, message, count = db.load_employees(employee_df)

# Get employee by email
employee = db.get_employee_by_email('user@company.com')

# Get all employees
employees_df = db.get_all_employees()

# Get unique departments from employee table
departments = db.get_employee_departments()

# Get users not in employee table
unidentified_df = db.get_unidentified_users()

# Get employee count
count = db.get_employee_count()
```

## Future Enhancements

Potential improvements for future versions:
- Import employee data from HR systems (HRIS API integration)
- Historical tracking of employee department changes
- Automated alerts for high usage by unidentified users
- Employee onboarding/offboarding workflow integration
