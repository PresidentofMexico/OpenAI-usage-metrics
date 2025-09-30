# Sample Data for Multi-Provider Analytics Dashboard

This directory contains sample CSV files for each supported AI provider. Use these files to test the multi-provider analytics dashboard functionality.

## Provider Formats

### OpenAI Format (`openai_sample.csv`)
```csv
email,name,department,period_start,messages,tool_messages,project_messages
```

**Fields:**
- `email`: User email address
- `name`: User's full name
- `department`: Department name
- `period_start`: Date of the usage period (YYYY-MM-DD)
- `messages`: Number of ChatGPT messages
- `tool_messages`: Number of tool messages
- `project_messages`: Number of project messages

**Cost Model:**
- ChatGPT Messages: $0.02 per message
- Tool Messages: $0.01 per message
- Project Messages: $0.015 per message

---

### BlueFlame AI Format (`blueflame_sample.csv`)
```csv
user_id,username,team,date,queries,api_calls,tokens_used,cost
```

**Fields:**
- `user_id`: Unique user identifier
- `username`: Username
- `team`: Team/department name
- `date`: Usage date (YYYY-MM-DD)
- `queries`: Number of queries
- `api_calls`: Number of API calls
- `tokens_used`: Total tokens used
- `cost`: Total cost in USD

**Cost Model:**
- Queries: $0.01 per query
- API Calls: $0.001 per call

---

### Anthropic Format (`anthropic_sample.csv`)
```csv
email,full_name,department,usage_date,claude_messages,api_requests,total_cost
```

**Fields:**
- `email`: User email address
- `full_name`: User's full name
- `department`: Department name
- `usage_date`: Date of usage (YYYY-MM-DD)
- `claude_messages`: Number of Claude messages
- `api_requests`: Number of API requests
- `total_cost`: Total cost in USD

**Cost Model:**
- Claude Messages: $0.015 per message
- API Requests: $0.02 per request

---

### Google AI Format (`google_sample.csv`)
```csv
email,name,department,date,gemini_requests,api_calls,tokens,cost
```

**Fields:**
- `email`: User email address
- `name`: User's full name
- `department`: Department name
- `date`: Usage date (YYYY-MM-DD)
- `gemini_requests`: Number of Gemini requests
- `api_calls`: Number of API calls
- `tokens`: Total tokens used
- `cost`: Total cost in USD

**Cost Model:**
- Gemini Requests: $0.0125 per request
- API Calls: $0.01 per call

---

## How to Use

1. **Select a Provider**: In the dashboard sidebar, select the provider from the dropdown
2. **Upload Sample Data**: Click "Browse files" and select the corresponding sample CSV
3. **Process Upload**: Click "Process Upload" to load the data
4. **View Analytics**: The dashboard will display provider-specific analytics

## Testing Multi-Provider

To test the multi-provider functionality:

1. Upload `openai_sample.csv` with "OpenAI" selected
2. Upload `blueflame_sample.csv` with "BlueFlame AI" selected
3. Upload `anthropic_sample.csv` with "Anthropic" selected
4. Upload `google_sample.csv` with "Google AI" selected
5. Switch between providers using the dropdown to see bifurcated analytics

## Custom Provider Format

If you have a different CSV format, select "Custom" as the provider. The dashboard will attempt to map common column names:

**Flexible Mapping:**
- User ID: `user_id`, `email`, `user_email`
- User Name: `user_name`, `name`, `display_name`
- Department: `department`, `dept`, `team`
- Date: `date`, `usage_date`, `timestamp`
- Feature: `feature_used`, `feature`, `service`
- Usage Count: `usage_count`, `count`, `interactions`
- Cost: `cost_usd`, `cost`, `price`
