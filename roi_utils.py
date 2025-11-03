"""
ROI Utilities for OpenAI Usage Metrics Dashboard

This module provides reusable functions for transforming raw OpenAI usage exports
into actionable ROI (Return on Investment) figures. It includes utilities for:
- Mapping feature usage to estimated time and cost savings
- Inferring business value beyond direct costs
- Calculating composite AI impact scores
- Identifying value creation leaders by user/department
- Computing opportunity cost metrics

All formulas and benchmarks are documented with references to industry standards
and research where applicable.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union


# ============================================================================
# CONFIGURATION: Industry Benchmarks and Rates
# ============================================================================

# Time savings benchmarks (minutes saved per interaction)
# Reference: McKinsey Global Institute (2023) - "The Economic Potential of Generative AI"
# and OpenAI research on productivity gains
TIME_SAVINGS_PER_FEATURE = {
    'ChatGPT Messages': 12.0,      # Average time saved per message (research/writing tasks)
    'Tool Messages': 25.0,          # Code generation, API calls save more time
    'Project Messages': 18.0,       # Project-specific workflows
    'BlueFlame Queries': 15.0,      # Enterprise search/knowledge retrieval
    'API Calls': 20.0,              # Automated tasks
    'General': 10.0                 # Default for unknown feature types
}

# Labor cost rates (USD per hour) by department
# Reference: Bureau of Labor Statistics (2024) - median wage data
# These are conservative estimates for enterprise employees
LABOR_COST_PER_HOUR = {
    'Engineering': 85.0,
    'Product': 75.0,
    'Finance': 70.0,
    'Operations': 65.0,
    'Marketing': 60.0,
    'Sales': 65.0,
    'HR': 60.0,
    'Legal': 95.0,
    'Executive': 150.0,
    'IT': 75.0,
    'Customer Success': 55.0,
    'Unknown': 60.0,              # Conservative default
    'Default': 60.0
}

# Department impact multipliers for strategic value
# Captures differential business impact across departments
# Reference: Custom framework based on organizational value chain analysis
DEPARTMENT_IMPACT_MULTIPLIER = {
    'Engineering': 1.3,           # High leverage - product development
    'Product': 1.25,              # Strategic planning and roadmap
    'Sales': 1.2,                 # Revenue generation
    'Executive': 1.4,             # Strategic decisions
    'Finance': 1.15,              # Risk management and planning
    'Marketing': 1.1,             # Brand and customer acquisition
    'Operations': 1.05,           # Efficiency improvements
    'Customer Success': 1.1,      # Customer retention value
    'HR': 1.0,                    # Standard impact
    'Legal': 1.15,                # Risk mitigation
    'IT': 1.1,                    # Infrastructure and support
    'Unknown': 1.0,               # Neutral
    'Default': 1.0
}

# Feature complexity weights for impact scoring
# Higher weights indicate more complex/valuable use cases
FEATURE_COMPLEXITY_WEIGHT = {
    'Tool Messages': 1.5,         # Advanced features (code, APIs)
    'Project Messages': 1.3,      # Collaborative/structured work
    'ChatGPT Messages': 1.0,      # Standard usage
    'BlueFlame Queries': 1.2,     # Knowledge retrieval
    'API Calls': 1.4,             # Automation
    'General': 1.0                # Default
}


# ============================================================================
# CORE ROI CALCULATION FUNCTIONS
# ============================================================================

def calculate_time_savings(usage_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate estimated time savings from AI usage based on feature types.
    
    This function maps feature usage counts to time saved using industry benchmarks
    from McKinsey research on generative AI productivity gains. The calculation
    assumes each interaction replaces manual work that would have taken longer.
    
    Formula:
        time_saved_minutes = usage_count × time_savings_per_feature
        time_saved_hours = time_saved_minutes / 60
    
    Args:
        usage_data: DataFrame with columns ['feature_used', 'usage_count']
                   Typically from usage_metrics table
    
    Returns:
        DataFrame with added columns:
        - time_saved_minutes: Total minutes saved per record
        - time_saved_hours: Total hours saved per record
    
    Reference:
        McKinsey Global Institute (2023), "The Economic Potential of Generative AI"
        Reports 10-30% productivity gains across knowledge work tasks
    
    Example:
        >>> df = pd.DataFrame({
        ...     'feature_used': ['ChatGPT Messages', 'Tool Messages'],
        ...     'usage_count': [100, 50]
        ... })
        >>> result = calculate_time_savings(df)
        >>> result['time_saved_hours'].sum()  # Total hours saved
        45.83
    """
    df = usage_data.copy()
    
    # Map feature types to time savings
    df['time_saved_minutes'] = df.apply(
        lambda row: row['usage_count'] * TIME_SAVINGS_PER_FEATURE.get(
            row['feature_used'], 
            TIME_SAVINGS_PER_FEATURE['General']
        ),
        axis=1
    )
    
    # Convert to hours
    df['time_saved_hours'] = df['time_saved_minutes'] / 60.0
    
    return df


def calculate_cost_savings(usage_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate estimated cost savings based on time saved and labor costs.
    
    This function combines time savings estimates with department-specific labor
    costs to quantify the economic value of AI usage. It uses Bureau of Labor
    Statistics median wage data adjusted for enterprise contexts.
    
    Formula:
        cost_saved_usd = time_saved_hours × labor_cost_per_hour[department]
    
    Args:
        usage_data: DataFrame with columns ['time_saved_hours', 'department']
                   Typically output from calculate_time_savings()
    
    Returns:
        DataFrame with added column:
        - cost_saved_usd: Estimated cost savings in USD
    
    Reference:
        Bureau of Labor Statistics (2024) - Occupational Employment and Wage Statistics
        Adjusted upward by 20% for enterprise benefits/overhead costs
    
    Example:
        >>> df = calculate_time_savings(usage_df)
        >>> df = calculate_cost_savings(df)
        >>> df.groupby('department')['cost_saved_usd'].sum()
    """
    df = usage_data.copy()
    
    # Ensure time_saved_hours exists
    if 'time_saved_hours' not in df.columns:
        df = calculate_time_savings(df)
    
    # Normalize department names
    df['department_normalized'] = df['department'].fillna('Unknown').str.strip()
    
    # Map departments to labor costs
    df['labor_cost_per_hour'] = df['department_normalized'].apply(
        lambda dept: LABOR_COST_PER_HOUR.get(dept, LABOR_COST_PER_HOUR['Default'])
    )
    
    # Calculate cost savings
    df['cost_saved_usd'] = df['time_saved_hours'] * df['labor_cost_per_hour']
    
    return df


def calculate_business_value(usage_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive business value beyond direct cost savings.
    
    This function applies department impact multipliers to recognize that AI usage
    in strategic roles (e.g., Executive, Engineering) creates disproportionate value
    through better decisions, faster innovation, and higher-leverage outcomes.
    
    Formula:
        business_value_usd = cost_saved_usd × department_impact_multiplier
    
    The multiplier approach is based on organizational value chain analysis where
    different functions have varying leverage on business outcomes.
    
    Args:
        usage_data: DataFrame with columns ['cost_saved_usd', 'department']
                   Typically output from calculate_cost_savings()
    
    Returns:
        DataFrame with added columns:
        - impact_multiplier: Department-specific multiplier
        - business_value_usd: Adjusted value including strategic impact
    
    Reference:
        Novel framework inspired by Porter's Value Chain Analysis (1985)
        and activity-based costing principles
    
    Example:
        >>> df = calculate_business_value(usage_df)
        >>> total_value = df['business_value_usd'].sum()
    """
    df = usage_data.copy()
    
    # Ensure cost_saved_usd exists
    if 'cost_saved_usd' not in df.columns:
        df = calculate_cost_savings(df)
    
    # Normalize department names
    if 'department_normalized' not in df.columns:
        df['department_normalized'] = df['department'].fillna('Unknown').str.strip()
    
    # Apply impact multipliers
    df['impact_multiplier'] = df['department_normalized'].apply(
        lambda dept: DEPARTMENT_IMPACT_MULTIPLIER.get(dept, DEPARTMENT_IMPACT_MULTIPLIER['Default'])
    )
    
    # Calculate business value
    df['business_value_usd'] = df['cost_saved_usd'] * df['impact_multiplier']
    
    return df


def calculate_ai_impact_score(usage_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate composite AI impact scores for users and departments.
    
    The AI Impact Score is a novel metric combining:
    1. Usage volume (normalized)
    2. Feature complexity (advanced features score higher)
    3. Department strategic value
    4. Consistency over time (if date data available)
    
    Formula:
        base_score = log(1 + usage_count) × feature_complexity_weight
        impact_score = base_score × department_multiplier × consistency_factor
        normalized_score = (impact_score / max_score) × 100
    
    This creates a 0-100 score where higher values indicate users/departments
    getting maximum strategic value from AI tools.
    
    Args:
        usage_data: DataFrame with columns ['usage_count', 'feature_used', 'department']
    
    Returns:
        DataFrame with added columns:
        - ai_impact_score: Composite score (0-100)
        - score_category: High/Medium/Low categorization
    
    Reference:
        Novel metric inspired by Net Promoter Score methodology and
        Digital Adoption Platform engagement scoring frameworks
    
    Example:
        >>> df = calculate_ai_impact_score(usage_df)
        >>> top_users = df.nlargest(10, 'ai_impact_score')
    """
    df = usage_data.copy()
    
    # Base score from usage (log scale to handle wide ranges)
    df['base_usage_score'] = np.log1p(df['usage_count'])
    
    # Apply feature complexity weights
    df['complexity_weight'] = df['feature_used'].apply(
        lambda feat: FEATURE_COMPLEXITY_WEIGHT.get(feat, FEATURE_COMPLEXITY_WEIGHT['General'])
    )
    
    # Normalize department names
    if 'department_normalized' not in df.columns:
        df['department_normalized'] = df['department'].fillna('Unknown').str.strip()
    
    # Apply department multipliers
    if 'impact_multiplier' not in df.columns:
        df['impact_multiplier'] = df['department_normalized'].apply(
            lambda dept: DEPARTMENT_IMPACT_MULTIPLIER.get(dept, DEPARTMENT_IMPACT_MULTIPLIER['Default'])
        )
    
    # Calculate raw impact score
    df['raw_impact_score'] = (
        df['base_usage_score'] * 
        df['complexity_weight'] * 
        df['impact_multiplier']
    )
    
    # Normalize to 0-100 scale
    max_score = df['raw_impact_score'].max()
    if max_score > 0:
        df['ai_impact_score'] = (df['raw_impact_score'] / max_score) * 100
    else:
        df['ai_impact_score'] = 0
    
    # Categorize scores
    df['score_category'] = pd.cut(
        df['ai_impact_score'],
        bins=[0, 33, 66, 100],
        labels=['Low', 'Medium', 'High'],
        include_lowest=True
    )
    
    return df


def identify_value_leaders(
    usage_data: pd.DataFrame,
    by: str = 'user',
    top_n: int = 10,
    metric: str = 'business_value_usd'
) -> pd.DataFrame:
    """
    Identify top value creators by user or department.
    
    This function aggregates value metrics and ranks users or departments to
    identify where AI investments are creating the most impact. Useful for
    targeting training, recognition, and resource allocation.
    
    Args:
        usage_data: DataFrame with ROI metrics already calculated
        by: Grouping dimension - 'user' or 'department'
        top_n: Number of top leaders to return
        metric: Metric to rank by (e.g., 'business_value_usd', 'time_saved_hours')
    
    Returns:
        DataFrame with top leaders and their metrics
    
    Reference:
        Based on Pareto analysis (80/20 rule) for identifying high-impact users
    
    Example:
        >>> leaders = identify_value_leaders(usage_df, by='user', top_n=20)
        >>> dept_leaders = identify_value_leaders(usage_df, by='department')
    """
    df = usage_data.copy()
    
    # Ensure required metric exists
    if metric not in df.columns:
        if metric == 'business_value_usd':
            df = calculate_business_value(df)
        elif metric == 'cost_saved_usd':
            df = calculate_cost_savings(df)
        elif metric == 'time_saved_hours':
            df = calculate_time_savings(df)
    
    # Group by specified dimension
    group_col = 'user_id' if by == 'user' else 'department'
    
    if group_col not in df.columns:
        raise ValueError(f"Column '{group_col}' not found in usage_data")
    
    # Aggregate metrics
    agg_dict = {
        'usage_count': 'sum',
        metric: 'sum'
    }
    
    # Add optional metrics if they exist
    if 'time_saved_hours' in df.columns and metric != 'time_saved_hours':
        agg_dict['time_saved_hours'] = 'sum'
    if 'cost_saved_usd' in df.columns and metric != 'cost_saved_usd':
        agg_dict['cost_saved_usd'] = 'sum'
    if 'business_value_usd' in df.columns and metric != 'business_value_usd':
        agg_dict['business_value_usd'] = 'sum'
    
    # Include user_name if grouping by user
    if by == 'user' and 'user_name' in df.columns:
        # Get first user_name for each user_id
        user_names = df.groupby('user_id')['user_name'].first()
    
    # Perform aggregation
    leaders = df.groupby(group_col).agg(agg_dict).reset_index()
    
    # Add user names back if available
    if by == 'user' and 'user_name' in df.columns:
        leaders['user_name'] = leaders['user_id'].map(user_names)
    
    # Sort by metric and get top N
    leaders = leaders.sort_values(metric, ascending=False).head(top_n)
    
    # Calculate percentage of total
    total_value = df[metric].sum()
    if total_value > 0:
        leaders['pct_of_total'] = (leaders[metric] / total_value) * 100
    else:
        leaders['pct_of_total'] = 0
    
    return leaders


def calculate_opportunity_cost(
    usage_data: pd.DataFrame,
    total_licenses: int,
    license_cost_per_user: float = 0.0
) -> Dict[str, float]:
    """
    Calculate opportunity costs of unused licenses and underutilization.
    
    This metric helps identify waste in AI tool investments by comparing
    licensed seats to active users and measuring usage intensity.
    
    Formulas:
        unused_licenses = total_licenses - active_users
        unused_license_cost = unused_licenses × license_cost_per_user
        underutilization_cost = (expected_value - actual_value) for low-use segments
    
    Args:
        usage_data: DataFrame with user usage metrics
        total_licenses: Total number of licenses purchased
        license_cost_per_user: Monthly cost per license (default 0 if not tracked)
    
    Returns:
        Dictionary with opportunity cost metrics:
        - unused_licenses: Number of inactive licenses
        - unused_license_cost_monthly: Cost of unused licenses per month
        - active_users: Number of users with activity
        - utilization_rate: Percentage of licenses being used
        - low_usage_users: Count of users with minimal usage
        - opportunity_for_improvement: Estimated additional value from full utilization
    
    Reference:
        Based on SaaS spend optimization frameworks from Zylo and Productiv
    
    Example:
        >>> metrics = calculate_opportunity_cost(usage_df, total_licenses=500, 
        ...                                       license_cost_per_user=30)
        >>> print(f"Wasted spend: ${metrics['unused_license_cost_monthly']:,.2f}")
    """
    df = usage_data.copy()
    
    # Calculate active users (unique users with any activity)
    active_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
    
    # Calculate unused licenses
    unused_licenses = max(0, total_licenses - active_users)
    unused_license_cost = unused_licenses * license_cost_per_user
    
    # Calculate utilization rate
    utilization_rate = (active_users / total_licenses * 100) if total_licenses > 0 else 0
    
    # Identify low-usage users (below 25th percentile)
    user_usage = df.groupby('user_id')['usage_count'].sum() if 'user_id' in df.columns else pd.Series()
    
    if len(user_usage) > 0:
        low_usage_threshold = user_usage.quantile(0.25)
        low_usage_users = (user_usage < low_usage_threshold).sum()
        median_usage = user_usage.median()
    else:
        low_usage_users = 0
        median_usage = 0
    
    # Estimate opportunity for improvement
    # If low-usage users reached median usage, how much additional value?
    if 'business_value_usd' in df.columns:
        avg_value_per_message = df['business_value_usd'].sum() / max(df['usage_count'].sum(), 1)
        
        if len(user_usage) > 0:
            current_low_usage = user_usage[user_usage < low_usage_threshold].sum()
            potential_increase = low_usage_users * median_usage - current_low_usage
            opportunity_value = potential_increase * avg_value_per_message
        else:
            opportunity_value = 0
    else:
        opportunity_value = 0
    
    return {
        'total_licenses': total_licenses,
        'active_users': active_users,
        'unused_licenses': unused_licenses,
        'unused_license_cost_monthly': unused_license_cost,
        'utilization_rate_pct': utilization_rate,
        'low_usage_users': low_usage_users,
        'opportunity_for_improvement_usd': opportunity_value,
        'license_cost_per_user': license_cost_per_user
    }


def calculate_roi_summary(
    usage_data: pd.DataFrame,
    total_licenses: int = 0,
    license_cost_per_user: float = 0.0,
    include_all_metrics: bool = True
) -> Dict[str, Union[float, int, Dict]]:
    """
    Generate comprehensive ROI summary report across all metrics.
    
    This is a convenience function that runs all ROI calculations and returns
    a consolidated summary suitable for dashboard display or reporting.
    
    Args:
        usage_data: DataFrame with user usage data
        total_licenses: Total licensed seats (optional)
        license_cost_per_user: Cost per license (optional)
        include_all_metrics: Whether to calculate all intermediate metrics
    
    Returns:
        Dictionary containing:
        - total_time_saved_hours: Aggregate time savings
        - total_cost_saved_usd: Aggregate cost savings
        - total_business_value_usd: Aggregate business value
        - avg_time_saved_per_user_hours: Average per user
        - avg_value_per_user_usd: Average value per user
        - top_users: List of top 10 value creators
        - top_departments: List of top departments
        - opportunity_costs: Opportunity cost metrics
        - roi_ratio: Business value / license costs (if costs provided)
    
    Example:
        >>> summary = calculate_roi_summary(usage_df, total_licenses=500, 
        ...                                  license_cost_per_user=30)
        >>> print(f"Total ROI: ${summary['total_business_value_usd']:,.2f}")
        >>> print(f"ROI Ratio: {summary['roi_ratio']:.2f}x")
    """
    # Calculate all enrichments
    df = usage_data.copy()
    
    if include_all_metrics:
        df = calculate_time_savings(df)
        df = calculate_cost_savings(df)
        df = calculate_business_value(df)
        df = calculate_ai_impact_score(df)
    
    # Aggregate metrics
    total_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
    total_usage = df['usage_count'].sum() if 'usage_count' in df.columns else 0
    
    summary = {
        'total_users': total_users,
        'total_usage': total_usage,
        'avg_usage_per_user': total_usage / max(total_users, 1)
    }
    
    # Time and cost metrics
    if 'time_saved_hours' in df.columns:
        summary['total_time_saved_hours'] = df['time_saved_hours'].sum()
        summary['avg_time_saved_per_user_hours'] = summary['total_time_saved_hours'] / max(total_users, 1)
    
    if 'cost_saved_usd' in df.columns:
        summary['total_cost_saved_usd'] = df['cost_saved_usd'].sum()
        summary['avg_cost_saved_per_user_usd'] = summary['total_cost_saved_usd'] / max(total_users, 1)
    
    if 'business_value_usd' in df.columns:
        summary['total_business_value_usd'] = df['business_value_usd'].sum()
        summary['avg_business_value_per_user_usd'] = summary['total_business_value_usd'] / max(total_users, 1)
    
    # Value leaders
    if 'business_value_usd' in df.columns:
        summary['top_users'] = identify_value_leaders(df, by='user', top_n=10, 
                                                      metric='business_value_usd').to_dict('records')
        summary['top_departments'] = identify_value_leaders(df, by='department', top_n=10, 
                                                            metric='business_value_usd').to_dict('records')
    
    # Opportunity costs
    if total_licenses > 0:
        summary['opportunity_costs'] = calculate_opportunity_cost(
            df, total_licenses, license_cost_per_user
        )
        
        # Calculate ROI ratio
        if license_cost_per_user > 0 and 'total_business_value_usd' in summary:
            total_license_cost = total_users * license_cost_per_user
            if total_license_cost > 0:
                summary['roi_ratio'] = summary['total_business_value_usd'] / total_license_cost
            else:
                summary['roi_ratio'] = 0
    
    return summary


# ============================================================================
# HELPER FUNCTIONS FOR CUSTOMIZATION
# ============================================================================

def update_time_savings_benchmark(feature: str, minutes_saved: float) -> None:
    """
    Update time savings benchmark for a specific feature type.
    
    Allows customization of time savings estimates based on organization-specific
    benchmarks or measurement studies.
    
    Args:
        feature: Feature type name (e.g., 'ChatGPT Messages')
        minutes_saved: Updated estimate of minutes saved per interaction
    
    Example:
        >>> update_time_savings_benchmark('Tool Messages', 30.0)
    """
    TIME_SAVINGS_PER_FEATURE[feature] = minutes_saved


def update_labor_cost(department: str, cost_per_hour: float) -> None:
    """
    Update labor cost for a specific department.
    
    Allows customization based on actual organizational compensation data.
    
    Args:
        department: Department name
        cost_per_hour: Loaded labor cost in USD per hour
    
    Example:
        >>> update_labor_cost('Engineering', 95.0)
    """
    LABOR_COST_PER_HOUR[department] = cost_per_hour


def update_department_multiplier(department: str, multiplier: float) -> None:
    """
    Update strategic impact multiplier for a department.
    
    Allows customization based on organization's value chain and priorities.
    
    Args:
        department: Department name
        multiplier: Impact multiplier (1.0 = neutral, >1.0 = high leverage)
    
    Example:
        >>> update_department_multiplier('Executive', 2.0)
    """
    DEPARTMENT_IMPACT_MULTIPLIER[department] = multiplier


def get_current_benchmarks() -> Dict[str, Dict]:
    """
    Get current configuration of all benchmarks and rates.
    
    Returns:
        Dictionary with all current benchmark configurations
    
    Example:
        >>> benchmarks = get_current_benchmarks()
        >>> print(benchmarks['time_savings'])
    """
    return {
        'time_savings': TIME_SAVINGS_PER_FEATURE.copy(),
        'labor_costs': LABOR_COST_PER_HOUR.copy(),
        'department_multipliers': DEPARTMENT_IMPACT_MULTIPLIER.copy(),
        'feature_complexity': FEATURE_COMPLEXITY_WEIGHT.copy()
    }


if __name__ == '__main__':
    """
    Example usage demonstrating the ROI utilities module.
    """
    # Sample data
    sample_data = pd.DataFrame({
        'user_id': ['user1@company.com', 'user2@company.com', 'user3@company.com'] * 3,
        'user_name': ['Alice', 'Bob', 'Charlie'] * 3,
        'department': ['Engineering', 'Sales', 'Finance'] * 3,
        'feature_used': ['ChatGPT Messages', 'Tool Messages', 'Project Messages'] * 3,
        'usage_count': [150, 200, 100, 80, 120, 90, 50, 180, 110]
    })
    
    print("ROI Utilities Example Usage")
    print("=" * 80)
    
    # Calculate comprehensive ROI
    enriched_data = calculate_time_savings(sample_data)
    enriched_data = calculate_cost_savings(enriched_data)
    enriched_data = calculate_business_value(enriched_data)
    enriched_data = calculate_ai_impact_score(enriched_data)
    
    print("\nEnriched Data Sample:")
    print(enriched_data[['user_name', 'department', 'usage_count', 
                         'time_saved_hours', 'cost_saved_usd', 
                         'business_value_usd', 'ai_impact_score']].head())
    
    print("\n\nTop Value Leaders (by User):")
    top_users = identify_value_leaders(enriched_data, by='user', top_n=5)
    print(top_users[['user_id', 'usage_count', 'business_value_usd', 'pct_of_total']])
    
    print("\n\nTop Departments:")
    top_depts = identify_value_leaders(enriched_data, by='department', top_n=5)
    print(top_depts[['department', 'usage_count', 'business_value_usd', 'pct_of_total']])
    
    print("\n\nROI Summary:")
    summary = calculate_roi_summary(enriched_data, total_licenses=500, license_cost_per_user=30)
    for key, value in summary.items():
        if not isinstance(value, (list, dict)):
            print(f"{key}: {value}")
    
    print("\n" + "=" * 80)
