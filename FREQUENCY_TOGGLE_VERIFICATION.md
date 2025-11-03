# Frequency Toggle Feature - Visual Verification Guide

## Feature Overview
This document describes the visual appearance and behavior of the new frequency toggle and partial period filtering features.

## 1. Sidebar Controls

### Location
The new controls appear in the sidebar under the "📅 Filters" section, after the department filter.

### Controls Added

#### Frequency Toggle (Radio Button)
```
**📊 Analysis Frequency**

○ Monthly (default)  [selected by default]
○ Weekly

Help: "Monthly: aggregate OpenAI weeks to months; Weekly: estimate Blueflame weeks from monthly totals."
```

#### Partial Period Checkbox
```
☑ Exclude current in-progress period

Help: "Exclude the current incomplete week/month from analysis to avoid skewed trends"
```

## 2. Executive Overview Tab

### Weekly Mode Caption
When "Weekly" frequency is selected, a caption appears immediately after the divider:

```
───────────────────────────────────────────────────────────

ⓘ Blueflame weekly values are estimated from monthly totals (even-by-day allocation).

📊 Executive Summary
Key performance metrics and trends
```

### Monthly Mode
When "Monthly (default)" is selected, no caption appears.

## 3. Data Behavior

### Monthly View (Default)
- **OpenAI Data**: Weekly data is prorated by day into calendar months
  - If a week spans two months (e.g., Jan 29 - Feb 4), the data is split proportionally
  - Example: 70 messages over 7 days → ~30 to January, ~40 to February
  
- **BlueFlame Data**: Already monthly, no transformation needed
  - Data remains as-is with month start dates

- **Partial Period Exclusion**: 
  - When checkbox is checked (default), excludes the current incomplete month
  - Current month start = first day of current month
  - Only records with `period_start < current_month_start` are shown

### Weekly View
- **OpenAI Data**: Already weekly, minimal transformation
  - Period start is normalized to ISO week start (Monday)
  
- **BlueFlame Data**: Monthly data is allocated to ISO weeks
  - Each month's data is split evenly across all weeks touching that month
  - Example: January 2024 has 5 weeks → 100 messages ÷ 5 = 20 messages per week
  
- **Partial Period Exclusion**:
  - When checkbox is checked (default), excludes the current incomplete week
  - Current week start = Monday of the current week
  - Only records with `period_start < current_week_start` are shown

## 4. User Workflows

### Use Case 1: View Monthly Trends (Default)
1. User opens the dashboard
2. Frequency is set to "Monthly (default)" by default
3. "Exclude current in-progress period" is checked by default
4. Charts show monthly aggregated data
5. Current incomplete month is excluded from trends

### Use Case 2: Switch to Weekly Analysis
1. User selects "Weekly" from frequency radio button
2. Dashboard immediately updates:
   - BlueFlame caption appears
   - OpenAI data shows weekly periods
   - BlueFlame data is split into weekly estimates
3. Current incomplete week is excluded (checkbox checked by default)

### Use Case 3: Include Partial Periods
1. User unchecks "Exclude current in-progress period"
2. Dashboard updates to include:
   - Current incomplete month (Monthly view)
   - Current incomplete week (Weekly view)
3. User can see real-time partial data

## 5. Expected Visual Changes

### Sidebar Before
```
📅 Filters
─────────────
📊 Data Available: 2024-01-01 to 2024-12-31 (365 days)

Select date range: [2024-01-01] to [2024-12-31]

Select Data Provider:
○ All Tools
○ ChatGPT
○ BlueFlame AI

Departments (5 total):
[Multi-select dropdown]
```

### Sidebar After
```
📅 Filters
─────────────
📊 Data Available: 2024-01-01 to 2024-12-31 (365 days)

Select date range: [2024-01-01] to [2024-12-31]

Select Data Provider:
○ All Tools
○ ChatGPT
○ BlueFlame AI

Departments (5 total):
[Multi-select dropdown]

─────────────
**📊 Analysis Frequency**

○ Monthly (default)
○ Weekly

☑ Exclude current in-progress period
```

## 6. Test Scenarios

### Scenario 1: Toggle Frequency
1. Start with Monthly view → No BlueFlame caption
2. Switch to Weekly view → BlueFlame caption appears
3. Switch back to Monthly → Caption disappears

### Scenario 2: Partial Period Exclusion
1. With checkbox CHECKED (default):
   - Monthly: Current month data excluded
   - Weekly: Current week data excluded
2. With checkbox UNCHECKED:
   - Monthly: Current month data included
   - Weekly: Current week data included

### Scenario 3: Data Transformation
1. Monthly view:
   - OpenAI weekly data spanning months is split correctly
   - Total usage preserved across months
2. Weekly view:
   - BlueFlame monthly data split across weeks
   - Total usage preserved across weeks

## 7. Success Criteria

✅ Frequency radio button appears in sidebar
✅ Partial period checkbox appears in sidebar
✅ Weekly mode shows Blueflame caption
✅ Monthly mode hides Blueflame caption
✅ Partial period exclusion works for both views
✅ Data totals are preserved during normalization
✅ Charts update when frequency changes
✅ No errors in browser console
