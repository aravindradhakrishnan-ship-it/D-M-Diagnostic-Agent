"""
Google Sheets client for accessing KPI data.
Handles authentication and data retrieval from Google Sheets.
"""
import streamlit as st
from typing import Optional, List, Dict
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsClient:
    """Client for interacting with Google Sheets API."""
    
    def __init__(self, credentials_file: Optional[str] = None, sheet_id: Optional[str] = None):
        """
        Initialize Google Sheets client.
        
        Args:
            credentials_file: Path to service account JSON file
            sheet_id: Google Sheet ID
        """
        self.credentials_file = credentials_file or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        
        # Check env var first, then secrets
        self.sheet_id = sheet_id or os.getenv('GOOGLE_SHEET_ID')
        if not self.sheet_id and "GOOGLE_SHEET_ID" in st.secrets:
             self.sheet_id = st.secrets["GOOGLE_SHEET_ID"]
        
        # We will check for credentials availability in connect()
        # if not self.credentials_file:
        #     raise ValueError("Google service account file not specified. Set GOOGLE_SERVICE_ACCOUNT_FILE in .env")
        
        if not self.sheet_id:
            raise ValueError("Google Sheet ID not specified. Set GOOGLE_SHEET_ID in .env or secrets.toml")
        
        self._client = None
        self._spreadsheet = None
    
    def connect(self):
        """Establish connection to Google Sheets."""
        try:
            # Define the scope
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
            
            # Authenticate using service account
            if self.credentials_file and os.path.exists(self.credentials_file):
                 credentials = Credentials.from_service_account_file(
                    self.credentials_file,
                    scopes=scopes
                )
            elif "gcp_service_account" in st.secrets:
                # Use secrets from Streamlit Cloud
                service_account_info = st.secrets["gcp_service_account"]
                credentials = Credentials.from_service_account_info(
                    service_account_info,
                    scopes=scopes
                )
            else:
                 raise FileNotFoundError(f"Credentials file not found at {self.credentials_file} and 'gcp_service_account' not in secrets.")

            # Create client
            self._client = gspread.authorize(credentials)
            
            # Open spreadsheet
            self._spreadsheet = self._client.open_by_key(self.sheet_id)
            
            print(f"✅ Successfully connected to Google Sheet: {self._spreadsheet.title}")
            return True
            
        except FileNotFoundError:
            print(f"❌ Error: Credentials file not found at {self.credentials_file}")
            print("Please check the path in your .env file or add [gcp_service_account] to .streamlit/secrets.toml")
            return False
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {str(e)}")
            print("\nTroubleshooting tips:")
            print("1. Verify the service account JSON file exists")
            print("2. Check that Google Sheets API is enabled in Google Cloud Console")
            print("3. Ensure the Sheet ID is correct")
            print("4. Confirm the sheet is shared with the service account email")
            return False
    
    def get_worksheet(self, sheet_name: str):
        """
        Get a specific worksheet by name.
        
        Args:
            sheet_name: Name of the worksheet tab
            
        Returns:
            Worksheet object or None if not found
        """
        if not self._spreadsheet:
            if not self.connect():
                return None
        
        try:
            worksheet = self._spreadsheet.worksheet(sheet_name)
            print(f"✅ Found worksheet: {sheet_name}")
            return worksheet
        except gspread.WorksheetNotFound:
            print(f"❌ Worksheet '{sheet_name}' not found.")
            print(f"Available worksheets: {[ws.title for ws in self._spreadsheet.worksheets()]}")
            return None
    
    def read_sheet_to_dataframe(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Read a worksheet into a pandas DataFrame.
        
        Args:
            sheet_name: Name of the worksheet tab
            
        Returns:
            DataFrame with the sheet data
        """
        worksheet = self.get_worksheet(sheet_name)
        if not worksheet:
            return None
        
        try:
            # Get all values from the worksheet
            data = worksheet.get_all_values()
            
            if not data:
                print(f"⚠️  Worksheet '{sheet_name}' is empty")
                return None
            
            # First row is headers
            headers = data[0]
            rows = data[1:]
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=headers)
            
            print(f"✅ Loaded {len(df)} rows from '{sheet_name}'")
            return df
            
        except Exception as e:
            print(f"❌ Error reading worksheet '{sheet_name}': {str(e)}")
            return None
    
    def get_kpi_catalogue(self) -> Optional[pd.DataFrame]:
        """
        Read the KPI Catalogue sheet.
        
        Returns:
            DataFrame with KPI definitions
        """
        sheet_name = os.getenv('KPI_CATALOGUE_SHEET_NAME', 'KPI Catalogue')
        return self.read_sheet_to_dataframe(sheet_name)
    
    def get_kpi_data(self) -> Optional[pd.DataFrame]:
        """
        Read the main KPI data sheet.
        
        Returns:
            DataFrame with time-series KPI data
        """
        sheet_name = os.getenv('KPI_DATA_SHEET_NAME', 'KPIs')
        df = self.read_sheet_to_dataframe(sheet_name)
        
        if df is not None and 'Date' in df.columns:
            # Convert Date column to datetime
            try:
                df['Date'] = pd.to_datetime(df['Date'])
                print("✅ Converted 'Date' column to datetime")
            except Exception as e:
                print(f"⚠️  Could not convert Date column: {str(e)}")
        
        return df
    
    def get_user_permissions_map(self) -> Dict[str, List[str]]:
        """
        Read the 'User Permissions' sheet to get user access mapping.
        
        Returns:
            Dictionary mapping email to list of allowed countries.
            Example: {'admin@example.com': ['ALL'], 'user@example.com': ['France', 'Germany']}
        """
        sheet_name = os.getenv('PERMISSIONS_SHEET_NAME', 'User Permissions')
        df = self.read_sheet_to_dataframe(sheet_name)
        
        permissions = {}
        
        if df is None:
            # Debug: List available sheets
            all_sheets = [ws.title for ws in self._spreadsheet.worksheets()]
            print(f"DEBUG: Permissions sheet '{sheet_name}' returned None. Available sheets: {all_sheets}")
            return permissions
            
        print(f"DEBUG: Permissions sheet '{sheet_name}' read successfully. Shape: {df.shape}")
        if df.empty:
             print("DEBUG: DataFrame is empty!")
             
        # unexpected columns? try to find Email and Allowed Countries
        # Normalize columns: lower case and strip
        df.columns = [str(c).strip() for c in df.columns]
        
        # Check if required columns exist (case insensitive)
        email_col = next((c for c in df.columns if 'email' in c.lower()), None)
        countries_col = next((c for c in df.columns if 'country' in c.lower() or 'countries' in c.lower()), None)
        
        if not email_col or not countries_col:
            print(f"⚠️  Permissions sheet missing 'Email' or 'Allowed Countries' columns. Found: {df.columns.tolist()}")
            return permissions
            
        print(f"DEBUG: Reading permissions from columns: {email_col}, {countries_col}")
        
        for _, row in df.iterrows():
            email_raw = str(row[email_col])
            countries_raw = str(row[countries_col])
            
            # Normalize: lower case and strip
            email = email_raw.strip().lower()
            countries_str = countries_raw.strip()
            
            # print(f"DEBUG: Processing row - Email: '{email}', Countries: '{countries_str}'")
            
            if not email or not countries_str:
                continue
                
            if countries_str.upper() == 'ALL':
                permissions[email] = ['ALL']
            else:
                # Split by comma and strip
                countries = [c.strip() for c in countries_str.split(',') if c.strip()]
                permissions[email] = countries
                
        print(f"✅ Loaded permissions for users: {list(permissions.keys())}")
        return permissions

    def list_worksheets(self) -> List[str]:
        """
        List all available worksheets in the spreadsheet.
        
        Returns:
            List of worksheet names
        """
        if not self._spreadsheet:
            if not self.connect():
                return []
        
        return [ws.title for ws in self._spreadsheet.worksheets()]


def test_connection():
    """Test the Google Sheets connection."""
    print("🔍 Testing Google Sheets connection...\n")
    
    try:
        client = GoogleSheetsClient()
        
        if client.connect():
            print("\n📊 Available worksheets:")
            worksheets = client.list_worksheets()
            for ws in worksheets:
                print(f"  - {ws}")
            
            print("\n📖 Testing KPI Catalogue access:")
            catalogue = client.get_kpi_catalogue()
            if catalogue is not None:
                print(f"  Columns: {list(catalogue.columns)}")
                print(f"  Rows: {len(catalogue)}")
            
            print("\n📈 Testing KPI Data access:")
            kpi_data = client.get_kpi_data()
            if kpi_data is not None:
                print(f"  Columns: {list(kpi_data.columns)}")
                print(f"  Rows: {len(kpi_data)}")
            
            print("\n✅ All tests passed!")
            return True
        else:
            print("\n❌ Connection test failed")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        return False


if __name__ == "__main__":
    test_connection()
