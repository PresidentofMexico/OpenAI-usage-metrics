# ROI Utilities Guide

## Overview

The ROI utilities module (`roi_utils.py`) provides comprehensive Return on Investment (ROI) calculation functions for AI usage analytics. These utilities map usage events to estimated time savings and monetary value, enabling data-driven decision making for enterprise AI tool deployments.

## Features

- **Time Savings Estimation**: Calculate hours saved based on usage patterns
- **Monetary Value Calculation**: Convert time savings to dollar value using department-specific rates
- **Per-User ROI**: Aggregate ROI metrics for individual users
- **Per-Department ROI**: Analyze ROI by organizational department
- **Composite ROI**: Organization-wide ROI summary with trend analysis
- **Date Validation**: Ensure data quality with built-in date validation

## Quick Start

```python
import pandas as pd
from roi_utils import (
    estimate_hours_saved,
    calculate_monetary_value,
    calculate_roi_per_user,
    calculate_roi_per_department,
    calculate_composite_roi
)

# Load your usage data
usage_df = pd.read_csv('usage_data.csv')

# Calculate composite ROI for the entire organization
roi_summary = calculate_composite_roi(usage_df)
print(f"Total value delivered: ${roi_summary['total_monetary_value_usd']:,.2f}")
print(f"Hours saved: {roi_summary['total_hours_saved']:,.0f}")

# Analyze ROI by department
dept_roi = calculate_roi_per_department(usage_df)
print(dept_roi[['department', 'hours_saved', 'monetary_value_usd']])
```

## Core Functions

### estimate_hours_saved()

Estimates time saved based on usage count and feature type.

**Parameters:**
- `usage_count` (int/float): Number of usage events
- `feature_type` (str): Type of feature ('ChatGPT Messages', 'Tool Messages', etc.)
- `config` (dict, optional): Custom configuration for time estimates

**Returns:** `float` - Hours saved

**Example:**
```python
# 60 standard messages = 5 hours saved (default: 5 min/message)
hours = estimate_hours_saved(60, 'ChatGPT Messages')

# 30 tool messages = 5 hours saved (default: 10 min/message)
hours = estimate_hours_saved(30, 'Tool Messages')

# Custom time estimates
custom_config = {'minutes_saved_per_message': 10}
hours = estimate_hours_saved(60, 'ChatGPT Messages', config=custom_config)
```

### calculate_monetary_value()

Converts hours saved to monetary value using department-specific or custom hourly rates.

**Parameters:**
- `hours_saved` (float): Number of hours saved
- `department` (str): Department name for rate lookup
- `hourly_rate` (float, optional): Custom hourly rate (overrides department rate)
- `config` (dict, optional): Custom configuration with rate tables

**Returns:** `float` - Monetary value in USD

**Default Hourly Rates:**
- Engineering: $75
- Finance: $70
- Legal: $100
- Marketing: $55
- Sales: $60
- HR: $50
- IT: $65
- Operations: $55
- Executive: $150
- Unknown: $50 (default)

**Example:**
```python
# Engineering department rate
value = calculate_monetary_value(10, 'Engineering')  # $750

# Custom hourly rate
value = calculate_monetary_value(10, 'Engineering', hourly_rate=100)  # $1000
```

### calculate_roi_per_user()

Aggregates usage data by user and calculates comprehensive ROI metrics.

**Parameters:**
- `usage_df` (DataFrame): Usage data with columns: `user_id`, `user_name`, `department`, `feature_used`, `usage_count`
- `config` (dict, optional): Custom configuration

**Returns:** DataFrame with columns:
- `user_id`: User identifier
- `user_name`: User's name
- `department`: User's department
- `total_usage`: Total usage events
- `hours_saved`: Total hours saved
- `monetary_value_usd`: Total monetary value

**Example:**
```python
user_roi = calculate_roi_per_user(usage_df)

# Top 10 users by value delivered
top_users = user_roi.nlargest(10, 'monetary_value_usd')
print(top_users[['user_name', 'hours_saved', 'monetary_value_usd']])
```

### calculate_roi_per_department()

Aggregates usage data by department with per-user averages.

**Parameters:**
- `usage_df` (DataFrame): Usage data with columns: `department`, `feature_used`, `usage_count`, `user_id` (optional)
- `config` (dict, optional): Custom configuration

**Returns:** DataFrame with columns:
- `department`: Department name
- `total_usage`: Total usage events
- `active_users`: Number of unique users
- `hours_saved`: Total hours saved
- `monetary_value_usd`: Total monetary value
- `avg_value_per_user`: Average value per user

**Example:**
```python
dept_roi = calculate_roi_per_department(usage_df)

# Departments sorted by total value (descending)
print(dept_roi[['department', 'active_users', 'monetary_value_usd', 'avg_value_per_user']])
```

### calculate_composite_roi()

Calculates organization-wide ROI summary with temporal analysis.

**Parameters:**
- `usage_df` (DataFrame): Complete usage data
- `date_column` (str): Name of the date column (default: 'date')
- `config` (dict, optional): Custom configuration

**Returns:** Dictionary with:
- `total_hours_saved`: Total hours saved across all users
- `total_monetary_value_usd`: Total monetary value delivered
- `total_users`: Number of unique users
- `total_usage_events`: Total usage events
- `avg_hours_per_user`: Average hours saved per user
- `avg_value_per_user`: Average value per user
- `date_range`: Date range of the data (if available)
- `monthly_average_value`: Average monthly value (if dates available)

**Example:**
```python
composite = calculate_composite_roi(usage_df)

print(f"Organization ROI Summary:")
print(f"  Total Value: ${composite['total_monetary_value_usd']:,.2f}")
print(f"  Hours Saved: {composite['total_hours_saved']:,.0f}")
print(f"  Active Users: {composite['total_users']}")
print(f"  Avg Value/User: ${composite['avg_value_per_user']:,.2f}")
print(f"  Date Range: {composite['date_range']}")
print(f"  Monthly Average: ${composite['monthly_average_value']:,.2f}")
```

### validate_date_field()

Validates date fields to ensure data quality.

**Parameters:**
- `date_value` (str/datetime/date/Timestamp): Date value to validate

**Returns:** `bool` - True if valid and not in future, False otherwise

**Example:**
```python
# Validate dates in your data
usage_df['date_valid'] = usage_df['date'].apply(validate_date_field)
valid_data = usage_df[usage_df['date_valid']]
```

## Configuration

Customize ROI calculations by providing a configuration dictionary:

```python
custom_config = {
    # Time savings (minutes per message)
    'minutes_saved_per_message': 7,          # Standard messages
    'minutes_saved_per_tool_message': 12,    # Tool usage
    'minutes_saved_per_project_message': 20, # Project work
    
    # Default hourly rate
    'hourly_rate_default': 60,
    
    # Department-specific hourly rates
    'hourly_rate_by_department': {
        'Engineering': 80,
        'Finance': 75,
        'Marketing': 60,
        # ... add more departments
    }
}

# Use custom config
hours = estimate_hours_saved(60, 'ChatGPT Messages', config=custom_config)
value = calculate_monetary_value(hours, 'Engineering', config=custom_config)
```

## Edge Case Handling

The ROI utilities are designed to handle common edge cases gracefully:

### Zero Usage
```python
hours = estimate_hours_saved(0, 'ChatGPT Messages')  # Returns 0.0
value = calculate_monetary_value(0, 'Engineering')   # Returns 0.0
```

### Unknown Department
```python
# Uses default hourly rate ($50)
value = calculate_monetary_value(10, 'NewDepartment')  # $500
```

### Invalid Dates
```python
# Returns False for invalid dates
validate_date_field('not-a-date')  # False
validate_date_field(None)          # False

# Returns False for future dates
future_date = '2099-12-31'
validate_date_field(future_date)   # False
```

### Missing Data
```python
# Empty DataFrames return empty results or zero metrics
empty_df = pd.DataFrame()
roi = calculate_composite_roi(empty_df)
# Returns all metrics as 0 or None
```

## Testing

A comprehensive test suite is available in `tests/test_roi_utils.py`:

```bash
# Run the ROI utilities test suite
python tests/test_roi_utils.py
```

**Test Coverage:**
- ✅ Basic hours saved calculations
- ✅ Monetary value calculations
- ✅ Per-user ROI aggregation
- ✅ Per-department ROI aggregation
- ✅ Composite ROI metrics
- ✅ Edge cases (zero usage, unknown dept, invalid dates)
- ✅ Date validation
- ✅ Sample CSV integration

## Integration with Dashboard

To integrate ROI utilities into the main dashboard (`app.py`):

```python
from roi_utils import calculate_composite_roi, calculate_roi_per_department

# In your dashboard code
if not usage_data.empty:
    # Calculate ROI metrics
    roi_summary = calculate_composite_roi(usage_data)
    dept_roi = calculate_roi_per_department(usage_data)
    
    # Display in dashboard
    st.metric("Total Value Delivered", f"${roi_summary['total_monetary_value_usd']:,.2f}")
    st.metric("Hours Saved", f"{roi_summary['total_hours_saved']:,.0f}")
    
    # Department breakdown
    st.dataframe(dept_roi)
```

## Best Practices

1. **Customize Time Estimates**: Adjust `minutes_saved_per_message` based on your organization's actual usage patterns
2. **Update Hourly Rates**: Ensure department hourly rates reflect current market rates or internal cost structures
3. **Validate Dates**: Always validate date fields before aggregating temporal metrics
4. **Handle Edge Cases**: The utilities handle edge cases, but always validate input data quality
5. **Test with Sample Data**: Use the test suite to verify calculations with your data structure

## Frequently Asked Questions

**Q: How are time savings calculated?**  
A: Time savings are estimated by multiplying usage count by configurable minutes-per-message rates that vary by feature type (standard messages: 5 min, tool messages: 10 min, project messages: 15 min by default).

**Q: Can I customize hourly rates?**  
A: Yes, either provide a custom `hourly_rate` parameter or modify the `hourly_rate_by_department` configuration.

**Q: What happens with unknown departments?**  
A: Unknown departments use the default hourly rate ($50 by default), which can be customized via the `hourly_rate_default` configuration.

**Q: Are future dates allowed?**  
A: No, the `validate_date_field()` function returns False for future dates to ensure data quality.

**Q: How is monthly average calculated?**  
A: Monthly average is calculated by dividing total monetary value by the number of months in the date range (using 30.44 average days per month).

## Related Documentation

- [Cost Model Comparison](COST_MODEL_COMPARISON.md) - Enterprise pricing model vs. per-message pricing
- [Enterprise Pricing Update](ENTERPRISE_PRICING_UPDATE.md) - License-based cost calculations
- [Quick Reference](QUICK_REFERENCE.md) - Dashboard features and navigation

## Support

For issues or questions about ROI utilities:
1. Review the test suite in `tests/test_roi_utils.py` for usage examples
2. Check the inline documentation in `roi_utils.py`
3. Refer to the configuration options in `DEFAULT_ROI_CONFIG`
