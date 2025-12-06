"""
Utility functions for the diagnostic agent dashboard.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np


def format_percentage(value: float) -> str:
    """Format a decimal as a percentage string."""
    return f"{value * 100:.1f}%"


def format_number(value: float) -> str:
    """Format a number with thousands separator."""
    return f"{value:,.0f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return 0 if new_value == 0 else float('inf')
    return (new_value - old_value) / old_value


def get_trend_direction(change: float, threshold: float = 0.05) -> str:
    """Determine trend direction based on percentage change."""
    if abs(change) < threshold:
        return "stable"
    elif change > 0:
        return "increasing"
    else:
        return "decreasing"


def get_date_ranges(df: pd.DataFrame, date_column: str = 'Date') -> Tuple[datetime, datetime]:
    """Get the min and max dates from a dataframe."""
    dates = pd.to_datetime(df[date_column])
    return dates.min(), dates.max()


def filter_by_date_range(df: pd.DataFrame, start_date: datetime, end_date: datetime, 
                         date_column: str = 'Date') -> pd.DataFrame:
    """Filter dataframe by date range."""
    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column])
    mask = (df[date_column] >= start_date) & (df[date_column] <= end_date)
    return df[mask]


def get_kpi_columns(df: pd.DataFrame, exclude_cols: List[str] = None) -> List[str]:
    """Get list of KPI columns (excluding date and other non-KPI columns)."""
    if exclude_cols is None:
        exclude_cols = ['Date', 'date', 'timestamp', 'Timestamp']
    
    return [col for col in df.columns if col not in exclude_cols]


def calculate_moving_average(series: pd.Series, window: int = 7) -> pd.Series:
    """Calculate moving average for a time series."""
    return series.rolling(window=window, min_periods=1).mean()


def detect_anomalies(series: pd.Series, threshold: float = 2.0) -> pd.Series:
    """Detect anomalies using z-score method."""
    z_scores = np.abs((series - series.mean()) / series.std())
    return z_scores > threshold


def get_color_for_trend(trend: str) -> str:
    """Get color code for trend visualization."""
    colors = {
        'increasing': '#10b981',  # green
        'decreasing': '#ef4444',  # red
        'stable': '#6b7280'       # gray
    }
    return colors.get(trend, '#6b7280')


def summarize_period_stats(df: pd.DataFrame, kpi_column: str) -> dict:
    """Calculate summary statistics for a KPI over a period."""
    values = df[kpi_column].dropna()
    
    return {
        'mean': values.mean(),
        'median': values.median(),
        'std': values.std(),
        'min': values.min(),
        'max': values.max(),
        'total': values.sum(),
        'count': len(values)
    }
