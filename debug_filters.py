import sys
sys.path.insert(0, 'src')
from google_sheets_client import GoogleSheetsClient
from calculation_engine import KPICalculationEngine
from country_mapping import get_country_data_value
import pandas as pd

client = GoogleSheetsClient()
engine = KPICalculationEngine(client)

# Get the KPI def
kpi_def = engine.catalogue[engine.catalogue['kpi_id'] == 'planned_interventions'].iloc[0]

# Get raw data
raw_data = engine.get_raw_data('MNT Stages RAW')
print(f'Starting with: {len(raw_data)} rows\\n')

#  Apply filters using engine's apply_filters method
filtered = engine.apply_filters(raw_data, kpi_def, 'FR🇫🇷', '2025_W48')
print(f'After engine.apply_filters: {len(filtered)} rows\\n')

# Now do it manually to compare
manual = raw_data.copy()

# Filter 1: Country
country_value = get_country_data_value('FR🇫🇷')
print(f'Filter 1: Country == {country_value}')
manual = manual[manual['Country'].notna() & (manual['Country'].astype(str) == str(country_value))]
print(f'  Result: {len(manual)} rows')

# Filter 2: Planned Week  
print(f'Filter 2: Planned Week == 2025_W48')
manual = manual[manual['Planned Week'].notna() & (manual['Planned Week'].astype(str) == '2025_W48')]
print(f'  Result: {len(manual)} rows')

# Filter 3
print(f'Filter 3: Client Request Flag : Maintenance == 1')
manual = manual[manual['Client Request Flag : Maintenance'].notna() & (manual['Client Request Flag : Maintenance'].astype(str) == '1')]
print(f'  Result: {len(manual)} rows')

# Filter 4
print(f'Filter 4: Stage == Work order')
manual = manual[manual['Stage'].notna() & (manual['Stage'].astype(str) == 'Work order')]
print(f'  Result: {len(manual)} rows')
