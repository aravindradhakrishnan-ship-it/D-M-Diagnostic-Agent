# 🔐 Google Sheets API Setup Guide

This guide will walk you through setting up Google Sheets API access for the KPI Diagnostic Engine.

**Time Required**: ~10-15 minutes  
**Prerequisites**: Google account with access to Google Cloud Console

---

## Step 1: Create a Google Cloud Project

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project**:
   - Click the project dropdown at the top (next to "Google Cloud")
   - Click **"NEW PROJECT"**
   - Enter project name: `KPI-Diagnostic-Engine` (or your preferred name)
   - Click **"CREATE"**
   - Wait for the project to be created (~30 seconds)

3. **Select Your Project**:
   - Click the project dropdown again
   - Select your newly created project

---

## Step 2: Enable Google Sheets API

1. **Open API Library**:
   - In the left sidebar, click **"APIs & Services"** → **"Library"**
   - Or visit: https://console.cloud.google.com/apis/library

2. **Search for Google Sheets API**:
   - In the search bar, type: `Google Sheets API`
   - Click on **"Google Sheets API"** from the results

3. **Enable the API**:
   - Click the blue **"ENABLE"** button
   - Wait for it to be enabled (~5 seconds)

---

## Step 3: Create Service Account Credentials

1. **Go to Credentials**:
   - In the left sidebar, click **"APIs & Services"** → **"Credentials"**
   - Or visit: https://console.cloud.google.com/apis/credentials

2. **Create Service Account**:
   - Click **"+ CREATE CREDENTIALS"** at the top
   - Select **"Service Account"**

3. **Service Account Details**:
   - **Service account name**: `kpi-diagnostic-agent`
   - **Service account ID**: (auto-filled, keep as is)
   - **Description**: `Service account for KPI diagnostic dashboard`
   - Click **"CREATE AND CONTINUE"**

4. **Grant Permissions (Optional)**:
   - Skip this step - Click **"CONTINUE"** (no role needed for Sheets access)

5. **Grant Users Access (Optional)**:
   - Skip this step - Click **"DONE"**

---

## Step 4: Create and Download JSON Key

1. **Find Your Service Account**:
   - You should now see your service account in the credentials list
   - Click on the service account email (it looks like: `kpi-diagnostic-agent@your-project.iam.gserviceaccount.com`)

2. **Create Key**:
   - Click the **"KEYS"** tab at the top
   - Click **"ADD KEY"** → **"Create new key"**

3. **Download JSON Key**:
   - Select **"JSON"** as the key type
   - Click **"CREATE"**
   - A JSON file will automatically download to your computer
   - **IMPORTANT**: Keep this file secure! It contains credentials.

4. **Save the Key File**:
   - Move the downloaded JSON file to your project directory
   - Recommended location: `/Users/aravindradhakrishnan/diagnostic-agent/credentials/`
   - Rename it to something simple: `service-account-key.json`

   ```bash
   # Create credentials directory (if not exists)
   mkdir -p /Users/aravindradhakrishnan/diagnostic-agent/credentials
   
   # Move the downloaded file (replace 'Downloads' path if different)
   mv ~/Downloads/kpi-diagnostic-engine-*.json /Users/aravindradhakrishnan/diagnostic-agent/credentials/service-account-key.json
   ```

---

## Step 5: Share Google Sheet with Service Account

**This is a critical step!** The service account needs permission to access your Google Sheet.

1. **Copy Service Account Email**:
   - From the Google Cloud Console credentials page, copy the service account email
   - It looks like: `kpi-diagnostic-agent@your-project.iam.gserviceaccount.com`

2. **Open Your Google Sheet**:
   - Go to your Google Sheet containing the KPI data
   - Click the **"Share"** button (top right)

3. **Share with Service Account**:
   - Paste the service account email in the "Add people and groups" field
   - Set permission to **"Viewer"** (or "Editor" if you want to write data later)
   - **UNCHECK** "Notify people" (the service account won't receive emails)
   - Click **"Share"**

4. **Get Your Sheet ID**:
   - Copy the Sheet ID from the URL
   - URL format: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
   - Example: If URL is `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9/edit`
   - Sheet ID is: `1a2b3c4d5e6f7g8h9`
   - Save this ID - you'll need it in the next step

---

## Step 6: Configure Environment Variables

1. **Edit the .env file**:
   - Open `/Users/aravindradhakrishnan/diagnostic-agent/.env`
   - Add the following configuration:

   ```bash
   # Google Sheets Configuration
   USE_MOCK_DATA=false
   GOOGLE_SHEET_ID=YOUR_SHEET_ID_HERE
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service-account-key.json
   KPI_CATALOGUE_SHEET_NAME=KPI Catalogue
   ```

2. **Replace with Your Values**:
   - `USE_MOCK_DATA`: Set to `false` to use real Google Sheets data
   - `GOOGLE_SHEET_ID`: Paste your actual Sheet ID from Step 5.4
   - `GOOGLE_SERVICE_ACCOUNT_FILE`: Path to your JSON key file (keep as-is)
   - `KPI_CATALOGUE_SHEET_NAME`: Name of the sheet tab with KPI definitions (adjust if different)

   > **Note**: The engine will automatically discover:
   > - All raw data tables (MNT Projects RAW, MNT Stages RAW, etc.)
   > - All country-specific sheets (Weekly Template-FR, Weekly Template-ES, etc.)
   > - You don't need to list them!

3. **Final .env file should look like**:
   ```bash
   # Google Sheets Configuration
   USE_MOCK_DATA=false
   GOOGLE_SHEET_ID=1a2b3c4d5e6f7g8h9
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service-account-key.json
   KPI_CATALOGUE_SHEET_NAME=KPI Catalogue
   ```

**That's it!** Just 4 simple settings.

---

## Step 7: Install Required Dependencies

Run this command in your terminal:

```bash
cd /Users/aravindradhakrishnan/diagnostic-agent
source venv/bin/activate
pip install gspread google-auth google-auth-oauthlib
```

---

## Step 8: Test the Connection

I'll create a test script to verify everything works. Run:

```bash
python test_google_sheets.py
```

If successful, you should see:
```
✅ Successfully connected to Google Sheets!
✅ Found sheet: KPI Catalogue
✅ Found sheet: KPIs
✅ Sample data loaded successfully
```

---

## 🎯 Quick Checklist

Before proceeding, ensure you have:

- [ ] Created Google Cloud project
- [ ] Enabled Google Sheets API
- [ ] Created service account
- [ ] Downloaded JSON key file to `credentials/` folder
- [ ] Shared Google Sheet with service account email
- [ ] Copied Sheet ID from URL
- [ ] Updated `.env` file with all values
- [ ] Installed required packages
- [ ] Added `credentials/` to `.gitignore` (security!)

---

## 🔒 Security Best Practices

1. **Never commit credentials to Git**:
   - Add to `.gitignore`:
     ```
     credentials/
     *.json
     .env
     ```

2. **Restrict service account permissions**:
   - Only share specific sheets, not entire Drive
   - Use "Viewer" permission unless write access needed

3. **Rotate credentials periodically**:
   - Delete old keys from Google Cloud Console
   - Create new keys every 6-12 months

---

## 🐛 Troubleshooting

### Error: "Permission denied"
- **Solution**: Make sure you shared the Sheet with the service account email

### Error: "Invalid credentials"
- **Solution**: Check that the JSON file path in `.env` is correct

### Error: "Sheet not found"
- **Solution**: Verify `KPI_CATALOGUE_SHEET_NAME` matches your actual tab name (case-sensitive!)

### Error: "API not enabled"
- **Solution**: Go back to Step 2 and enable Google Sheets API

---

## 📞 Next Steps

Once setup is complete, let me know and I'll:
1. Read your KPI Catalogue structure
2. Parse the KPI definitions
3. Build the calculation engine based on your formulas
4. Update the dashboard to show driver-based analysis

---

**Need Help?** If you encounter any issues during setup, share the error message and I'll help troubleshoot!
