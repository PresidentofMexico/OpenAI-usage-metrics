"""
Example: Using ROI Utilities in Dashboard

This example demonstrates how to integrate roi_utils.py into the
OpenAI Usage Metrics Dashboard (app.py) to create an ROI analytics tab.

USAGE IN DASHBOARD:
-------------------
1. Import the module at the top of app.py:
   from roi_utils import (
       calculate_time_savings,
       calculate_cost_savings, 
       calculate_business_value,
       calculate_ai_impact_score,
       identify_value_leaders,
       calculate_roi_summary
   )

2. Add the ROI calculations to your data processing:
   See example_roi_tab() function below for implementation

3. Add a new tab to your dashboard:
   Update the st.tabs() call to include "💰 ROI Analytics"
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import ROI utilities
from roi_utils import (
    calculate_time_savings,
    calculate_cost_savings,
    calculate_business_value,
    calculate_ai_impact_score,
    identify_value_leaders,
    calculate_roi_summary
)


def example_roi_tab(usage_data: pd.DataFrame, total_licenses: int = 500, 
                    license_cost_per_user: float = 30.0):
    """
    Example ROI Analytics Tab for Streamlit Dashboard.
    
    This function demonstrates how to create a comprehensive ROI analytics
    section using the roi_utils module. It can be added as a new tab in app.py.
    
    Args:
        usage_data: DataFrame from database with usage metrics
        total_licenses: Total number of licenses purchased (for utilization calc)
        license_cost_per_user: Monthly cost per license
    
    Example integration in app.py:
        # After defining tabs
        tab1, tab2, tab_openai, tab3, tab4, tab5, tab6, tab_roi = st.tabs([
            "📊 Executive Overview", 
            "🔄 Tool Comparison",
            "🤖 OpenAI Analytics",
            "⭐ Power Users",
            "📈 Message Type Analytics",
            "🏢 Department Mapper",
            "🔧 Database Management",
            "💰 ROI Analytics"  # NEW TAB
        ])
        
        with tab_roi:
            example_roi_tab(data, total_licenses=500, license_cost_per_user=30)
    """
    st.header("💰 ROI Analytics & Business Value")
    
    if usage_data.empty:
        st.warning("No usage data available. Please upload data to see ROI analytics.")
        return
    
    # Calculate all ROI metrics
    with st.spinner("Calculating ROI metrics..."):
        enriched_data = calculate_time_savings(usage_data)
        enriched_data = calculate_cost_savings(enriched_data)
        enriched_data = calculate_business_value(enriched_data)
        enriched_data = calculate_ai_impact_score(enriched_data)
        
        # Generate summary
        roi_summary = calculate_roi_summary(
            usage_data,
            total_licenses=total_licenses,
            license_cost_per_user=license_cost_per_user,
            include_all_metrics=True
        )
    
    # ========================================================================
    # SECTION 1: Executive Summary Metrics
    # ========================================================================
    st.subheader("📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Business Value",
            value=f"${roi_summary['total_business_value_usd']:,.0f}",
            help="Estimated total business value generated from AI usage, including strategic impact"
        )
    
    with col2:
        st.metric(
            label="Time Saved",
            value=f"{roi_summary['total_time_saved_hours']:,.0f} hrs",
            help="Total hours saved across all users and features"
        )
    
    with col3:
        st.metric(
            label="ROI Ratio",
            value=f"{roi_summary.get('roi_ratio', 0):.1f}x",
            help="Business value generated per dollar of license cost"
        )
    
    with col4:
        st.metric(
            label="Avg Value/User",
            value=f"${roi_summary['avg_business_value_per_user_usd']:,.0f}",
            help="Average business value per active user"
        )
    
    # ========================================================================
    # SECTION 2: Value Distribution Visualizations
    # ========================================================================
    st.subheader("📈 Value Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top users by value
        st.markdown("**🏆 Top Value Creators (Users)**")
        top_users = identify_value_leaders(enriched_data, by='user', top_n=10, 
                                           metric='business_value_usd')
        
        if not top_users.empty:
            # Bar chart
            fig = px.bar(
                top_users,
                x='business_value_usd',
                y='user_name' if 'user_name' in top_users.columns else 'user_id',
                orientation='h',
                title='Top 10 Users by Business Value',
                labels={'business_value_usd': 'Business Value ($)', 
                       'user_name': 'User'},
                color='business_value_usd',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top departments by value
        st.markdown("**🏢 Top Departments by Value**")
        top_depts = identify_value_leaders(enriched_data, by='department', top_n=10,
                                           metric='business_value_usd')
        
        if not top_depts.empty:
            fig = px.bar(
                top_depts,
                x='business_value_usd',
                y='department',
                orientation='h',
                title='Departments by Business Value',
                labels={'business_value_usd': 'Business Value ($)', 
                       'department': 'Department'},
                color='business_value_usd',
                color_continuous_scale='Plasma'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # SECTION 3: AI Impact Scores
    # ========================================================================
    st.subheader("🎯 AI Impact Scores")
    
    st.markdown("""
    The AI Impact Score is a composite metric (0-100) that combines:
    - Usage volume and consistency
    - Feature complexity (advanced features score higher)
    - Department strategic value
    """)
    
    # Score distribution
    score_dist = enriched_data.groupby('score_category').size().reset_index(name='count')
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Category counts
        st.markdown("**Score Distribution**")
        for _, row in score_dist.iterrows():
            st.metric(
                label=f"{row['score_category']} Impact",
                value=row['count']
            )
    
    with col2:
        # Top scoring users
        st.markdown("**Top AI Impact Scores**")
        top_scores = enriched_data.nlargest(10, 'ai_impact_score')[
            ['user_name', 'department', 'ai_impact_score', 'score_category']
        ] if 'user_name' in enriched_data.columns else enriched_data.nlargest(10, 'ai_impact_score')[
            ['user_id', 'department', 'ai_impact_score', 'score_category']
        ]
        
        # Format for display
        display_df = top_scores.copy()
        display_df['ai_impact_score'] = display_df['ai_impact_score'].round(1)
        st.dataframe(display_df, hide_index=True, use_container_width=True)
    
    # ========================================================================
    # SECTION 4: Opportunity Analysis
    # ========================================================================
    if 'opportunity_costs' in roi_summary:
        st.subheader("💡 Opportunity & Utilization Analysis")
        
        opp = roi_summary['opportunity_costs']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="License Utilization",
                value=f"{opp['utilization_rate_pct']:.1f}%",
                delta=f"{opp['active_users']} of {opp['total_licenses']} licenses",
                help="Percentage of purchased licenses being actively used"
            )
        
        with col2:
            st.metric(
                label="Unused Licenses",
                value=opp['unused_licenses'],
                delta=f"-${opp['unused_license_cost_monthly']:,.0f}/month",
                delta_color="inverse",
                help="Number of licenses not being used and their monthly cost"
            )
        
        with col3:
            st.metric(
                label="Improvement Potential",
                value=f"${opp['opportunity_for_improvement_usd']:,.0f}",
                help="Additional value possible if low-usage users reached median usage"
            )
        
        # Utilization gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=opp['utilization_rate_pct'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "License Utilization Rate"},
            delta={'reference': 100},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 33], 'color': "lightgray"},
                    {'range': [33, 66], 'color': "gray"},
                    {'range': [66, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # ========================================================================
    # SECTION 5: Detailed Metrics Table
    # ========================================================================
    with st.expander("📋 View Detailed ROI Metrics by User"):
        # Aggregate by user
        user_metrics = enriched_data.groupby('user_id').agg({
            'user_name': 'first',
            'department': 'first',
            'usage_count': 'sum',
            'time_saved_hours': 'sum',
            'cost_saved_usd': 'sum',
            'business_value_usd': 'sum',
            'ai_impact_score': 'max'
        }).reset_index()
        
        # Format currency columns
        user_metrics['cost_saved_usd'] = user_metrics['cost_saved_usd'].apply(
            lambda x: f"${x:,.2f}"
        )
        user_metrics['business_value_usd'] = user_metrics['business_value_usd'].apply(
            lambda x: f"${x:,.2f}"
        )
        user_metrics['time_saved_hours'] = user_metrics['time_saved_hours'].apply(
            lambda x: f"{x:,.1f}"
        )
        user_metrics['ai_impact_score'] = user_metrics['ai_impact_score'].apply(
            lambda x: f"{x:.1f}"
        )
        
        # Rename for display
        user_metrics.rename(columns={
            'user_id': 'Email',
            'user_name': 'Name',
            'department': 'Department',
            'usage_count': 'Total Usage',
            'time_saved_hours': 'Time Saved (hrs)',
            'cost_saved_usd': 'Cost Saved',
            'business_value_usd': 'Business Value',
            'ai_impact_score': 'Impact Score'
        }, inplace=True)
        
        st.dataframe(user_metrics, hide_index=True, use_container_width=True)
    
    # ========================================================================
    # SECTION 6: Methodology & References
    # ========================================================================
    with st.expander("ℹ️ Methodology & Benchmarks"):
        st.markdown("""
        ### ROI Calculation Methodology
        
        **Time Savings Estimation:**
        - ChatGPT Messages: 12 minutes saved per message
        - Tool Messages (Code, APIs): 25 minutes saved per message
        - Project Messages: 18 minutes saved per message
        - Source: McKinsey Global Institute (2023) - "The Economic Potential of Generative AI"
        
        **Labor Cost Rates:**
        - Engineering: $85/hour
        - Sales: $65/hour
        - Finance: $70/hour
        - Other departments: $60/hour (default)
        - Source: Bureau of Labor Statistics (2024) + 20% for benefits/overhead
        
        **Business Value Multipliers:**
        - Strategic departments (Executive, Engineering) receive higher multipliers (1.3-1.4x)
        - Reflects differential impact on business outcomes
        - Based on Porter's Value Chain Analysis
        
        **AI Impact Score:**
        - Novel composite metric (0-100 scale)
        - Combines: usage volume, feature complexity, department value
        - Inspired by NPS and digital adoption frameworks
        
        **Opportunity Costs:**
        - Based on SaaS spend optimization frameworks
        - Identifies underutilization and waste
        - Estimates improvement potential
        
        ### Customization
        
        These benchmarks can be customized using:
        ```python
        from roi_utils import (
            update_time_savings_benchmark,
            update_labor_cost,
            update_department_multiplier
        )
        
        # Example: Update Engineering labor cost
        update_labor_cost('Engineering', 95.0)
        ```
        """)


if __name__ == '__main__':
    """
    Standalone demo of the ROI tab.
    Run with: streamlit run example_roi_dashboard.py
    """
    st.set_page_config(page_title="ROI Analytics Demo", page_icon="💰", layout="wide")
    
    # Generate sample data
    import numpy as np
    np.random.seed(42)
    
    users = [f'user{i}@company.com' for i in range(1, 31)]
    departments = ['Engineering', 'Sales', 'Finance', 'Marketing', 'Operations']
    features = ['ChatGPT Messages', 'Tool Messages', 'Project Messages']
    
    rows = []
    for user in users:
        dept = np.random.choice(departments)
        name = user.split('@')[0].title()
        for feature in features:
            usage = int(np.random.uniform(20, 300))
            rows.append({
                'user_id': user,
                'user_name': name,
                'department': dept,
                'feature_used': feature,
                'usage_count': usage,
                'date': '2024-01-01',
                'tool_source': 'ChatGPT'
            })
    
    sample_data = pd.DataFrame(rows)
    
    # Display the ROI tab
    example_roi_tab(sample_data, total_licenses=100, license_cost_per_user=30.0)
