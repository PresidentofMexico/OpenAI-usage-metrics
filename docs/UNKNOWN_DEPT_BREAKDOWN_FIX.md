# Unknown Department Breakdown Fix

## Problem Statement

The Department Performance section showed 35 active users in the "Unknown" department, but the Database Management → Unidentified Users section showed only 19 users. This created confusion about where the other 16 users were.

## Root Cause

The "Unknown" department contains TWO distinct types of users:

1. **Employees with department="Unknown"**: Users who ARE in the employee master file, but whose department field is set to "Unknown"
2. **Unidentified users**: Users who are NOT in the employee master file at all (e.g., contractors, external users)

The Department Performance section counts ALL users in the "Unknown" department (both types), while the Unidentified Users section only shows the second type (non-employees).

## Example Scenario

Consider this data:

**Employee Master File:**
- Alice Employee (department: Engineering)
- Bob Manager (department: Unknown)
- Charlie Analyst (department: Unknown)

**Usage Data:**
- alice@company.com → Applied dept from master: Engineering
- bob@company.com → Applied dept from master: Unknown
- charlie@company.com → Applied dept from master: Unknown
- contractor1@vendor.com → Not in master: stays as Unknown
- contractor2@vendor.com → Not in master: stays as Unknown

**Result:**
- Department Performance "Unknown": 4 users (Bob, Charlie, contractor1, contractor2)
- Unidentified Users: 2 users (contractor1, contractor2)
- Discrepancy: 4 - 2 = 2 (Bob and Charlie are employees with Unknown dept)

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

**File: `app.py`**

Added after displaying each top department (lines 2665-2682):

```python
# Add breakdown for "Unknown" department if present
if row['Department'] == 'Unknown':
    # Get breakdown of Unknown department users
    unidentified_users = db.get_unidentified_users()
    unidentified_count = len(unidentified_users)
    total_unknown = int(row['Active Users'])
    employees_with_unknown_dept = total_unknown - unidentified_count
    
    st.markdown(f"""
    <div style="margin-top: 0.5rem; padding: 0.5rem; background: var(--background-secondary); border-radius: 0.5rem; border-left: 3px solid #f59e0b;">
        <p style="margin: 0; font-size: 0.75rem; color: var(--text-secondary); font-weight: 600;">ℹ️ "Unknown" Department Breakdown:</p>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; color: var(--text-tertiary);">
            • <strong>{employees_with_unknown_dept}</strong> employees with department = "Unknown" in employee master file<br>
            • <strong>{unidentified_count}</strong> unidentified users (not in employee master file)
        </p>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.7rem; color: var(--text-tertiary); font-style: italic;">
            Note: Check Database Management → Unidentified Users to review non-employees
        </p>
    </div>
    """, unsafe_allow_html=True)
```

### Test Coverage

Created `test_unknown_dept_breakdown.py` to verify:
- Employees with "Unknown" department are counted separately
- Unidentified users are counted separately
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
