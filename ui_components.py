import streamlit as st
import plotly.express as px

def render_metric_card(label, value, subtext=None, tooltip=None):
    """Renders a styled metric card."""
    help_str = f'help="{tooltip}"' if tooltip else ""
    html = f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; color: #64748b;">{label}</div>
        <div style="font-size: 1.8rem; font-weight: bold; color: #1e293b;">{value}</div>
        {f'<div style="font-size: 0.8rem; color: #64748b;">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_kpi_row(metrics):
    """Renders a row of metrics (dict: label -> value)."""
    cols = st.columns(len(metrics))
    for idx, (label, data) in enumerate(metrics.items()):
        with cols[idx]:
            render_metric_card(label, data['value'], data.get('subtext'), data.get('tooltip'))

def render_trend_chart(df, x_col, y_col, title, color=None):
    """Standardized Plotly chart."""
    if df.empty:
        st.info("No data available for chart.")
        return
    
    fig = px.bar(df, x=x_col, y=y_col, color=color, title=title)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)
