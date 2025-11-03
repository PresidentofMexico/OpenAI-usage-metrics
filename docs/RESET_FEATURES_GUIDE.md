# File Processing Reset & Refresh Features - Implementation Guide

## Overview
This document describes the new file processing, reset, and refresh features added to the OpenAI Usage Metrics Dashboard.

## Features Implemented

### 1. Complete Reset & Clear All
**Location:** Database Management Tab → Database Actions section

**Button:** "💣 Clear & Reset"

**Functionality:**
- Deletes ALL database records
- Removes file tracking history (file_tracking.json)
- Clears all employee file markers (.loaded files)
- Requires double-click confirmation to prevent accidental data loss

**Use Case:**
When you need to completely start over with all data processing, including re-importing employee files and reprocessing all CSV files.

**Confirmation Message:**
```
⚠️ WARNING: COMPLETE RESET

This will:
- Delete ALL database records
- Remove file tracking history (all files will appear as new)
- Clear employee file markers (allowing re-import)

Click "Clear & Reset" again to confirm this action.
```

---

### 2. Force Reprocess All Files
**Location:** Data Upload Tab → Auto-Detect Files section

**Button:** "🔄 Force Reprocess All"

**Functionality:**
- Marks all files in scan folders as "new" status
- Does NOT delete any data from the database
- Allows batch reprocessing of previously processed files
- Useful when file contents have changed but filenames remain the same

**Use Case:**
When you've updated existing CSV files and want to reprocess them without doing a complete database reset.

**Confirmation Message:**
```
💡 This will mark all files as 'new' so they can be reprocessed. No data will be deleted.
```

---

### 3. Individual File Reset
**Location:** Data Upload Tab → Auto-Detect Files → Processed Files section

**Button:** "🔄 Reset" (appears next to each processed file)

**Functionality:**
- Resets processing status for a single file
- File will move from "Processed Files" to "New Files"
- No confirmation required (low risk - only affects one file)

**Use Case:**
When you need to reprocess a specific file that was updated or had errors.

---

### 4. Force Re-import Employee File
**Location:** Database Management Tab → Employee Master File section

**Button:** "🔄 Force Re-import Employee File"

**Functionality:**
- Clears the employee file marker (.loaded file)
- Triggers immediate reload of the employee CSV
- Updates employee roster in the database
- Clears cache to refresh all displays

**Use Case:**
When the employee roster has been updated (new hires, department changes, etc.) and you need to refresh the data.

---

### 5. Automatic Employee File Update Detection
**Location:** Background process during app startup

**Functionality:**
- Automatically detects when employee CSV file has been modified
- Compares file modification time to marker file modification time
- Auto-reloads employee data if CSV is newer than marker
- No manual intervention needed

**Use Case:**
You replace the employee CSV file with an updated version - the app automatically picks up changes on next load.

---

## Technical Implementation

### FileScanner Methods Added

```python
# Reset a single file's status
scanner.reset_file_status(file_path)

# Reset all files in specified folders
scanner.reset_all_files_status(folder_paths)

# Completely clear tracking file
scanner.reset_all_tracking()
```

### App.py Functions Added

```python
# Clear all employee marker files
clear_employee_markers()

# Comprehensive reset (DB + tracking + markers)
clear_and_reset_all()

# Force reload employee file
force_reload_employee_file()
```

### Modified Functions

**auto_load_employee_file():**
- Now compares CSV file modification time to marker file time
- Auto-reloads if CSV is newer
- Enables seamless employee roster updates

---

## UI Changes Summary

### Database Management Tab
- Added 4th column to Database Actions: "Clear & Reset All"
- Added "Force Re-import Employee File" button in Employee section
- Enhanced confirmation dialogs with detailed warnings

### Data Upload Tab
- Added "Force Reprocess All" button next to "Refresh Files"
- Added individual "Reset" buttons for each processed file
- Improved layout with better button grouping

---

## Testing

All functionality has been tested with automated test suites:

1. **test_reset_functionality.py** - Unit tests for FileScanner methods
2. **test_integration_reset.py** - Integration tests for app.py functions
3. Manual testing scenarios covered:
   - Complete database reset
   - Selective file reprocessing
   - Employee file auto-update
   - Individual file reset

---

## User Workflows

### Workflow 1: Complete Data Refresh
1. Navigate to Database Management tab
2. Click "💣 Clear & Reset"
3. Confirm by clicking again
4. All files will now appear as "new" in Auto-Detect Files
5. Use "⚡ Process All" to batch process everything

### Workflow 2: Reprocess Specific Files
1. Navigate to Data Upload tab → Auto-Detect Files
2. Expand "✅ Processed Files"
3. Find the file you want to reprocess
4. Click "🔄 Reset" next to that file
5. File moves to "New Files" section
6. Click "▶️ Process" to reprocess it

### Workflow 3: Update Employee Roster
**Option A - Automatic:**
1. Replace employee CSV file with updated version
2. Restart the Streamlit app
3. System automatically detects and reloads

**Option B - Manual:**
1. Navigate to Database Management tab
2. Scroll to Employee Master File section
3. Click "🔄 Force Re-import Employee File"
4. System immediately reloads the file

### Workflow 4: Reprocess All Files Without Data Loss
1. Navigate to Data Upload tab → Auto-Detect Files
2. Click "🔄 Force Reprocess All"
3. Confirm by clicking again
4. All files marked as "new"
5. Use batch processing to reimport (data will be deduplicated if needed)

---

## Safety Features

1. **Double-click confirmation** on destructive actions (Clear & Reset All, Force Reprocess All)
2. **Clear warning messages** explaining what will happen
3. **Cache clearing** after major operations to ensure UI reflects changes
4. **Automatic page refresh** after successful operations
5. **Error handling** with user-friendly messages

---

## Troubleshooting

### Files Not Appearing as New After Reset
- Check that you clicked "Refresh Files" after reset
- Verify files are in the correct scan folders (OpenAI User Data, BlueFlame User Data)

### Employee File Not Reloading
- Verify the CSV file exists in the repository root
- Check file has expected columns (First Name, Last Name, Email, Function, Status)
- Look at browser console for any error messages

### Clear & Reset Not Working
- Ensure you clicked the button twice (confirmation required)
- Check Database Management tab for any error messages
- Verify you have write permissions in the project directory

---

## Files Modified

1. **file_scanner.py** - Added reset methods
2. **app.py** - Added reset functions and UI elements
3. **tests/test_reset_functionality.py** - New test file
4. **tests/test_integration_reset.py** - New integration test

---

## Migration Notes

- No database schema changes required
- Existing file_tracking.json format is compatible
- No breaking changes to existing functionality
- All new features are additive (backward compatible)
