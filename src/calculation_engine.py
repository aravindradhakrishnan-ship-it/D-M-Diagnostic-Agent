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


import streamlit as st

class KPICalculationEngine:
    # ... (existing code)

    def analyze_cancellations(self, kpi_id: str, country: str, week: str, client: str = None) -> pd.DataFrame:
        """
        Analyze cancelled interventions to find context (previous job, distance, time).
        Uses wider dataset (skipping status filter) to find the actual previous performed job.
        """
        st.write(f"🔍 DEBUG: Analyzing KPI: {kpi_id}, Country: {country}, Week: {week}")

        # 1. Get KPI Definition
        kpi_defs = self.catalogue[self.catalogue['kpi_id'] == kpi_id]
        if kpi_defs.empty:
            st.error(f"❌ DEBUG: KPI Definition not found for ID: {kpi_id}")
            return pd.DataFrame()
        kpi_def = kpi_defs.iloc[0]

        # 2. Get Raw Data
        source_table = kpi_def['source_table']
        st.write(f"🔍 DEBUG: Loading raw data from table: {source_table}")
        
        raw_data = self.get_raw_data(source_table)
        if raw_data is None or raw_data.empty:
            st.error(f"❌ DEBUG: Raw data is None or Empty for table: {source_table}")
            return pd.DataFrame()
        
        st.write(f"✅ DEBUG: Raw Data Loaded. Shape: {raw_data.shape}")

        # 3. Apply Filters EXCEPT strict status (to see Done + Cancelled)
        # We skip filters that look like they select for 'cancelled' status
        df = self.apply_filters(
            raw_data, 
            kpi_def, 
            country, 
            week,
            client, 
            exclude_values=['cancelled', 'anulled', 'canceled']
        )
        
        st.write(f"✅ DEBUG: Data Shape after filtering: {df.shape}")
        
        if df.empty:
            st.warning("⚠️ DEBUG: Filtered DataFrame is empty!")
            return pd.DataFrame()

        # Check required columns
        required_cols = ['Latitude', 'Longitude', 'Intervention Start Date', 'Intervention Done Date']
        # Technician column: use only the explicit header we expect
        tech_col = next((c for c in df.columns if c.strip().lower() == 'chosen team / technician'), None)
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        planned_col = next((c for c in df.columns if 'planned' in c.lower()), None)
        
        st.write(f"🔍 DEBUG: Columns Found - Tech: {tech_col}, Status: {status_col}, Planned: {planned_col}")
        st.write(f"DEBUG: All Columns: {df.columns.tolist()}") # verbose
    
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
                     country: str = None, week: str = None, client: str = None,
                     exclude_values: List[str] = None) -> pd.DataFrame:
        """
        Apply all filters defined in KPI definition.
        
        Args:
            df: DataFrame to filter
            kpi_def: KPI definition row from catalogue
            country: Selected country (for dynamic filters)
            week: Selected week (for dynamic filters)
            exclude_values: List of filter values to skip (e.g. ['cancelled'])
            
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

            # Check for exclusions
            if exclude_values:
                should_skip = False
                str_val = str(filter_value).lower()
                for excl in exclude_values:
                    if excl.lower() in str_val:
                        should_skip = True
                        break
                if should_skip:
                    continue
            
            # Resolve dynamic values
            if filter_value_type == 'dynamic':
                if filter_value == 'selected_country' and country:
                    # Convert country code to data value (e.g., 'FR🇫🇷' -> 'France')
                    filter_value = get_country_data_value(country)
                elif filter_value == 'selected_week' and week:
                    filter_value = week
                elif filter_value == 'selected_client' and client:
                    filter_value = client
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
                     week: str = None, client: str = None) -> Dict[str, Any]:
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
            return self._calculate_ratio_kpi(kpi_def, country, week, client)
        
        # Get source data
        source_table = kpi_def['source_table']
        raw_data = self.get_raw_data(source_table)
        
        if raw_data is None:
            return {'error': f'Could not load data from {source_table}'}
        
        # Apply filters
        filtered_data = self.apply_filters(raw_data, kpi_def, country, week, client)
        if client and 'Client' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Client'] == client]
        
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
                            week: str = None, client: str = None) -> Dict[str, Any]:
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
        num_result = self.calculate_kpi(numerator_kpi, country, week, client)
        denom_result = self.calculate_kpi(denominator_kpi, country, week, client)
        
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
                             week: str = None, client: str = None) -> pd.DataFrame:
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
                return self.get_filtered_kpi_data(kpi_id, country, week, client)
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
        filtered_data = self.apply_filters(raw_data, kpi_def, country, week, client)
        if client and 'Client' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['Client'] == client]
        
        return filtered_data
    
    def calculate_all_kpis(self, country: str, week: str, client: str = None) -> List[Dict[str, Any]]:
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
            result = self.calculate_kpi(kpi_id, country, week, client)
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

    def analyze_cancellations(self, kpi_id: str, country: str, week: str, client: str = None) -> pd.DataFrame:
        """
        Analyze cancelled interventions to find context (previous job, distance, time).
        Uses wider dataset (skipping status filter) to find the actual previous performed job.
        """
        print(f"DEBUG: analyze_cancellations called for KPI: {kpi_id}, Country: {country}, Week: {week}, Client: {client}")

        # 1. Get KPI Definition
        kpi_defs = self.catalogue[self.catalogue['kpi_id'] == kpi_id]
        if kpi_defs.empty:
            print(f"DEBUG: KPI Definition not found for ID: {kpi_id}")
            return pd.DataFrame()
        kpi_def = kpi_defs.iloc[0]

        # 2. Get Raw Data
        source_table = kpi_def['source_table']
        print(f"DEBUG: Loading raw data from table: {source_table}")
        
        raw_data = self.get_raw_data(source_table)
        if raw_data is None or raw_data.empty:
            print(f"DEBUG: Raw data is None or Empty for table: {source_table}")
            return pd.DataFrame()
        
        print(f"DEBUG: Raw Data Loaded. Shape: {raw_data.shape}")

        # 3. Apply Filters EXCEPT strict status (to see Done + Cancelled)
        # We skip filters that look like they select for 'cancelled' status
        df = self.apply_filters(
            raw_data, 
            kpi_def, 
            country, 
            week,
            client, 
            exclude_values=['cancelled', 'anulled', 'canceled']
        )
        
        print(f"DEBUG: Data Shape after filtering (excluding 'cancelled'): {df.shape}")
        
        if df.empty:
            print("DEBUG: Filtered DataFrame is empty!")
            return pd.DataFrame()

        # Check required columns
        required_cols = ['Latitude', 'Longitude', 'Intervention Start Date', 'Intervention Done Date']
        # Technician column: use only the explicit header we expect
        tech_col = next((c for c in df.columns if c.strip().lower() == 'chosen team / technician'), None)
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        planned_col = next((c for c in df.columns if 'planned' in c.lower()), None)
        
        print(f"DEBUG: Analysis Columns Found - Tech: {tech_col}, Status: {status_col}, Planned: {planned_col}")
        print(f"DEBUG: All Columns: {df.columns.tolist()}")

        if not tech_col or not status_col:
            print(f"⚠️ Missing columns for analysis. Tech: {tech_col}, Status: {status_col}")
            return pd.DataFrame()
            
        print(f"DEBUG: Data Shape after filtering: {df.shape}")
        if not df.empty and status_col:
             print(f"DEBUG: Unique Statuses: {df[status_col].unique()}")
            
        # Ensure date columns are datetime
        for col in ['Intervention Start Date', 'Intervention Done Date', planned_col if planned_col else None]:
            if col and col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Use planned date/time if available to determine order
        time_order_col = planned_col if planned_col else 'Intervention Start Date'
        df = df.sort_values(by=[tech_col, time_order_col])
        
        # Precompute cancel mask for the whole frame
        cancel_mask = df[status_col].astype(str).str.lower().str.contains('cancel') | df[status_col].astype(str).str.lower().str.contains('anul')
        df['Intervention Date'] = df[time_order_col].dt.date
        
        analysis_results = []
        
        # Group by technician
        for technician, tech_group in df.groupby(tech_col):
            tech_group = tech_group.sort_values(by=time_order_col)
            tech_cancel_mask = cancel_mask.loc[tech_group.index]
            
            # For each day with cancellations, find first cancelled and last non-cancelled BEFORE that cancelled (using positional order)
            cancel_days = tech_group.loc[tech_cancel_mask, 'Intervention Date'].dropna().unique()
            for day in cancel_days:
                day_rows = tech_group[tech_group['Intervention Date'] == day]
                day_cancel_mask = tech_cancel_mask.loc[day_rows.index]
                day_cancelled = day_rows[day_cancel_mask].sort_values(by=time_order_col)
                if day_cancelled.empty:
                    continue
                
                # Position of first cancelled within technician-ordered rows
                first_cancel_pos = tech_group.index.get_loc(day_cancelled.index[0])
                first_cancel = day_cancelled.iloc[0]
                
                prior_rows = tech_group.iloc[:first_cancel_pos]
                prior_done_mask = ~tech_cancel_mask.loc[prior_rows.index]
                prior_done = prior_rows[prior_done_mask].dropna(subset=['Intervention Done Date'])
                last_done = prior_done.iloc[-1] if not prior_done.empty else None
                
                dist = None
                prev_done_date = None
                prev_done_time = None
                if last_done is not None:
                    dist = self._haversine_distance(
                        last_done.get('Latitude'), last_done.get('Longitude'),
                        first_cancel.get('Latitude'), first_cancel.get('Longitude')
                    )
                    done_dt = last_done.get('Intervention Done Date')
                    if pd.notna(done_dt):
                        prev_done_date = done_dt.date()
                        prev_done_time = done_dt.time()
                
                analysis_results.append({
                    'Technician': technician,
                    'Intervention date': first_cancel[time_order_col].date() if pd.notna(first_cancel[time_order_col]) else None,
                    'Number of cancelled jobs': day_cancelled.shape[0],
                    'Prev Job Done Date': prev_done_date,
                    'Prev Job Done Time': prev_done_time,
                    'Distance (km)': round(dist, 1) if dist is not None else None
                })

        return pd.DataFrame(analysis_results)
