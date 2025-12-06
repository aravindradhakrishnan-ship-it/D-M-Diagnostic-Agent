"""
Diagnostic analyzer module.
Performs KPI analysis and generates insights about metric changes.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

from utils import (
    calculate_percentage_change,
    get_trend_direction,
    summarize_period_stats,
    filter_by_date_range,
    calculate_moving_average
)

load_dotenv()


class KPIAnalyzer:
    """Main analyzer class for KPI diagnostics."""
    
    def __init__(self, df: pd.DataFrame, kpi_name: str):
        """
        Initialize the analyzer with data and selected KPI.
        
        Args:
            df: DataFrame with Date and KPI columns
            kpi_name: Name of the KPI to analyze
        """
        self.df = df.copy()
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.kpi_name = kpi_name
        
    def compare_periods(self, period1_start: datetime, period1_end: datetime,
                       period2_start: datetime, period2_end: datetime) -> Dict:
        """
        Compare KPI performance between two time periods.
        
        Returns:
            Dictionary with comparison metrics and insights
        """
        # Filter data for each period
        period1_data = filter_by_date_range(self.df, period1_start, period1_end)
        period2_data = filter_by_date_range(self.df, period2_start, period2_end)
        
        # Calculate statistics for each period
        period1_stats = summarize_period_stats(period1_data, self.kpi_name)
        period2_stats = summarize_period_stats(period2_data, self.kpi_name)
        
        # Calculate changes
        mean_change = calculate_percentage_change(period1_stats['mean'], period2_stats['mean'])
        total_change = calculate_percentage_change(period1_stats['total'], period2_stats['total'])
        
        # Determine trend
        trend = get_trend_direction(mean_change)
        
        # Get correlation with other KPIs
        correlations = self._find_correlations(period2_data)
        
        return {
            'period1': {
                'start': period1_start,
                'end': period1_end,
                'stats': period1_stats
            },
            'period2': {
                'start': period2_start,
                'end': period2_end,
                'stats': period2_stats
            },
            'changes': {
                'mean_change': mean_change,
                'total_change': total_change,
                'absolute_mean_change': period2_stats['mean'] - period1_stats['mean'],
                'absolute_total_change': period2_stats['total'] - period1_stats['total']
            },
            'trend': trend,
            'correlations': correlations
        }
    
    def _find_correlations(self, df: pd.DataFrame, top_n: int = 5) -> List[Tuple[str, float]]:
        """Find KPIs most correlated with the selected KPI."""
        # Get numeric columns (excluding Date)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if self.kpi_name not in numeric_cols:
            return []
        
        # Calculate correlations
        correlations = df[numeric_cols].corr()[self.kpi_name].sort_values(ascending=False)
        
        # Remove self-correlation and get top N
        correlations = correlations[correlations.index != self.kpi_name]
        top_correlations = correlations.head(top_n)
        
        return [(kpi, corr) for kpi, corr in top_correlations.items()]
    
    def detect_change_points(self) -> List[datetime]:
        """Detect significant change points in the KPI time series."""
        values = self.df[self.kpi_name].values
        dates = self.df['Date'].values
        
        # Calculate rolling statistics
        window = 7
        rolling_mean = pd.Series(values).rolling(window=window).mean()
        rolling_std = pd.Series(values).rolling(window=window).std()
        
        # Detect points where value is significantly different from recent trend
        change_points = []
        for i in range(window, len(values)):
            z_score = abs((values[i] - rolling_mean[i]) / (rolling_std[i] + 1e-10))
            if z_score > 2.5:  # Significant deviation
                change_points.append(dates[i])
        
        return change_points[:5]  # Return top 5 most recent
    
    def generate_insights(self, comparison: Dict) -> Dict[str, str]:
        """
        Generate human-readable insights from comparison data.
        
        Args:
            comparison: Output from compare_periods()
        
        Returns:
            Dictionary with different types of insights
        """
        changes = comparison['changes']
        trend = comparison['trend']
        period1_stats = comparison['period1']['stats']
        period2_stats = comparison['period2']['stats']
        correlations = comparison['correlations']
        
        # Basic change insight
        pct_change = changes['mean_change'] * 100
        direction = "increased" if pct_change > 0 else "decreased"
        
        basic_insight = (
            f"The {self.kpi_name} {direction} by {abs(pct_change):.1f}% "
            f"from an average of {period1_stats['mean']:.1f} to {period2_stats['mean']:.1f}."
        )
        
        # Variability insight
        variability_change = calculate_percentage_change(period1_stats['std'], period2_stats['std'])
        if abs(variability_change) > 0.2:
            variability_direction = "more volatile" if variability_change > 0 else "more stable"
            variability_insight = (
                f"The metric has become {variability_direction}, with standard deviation "
                f"changing from {period1_stats['std']:.1f} to {period2_stats['std']:.1f}."
            )
        else:
            variability_insight = "Variability remained relatively stable between periods."
        
        # Correlation insight
        if correlations:
            top_corr_kpi, top_corr_value = correlations[0]
            corr_type = "positive" if top_corr_value > 0 else "negative"
            correlation_insight = (
                f"The {self.kpi_name} shows a strong {corr_type} correlation "
                f"({top_corr_value:.2f}) with {top_corr_kpi}."
            )
        else:
            correlation_insight = "No significant correlations detected with other KPIs."
        
        # Root cause hypothesis (rule-based)
        root_cause = self._generate_root_cause_hypothesis(comparison)
        
        return {
            'summary': basic_insight,
            'variability': variability_insight,
            'correlation': correlation_insight,
            'root_cause_hypothesis': root_cause,
            'trend': trend
        }
    
    def _generate_root_cause_hypothesis(self, comparison: Dict) -> str:
        """Generate a rule-based hypothesis about root causes."""
        changes = comparison['changes']
        correlations = comparison['correlations']
        trend = comparison['trend']
        
        hypotheses = []
        
        # Check magnitude of change
        pct_change = abs(changes['mean_change'] * 100)
        if pct_change > 50:
            hypotheses.append("The significant change magnitude suggests a major operational shift or external factor.")
        elif pct_change > 20:
            hypotheses.append("The moderate change indicates potential process adjustments or efficiency improvements.")
        else:
            hypotheses.append("The minor change could be due to normal operational variations.")
        
        # Check correlations
        if correlations:
            top_kpi, top_corr = correlations[0]
            if abs(top_corr) > 0.7:
                hypotheses.append(
                    f"Strong correlation with {top_kpi} suggests these metrics are interconnected. "
                    f"Changes in one likely affect the other."
                )
        
        # Trend-based insights
        if trend == "increasing":
            if "Cost" in self.kpi_name or "Downtime" in self.kpi_name or "Failures" in self.kpi_name:
                hypotheses.append("The increase may indicate deteriorating performance or efficiency issues requiring attention.")
            else:
                hypotheses.append("The upward trend suggests improving performance or increased activity levels.")
        elif trend == "decreasing":
            if "Cost" in self.kpi_name or "Downtime" in self.kpi_name or "Failures" in self.kpi_name:
                hypotheses.append("The decrease indicates positive improvements in efficiency or reliability.")
            else:
                hypotheses.append("The decline may signal reduced capacity, resource constraints, or declining activity.")
        
        return " ".join(hypotheses)
    
    def get_time_series_data(self) -> pd.DataFrame:
        """Get the full time series for the selected KPI."""
        return self.df[['Date', self.kpi_name]].copy()


def get_ai_analysis(kpi_name: str, comparison: Dict, insights: Dict) -> Optional[str]:
    """
    Get AI-powered analysis using OpenAI API (if configured).
    Falls back to rule-based analysis if API key not available.
    
    Args:
        kpi_name: Name of the KPI
        comparison: Comparison data from analyzer
        insights: Generated insights
    
    Returns:
        AI-generated analysis or None if not available
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        # Return rule-based analysis
        return insights['root_cause_hypothesis']
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Prepare context for AI
        context = f"""
        Analyze the following KPI change:
        
        KPI Name: {kpi_name}
        Period 1 Average: {comparison['period1']['stats']['mean']:.1f}
        Period 2 Average: {comparison['period2']['stats']['mean']:.1f}
        Change: {comparison['changes']['mean_change'] * 100:.1f}%
        Trend: {comparison['trend']}
        
        Summary: {insights['summary']}
        Variability: {insights['variability']}
        Correlations: {insights['correlation']}
        
        Provide a concise root cause analysis explaining why this change might have occurred.
        Focus on actionable insights and potential underlying factors.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a data analyst specializing in KPI analysis and root cause investigation."},
                {"role": "user", "content": context}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"AI analysis failed: {e}")
        return insights['root_cause_hypothesis']
