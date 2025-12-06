# Google OAuth Setup Guide

## Prerequisites
- A Google Cloud Account
- Access to the [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create a Project
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click the project dropdown at the top of the page.
3.  Click **New Project**.
4.  Enter a project name (e.g., "Bloq Diagnostic Dashboard") and click **Create**.
5.  Select the newly created project.

## Step 2: Configure OAuth Consent Screen
*This step is required before creating credentials.*
1.  In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
2.  **User Type**:
    -   Select **Internal** if you have a Google Workspace organization and only want users from your org to login.
    -   Select **External** if you don't have an org or want to allow any Google account (requires app verification for public use, but works for testing).
3.  Click **Create**.
4.  **App Information**:
    -   **App name**: Bloq Dashboard
    -   **User support email**: Select your email.
5.  **Developer Contact Information**: Enter your email.
6.  Click **Save and Continue** until you finish the wizard (Scopes can be left default for now).
7.  *If External*: Go to the **Test users** step and add the email addresses you want to allow for testing (e.g., `admin@bloq.it`).

## Step 3: Create OAuth Credentials
1.  In the left sidebar, click **Credentials**.
2.  Click **+ CREATE CREDENTIALS** at the top.
3.  Select **OAuth client ID**.
4.  **Application type**: Select **Web application**.
5.  **Name**: Enter "Streamlit Dashboard".
6.  **Authorized redirect URIs**:
    -   Click **+ ADD URI**.
    -   Enter: `http://localhost:8501`
    *(Note: If you deploy to a server later, add that URL here too, e.g., `https://dashboard.bloq.it`)*
7.  Click **Create**.

## Step 4: Get Your Keys
1.  A popup will appear with your **Client ID** and **Client Secret**.
2.  **Copy these values**.
3.  Open your local file `.streamlit/secrets.toml`.
4.  Paste them into the `[google_auth]` section:

```toml
[google_auth]
mock_mode = false
client_id = "YOUR_COPIED_CLIENT_ID"
client_secret = "YOUR_COPIED_CLIENT_SECRET"
redirect_uri = "http://localhost:8501"
```

## Step 5: Test
1.  Restart your Streamlit server:
    ```bash
    pkill -f streamlit
    streamlit run src/dashboard.py
    ```
2.  The "Sign in with Google" button should now redirect you to the real Google login page.
