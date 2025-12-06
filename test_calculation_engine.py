"""
Test script for the KPI Calculation Engine
"""
import sys
sys.path.insert(0, 'src')

from google_sheets_client import GoogleSheetsClient
from calculation_engine import KPICalculationEngine

def test_calculation_engine():
    print("=" * 60)
    print("  KPI Calculation Engine Test")
    print("=" * 60)
    print()
    
    # Initialize
    print("🔧 Initializing engine...")
    client = GoogleSheetsClient()
    engine = KPICalculationEngine(client)
    
    print()
    print("📊 Available Countries:")
    countries = engine.get_available_countries()
    for country in countries:
        print(f"  - {country}")
    
    # Test with first country
    if len(countries) > 0:
        test_country = 'FR🇫🇷'  # France
        print(f"\n🧪 Testing calculations for: {test_country}")
        print()
        
        # Calculate a specific KPI
        print("📈 Calculating 'planned_interventions'...")
        result = engine.calculate_kpi('planned_interventions', country=test_country)
        
        print(f"\nResults:")
        print(f"  KPI: {result.get('kpi_name')}")
        print(f"  Value: {result.get('value')}")
        print(f"  Source: {result.get('source_table')}")
        print(f"  Records: {result.get('record_count')}")
        
        # Get root cause breakdown
        print(f"\n🔍 Root Cause Breakdown:")
        breakdown = engine.get_root_cause_breakdown('planned_interventions', country=test_country)
        
        if 'breakdowns' in breakdown:
            for dim_name, values in breakdown['breakdowns'].items():
                print(f"\n  {dim_name}:")
                for key, count in list(values.items())[:5]:  # Show top 5
                    print(f"    {key}: {count}")
        
        # Test ratio KPI
        print(f"\n📊 Calculating ratio KPI 'performed_interventions_pct'...")
        ratio_result = engine.calculate_kpi('performed_interventions_pct', country=test_country)
        
        if 'numerator' in ratio_result:
            print(f"\nRatio Calculation:")
            print(f"  Numerator ({ratio_result['numerator']['kpi']}): {ratio_result['numerator']['value']}")
            print(f"  Denominator ({ratio_result['denominator']['kpi']}): {ratio_result['denominator']['value']}")
            print(f"  Result: {ratio_result['value']:.1f}%")
    
    print()
    print("=" * 60)
    print("✅ Calculation Engine Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_calculation_engine()
