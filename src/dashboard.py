"""
KPI Diagnostic Dashboard - Clean Light Theme
Matching reference screenshot design
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets_client import GoogleSheetsClient
from calculation_engine import KPICalculationEngine
from country_mapping import COUNTRY_MAPPING

# Page config
st.set_page_config(
    page_title="KPI Diagnostic Dashboard - Bloq.it",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Light Color Palette (matching reference screenshot)
BG_LIGHT = "#f8f9fa"
TABLE_HEADER_BG = "#e9ecef"
ROW_EVEN_BG = "#ffffff"
ROW_ODD_BG = "#f8f9fa"
TEXT_PRIMARY = "#000000"
TEXT_SECONDARY = "#666666"
POSITIVE_GREEN = "#10b981"
NEGATIVE_RED = "#ef4444"
BLOQ_ORANGE = "#FF5733"

# Custom CSS - CLEAN LIGHT THEME
st.markdown(f"""
<style>
    /* Light background */
    .stApp {{
        background-color: {BG_LIGHT};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }}
    
    /* Headers - dark text */
    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT_PRIMARY} !important;
    }}
    
    /* Table styling */
    .metric-header {{
        color: {TEXT_SECONDARY};
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.75rem;
        background-color: {TABLE_HEADER_BG};
        text-align: center;
    }}
    
    .kpi-name-cell {{
        font-weight: 500;
        font-size: 0.9rem;
        padding: 1rem 0.75rem;
        color: {TEXT_PRIMARY};
        background-color: white;
        border-bottom: 1px solid #e0e0e0;
    }}
    
    .value-cell {{
        text-align: center;
        padding: 1rem 0.5rem;
        background-color: white;
        border-bottom: 1px solid #e0e0e0;
        color: {TEXT_PRIMARY} !important;
        font-size: 1rem;
        font-weight: 500;
    }}
    
    .value-number {{
        color: {TEXT_PRIMARY};
        font-weight: 600;
        font-size: 1.1rem;
    }}
    
    .change-positive {{
        color: {POSITIVE_GREEN};
        font-weight: 600;
        margin-left: 0.5rem;
    }}
    
    .change-negative {{
        color: {NEGATIVE_RED};
        font-weight: 600;
        margin-left: 0.5rem;
    }}
    
    /* Back button */
    div[data-testid="stButton"] button {{
        background-color: #e0e0e0;
        color: #000000;
        font-weight: 500;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1.5rem;
    }}
    
    div[data-testid="stButton"] button:hover {{
        background-color: #d0d0d0;
        color: #000000;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_cell' not in st.session_state:
    st.session_state.selected_cell = None

@st.cache_resource
def initialize_engine():
    """Initialize the calculation engine with caching."""
    client = GoogleSheetsClient()
    engine = KPICalculationEngine(client)
    return engine

def get_available_weeks(engine):
    """Get list of available weeks from raw data."""
    weeks = engine.get_available_weeks()
    
    if len(weeks) > 0:
        unique_weeks = sorted(set([str(w) for w in weeks if pd.notna(w) and w != '']))
        return unique_weeks[-12:] if len(unique_weeks) > 12 else unique_weeks
    
    return [f"2025_W{i}" for i in range(36, 49)]

def calculate_change_pct(current, previous):
    """Calculate percentage change."""
    if previous == 0 or previous is None or pd.isna(previous):
        return None
    return ((current - previous) / previous) * 100

def create_kpi_week_table_with_changes(engine, country, weeks):
    """Create table with KPIs, weeks, and week-over-week changes."""
    kpi_list = []
    for _, kpi_def in engine.catalogue.iterrows():
        kpi_list.append({
            'kpi_id': kpi_def['kpi_id'],
            'kpi_name': kpi_def['kpi_name'],
            'agg_type': kpi_def['aggregation_type']
        })
    
    table_data = []
    
    for kpi in kpi_list:
        row = {'KPI': kpi['kpi_name'], 'kpi_id': kpi['kpi_id'], 'agg_type': kpi['agg_type']}
        
        prev_value = None
        for week in weeks:
            result = engine.calculate_kpi(kpi['kpi_id'], country, week)
            
            if 'error' not in result:
                value = result.get('value', 0)
                
                # Calculate change from previous week
                change_pct = calculate_change_pct(value, prev_value) if prev_value is not None else None
                
                # Store value and change
                row[f"{week}_value"] = value
                row[f"{week}_change"] = change_pct
                
                prev_value = value
            else:
                row[f"{week}_value"] = None
                row[f"{week}_change"] = None
                prev_value = None
        
        table_data.append(row)
    
    return pd.DataFrame(table_data), weeks

def format_value(value, agg_type):
    """Format value based on aggregation type."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    elif agg_type == 'RATIO':
        return f"{value:.0f}%"
    elif isinstance(value, (int, float)):
        return f"{value:,.0f}" if value == int(value) else f"{value:,.1f}"
    return str(value)

def format_change_html(change):
    """Format change percentage with colored HTML."""
    if change is None or pd.isna(change):
        return ""
    sign = "+" if change > 0 else ""
    color_class = "change-positive" if change > 0 else "change-negative"
    return f'<span class="{color_class}">{sign}{change:.0f}%</span>'

def show_cell_diagnostic(engine, kpi_id, kpi_name, country, week):
    """Show diagnostic for specific KPI + Week."""
    # Back button at the top
    if st.button("← Back to Overview"):
        st.session_state.selected_cell = None
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"### 🔍 Diagnostic: {kpi_name} - {week.split('_')[-1]}")
    
    # Calculate KPI
    result = engine.calculate_kpi(kpi_id, country, week)
    
    if 'error' in result:
        st.error(f"Error: {result['error']}")
        return

    # --- TREND GRAPH ---
    st.markdown("#### 📈 Trend Analysis")
    
    # Fetch historical data (using all available weeks)
    available_weeks = get_available_weeks(engine)
    # Filter to last 12 weeks for better visibility if too many
    display_weeks = available_weeks[-12:] if len(available_weeks) > 12 else available_weeks
    
    trend_data = []
    for w in display_weeks:
        res = engine.calculate_kpi(kpi_id, country, w)
        if 'error' not in res:
            trend_data.append({
                'Week': w.split('_')[-1],
                'Value': res.get('value', None)
            })
    
    if trend_data:
        trend_df = pd.DataFrame(trend_data)
        fig_trend = px.line(
            trend_df, 
            x='Week', 
            y='Value', 
            title=f"{kpi_name} Trend ({country})",
            markers=True
        )
        fig_trend.update_traces(line_color=BLOQ_ORANGE, line_width=3)
        fig_trend.update_layout(
            height=350,
            xaxis_title="Week",
            yaxis_title="Value",
            hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("---")
    # -------------------
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        value = result.get('value', 0)
        if result.get('aggregation_type') == 'RATIO':
            st.metric("Value", f"{value:.1f}%")
        else:
            st.metric("Value", f"{value:,.0f}")
    
    with col2:
        st.metric("Week", week.split('_')[-1])
    
    with col3:
        st.metric("Country", country)
    
    with col4:
        if 'record_count' in result:
            st.metric("Records", f"{result['record_count']:,}")
    
    # Ratio calculation if applicable
    if result.get('aggregation_type') == 'RATIO':
        st.markdown("#### 📊 Calculation")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                f"Numerator: {result['numerator']['name']}",
                f"{result['numerator']['value']:,.0f}"
            )
        with col2:
            st.markdown("<div style='text-align: center; padding-top: 20px; font-size: 24px;'>÷</div>", unsafe_allow_html=True)
        with col3:
            st.metric(
                f"Denominator: {result['denominator']['name']}",
                f"{result['denominator']['value']:,.0f}"
            )
    
    # Root cause analysis
    st.markdown("#### 🎯 Root Cause Analysis")
    breakdown = engine.get_root_cause_breakdown(kpi_id, country, week)
    
    if 'breakdowns' in breakdown and len(breakdown['breakdowns']) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            first_dim = list(breakdown['breakdowns'].keys())[0]
            breakdown_data = breakdown['breakdowns'][first_dim]
            
            categories = list(breakdown_data.keys())[:10]
            values = [breakdown_data[cat] for cat in categories]
            
            fig = go.Figure(go.Bar(
                x=categories,
                y=values,
                marker_color=BLOQ_ORANGE,
                text=values,
                textposition='auto'
            ))
            fig.update_layout(
                title=f"Breakdown by {first_dim}",
                xaxis_title=first_dim,
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart
            sorted_data = sorted(breakdown_data.items(), key=lambda x: x[1], reverse=True)
            top_data = dict(sorted_data[:8])
            if len(sorted_data) > 8:
                top_data['Other'] = sum([v for k, v in sorted_data[8:]])
            
            fig = px.pie(
                values=list(top_data.values()),
                names=list(top_data.keys()),
                title=f"Distribution by {first_dim}",
                color_discrete_sequence=[BLOQ_ORANGE, '#FFA07A', '#FF7F50', '#FF6347', '#FF4500', '#DC143C', '#B22222', '#8B0000']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed tables
        st.markdown("#### 📋 Detailed Breakdown")
        tabs = st.tabs(list(breakdown['breakdowns'].keys()))
        
        for i, (dim_name, dim_data) in enumerate(breakdown['breakdowns'].items()):
            with tabs[i]:
                df = pd.DataFrame(
                    list(dim_data.items()),
                    columns=[dim_name, 'Count']
                ).sort_values('Count', ascending=False)
                
                total = df['Count'].sum()
                df['Percentage'] = (df['Count'] / total * 100).round(1).astype(str) + '%'
                
                st.dataframe(df, hide_index=True, use_container_width=True, height=400)
    else:
        st.info("No root cause dimensions available")

    # Raw Data Explorer
    st.markdown("---")
    st.markdown("#### 📋 Raw Data Explorer")
    
    # Fetch data
    raw_df = engine.get_filtered_kpi_data(kpi_id, country, week)
    
    if len(raw_df) > 0:
        # Search functionality
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search", placeholder="Type to search across all columns...")
        
        # Filter functionality
        all_columns = raw_df.columns.tolist()
        
        # Default columns: show first 10 columns by default to avoid clutter
        default_cols = all_columns[:10] if len(all_columns) > 10 else all_columns
        
        with col2:
            selected_columns = st.multiselect("Select Columns", all_columns, default=default_cols)
        
        # Apply filters
        display_df = raw_df.copy()
        
        if search_term:
            # Create a mask for string match across all columns
            # Convert to string, lowercase for case-insensitive search
            mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]
        
        if selected_columns:
            display_df = display_df[selected_columns]
            
        # Display data
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(display_df)} of {len(raw_df)} records")
        
        # Download button
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{kpi_name}_{country}_{week}_raw_data.csv",
            mime='text/csv',
        )
    else:
        st.info("No raw data available for this selection.")

import auth

def main():
    """Main application."""
    
    # Check authentication
    if not auth.check_authentication():
        st.stop()
    
    # Sidebar Logout
    with st.sidebar:
        if st.button("Log out"):
            auth.logout()
    
    # Logo and header
    col1, col2 = st.columns([1, 5])
    with col1:
        logo_path = "assets/bloq_logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
    with col2:
        st.markdown(f'<h1>KPI Diagnostic Dashboard</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #666;">Click on any KPI value to see detailed analysis</p>', unsafe_allow_html=True)
        
        # Display current user
        if "username" in st.session_state:
            st.caption(f"Logged in as: {st.session_state['username']}")
    
    # Initialize engine
    with st.spinner("Connecting to Google Sheets..."):
        try:
            engine = initialize_engine()
        except Exception as e:
            st.error(f"Failed to connect: {str(e)}")
            st.stop()
    
    # Sidebar
    st.sidebar.markdown("## 🎛️ Filters")
    
    # Access Control: Get allowed countries
    username = st.session_state.get("username", "")
    allowed_countries = auth.get_user_permissions(username)
    
    # Country selector with permissions
    all_countries = engine.get_available_countries()
    
    if "ALL" in allowed_countries:
        countries = all_countries
    else:
        # Filter countries based on permissions
        # Match roughly (e.g., "France" in permissions matches "France 🇫🇷" in list)
        countries = []
        for c in all_countries:
            for allowed in allowed_countries:
                if allowed.lower() in c.lower():
                    countries.append(c)
                    break
    
    if len(countries) == 0:
        st.error("No countries available for your account.")
        st.stop()
        
    selected_country = st.sidebar.selectbox(
        "Select Country",
        countries,
        index=0 if len(countries) > 0 else None
    )
    
    # Week range
    all_weeks = get_available_weeks(engine)
    
    st.sidebar.markdown("### Week Range")
    if len(all_weeks) >= 2:
        start_idx = st.sidebar.select_slider(
            "From Week",
            options=list(range(len(all_weeks))),
            value=max(0, len(all_weeks) - 12),
            format_func=lambda x: all_weeks[x].split('_')[-1] if '_' in all_weeks[x] else all_weeks[x]
        )
        end_idx = st.sidebar.select_slider(
            "To Week",
            options=list(range(len(all_weeks))),
            value=len(all_weeks) - 1,
            format_func=lambda x: all_weeks[x].split('_')[-1] if '_' in all_weeks[x] else all_weeks[x]
        )
        
        selected_weeks = all_weeks[start_idx:end_idx + 1]
    else:
        selected_weeks = all_weeks
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Current Selection")
    st.sidebar.markdown(f"**Country:** {selected_country}")
    st.sidebar.markdown(f"**Weeks:** {len(selected_weeks)} weeks")
    
    # Main content
    if st.session_state.selected_cell is None:
        # Show KPI table
        st.markdown("---")
        
        with st.spinner(f"Calculating KPIs for {selected_country}..."):
            df, weeks = create_kpi_week_table_with_changes(engine, selected_country, selected_weeks)
        
        if len(df) > 0:
            # Column headers
            header_cols = st.columns([2.5, 0.8] + [1.1] * len(selected_weeks))
            with header_cols[0]:
                st.markdown('<div class="metric-header" style="text-align: left;">METRIC</div>', unsafe_allow_html=True)
            with header_cols[1]:
                st.markdown('<div class="metric-header">TARGET</div>', unsafe_allow_html=True)
            for i, week in enumerate(selected_weeks):
                with header_cols[i + 2]:
                    week_display = week.split('_')[-1] if '_' in week else week
                    st.markdown(f'<div class="metric-header">{week_display}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # KPI rows with clickable cells
            for idx, row in df.iterrows():
                cols = st.columns([2.5, 0.8] + [1.1] * len(selected_weeks))
                
                # KPI name
                with cols[0]:
                    st.markdown(f'<div class="kpi-name-cell">{row["KPI"]}</div>', unsafe_allow_html=True)
                
                # Target column
                with cols[1]:
                    st.markdown('<div class="value-cell">N/A</div>', unsafe_allow_html=True)
                
                # Week values - CLICKABLE CELLS
                for i, week in enumerate(selected_weeks):
                    with cols[i + 2]:
                        value = row[f"{week}_value"]
                        change = row[f"{week}_change"]
                        
                        formatted_value = format_value(value, row['agg_type'])
                        
                        # Build display with value and colored change
                        # Build display with value and colored change logic (for tooltip only)
                        if change is not None and not pd.isna(change):
                            sign = "+" if change > 0 else ""
                            change_text = f"{sign}{change:.0f}%"
                        else:
                            change_text = ""
                        
                        # Button with value only (requested change)
                        if st.button(formatted_value, key=f"cell_{row['kpi_id']}_{week}", help=f"Change: {change_text}" if change_text else "Click to analyze", use_container_width=True):
                                st.session_state.selected_cell = {
                                    'kpi_id': row['kpi_id'],
                                    'kpi_name': row['KPI'],
                                    'week': week
                                }
                                st.rerun()
                
                # Row separator
                st.markdown('<div style="height: 0; border-bottom: 1px solid #e0e0e0; margin: 0;"></div>', unsafe_allow_html=True)
        else:
            st.warning("No KPIs to display")
    
    else:
        # Show diagnostic view
        show_cell_diagnostic(
            engine,
            st.session_state.selected_cell['kpi_id'],
            st.session_state.selected_cell['kpi_name'],
            selected_country,
            st.session_state.selected_cell['week']
        )

if __name__ == "__main__":
    main()
