"""
Export utilities for AI Usage Analytics Dashboard

Provides PDF and Excel export functionality with executive-ready formatting.
"""
import pandas as pd
from datetime import datetime
from io import BytesIO
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def generate_excel_export(data, include_pivots=True):
    """
    Generate Excel export with multiple sheets including pivot tables.
    
    Args:
        data: DataFrame with usage metrics
        include_pivots: Whether to include pivot table sheets
        
    Returns:
        BytesIO object containing Excel file
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main data sheet
        data.to_excel(writer, sheet_name='Raw Data', index=False)
        
        if include_pivots and not data.empty:
            # User summary pivot
            user_summary = data.groupby(['user_name', 'email', 'department']).agg({
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            user_summary.columns = ['User Name', 'Email', 'Department', 'Total Usage', 'Total Cost']
            user_summary = user_summary.sort_values('Total Usage', ascending=False)
            user_summary.to_excel(writer, sheet_name='User Summary', index=False)
            
            # Department summary pivot
            dept_summary = data.groupby('department').agg({
                'user_id': 'nunique',
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            dept_summary.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
            dept_summary['Avg Cost per User'] = dept_summary['Total Cost'] / dept_summary['Active Users']
            dept_summary = dept_summary.sort_values('Total Usage', ascending=False)
            dept_summary.to_excel(writer, sheet_name='Department Summary', index=False)
            
            # Monthly trends pivot
            try:
                monthly_data = data.copy()
                monthly_data['date'] = pd.to_datetime(monthly_data['date'], errors='coerce')
                monthly_data = monthly_data.dropna(subset=['date'])
                monthly_data['month'] = monthly_data['date'].dt.to_period('M').astype(str)
                
                monthly_summary = monthly_data.groupby('month').agg({
                    'user_id': 'nunique',
                    'usage_count': 'sum',
                    'cost_usd': 'sum'
                }).reset_index()
                monthly_summary.columns = ['Month', 'Active Users', 'Total Usage', 'Total Cost']
                monthly_summary.to_excel(writer, sheet_name='Monthly Trends', index=False)
            except:
                pass
            
            # Feature usage pivot
            feature_summary = data.groupby('feature_used').agg({
                'user_id': 'nunique',
                'usage_count': 'sum',
                'cost_usd': 'sum'
            }).reset_index()
            feature_summary.columns = ['Feature', 'Unique Users', 'Total Usage', 'Total Cost']
            feature_summary = feature_summary.sort_values('Total Usage', ascending=False)
            feature_summary.to_excel(writer, sheet_name='Feature Usage', index=False)
    
    output.seek(0)
    return output

def generate_pdf_report_html(data, report_title="AI Usage Analytics Report"):
    """
    Generate HTML for PDF export with executive summary.
    
    Args:
        data: DataFrame with usage metrics
        report_title: Title for the report
        
    Returns:
        HTML string for PDF conversion
    """
    # Calculate key metrics
    total_cost = data['cost_usd'].sum()
    total_users = data['user_id'].nunique()
    total_usage = data['usage_count'].sum()
    avg_cost_per_user = total_cost / max(total_users, 1)
    
    # Get top departments
    dept_stats = data.groupby('department').agg({
        'user_id': 'nunique',
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    dept_stats.columns = ['Department', 'Active Users', 'Total Usage', 'Total Cost']
    dept_stats = dept_stats.sort_values('Total Usage', ascending=False).head(5)
    
    # Get top users
    user_stats = data.groupby(['user_name', 'department']).agg({
        'usage_count': 'sum',
        'cost_usd': 'sum'
    }).reset_index()
    user_stats = user_stats.sort_values('usage_count', ascending=False).head(10)
    
    # Calculate monthly trends
    monthly_html = ""
    try:
        monthly_data = data.copy()
        monthly_data['date'] = pd.to_datetime(monthly_data['date'], errors='coerce')
        monthly_data = monthly_data.dropna(subset=['date'])
        monthly_data['month'] = monthly_data['date'].dt.to_period('M').astype(str)
        
        monthly_summary = monthly_data.groupby('month').agg({
            'user_id': 'nunique',
            'usage_count': 'sum',
            'cost_usd': 'sum'
        }).reset_index()
        monthly_summary.columns = ['Month', 'Active Users', 'Total Usage', 'Total Cost']
        
        monthly_html = monthly_summary.to_html(index=False, classes='data-table')
    except:
        monthly_html = "<p>Monthly trend data not available</p>"
    
    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{report_title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px;
                color: #1e293b;
                line-height: 1.6;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: #f8fafc;
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #e2e8f0;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .metric-label {{
                color: #64748b;
                font-size: 0.9em;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section h2 {{
                color: #667eea;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .data-table th {{
                background: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            .data-table td {{
                padding: 10px 12px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .data-table tr:nth-child(even) {{
                background: #f8fafc;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
                color: #64748b;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{report_title}</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Cost</div>
                <div class="metric-value">${total_cost:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Active Users</div>
                <div class="metric-value">{total_users:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Usage</div>
                <div class="metric-value">{total_usage:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Cost per User</div>
                <div class="metric-value">${avg_cost_per_user:.2f}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Top Departments by Usage</h2>
            {dept_stats.to_html(index=False, classes='data-table')}
        </div>
        
        <div class="section">
            <h2>Top Users</h2>
            {user_stats.to_html(index=False, classes='data-table')}
        </div>
        
        <div class="section">
            <h2>Monthly Trends</h2>
            {monthly_html}
        </div>
        
        <div class="footer">
            <p><strong>AI Usage Analytics Dashboard</strong> | Executive Report</p>
            <p>This report is confidential and intended for internal use only.</p>
        </div>
    </body>
    </html>
    """
    
    return html
