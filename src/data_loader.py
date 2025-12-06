"""
Data loader module for the diagnostic agent.
Supports both mock data (demo mode) and Google Sheets integration.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def generate_mock_data(num_days: int = 90, num_kpis: int = 59) -> pd.DataFrame:
    """
    Generate mock KPI data for demonstration purposes.
    Creates realistic-looking time series data with trends and variations.
    """
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days - 1)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Initialize dataframe with dates
    data = {'Date': dates}
    
    # Define some realistic KPI names
    kpi_names = [
        'Performed Intervention',
        'Asset Availability',
        'Work Orders Completed',
        'Preventive Maintenance Completed',
        'Corrective Maintenance Completed',
        'Average Response Time (hrs)',
        'Mean Time Between Failures (hrs)',
        'Mean Time To Repair (hrs)',
        'Spare Parts Consumption',
        'Maintenance Cost ($)',
        'Labor Hours',
        'Equipment Downtime (hrs)',
        'Safety Incidents',
        'Compliance Score (%)',
        'Customer Satisfaction Score',
        'Backlog Work Orders',
        'Emergency Work Orders',
        'Planned Work Completion Rate (%)',
        'First Time Fix Rate (%)',
        'Repeat Failures',
        'Technician Utilization Rate (%)',
        'Parts Availability (%)',
        'Maintenance Schedule Adherence (%)',
        'Asset Health Score',
        'Energy Consumption (kWh)',
        'Environmental Incidents',
        'Training Hours Completed',
        'Work Order Cycle Time (days)',
        'Inventory Turnover Rate',
        'Vendor Performance Score',
        'Budget Variance (%)',
        'ROI on Maintenance (%)',
        'Predictive Maintenance Alerts',
        'Critical Equipment Failures',
        'Planned Downtime (hrs)',
        'Unplanned Downtime (hrs)',
        'Maintenance Backlog (days)',
        'Tool Calibration Compliance (%)',
        'Asset Lifecycle Cost ($)',
        'Warranty Claims',
        'Overtime Hours',
        'Contractor Usage (hrs)',
        'Quality Defects',
        'On-Time Delivery Rate (%)',
        'Asset Utilization Rate (%)',
        'Maintenance Rework Rate (%)',
        'Critical Spare Stock Level',
        'Work Permit Compliance (%)',
        'Equipment Age (avg years)',
        'Maintenance Cost per Asset ($)',
        'Production Impact (units)',
        'System Availability (%)',
        'Reliability Index',
        'Risk Score',
        'Audit Findings',
        'Documentation Accuracy (%)',
        'Mobile Work Order Usage (%)',
        'Digital Twin Accuracy (%)',
        'IoT Sensor Coverage (%)'
    ]
    
    # Use the first num_kpis names
    selected_kpis = kpi_names[:num_kpis]
    
    # Generate data for each KPI with different characteristics
    np.random.seed(42)  # For reproducibility
    
    for i, kpi_name in enumerate(selected_kpis):
        # Each KPI has a different base value and trend
        base_value = np.random.uniform(50, 500)
        trend = np.random.uniform(-0.5, 0.5)  # Daily trend
        seasonality = np.random.uniform(0, 20)  # Seasonal amplitude
        noise_level = np.random.uniform(5, 15)  # Random variation
        
        # Create time series with trend, seasonality, and noise
        t = np.arange(num_days)
        values = (
            base_value +
            trend * t +
            seasonality * np.sin(2 * np.pi * t / 30) +  # Monthly seasonality
            np.random.normal(0, noise_level, num_days)
        )
        
        # Add some sudden changes for interesting analysis
        if i % 5 == 0:  # Some KPIs have sudden drops
            change_point = num_days // 2
            values[change_point:] *= 0.8
        elif i % 7 == 0:  # Some KPIs have sudden increases
            change_point = num_days // 3
            values[change_point:] *= 1.2
        
        # Ensure non-negative values for most KPIs
        if 'Rate' in kpi_name or 'Score' in kpi_name or '%' in kpi_name:
            values = np.clip(values, 0, 100)
        else:
            values = np.maximum(values, 0)
        
        data[kpi_name] = values
    
    return pd.DataFrame(data)


def load_kpi_data(use_mock: Optional[bool] = None) -> pd.DataFrame:
    """
    Load KPI data either from Google Sheets or generate mock data.
    
    Args:
        use_mock: If True, use mock data. If None, check environment variable.
    
    Returns:
        DataFrame with Date column and KPI columns
    """
    if use_mock is None:
        use_mock = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
    
    if use_mock:
        return generate_mock_data()
    else:
        # Google Sheets integration would go here
        # For now, return mock data with a note
        print("Google Sheets integration not yet configured. Using mock data.")
        return generate_mock_data()


def get_kpi_list(df: pd.DataFrame) -> list:
    """Get list of available KPIs from the dataframe."""
    return [col for col in df.columns if col != 'Date']


def load_and_cache_data():
    """Load data with caching for better performance in Streamlit."""
    import streamlit as st
    
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def _load_data():
        return load_kpi_data()
    
    return _load_data()
