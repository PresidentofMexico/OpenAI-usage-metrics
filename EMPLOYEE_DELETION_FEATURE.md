# Employee Deletion Feature Documentation

## Overview
This feature enables administrators to manage the employee roster by excluding or deleting individual employees from the database. This is particularly useful when employees resign, terminate, or are contract workers who should be removed from analytics.

## Feature Location
The employee deletion functionality is located in the **Database Management** tab (Tab 5) of the AI Usage Analytics Dashboard.

## Access the Feature
1. Navigate to the **🔧 Database Management** tab
2. Locate the **👥 Employee Master File** section
3. Click the **👁️ View Employees** button to display the employee list

## Functionality

### Employee List Display
When you click "View Employees", the interface shows:
- **Search Bar**: Filter employees by name or email
- **Employee Cards**: Each showing:
  - Full name
  - Email address
  - Department
  - Current status
  - 🗑️ Delete button

### Deletion Options
When you click the 🗑️ delete button for an employee, you'll see three options:

#### 1. ❌ Cancel
- Cancels the deletion operation
- No changes are made to the database

#### 2. 🗑️ Delete Employee Only
- Removes the employee from the employee roster
- **Keeps all their usage data** in analytics
- Use this when:
  - You want to maintain historical usage records
  - The employee contributed significantly to metrics
  - You need to preserve data for reporting/compliance

#### 3. 💣 Delete All Data
- Removes the employee from the roster
- **Deletes all their usage records** from analytics  
- Use this when:
  - An employee was added in error
  - Contract worker data should not be included
  - Complete removal is required for privacy/legal reasons

## Impact on Analytics

### Employee-Only Deletion
- Employee removed from employee master list
- Usage data **remains** in all dashboards and reports
- Department assignments from deleted employee remain unchanged
- Historical analytics are **preserved**

### Complete Deletion (Employee + Usage)
- Employee removed from employee master list
- All usage records **deleted** from database
- Metrics **automatically update** across:
  - Executive Summary totals
  - Department breakdowns
  - Power User rankings
  - Cost calculations
  - All other analytics
- Cache is cleared to ensure fresh data

## Data Safety

### Confirmation Flow
1. Click 🗑️ button
2. Warning message appears
3. Must click a second time to confirm
4. Success message confirms completion

### No Undo
⚠️ **Warning**: Deletions are permanent. There is no undo function. Always verify before confirming deletion.

### Best Practices
1. **Before Deleting**: Review the employee's usage metrics to understand impact
2. **Download First**: Consider exporting data before major deletions
3. **Communicate**: Inform stakeholders of significant employee removals
4. **Document**: Keep records of why employees were removed

## Technical Details

### Database Operations
- Employee records stored in `employees` table
- Usage metrics stored in `usage_metrics` table  
- Deletions use SQL transactions for data integrity
- Foreign key relationships handled automatically

### Affected Tables
1. **Employee-Only**: `employees` table
2. **Complete**: Both `employees` and `usage_metrics` tables

### Metrics Recalculation
After a complete deletion:
- Total cost recalculated
- User counts updated
- Department metrics refreshed
- Power user rankings recomputed
- All charts and graphs update automatically

## Use Cases

### Terminated Employee
**Scenario**: Employee has left the company
**Action**: Delete Employee Only
**Reason**: Preserve historical contribution to company metrics

### Contract Worker  
**Scenario**: Short-term contractor accidentally added to roster
**Action**: Delete All Data
**Reason**: Contract workers may not count toward headcount/metrics

### Data Entry Error
**Scenario**: Employee added with wrong information
**Action**: Delete All Data, then re-add correctly
**Reason**: Clean slate for accurate data

### Privacy Request
**Scenario**: Former employee requests data removal
**Action**: Delete All Data
**Reason**: Comply with privacy regulations

## Testing

A comprehensive test suite (`test_delete_employee.py`) validates:
- ✅ Employee-only deletion
- ✅ Usage-only deletion  
- ✅ Complete deletion (employee + usage)
- ✅ Metrics update correctly after deletion
- ✅ Type conversion for numpy int64 IDs

## API Reference

### DatabaseManager Methods

```python
# Delete employee from roster only
success, message = db.delete_employee(employee_id)

# Delete usage data only
success, message, records_deleted = db.delete_employee_usage(email)

# Delete employee and all usage data
success, message = db.delete_employee_and_usage(employee_id)
```

### Return Values
- `success`: Boolean indicating if operation succeeded
- `message`: Human-readable success or error message
- `records_deleted`: Number of usage records removed (usage deletion only)

## Troubleshooting

### Employee Not Found
- Verify employee exists in database
- Check employee_id is correct
- Ensure no concurrent deletions occurred

### Deletion Failed
- Check database permissions
- Verify database file is not read-only
- Look for constraint violations in logs

### Metrics Not Updating
- Click "🔄 Refresh Dashboard" in Database Management
- Clear browser cache
- Restart Streamlit application

## Future Enhancements

Potential improvements for future releases:
- Bulk deletion for multiple employees
- Soft delete with recovery option
- Export employee data before deletion
- Audit log of all deletions
- Role-based access control for deletions

## Support

For issues or questions about the employee deletion feature:
1. Check the test suite for examples
2. Review database logs for error details
3. Contact the development team with specific error messages
