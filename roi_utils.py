"""
ROI Utilities for AI Usage Analytics

Calculates Return on Investment (ROI) metrics by mapping usage events to
estimated time savings and monetary value. Provides per-user, per-department,
and composite ROI calculations for enterprise AI tool deployments.
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, Optional, Union


# Default configuration for ROI calculations
DEFAULT_ROI_CONFIG = {
    'minutes_saved_per_message': 5,  # Average time saved per AI interaction
    'minutes_saved_per_tool_message': 10,  # Tool usage typically saves more time
    'minutes_saved_per_project_message': 15,  # Project work has higher complexity
    'hourly_rate_default': 50,  # Default hourly rate in USD
    'hourly_rate_by_department': {
        'Engineering': 75,
        'Finance': 70,
        'Legal': 100,
        'Marketing': 55,
        'Sales': 60,
        'HR': 50,
        'IT': 65,
        'Operations': 55,
        'Executive': 150,
        'Unknown': 50
    }
}


def estimate_hours_saved(
    usage_count: Union[int, float],
    feature_type: str = 'ChatGPT Messages',
    config: Optional[Dict] = None
) -> float:
    """
    Estimate hours saved based on usage count and feature type.
    
    Maps usage events to estimated time savings using configurable
    minutes-per-message rates that vary by feature type.
    
    Args:
        usage_count: Number of usage events (messages, queries, etc.)
        feature_type: Type of feature used (e.g., 'ChatGPT Messages', 'Tool Messages')
        config: Optional configuration dict with custom minutes_saved rates
        
    Returns:
        float: Estimated hours saved
        
    Examples:
        >>> estimate_hours_saved(60, 'ChatGPT Messages')
        5.0
        >>> estimate_hours_saved(0, 'Tool Messages')
        0.0
        >>> estimate_hours_saved(30, 'Project Messages')
        7.5
    """
    if config is None:
        config = DEFAULT_ROI_CONFIG
    
    # Handle edge cases
    if usage_count is None or pd.isna(usage_count):
        return 0.0
    
    if usage_count <= 0:
        return 0.0
    
    # Determine minutes saved per message based on feature type
    feature_lower = str(feature_type).lower()
    
    if 'tool' in feature_lower:
        minutes_per_message = config.get('minutes_saved_per_tool_message', 10)
    elif 'project' in feature_lower:
        minutes_per_message = config.get('minutes_saved_per_project_message', 15)
    else:
        minutes_per_message = config.get('minutes_saved_per_message', 5)
    
    # Calculate total minutes and convert to hours
    total_minutes = usage_count * minutes_per_message
    hours_saved = total_minutes / 60.0
    
    return round(hours_saved, 2)


def calculate_monetary_value(
    hours_saved: float,
    department: str = 'Unknown',
    hourly_rate: Optional[float] = None,
    config: Optional[Dict] = None
) -> float:
    """
    Calculate monetary value from hours saved.
    
    Uses department-specific or custom hourly rates to convert
    time savings into dollar value.
    
    Args:
        hours_saved: Number of hours saved
        department: Department name for department-specific rates
        hourly_rate: Optional custom hourly rate (overrides department rate)
        config: Optional configuration dict with hourly rates
        
    Returns:
        float: Estimated monetary value in USD
        
    Examples:
        >>> calculate_monetary_value(10, 'Engineering')
        750.0
        >>> calculate_monetary_value(5, 'Unknown', hourly_rate=100)
        500.0
        >>> calculate_monetary_value(0, 'Finance')
        0.0
    """
    if config is None:
        config = DEFAULT_ROI_CONFIG
    
    # Handle edge cases
    if hours_saved is None or pd.isna(hours_saved) or hours_saved <= 0:
        return 0.0
    
    # Determine hourly rate
    if hourly_rate is not None and hourly_rate > 0:
        rate = hourly_rate
    else:
        # Normalize department name for lookup
        # Converts to title case to match config keys (e.g., 'engineering' → 'Engineering')
        dept_normalized = str(department).strip().title() if department else 'Unknown'
        
        # Look up department-specific rate
        dept_rates = config.get('hourly_rate_by_department', {})
        rate = dept_rates.get(dept_normalized, config.get('hourly_rate_default', 50))
    
    # Calculate monetary value
    value = hours_saved * rate
    
    return round(value, 2)


def calculate_roi_per_user(
    usage_df: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Calculate ROI metrics per user.
    
    Aggregates usage data by user and calculates total hours saved,
    monetary value, and ROI metrics for each user.
    
    Args:
        usage_df: DataFrame with columns: user_id, user_name, department,
                  feature_used, usage_count
        config: Optional configuration dict for ROI calculations
        
    Returns:
        DataFrame with columns: user_id, user_name, department, total_usage,
                                hours_saved, monetary_value_usd
                                
    Raises:
        ValueError: If required columns are missing from usage_df
    """
    if usage_df.empty:
        return pd.DataFrame(columns=[
            'user_id', 'user_name', 'department', 'total_usage',
            'hours_saved', 'monetary_value_usd'
        ])
    
    # Validate required columns
    required_cols = ['user_id', 'usage_count']
    missing_cols = [col for col in required_cols if col not in usage_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if config is None:
        config = DEFAULT_ROI_CONFIG
    
    # Make a copy to avoid modifying original
    df = usage_df.copy()
    
    # Calculate hours saved for each row
    df['hours_saved'] = df.apply(
        lambda row: estimate_hours_saved(
            row.get('usage_count', 0),
            row.get('feature_used', 'ChatGPT Messages'),
            config
        ),
        axis=1
    )
    
    # Calculate monetary value for each row
    df['monetary_value'] = df.apply(
        lambda row: calculate_monetary_value(
            row.get('hours_saved', 0),
            row.get('department', 'Unknown'),
            config=config
        ),
        axis=1
    )
    
    # Aggregate by user
    user_cols = ['user_id']
    if 'user_name' in df.columns:
        user_cols.append('user_name')
    if 'department' in df.columns:
        user_cols.append('department')
    
    agg_dict = {
        'usage_count': 'sum',
        'hours_saved': 'sum',
        'monetary_value': 'sum'
    }
    
    result = df.groupby(user_cols, as_index=False).agg(agg_dict)
    
    # Rename columns for clarity
    result = result.rename(columns={
        'usage_count': 'total_usage',
        'monetary_value': 'monetary_value_usd'
    })
    
    # Round numeric columns
    result['hours_saved'] = result['hours_saved'].round(2)
    result['monetary_value_usd'] = result['monetary_value_usd'].round(2)
    
    return result


def calculate_roi_per_department(
    usage_df: pd.DataFrame,
    config: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Calculate ROI metrics per department.
    
    Aggregates usage data by department and calculates total hours saved,
    monetary value, and ROI metrics for each department.
    
    Args:
        usage_df: DataFrame with columns: department, feature_used, usage_count
        config: Optional configuration dict for ROI calculations
        
    Returns:
        DataFrame with columns: department, total_usage, active_users,
                                hours_saved, monetary_value_usd, avg_value_per_user
                                
    Raises:
        ValueError: If required columns are missing from usage_df
    """
    if usage_df.empty:
        return pd.DataFrame(columns=[
            'department', 'total_usage', 'active_users',
            'hours_saved', 'monetary_value_usd', 'avg_value_per_user'
        ])
    
    # Validate required columns
    required_cols = ['usage_count']
    missing_cols = [col for col in required_cols if col not in usage_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    if config is None:
        config = DEFAULT_ROI_CONFIG
    
    # Make a copy and ensure department column exists
    df = usage_df.copy()
    if 'department' not in df.columns:
        df['department'] = 'Unknown'
    
    # Calculate hours saved for each row
    df['hours_saved'] = df.apply(
        lambda row: estimate_hours_saved(
            row.get('usage_count', 0),
            row.get('feature_used', 'ChatGPT Messages'),
            config
        ),
        axis=1
    )
    
    # Calculate monetary value for each row
    df['monetary_value'] = df.apply(
        lambda row: calculate_monetary_value(
            row.get('hours_saved', 0),
            row.get('department', 'Unknown'),
            config=config
        ),
        axis=1
    )
    
    # Aggregate by department
    agg_dict = {
        'usage_count': 'sum',
        'hours_saved': 'sum',
        'monetary_value': 'sum'
    }
    
    # Add user count if user_id exists
    if 'user_id' in df.columns:
        agg_dict['user_id'] = 'nunique'
    
    result = df.groupby('department', as_index=False).agg(agg_dict)
    
    # Rename columns for clarity
    result = result.rename(columns={
        'usage_count': 'total_usage',
        'monetary_value': 'monetary_value_usd'
    })
    
    if 'user_id' in result.columns:
        result = result.rename(columns={'user_id': 'active_users'})
        # Calculate average value per user
        result['avg_value_per_user'] = (
            result['monetary_value_usd'] / result['active_users']
        ).round(2)
    else:
        result['active_users'] = 0
        result['avg_value_per_user'] = 0.0
    
    # Round numeric columns
    result['hours_saved'] = result['hours_saved'].round(2)
    result['monetary_value_usd'] = result['monetary_value_usd'].round(2)
    
    # Sort by monetary value descending
    result = result.sort_values('monetary_value_usd', ascending=False)
    
    return result


def calculate_composite_roi(
    usage_df: pd.DataFrame,
    date_column: str = 'date',
    config: Optional[Dict] = None
) -> Dict:
    """
    Calculate composite ROI metrics across all usage data.
    
    Provides organization-wide ROI summary including total hours saved,
    total monetary value, metrics by time period, and efficiency indicators.
    
    Args:
        usage_df: DataFrame with usage data
        date_column: Name of the date column for time-based analysis
        config: Optional configuration dict for ROI calculations
        
    Returns:
        dict: Composite ROI metrics including:
            - total_hours_saved
            - total_monetary_value_usd
            - total_users
            - total_usage_events
            - avg_hours_per_user
            - avg_value_per_user
            - date_range (if date column valid)
            - monthly_average_value (if date column valid)
    """
    if usage_df.empty:
        return {
            'total_hours_saved': 0.0,
            'total_monetary_value_usd': 0.0,
            'total_users': 0,
            'total_usage_events': 0,
            'avg_hours_per_user': 0.0,
            'avg_value_per_user': 0.0,
            'date_range': None,
            'monthly_average_value': 0.0
        }
    
    if config is None:
        config = DEFAULT_ROI_CONFIG
    
    # Make a copy
    df = usage_df.copy()
    
    # Calculate hours saved for each row
    df['hours_saved'] = df.apply(
        lambda row: estimate_hours_saved(
            row.get('usage_count', 0),
            row.get('feature_used', 'ChatGPT Messages'),
            config
        ),
        axis=1
    )
    
    # Calculate monetary value for each row
    df['monetary_value'] = df.apply(
        lambda row: calculate_monetary_value(
            row.get('hours_saved', 0),
            row.get('department', 'Unknown'),
            config=config
        ),
        axis=1
    )
    
    # Calculate aggregate metrics
    total_hours = df['hours_saved'].sum()
    total_value = df['monetary_value'].sum()
    total_usage = df['usage_count'].sum()
    
    # Calculate user metrics
    # Count unique emails to avoid over-counting users with multiple records
    total_users = df['email'].dropna().str.lower().nunique() if 'email' in df.columns else (df['user_id'].nunique() if 'user_id' in df.columns else 0)
    avg_hours_per_user = total_hours / total_users if total_users > 0 else 0.0
    avg_value_per_user = total_value / total_users if total_users > 0 else 0.0
    
    # Calculate date-based metrics if date column exists and is valid
    date_range = None
    monthly_avg = 0.0
    
    if date_column in df.columns:
        try:
            # Convert to datetime, handling various formats
            df['date_parsed'] = pd.to_datetime(df[date_column], errors='coerce')
            valid_dates = df['date_parsed'].dropna()
            
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                date_range = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
                
                # Calculate monthly average
                days_range = (max_date - min_date).days + 1
                months_range = days_range / 30.44  # Average days per month
                if months_range > 0:
                    monthly_avg = total_value / months_range
        except Exception:
            # If date parsing fails, leave date metrics as None/0
            pass
    
    return {
        'total_hours_saved': round(total_hours, 2),
        'total_monetary_value_usd': round(total_value, 2),
        'total_users': total_users,
        'total_usage_events': int(total_usage),
        'avg_hours_per_user': round(avg_hours_per_user, 2),
        'avg_value_per_user': round(avg_value_per_user, 2),
        'date_range': date_range,
        'monthly_average_value': round(monthly_avg, 2)
    }


def validate_date_field(date_value: Union[str, datetime, date, pd.Timestamp]) -> bool:
    """
    Validate if a date field is valid and not in the future.
    
    Args:
        date_value: Date value to validate
        
    Returns:
        bool: True if date is valid and not in the future, False otherwise
        
    Examples:
        >>> validate_date_field('2024-01-01')
        True
        >>> validate_date_field('invalid')
        False
        >>> validate_date_field(None)
        False
    """
    if date_value is None or pd.isna(date_value):
        return False
    
    try:
        # Convert to datetime if it's a string
        if isinstance(date_value, str):
            parsed_date = pd.to_datetime(date_value, errors='coerce')
            if pd.isna(parsed_date):
                return False
        elif isinstance(date_value, (datetime, date, pd.Timestamp)):
            parsed_date = pd.to_datetime(date_value)
        else:
            return False
        
        # Check if date is not in the future
        # Normalize both dates to remove time components for fair comparison
        today = pd.Timestamp.now().normalize()
        parsed_normalized = pd.Timestamp(parsed_date).normalize()
        if parsed_normalized > today:
            return False
        
        return True
    except Exception:
        return False
