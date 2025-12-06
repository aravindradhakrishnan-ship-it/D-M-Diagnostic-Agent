"""
Simple test script to verify Google Sheets connection.
Run this after completing the setup guide.
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google_sheets_client import test_connection

if __name__ == "__main__":
    print("=" * 60)
    print("  Google Sheets Connection Test")
    print("=" * 60)
    print()
    
    success = test_connection()
    
    print()
    print("=" * 60)
    if success:
        print("✅ SUCCESS! You're ready to use Google Sheets integration.")
        print()
        print("Next steps:")
        print("1. I'll read your KPI Catalogue to understand formulas")
        print("2. Build the calculation engine")
        print("3. Update the dashboard")
    else:
        print("❌ Test failed. Please review the error messages above.")
        print()
        print("Common issues:")
        print("- Check .env file has correct Sheet ID")
        print("- Verify credentials file path is correct")
        print("- Ensure sheet is shared with service account")
        print()
        print("See docs/google_sheets_setup.md for detailed help.")
    print("=" * 60)
