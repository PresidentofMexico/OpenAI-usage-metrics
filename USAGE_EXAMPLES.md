# Multi-Provider Usage Examples

This document provides practical examples of using the multi-provider dashboard.

## Quick Start

### 1. Upload OpenAI Data

Upload an OpenAI CSV export with columns like:
- email, name, department, period_start, messages, tool_messages, project_messages

The system automatically detects it as OpenAI and processes:
- ChatGPT Messages (estimated cost: $0.02/message)
- Tool Messages (estimated cost: $0.01/message)
- Project Messages (estimated cost: $0.015/message)

### 2. Upload BlueFlame AI Data

Upload a BlueFlame CSV with:
- user_email, user_name, team, date, api_calls, model_requests

Or include actual costs:
- user_email, user_name, team, date, api_calls, model_requests, total_cost

### 3. Select Provider

Use the dropdown in the sidebar to switch between providers:
- 🤖 OpenAI (ChatGPT)
- 🔥 BlueFlame AI
- 🧠 Anthropic (Claude)
- 🔍 Google (Gemini)

## Sample CSV Files

### OpenAI Format
```csv
email,name,department,period_start,messages,tool_messages,project_messages
john@company.com,John Doe,Engineering,2025-09-01,150,20,5
jane@company.com,Jane Smith,Marketing,2025-09-01,200,30,10
```

### BlueFlame AI Format
```csv
user_email,user_name,team,date,api_calls,model_requests,total_cost
john@company.com,John Doe,Engineering,2025-09-01,150,45,5.25
jane@company.com,Jane Smith,Marketing,2025-09-01,200,60,7.50
```

### Anthropic Format
```csv
user_id,display_name,organization,usage_date,claude_messages,api_usage,spend_usd
john@company.com,John Doe,Engineering,2025-09-01,100,50,15.50
jane@company.com,Jane Smith,Marketing,2025-09-01,150,75,22.50
```

### Google Format
```csv
email,full_name,dept,report_date,gemini_queries,bard_interactions,billing_amount
john@company.com,John Doe,Engineering,2025-09-01,200,50,9.50
jane@company.com,Jane Smith,Marketing,2025-09-01,150,100,7.50
```

## Using the Dashboard

### Analyzing a Single Provider

1. Select provider from dropdown
2. Choose date range
3. Optionally filter by users or departments
4. View analytics specific to that provider

### Comparing Providers (Manual)

While the dashboard doesn't show side-by-side comparisons, you can:
1. Export data for Provider A
2. Switch to Provider B
3. Export data for Provider B
4. Compare exports in Excel or another tool

### Viewing All Data

Use the Database Management tab to:
- See all uploaded files
- View record counts by provider
- Export complete database
- Delete specific uploads

## Cost Analysis

### Estimated vs Actual Costs

**Estimated Costs**: When provider doesn't supply costs
- Calculated using cost_per_unit from configuration
- Example: 100 messages × $0.02 = $2.00

**Actual Costs**: When provider supplies cost column
- Uses actual cost from CSV
- More accurate for billing purposes

### Customizing Cost Models

Edit `config.py` to adjust cost_per_unit:

```python
'usage_columns': {
    'api_calls': {
        'feature_name': 'API Calls',
        'cost_per_unit': 0.01  # Adjust this value
    }
}
```

## Filtering and Analysis

### Date Range Filtering
- Select start and end dates
- Dashboard shows only data within range
- Works independently for each provider

### User Filtering
- Multi-select users to analyze
- Leave empty to include all users
- User lists are provider-specific

### Department Filtering
- Filter by one or more departments
- Useful for cost allocation
- Department lists are provider-specific

## Data Quality

The dashboard performs quality checks:
- **Data Completeness**: % of non-null values
- **Duplicate Rate**: % of duplicate records
- **Active Users**: Count of unique users
- **Cost Anomalies**: Unusually high costs flagged

## Troubleshooting

### Provider Not Auto-Detected
- Check CSV has required signature columns
- Review MULTI_PROVIDER_GUIDE.md for detection rules
- Contact admin to add new provider configuration

### Wrong Cost Calculations
- Verify cost_per_unit in config.py
- Check if CSV includes actual cost column
- Review processed data in Database Management tab

### No Data Showing
- Ensure provider is selected in dropdown
- Check date range includes your data
- Verify upload was successful (check Recent Uploads)

## Best Practices

1. **Consistent Uploads**: Upload data at the same time each month
2. **File Naming**: Use descriptive names like "OpenAI_September_2025.csv"
3. **Backup**: Periodically export database (Database Management tab)
4. **Validation**: Review Data Quality metrics after each upload
5. **Documentation**: Keep notes on any manual cost adjustments

## Advanced Usage

### Multiple Months
Upload multiple monthly files for the same provider to see:
- Growth trends
- Month-over-month changes
- Usage patterns over time

### Export and Reporting
1. Filter data as needed
2. Use "Download Filtered Data" button
3. Create custom reports in Excel
4. Share with stakeholders

### Database Management
- View upload history
- Delete old or incorrect uploads
- Monitor database size
- Export complete dataset

## Support

For issues or questions:
1. Review MULTI_PROVIDER_GUIDE.md
2. Check README.md for setup instructions
3. Contact system administrator
