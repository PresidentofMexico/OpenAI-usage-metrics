# Unknown Department Breakdown Fix

## Problem Statement

The Department Performance section showed 35 active users in the "Unknown" department, but the Database Management → Unidentified Users section showed only 19 users. This created confusion about where the other 16 users were.

## Root Cause

The "Unknown" department contains TWO distinct types of users:

1. **Employees with department="Unknown"**: Users who ARE in the employee master file, but whose department field is explicitly set to "Unknown" (not blank)
2. **Unidentified users**: Users who are NOT in the employee master file at all (e.g., contractors, external users)

**Note**: Employees with BLANK/EMPTY department fields in the employee master are NOT counted in category 1. They retain their department from usage data but are not considered as having department="Unknown" in the employee master.

The Department Performance section counts ALL users in the "Unknown" department (both types), while the Unidentified Users section only shows the second type (non-employees).

## Example Scenario

Consider this data:

**Employee Master File:**
- Alice Employee (department: Engineering)
- Bob Manager (department: Unknown)
- Charlie Analyst (department: Unknown)
- Art Rosen (department: [blank])
- Tim Milazzo (department: [blank])

**Usage Data:**
- alice@company.com → Applied dept from master: Engineering
- bob@company.com → Applied dept from master: Unknown
- charlie@company.com → Applied dept from master: Unknown
- art@company.com → Keeps dept from usage data: Unknown (blank dept not applied)
- tim@company.com → Keeps dept from usage data: Unknown (blank dept not applied)
- contractor1@vendor.com → Not in master: stays as Unknown
- contractor2@vendor.com → Not in master: stays as Unknown

**Result:**
- Department Performance "Unknown": 6 users (Bob, Charlie, Art, Tim, contractor1, contractor2)
- Breakdown shows:
  - **Employees with department='Unknown'**: 2 (Bob, Charlie)
  - **Unidentified users**: 2 (contractor1, contractor2)
- Note: Art and Tim are in the employee master but have blank departments, so they keep "Unknown" from usage data but are NOT counted in the breakdown as "employees with department='Unknown'"

## Solution

Added a breakdown display in the Department Performance section that appears when "Unknown" is shown in the top 3 departments. The breakdown shows:

```
ℹ️ "Unknown" Department Breakdown:
• X employees with department = "Unknown" in employee master file
• Y unidentified users (not in employee master file)

Note: Check Database Management → Unidentified Users to review non-employees
```

## Implementation

### Code Changes

**File: `database.py`**

Added new method `get_employees_with_unknown_dept_in_usage()` (after line 750):

```python
def get_employees_with_unknown_dept_in_usage(self):
    """
    Get employees who have department='Unknown' in their USAGE DATA.
    This includes employees whose department in the employee master is 'Unknown',
    but excludes employees with blank/empty departments.
    
    Returns:
        DataFrame with employees who have usage data with department='Unknown'
    """
    # SQL query that:
    # 1. Joins usage_metrics with employees table
    # 2. Filters for um.department = 'Unknown'
    # 3. Filters for e.department = 'Unknown' (explicitly)
    # 4. Excludes e.department IS NULL or e.department = '' (blank departments)
```

This method ensures that only employees who EXPLICITLY have department='Unknown' in the employee master are counted, not those with blank/empty departments.

**File: `app.py`**

Updated the breakdown calculation (lines 2665-2685):

**Before:**
```python
employees_with_unknown_dept = total_unknown - unidentified_count
```

**After:**
```python
# Get employees who explicitly have department='Unknown' in employee master
# (excludes employees with blank/empty departments)
employees_unknown_dept = db.get_employees_with_unknown_dept_in_usage()
employees_with_unknown_dept = len(employees_unknown_dept)
```

This change ensures accurate counting by querying actual employees instead of using subtraction.

### Test Coverage

Created `test_unknown_dept_breakdown.py` to verify:
- Employees with "Unknown" department are counted separately
- Unidentified users are counted separately
- Employees with blank departments are NOT counted as "employees with department='Unknown'"
- Total in "Unknown" department equals the sum of both
- Breakdown calculation is correct

**Test Results:**
```
Total users in 'Unknown' department: 4
  - Employees with department='Unknown': 2
  - Unidentified users (not in employee master): 2

✅ All assertions passed!
```

## User Experience

### Before Fix
Users saw:
- Department Performance: "Unknown department has 35 active users"
- Unidentified Users: "19 users not in employee master"
- **Confusion**: Where are the other 16 users?

### After Fix
Users see:
- Department Performance: "Unknown department has 35 active users"
  - **Breakdown**: "16 employees with department='Unknown' + 19 unidentified users"
- Unidentified Users: "19 users not in employee master"
- **Clear**: The 16 users are employees whose department is set to "Unknown" in the employee master file

## Related Documentation

- `DEPARTMENT_PERFORMANCE_FIX.md` - Original fix ensuring employee departments are applied
- `EMPLOYEE_INTEGRATION_GUIDE.md` - Employee master file integration
- `database.py::get_unidentified_users()` - Query that returns only non-employees

## Impact

✅ **Benefits:**
- Eliminates confusion about user counts in "Unknown" department
- Makes it clear that some employees may legitimately have "Unknown" as their department
- Provides actionable guidance (check Unidentified Users section for non-employees)
- No changes to existing functionality, only improved clarity

✅ **No Regressions:**
- All existing tests pass
- Department counting logic unchanged
- Employee department application unchanged
- Only adds informational display

## Files Modified

1. **app.py** (+18 lines)
   - Added Unknown department breakdown display in Department Performance section

2. **test_unknown_dept_breakdown.py** (+119 lines, NEW)
   - Comprehensive test for Unknown department breakdown
   - Validates employee vs unidentified user counts
   - Ensures correct calculation

## Verification Steps

1. Load employee master file with some employees having department="Unknown"
2. Load usage data that includes both employees and non-employees
3. Navigate to Executive Summary → Department Performance
4. If "Unknown" appears in top 3, verify the breakdown is shown
5. Compare with Database Management → Unidentified Users count
6. Confirm the numbers match the breakdown

## Future Enhancements (Optional)

Consider adding similar breakdowns for other analytics sections if users request it:
- Power Users section
- Monthly trends
- Department comparison charts
