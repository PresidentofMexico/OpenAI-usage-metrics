# BlueFlame Date Format Parsing Fix

## Problem Summary
BlueFlame CSV exports use the date format `YY-Mon` (e.g., `25-Oct`, `25-Sep`) for month column headers, but the data processor was hardcoded to only parse the `Mon-YY` format (e.g., `Oct-24`, `Sep-24`). This caused month columns to be silently skipped during data processing, resulting in missing usage data for users like John Boddiford.

## Root Cause
In `data_processor.py`, the `normalize_blueflame_data()` method used:
```python
month_date = pd.to_datetime(month_col, format='%b-%y', errors='coerce')
if pd.isna(month_date):
    continue  # SKIPS THE COLUMN if format doesn't match!
```

This only worked for `Mon-YY` format. When encountering `YY-Mon` format, parsing would fail and return `NaT`, causing the entire month's data to be skipped.

## Solution
1. **Created `parse_blueflame_month_column()` helper function** that tries both date formats:
   - First tries `%b-%y` format (Mon-YY) for backward compatibility
   - Then tries `%y-%b` format (YY-Mon) for new CSV exports
   - Returns `pd.NaT` only if both formats fail

2. **Updated 4 locations** in `normalize_blueflame_data()` to use the new helper:
   - Line 345: Monthly trends processing (with Table column)
   - Line 427: User data processing (with Table column)
   - Line 471: Summary report processing (Metric column, no Table)
   - Line 554: Top users file format processing

3. **Added support for new table types**:
   - "All Users Total"
   - "All Increasing Users"
   - "All Decreasing Users"

## Testing
Created comprehensive test suite in `tests/test_blueflame_date_formats.py`:
- ✅ Tests both date formats parse correctly
- ✅ Tests YY-Mon format data processing
- ✅ Tests Mon-YY format backward compatibility
- ✅ Tests user-level data with YY-Mon format
- ✅ Verified with actual BlueFlame CSV files
- ✅ All existing tests continue to pass

## Verification
Tested with actual October 2025 BlueFlame CSV:
- **Before fix**: John Boddiford's data was completely missing
- **After fix**: Successfully captured 6 records across 2 months (Sep & Oct 2025)
- Total usage: 2,706 messages
- Date range: 2025-09-01 to 2025-10-01

## Sample Files
Added two sample CSV files for testing:
- `OpenAI User Data/sample_blueflame_yy_mon_format.csv` - Uses 25-Oct format
- `OpenAI User Data/sample_blueflame_mon_yy_format.csv` - Uses Oct-24 format

## Impact
- **CRITICAL FIX**: Resolves data loss for all BlueFlame exports using YY-Mon format
- **Backward Compatible**: Continues to support legacy Mon-YY format
- **Zero Breaking Changes**: All existing functionality preserved
- **Improved Coverage**: Now handles additional table format variations

## Files Modified
- `data_processor.py` - Core date parsing logic fix
- `tests/test_blueflame_date_formats.py` - Comprehensive test coverage
- `OpenAI User Data/sample_blueflame_yy_mon_format.csv` - Test sample
- `OpenAI User Data/sample_blueflame_mon_yy_format.csv` - Test sample
