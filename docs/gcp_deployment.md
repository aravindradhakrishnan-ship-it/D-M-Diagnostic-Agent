# Deploying to Google Cloud Platform (Cloud Run)

Yes, you can absolutely deploy to Google Cloud! We recommend **Google Cloud Run** because:
1.  It runs containers (which we already have).
2.  It scales to zero (costs \$0 when no one uses it).
3.  It handles HTTPS automatically.

## Prerequisites
1.  **Google Cloud SDK** (`gcloud`) installed on your machine.
2.  Use the same **Project ID** where you created your OAuth Credentials.

## Step 1: Enable Services
Run these commands in your terminal to enable necessary Google Cloud APIs:
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

## Step 2: Build & Push the Docker Image
Replace `YOUR_PROJECT_ID` with your actual GCP Project ID.
```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build the container from the current directory
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/diagnostic-dashboard
```

## Step 3: Handle Secrets (Important!)
You should NOT bundle `.streamlit/secrets.toml` into the image for security. Instead, use **Secret Manager**.

1.  **Create a Secret**:
    Go to [Secret Manager](https://console.cloud.google.com/security/secret-manager) in the console.
    -   Name: `dashboard-secrets`
    -   Value: Copy/Paste the entire content of your local `.streamlit/secrets.toml`.
    -   Click **Create Secret**.

2.  **Grant Access**:
    The service account used by Cloud Run needs permission to access this secret.
    (You can often skip this if you are Owner, or the UI will prompt you during deployment).

## Step 4: Deploy to Cloud Run
You can do this via command line or the Console (simpler for first time).

### Option A: Using the Console (Recommended)
1.  Go to [**Cloud Run**](https://console.cloud.google.com/run).
2.  Click **Create Service**.
3.  **Container image URL**: Select `gcr.io/YOUR_PROJECT_ID/diagnostic-dashboard` (from Step 2).
4.  **Service name**: `diagnostic-dashboard`.
5.  **Region**: Choose one close to you (e.g., `europe-west1`).
6.  **Authentication**: Select **Allow unauthenticated invocations**.
    *Why?* The app handles its own login via Google Sign-In. We need the login page to be publicly reachable.
7.  **Container, Networking, Security > Volumes**:
    -   Click **Add Volume** > **Secret**.
    -   Secret: `dashboard-secrets`.
    -   Mount path: `.streamlit/secrets.toml` (Select "Mount as file" if asked, map it to file path `app/.streamlit/secrets.toml` or just `/app/.streamlit/secrets.toml`).
    *Note: The Dockerfile WORKDIR is `/app`. So the file should end up at `/app/.streamlit/secrets.toml`.*
    
    *Correction*: While mounting secrets as files is powerful, for Streamlit it can be slightly tricky to get the path right if you aren't careful.
    
    **Easier Alternative for Secrets**:
    Just paste the secret values as **Environment Variables** in the "Variables & Secrets" tab if you prefer, BUT Streamlit expects `secrets.toml`. 
    
    **Let's stick to the Volume Mount**:
    1.  Mount volume: `dashboard-secrets`
    2.  Mount path: `/app/.streamlit/secrets.toml`
    3.  **Subpath**: If you created the secret with the filename as the key, use it. If you pasted the content directly as the secret value version, map the volume to `/app/.streamlit` and name the file `secrets.toml`.

8.  Click **Create**.

### Option B: Command Line (Fast)
If you skip Secret Manager for now and just want to verify with Environment Variables (Requires app code change usually) OR just bake it in (NOT SECURE):

*For this tutorial, let's assume you follow the Console steps above for best results.*

## Step 5: Update OAuth Redirect URI
Once deployed, Cloud Run will give you a URL (e.g., `https://diagnostic-dashboard-xyz.a.run.app`).

1.  Go back to [**APIs & Services > Credentials**](https://console.cloud.google.com/apis/credentials).
2.  Edit your OAuth 2.0 Client.
3.  Add the new Cloud Run URL to **Authorized redirect URIs**:
    -   `https://diagnostic-dashboard-xyz.a.run.app`
4.  **Save**.

## Step 6: Update Secrets to Production Header
If you used Secret Manager, edit the secret version to update `redirect_uri` in the TOML content to match the new Cloud Run URL.

```toml
[google_auth]
...
redirect_uri = "https://diagnostic-dashboard-xyz.a.run.app"
```

## Deployment Complete!
You can now access the dashboard via the Cloud Run URL.
