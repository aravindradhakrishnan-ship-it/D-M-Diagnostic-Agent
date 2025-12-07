"""
KPI Calculation Engine
Calculates KPIs based on definitions from KPI Catalogue and raw data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from country_mapping import get_country_data_value


class KPICalculationEngine:
    """
    Engine that calculates KPIs based on catalogue definitions.
    Applies filters, aggregations, and tracks driver contributions.
    """
    
    def __init__(self, google_sheets_client):
        """
        Initialize the calculation engine.
        
        Args:
            google_sheets_client: Instance of GoogleSheetsClient
        """
        self.client = google_sheets_client
        self.catalogue = None
        self.raw_data_cache = {}
        self._load_catalogue()
    
    def _load_catalogue(self):
        """Load and parse KPI Catalogue."""
        self.catalogue = self.client.get_kpi_catalogue()
        if self.catalogue is not None:
            print(f"✅ Loaded {len(self.catalogue)} KPI definitions")
    
    def get_raw_data(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get raw data from a specific table with caching.
        
        Args:
            table_name: Name of the raw data table
            
        Returns:
            DataFrame with raw data
        """
        if table_name in self.raw_data_cache:
            return self.raw_data_cache[table_name]
        
        df = self.client.read_sheet_to_dataframe(table_name)
        if df is not None:
            # Convert date columns only (NOT week columns which have format like '2025_W48')
            for col in df.columns:
                if 'date' in col.lower() and 'week' not in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except:
                        pass
            
            self.raw_data_cache[table_name] = df
        
        return df
    
    def apply_filters(self, df: pd.DataFrame, kpi_def: pd.Series, 
                     country: str = None, week: str = None) -> pd.DataFrame:
        """
        Apply all filters defined in KPI definition.
        
        Args:
            df: DataFrame to filter
            kpi_def: KPI definition row from catalogue
            country: Selected country (for dynamic filters)
            week: Selected week (for dynamic filters)
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        # Apply up to 5 filters
        for i in range(1, 6):
            filter_field = kpi_def.get(f'filter_{i}_field', '')
            filter_operator = kpi_def.get(f'filter_{i}_operator', '')
            filter_value_type = kpi_def.get(f'filter_{i}_value_type', '')
            filter_value = kpi_def.get(f'filter_{i}_value', '')
            
            if not filter_field or filter_field == '':
                continue
            
            if filter_field not in filtered_df.columns:
                print(f"⚠️  Warning: Filter field '{filter_field}' not found in data")
                continue
            
            # Resolve dynamic values
            if filter_value_type == 'dynamic':
                if filter_value == 'selected_country' and country:
                    # Convert country code to data value (e.g., 'FR🇫🇷' -> 'France')
                    filter_value = get_country_data_value(country)
                elif filter_value == 'selected_week' and week:
                    filter_value = week
                else:
                    continue  # Skip if dynamic value not provided
            
            # Skip if filter value is empty or invalid
            if filter_value is None or filter_value == '':
                continue
            
            # Apply filter based on operator
            try:
                if filter_operator == 'equal':
                    # Filter out NaN, then compare as strings (handles 1 vs '1')
                    filtered_df = filtered_df[filtered_df[filter_field].notna() & (filtered_df[filter_field].astype(str) == str(filter_value))]
                elif filter_operator == 'not_equal':
                    # Filter out NaN, then compare as strings
                    filtered_df = filtered_df[filtered_df[filter_field].notna() & (filtered_df[filter_field].astype(str) != str(filter_value))]
                elif filter_operator == 'greater_than':
                    # Convert to numeric, dropping non-numeric values
                    numeric_col = pd.to_numeric(filtered_df[filter_field], errors='coerce')
                    filtered_df = filtered_df[numeric_col > float(filter_value)]
                elif filter_operator == 'less_than':
                    # Convert to numeric, dropping non-numeric values
                    numeric_col = pd.to_numeric(filtered_df[filter_field], errors='coerce')
                    filtered_df = filtered_df[numeric_col < float(filter_value)]
                elif filter_operator == 'contains':
                    filtered_df = filtered_df[filtered_df[filter_field].astype(str).str.contains(str(filter_value), na=False)]
            except Exception as e:
                print(f"⚠️  Warning: Could not apply filter {filter_field} {filter_operator} {filter_value}: {str(e)}")
                continue
        
        return filtered_df
    
    def calculate_kpi(self, kpi_id: str, country: str = None, 
                     week: str = None) -> Dict[str, Any]:
        """
        Calculate a specific KPI value.
        
        Args:
            kpi_id: KPI identifier
            country: Country filter value
            week: Week filter value
            
        Returns:
            Dictionary with KPI value and metadata
        """
        # Find KPI definition
        kpi_def = self.catalogue[self.catalogue['kpi_id'] == kpi_id]
        if len(kpi_def) == 0:
            return {'error': f'KPI {kpi_id} not found in catalogue'}
        
        kpi_def = kpi_def.iloc[0]
        
        # Handle ratio KPIs (calculated from other KPIs)
        if kpi_def['aggregation_type'] == 'RATIO':
            return self._calculate_ratio_kpi(kpi_def, country, week)
        
        # Get source data
        source_table = kpi_def['source_table']
        raw_data = self.get_raw_data(source_table)
        
        if raw_data is None:
            return {'error': f'Could not load data from {source_table}'}
        
        # Apply filters
        filtered_data = self.apply_filters(raw_data, kpi_def, country, week)
        
        # Calculate based on aggregation type
        aggregation_type = kpi_def['aggregation_type']
        measure_field = kpi_def.get('measure_field', '')
        
        if aggregation_type == 'COUNT':
            value = len(filtered_data)
        elif aggregation_type == 'SUM' and measure_field:
            # Convert to numeric to handle string data
            numeric_values = pd.to_numeric(filtered_data[measure_field], errors='coerce')
            value = numeric_values.sum()
        elif aggregation_type == 'AVERAGE' and measure_field:
            # Convert to numeric to handle string data
            numeric_values = pd.to_numeric(filtered_data[measure_field], errors='coerce')
            value = numeric_values.mean()
        elif aggregation_type == 'MIN' and measure_field:
            # Convert to numeric to handle string data
            numeric_values = pd.to_numeric(filtered_data[measure_field], errors='coerce')
            value = numeric_values.min()
        elif aggregation_type == 'MAX' and measure_field:
            # Convert to numeric to handle string data
            numeric_values = pd.to_numeric(filtered_data[measure_field], errors='coerce')
            value = numeric_values.max()
        else:
            value = None
        
        return {
            'kpi_id': kpi_id,
            'kpi_name': kpi_def['kpi_name'],
            'value': value,
            'aggregation_type': aggregation_type,
            'source_table': source_table,
            'record_count': len(filtered_data),
            'filters_applied': {
                'country': country,
                'week': week
            }
        }
    
    def _calculate_ratio_kpi(self, kpi_def: pd.Series, country: str = None, 
                            week: str = None) -> Dict[str, Any]:
        """
        Calculate KPIs that are ratios of other KPIs.
        
        Args:
            kpi_def: KPI definition
            country: Country filter
            week: Week filter
            
        Returns:
            Calculated ratio with numerator and denominator tracking
        """
        measure_field = kpi_def.get('measure_field', '')
        
        # Parse formula (e.g., "performed_interventions / planned_interventions")
        match = re.match(r'(\w+)\s*/\s*(\w+)', measure_field)
        
        if not match:
            return {'error': 'Invalid ratio formula'}
        
        numerator_kpi = match.group(1)
        denominator_kpi = match.group(2)
        
        # Calculate both KPIs
        num_result = self.calculate_kpi(numerator_kpi, country, week)
        denom_result = self.calculate_kpi(denominator_kpi, country, week)
        
        if 'error' in num_result or 'error' in denom_result:
            return {'error': 'Could not calculate component KPIs'}
        
        num_value = num_result.get('value', 0)
        denom_value = denom_result.get('value', 1)
        
        # Calculate ratio
        if denom_value == 0 or denom_value is None:
            ratio_value = 0
        else:
            ratio_value = (num_value / denom_value) * 100  # As percentage
        
        return {
            'kpi_id': kpi_def['kpi_id'],
            'kpi_name': kpi_def['kpi_name'],
            'value': ratio_value,
            'aggregation_type': 'RATIO',
            'numerator': {
                'kpi': numerator_kpi,
                'value': num_value,
                'name': num_result.get('kpi_name', '')
            },
            'denominator': {
                'kpi': denominator_kpi,
                'value': denom_value,
                'name': denom_result.get('kpi_name', '')
            },
            'filters_applied': {
                'country': country,
                'week': week
            }
        }
    
    def get_root_cause_breakdown(self, kpi_id: str, country: str = None, 
                                 week: str = None) -> Dict[str, Any]:
        """
        Get breakdown by root cause dimensions.
        
        Args:
            kpi_id: KPI identifier
            country: Country filter
            week: Week filter
            
        Returns:
            Breakdown by each root cause dimension
        """
        # Find KPI definition
        kpi_def = self.catalogue[self.catalogue['kpi_id'] == kpi_id]
        if len(kpi_def) == 0:
            return {'error': f'KPI {kpi_id} not found'}
        
        kpi_def = kpi_def.iloc[0]
        
        # Get source data
        source_table = kpi_def['source_table']
        raw_data = self.get_raw_data(source_table)
        
        if raw_data is None:
            return {'error': f'Could not load data from {source_table}'}
        
        # Apply filters
        filtered_data = self.apply_filters(raw_data, kpi_def, country, week)
        
        # Get root cause dimensions
        breakdowns = {}
        for i in range(1, 6):
            dim_field = kpi_def.get(f'root_cause_dim_{i}', '')
            if dim_field and dim_field != '' and dim_field in filtered_data.columns:
                breakdown = filtered_data[dim_field].value_counts().to_dict()
                breakdowns[dim_field] = breakdown
        
        return {
            'kpi_id': kpi_id,
            'kpi_name': kpi_def['kpi_name'],
            'breakdowns': breakdowns,
            'total_records': len(filtered_data)
        }

    def get_filtered_kpi_data(self, kpi_id: str, country: str = None, 
                             week: str = None) -> pd.DataFrame:
        """
        Get the filtered raw data for a specific KPI.
        
        Args:
            kpi_id: KPI identifier
            country: Country filter value
            week: Week filter value
            
        Returns:
            DataFrame with filtered raw data
        """
        # Find KPI definition
        kpi_def = self.catalogue[self.catalogue['kpi_id'] == kpi_id]
        if len(kpi_def) == 0:
            return pd.DataFrame() # Return empty DF if not found
        
        kpi_def = kpi_def.iloc[0]
        
        # Handle ratio KPIs - use numerator as primary source for now
        if kpi_def['aggregation_type'] == 'RATIO':
            measure_field = kpi_def.get('measure_field', '')
            match = re.match(r'(\w+)\s*/\s*(\w+)', measure_field)
            if match:
                kpi_id = match.group(1) # Switch to numerator KPI
                # Recurse to get that KPI's definition
                return self.get_filtered_kpi_data(kpi_id, country, week)
            else:
                return pd.DataFrame()
        
        # Get source data
        source_table = kpi_def['source_table']
        raw_data = self.get_raw_data(source_table)
        
        if raw_data is None:
            return pd.DataFrame()
        
        # Apply filters
        # Note: We want to show the data relevant to the selected week/country
        # so we apply the same filters as the KPI calculation
        filtered_data = self.apply_filters(raw_data, kpi_def, country, week)
        
        return filtered_data
    
    def calculate_all_kpis(self, country: str, week: str) -> List[Dict[str, Any]]:
        """
        Calculate all KPIs for given country and week.
        
        Args:
            country: Country filter
            week: Week filter
            
        Returns:
            List of calculated KPI results
        """
        results = []
        for _, kpi_def in self.catalogue.iterrows():
            kpi_id = kpi_def['kpi_id']
            result = self.calculate_kpi(kpi_id, country, week)
            results.append(result)
        
        return results
    
    def get_available_countries(self) -> List[str]:
        """Get list of available countries from country sheets."""
        worksheets = self.client.list_worksheets()
        countries = []
        for ws in worksheets:
            if ws.startswith('Weekly Template-'):
                # Extract country code
                country = ws.replace('Weekly Template-', '').strip()
                countries.append(country)
        return sorted(countries)
    
    def get_available_weeks(self, source_table: str = 'MNT Stages RAW') -> List[str]:
        """
        Get list of available weeks from raw data.
        
        Args:
            source_table: Table to check for weeks
            
        Returns:
            List of unique weeks
        """
        raw_data = self.get_raw_data(source_table)
        if raw_data is None:
            return []
        
        # Look for week columns
        week_cols = [col for col in raw_data.columns if 'week' in col.lower()]
        if len(week_cols) > 0:
            weeks = raw_data[week_cols[0]].dropna().unique().tolist()
            return sorted(weeks)
        
        return []
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees).
        """
        try:
            lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        except (ValueError, TypeError):
            return None

        # Convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a)) 
        r = 6371 # Radius of earth in kilometers.
        return c * r

    def analyze_cancellations(self, kpi_id: str, country: str, week: str) -> pd.DataFrame:
        """
        Analyze cancelled interventions to find context (previous job, distance, time).
        """
        # Get raw data (assuming MNT Stages RAW contains the necessary info)
        # In a real scenario, we might need a specific table mapping
        df = self.get_filtered_kpi_data(kpi_id, country, week)
        
        if df is None or df.empty:
            return pd.DataFrame()

        # Check required columns
        required_cols = ['Latitude', 'Longitude', 'Intervention Start Date', 'Intervention Done Date']
        # flexible check for Technician Name
        tech_col = next((c for c in df.columns if 'technician' in c.lower() and 'name' in c.lower()), None)
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)

        if not tech_col or not status_col:
            print(f"⚠️ Missing columns for analysis. Tech: {tech_col}, Status: {status_col}")
            return pd.DataFrame()
            
        # Ensure date columns are datetime
        for col in ['Intervention Start Date', 'Intervention Done Date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Sort by Technician and Start Date
        df = df.sort_values(by=[tech_col, 'Intervention Start Date'])
        
        analysis_results = []
        
        # Group by technician to analyze sequence
        for technician, group in df.groupby(tech_col):
            group = group.sort_values('Intervention Start Date')
            
            # Find cancelled jobs
            # Assuming 'Cancelled' string in status, case insensitive
            is_cancelled = group[status_col].astype(str).str.contains('anul', case=False, na=False) | \
                           group[status_col].astype(str).str.contains('ancel', case=False, na=False)
            
            cancelled_indices = group[is_cancelled].index
            
            for idx in cancelled_indices:
                curr_job = group.loc[idx]
                
                # Find previous job (strictly before this one)
                # We look at the group up to this index
                prev_jobs = group[group['Intervention Start Date'] < curr_job['Intervention Start Date']]
                
                if not prev_jobs.empty:
                    prev_job = prev_jobs.iloc[-1] # The immediate previous one
                    
                    # Calculate metrics
                    dist = self._haversine_distance(
                        prev_job.get('Latitude'), prev_job.get('Longitude'),
                        curr_job.get('Latitude'), curr_job.get('Longitude')
                    )
                    
                    # Time gap: Start of Current - Done of Previous
                    gap_minutes = None
                    if pd.notna(curr_job['Intervention Start Date']) and pd.notna(prev_job['Intervention Done Date']):
                        delta = curr_job['Intervention Start Date'] - prev_job['Intervention Done Date']
                        gap_minutes = delta.total_seconds() / 60
                    
                    analysis_results.append({
                        'Technician': technician,
                        'Cancelled Job Start': curr_job['Intervention Start Date'],
                        'Prev Job Done': prev_job['Intervention Done Date'],
                        'Gap (min)': round(gap_minutes, 1) if gap_minutes is not None else None,
                        'Distance (km)': round(dist, 1) if dist is not None else None,
                        'Prev Job Status': prev_job[status_col]
                    })

        return pd.DataFrame(analysis_results)
