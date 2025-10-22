# Quick Reference: Unknown Department Breakdown

## What was fixed?
Department Performance now shows a breakdown when "Unknown" is in the top 3 departments, explaining the difference between:
- Employees with department="Unknown" 
- Unidentified users (not in employee master)

## Where to see it?
**Executive Summary → Department Performance → Top 3 Departments**

If "Unknown" appears, you'll see:
```
🥇 Unknown                                      36.4% of total
   📊 Total Messages: 2,550
   👥 Active Users: 35
   💰 Total Cost: $255.00
   
   ┌─────────────────────────────────────────────────┐
   │ ℹ️ "Unknown" Department Breakdown:              │
   │ • 16 employees with dept="Unknown" in master    │
   │ • 19 unidentified users (not in master)         │
   │ Note: Check Database Management → Unidentified  │
   │ Users to review non-employees                   │
   └─────────────────────────────────────────────────┘
```

## How does it work?

### Calculation
1. Get total users in "Unknown" from Department Performance query
2. Get unidentified users from database (`get_unidentified_users()`)
3. Calculate: `employees = total - unidentified`

### When shown
- Only when "Unknown" is in top 3 departments by usage
- Automatically calculated on each page load (minimal performance impact)

## Common scenarios

### "I see 16 employees with Unknown department"
**Action**: These employees need department assignments in the employee master file.
**How to fix**: 
1. Identify the 16 employees (you can export the list)
2. Update their departments in the employee master file
3. Re-upload the employee master file

### "I see 19 unidentified users"
**Action**: These are non-employees (contractors, external users, etc.)
**How to review**:
1. Go to Database Management tab
2. Click on "Unidentified Users" section
3. Review the list and assign departments as needed

### "Numbers don't match what I expect"
**Check**:
1. When was the employee master file last updated?
2. Are there new employees not yet in the master file?
3. Have departments changed for existing employees?

## Files modified
- `app.py` - Added breakdown display logic (lines 2666-2685)

## Tests
Run tests to verify:
```bash
python test_unknown_dept_breakdown.py
python test_realistic_unknown_dept.py
```

## Documentation
- `FIX_COMPLETE_SUMMARY.md` - Complete summary
- `UNKNOWN_DEPT_BREAKDOWN_FIX.md` - Technical details
- `UNKNOWN_DEPT_VISUAL_COMPARISON.md` - Visual examples
- `PR_SUMMARY_UNKNOWN_DEPT.md` - PR summary

## Related features
- Employee master file integration
- Department Performance analytics
- Unidentified Users tracking
- Department mapping tool
