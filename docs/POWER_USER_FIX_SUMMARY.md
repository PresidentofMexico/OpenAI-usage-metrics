# Power User Directory Deduplication Fix

## Problem
Users appearing in both OpenAI and BlueFlame datasets were being displayed as **duplicate entries** in the Power User Directory.

**Example:** Kaan Ertuk appeared twice:
- Once for OpenAI usage (department: 'finance')
- Once for BlueFlame usage (department: 'BlueFlame Users')

## Root Cause
The `calculate_power_users()` function was grouping by `['user_name', 'email', 'department']`, which treated the same user with different departments as separate users.

## Solution

### 1. Changed Grouping Strategy
**Before:**
```python
user_usage = data.groupby(['user_name', 'email', 'department']).agg({...})
```

**After:**
```python
user_usage = data.groupby('email').agg({
    'user_name': 'first',
    'department': lambda x: _select_primary_department(x),
    'usage_count': 'sum',
    'cost_usd': 'sum',
    'tool_source': lambda x: ', '.join(sorted(x.unique()))
})
```

### 2. Added Smart Department Selection
Created `_select_primary_department()` function that:
- Prefers organizational departments over 'BlueFlame Users'
- Returns first non-BlueFlame department when multiple exist
- Only returns 'BlueFlame Users' if that's the only department available

### 3. Enhanced Message Breakdown
Updated `get_user_message_breakdown()` to return structured data separating OpenAI and BlueFlame metrics:

```python
{
    'openai': {
        'ChatGPT Messages': 250,
        'Tool Messages': 75,
        'Project Messages': 0,
        'GPT Messages': 0
    },
    'blueflame': {
        'BlueFlame Messages': 420
    }
}
```

### 4. Improved UI Display
Updated the Power User Directory to show:
- **OpenAI Data:** with detailed breakdown (ChatGPT, Tools, Projects)
- **BlueFlame Data:** with total messages

## Results

### Before
- Kaan Ertuk appeared 2 times
- Usage split across duplicate entries
- No visibility into which tool generated which messages

### After
- Kaan Ertuk appears 1 time
- Total: 745 messages (325 OpenAI + 420 BlueFlame)
- Clear breakdown showing usage from each tool

## Testing
All unit tests pass:
- ✅ Deduplication works correctly
- ✅ Usage aggregates properly across tools
- ✅ Department selection prefers organizational departments
- ✅ Message breakdown separates tool sources

## Files Modified
- `app.py` (61 insertions, 20 deletions)
  - `calculate_power_users()` - Changed grouping logic
  - `_select_primary_department()` - New helper function
  - `get_user_message_breakdown()` - Enhanced to support multi-tool breakdown
  - Power User Directory UI - Updated display logic
