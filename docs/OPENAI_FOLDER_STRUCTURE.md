# OpenAI User Data Folder Structure

This document describes the expected folder structure for OpenAI user data files.

## Folder Structure

```
OpenAI User Data/
├── Monthly OpenAI User Data/
│   ├── Openai Eldridge Capital Management monthly user report March.xlsx
│   ├── Openai Eldridge Capital Management monthly user report April.xlsx
│   └── ... (other monthly files)
│
└── Weekly OpenAI User Data/
    ├── January/
    ├── February/
    ├── March/
    │   └── Eldridge Capital Management weekly user report 2025-03-30.csv
    ├── April/
    │   └── Eldridge Capital Management weekly user report 2025-04-06.csv
    ├── May/
    ├── June/
    ├── July/
    ├── August/
    ├── September/
    ├── October/
    ├── November/
    └── December/
```

## File Naming Conventions

### Monthly Files
- **Location**: `OpenAI User Data/Monthly OpenAI User Data/`
- **Pattern**: `Openai Eldridge Capital Management monthly user report <Month>.xlsx`
- **Example**: `Openai Eldridge Capital Management monthly user report March.xlsx`

### Weekly Files
- **Location**: `OpenAI User Data/Weekly OpenAI User Data/<Month>/`
- **Pattern**: `Eldridge Capital Management weekly user report YYYY-MM-DD.xlsx`
- **Example**: `Eldridge Capital Management weekly user report 2025-03-30.csv`
- **Note**: The date in the filename is the week start date (typically Sunday)

## How Weekly Files Are Processed

### Weekly File Detection
Files are identified as weekly reports if:
1. The filename contains the word "weekly" (case-insensitive)
2. The filename contains a date in YYYY-MM-DD format

### Date Assignment for Weekly Files

Weekly files often span two months (e.g., the last week of March may include days from April). The system intelligently assigns each record to the correct month based on actual usage:

1. **Primary Method - Actual Activity Dates**: If the file contains `first_day_active_in_period` and `last_day_active_in_period`, the system:
   - Calculates the midpoint of the user's activity period
   - Assigns the record to the month containing the midpoint

2. **Fallback Method - Period Dates**: If activity dates are not available, the system:
   - Checks if the period spans two months
   - Counts the number of days in each month
   - Assigns to the month with more days

### Example: Week Spanning Two Months

For a weekly file with period `2025-03-30` to `2025-04-05`:

- **User A**: Active March 30-31 (2 days in March)
  - ✅ Assigned to **March 2025**
  
- **User B**: Active April 2-5 (4 days in April)
  - ✅ Assigned to **April 2025**

This ensures accurate monthly reporting even when weeks cross month boundaries.

## Auto-Detection

The system automatically:
- Recursively scans all subdirectories in `OpenAI User Data/`
- Detects and processes both monthly and weekly files
- Assigns data to the correct month based on usage patterns
- Maintains backward compatibility with existing monthly file processing

## BlueFlame User Data

BlueFlame user data remains unchanged and uses a flat folder structure:
```
BlueFlame User Data/
├── file1.csv
├── file2.csv
└── ...
```

BlueFlame files are NOT scanned recursively.
