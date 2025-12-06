"""
Diagnostic Agent Dashboard - Main Streamlit Application
A demo dashboard for analyzing KPI changes and diagnosing root causes.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from data_loader import load_and_cache_data, get_kpi_list
from analyzer import KPIAnalyzer, get_ai_analysis
from utils import format_percentage, format_number, get_color_for_trend


# Page configuration
st.set_page_config(
    page_title="KPI Diagnostic Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }
    
    .insight-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    h1, h2, h3 {
        color: white;
        font-weight: 700;
    }
    
    .stSelectbox label, .stDateInput label {
        color: white !important;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)


def create_time_series_chart(df: pd.DataFrame, kpi_name: str, period1_range, period2_range):
    """Create an interactive time series chart with period highlights."""
    fig = go.Figure()
    
    # Main time series line
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df[kpi_name],
        mode='lines',
        name=kpi_name,
        line=dict(color='#667eea', width=3),
        hovertemplate='<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>'
    ))
    
    # Add moving average
    ma_7 = df[kpi_name].rolling(window=7, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=ma_7,
        mode='lines',
        name='7-day Moving Average',
        line=dict(color='#fbbf24', width=2, dash='dash'),
        hovertemplate='<b>%{x}</b><br>7-day MA: %{y:.2f}<extra></extra>'
    ))
    
    # Highlight period 1
    fig.add_vrect(
        x0=period1_range[0], x1=period1_range[1],
        fillcolor="rgba(255, 0, 0, 0.1)",
        layer="below", line_width=0,
        annotation_text="Period 1", annotation_position="top left"
    )
    
    # Highlight period 2
    fig.add_vrect(
        x0=period2_range[0], x1=period2_range[1],
        fillcolor="rgba(0, 255, 0, 0.1)",
        layer="below", line_width=0,
        annotation_text="Period 2", annotation_position="top left"
    )
    
    fig.update_layout(
        title=f"{kpi_name} Over Time",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        paper_bgcolor='rgba(255, 255, 255, 0.95)',
        plot_bgcolor='rgba(255, 255, 255, 0.95)',
        font=dict(size=12)
    )
    
    return fig


def create_comparison_chart(period1_stats: dict, period2_stats: dict, kpi_name: str):
    """Create a comparison chart between two periods."""
    metrics = ['mean', 'median', 'min', 'max', 'total']
    period1_values = [period1_stats[m] for m in metrics]
    period2_values = [period2_stats[m] for m in metrics]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Period 1',
        x=[m.capitalize() for m in metrics],
        y=period1_values,
        marker_color='#ef4444',
        text=[f'{v:.1f}' for v in period1_values],
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name='Period 2',
        x=[m.capitalize() for m in metrics],
        y=period2_values,
        marker_color='#10b981',
        text=[f'{v:.1f}' for v in period2_values],
        textposition='auto',
    ))
    
    fig.update_layout(
        title=f"{kpi_name} - Statistical Comparison",
        barmode='group',
        template='plotly_white',
        height=400,
        paper_bgcolor='rgba(255, 255, 255, 0.95)',
        plot_bgcolor='rgba(255, 255, 255, 0.95)',
        font=dict(size=12)
    )
    
    return fig


def main():
    """Main application logic."""
    
    # Header
    st.title("📊 KPI Diagnostic Agent")
    st.markdown("### Understand *why* your metrics changed")
    
    # Load data
    with st.spinner("Loading KPI data..."):
        df = load_and_cache_data()
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    
    # KPI Selection
    available_kpis = get_kpi_list(df)
    selected_kpi = st.sidebar.selectbox(
        "Select KPI to Analyze",
        available_kpis,
        index=0,
        help="Choose which KPI you want to analyze"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Time Period Selection")
    
    # Get date range from data
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    # Period 1 (baseline)
    st.sidebar.markdown("**Period 1 (Baseline)**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        period1_start = st.date_input(
            "Start",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="p1_start"
        )
    with col2:
        period1_end = st.date_input(
            "End",
            value=min_date + timedelta(days=30),
            min_value=min_date,
            max_value=max_date,
            key="p1_end"
        )
    
    # Period 2 (comparison)
    st.sidebar.markdown("**Period 2 (Comparison)**")
    col3, col4 = st.sidebar.columns(2)
    with col3:
        period2_start = st.date_input(
            "Start",
            value=max_date - timedelta(days=30),
            min_value=min_date,
            max_value=max_date,
            key="p2_start"
        )
    with col4:
        period2_end = st.date_input(
            "End",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="p2_end"
        )
    
    # Convert to datetime
    period1_start = pd.to_datetime(period1_start)
    period1_end = pd.to_datetime(period1_end)
    period2_start = pd.to_datetime(period2_start)
    period2_end = pd.to_datetime(period2_end)
    
    # Analyze button
    analyze_button = st.sidebar.button("🔍 Analyze", type="primary", use_container_width=True)
    
    # Info section
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Demo Mode Active**\n\n"
        "Using mock data with 59 simulated KPIs. "
        "Connect to Google Sheets in production."
    )
    
    # Main content area
    if analyze_button or 'analysis_done' not in st.session_state:
        st.session_state.analysis_done = True
        
        # Perform analysis
        with st.spinner("Analyzing KPI changes..."):
            analyzer = KPIAnalyzer(df, selected_kpi)
            comparison = analyzer.compare_periods(
                period1_start, period1_end,
                period2_start, period2_end
            )
            insights = analyzer.generate_insights(comparison)
            ai_analysis = get_ai_analysis(selected_kpi, comparison, insights)
        
        # Display Key Metrics
        st.markdown("## 📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            period1_mean = comparison['period1']['stats']['mean']
            st.metric(
                "Period 1 Average",
                f"{period1_mean:.1f}",
                help="Average value in the baseline period"
            )
        
        with col2:
            period2_mean = comparison['period2']['stats']['mean']
            change = comparison['changes']['mean_change'] * 100
            st.metric(
                "Period 2 Average",
                f"{period2_mean:.1f}",
                f"{change:+.1f}%",
                delta_color="normal" if change > 0 else "inverse"
            )
        
        with col3:
            trend = comparison['trend']
            trend_emoji = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
            st.metric(
                "Trend",
                f"{trend_emoji} {trend.capitalize()}",
                help="Overall trend direction"
            )
        
        with col4:
            volatility_change = abs(
                comparison['period2']['stats']['std'] - comparison['period1']['stats']['std']
            )
            st.metric(
                "Volatility Change",
                f"{volatility_change:.1f}",
                help="Change in standard deviation between periods"
            )
        
        # Time Series Visualization
        st.markdown("## 📊 Time Series Analysis")
        ts_data = analyzer.get_time_series_data()
        chart = create_time_series_chart(
            ts_data, selected_kpi,
            (period1_start, period1_end),
            (period2_start, period2_end)
        )
        st.plotly_chart(chart, use_container_width=True)
        
        # Statistical Comparison
        st.markdown("## 📊 Statistical Comparison")
        comp_chart = create_comparison_chart(
            comparison['period1']['stats'],
            comparison['period2']['stats'],
            selected_kpi
        )
        st.plotly_chart(comp_chart, use_container_width=True)
        
        # Diagnostic Insights
        st.markdown("## 🔍 Diagnostic Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Summary")
            st.info(insights['summary'])
            
            st.markdown("### 📊 Variability Analysis")
            st.info(insights['variability'])
        
        with col2:
            st.markdown("### 🔗 Correlations")
            st.info(insights['correlation'])
            
            if comparison['correlations']:
                st.markdown("**Top Correlated KPIs:**")
                for kpi, corr in comparison['correlations'][:3]:
                    st.write(f"- {kpi}: {corr:.3f}")
        
        # Root Cause Analysis
        st.markdown("## 🎯 Root Cause Analysis")
        st.markdown(
            f'<div class="insight-card">'
            f'<h4>Diagnostic Hypothesis</h4>'
            f'<p style="font-size: 16px; line-height: 1.6;">{ai_analysis}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Additional Context
        with st.expander("📋 Detailed Statistics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Period 1 Statistics**")
                stats_df1 = pd.DataFrame([comparison['period1']['stats']]).T
                stats_df1.columns = ['Value']
                st.dataframe(stats_df1, use_container_width=True)
            
            with col2:
                st.markdown("**Period 2 Statistics**")
                stats_df2 = pd.DataFrame([comparison['period2']['stats']]).T
                stats_df2.columns = ['Value']
                st.dataframe(stats_df2, use_container_width=True)


if __name__ == "__main__":
    main()
