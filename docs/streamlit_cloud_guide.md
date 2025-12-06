# Deploying to Streamlit Cloud

Streamlit Cloud is the easiest way to deploy your dashboard for free.

## Step 1: Create a GitHub Repository
1.  Go to [GitHub](https://github.com/new).
2.  Create a new repository (e.g., `diagnostic-dashboard`).
3.  Choose **Private** (Recommended) or Public.
4.  Do **not** initialize with README/gitignore (we already have them).

## Step 2: Push Your Code
Run these commands in your terminal to push your local code to your existing **D-M-Diagnostic-Agent** repository.
*Note: This will overwrite the main branch with the new dashboard code.*

```bash
git remote add origin https://github.com/aravindradhakrishnan-ship-it/D-M-Diagnostic-Agent.git
git branch -M main
git push -u origin main --force
```

## Step 3: Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Sign in with GitHub.
3.  Click **New app**.
4.  Select your repository (`diagnostic-dashboard`).
5.  Branch: `main`.
6.  Main file path: `src/dashboard.py`.
7.  Click **Deploy!**.

## Step 4: Add Secrets (Critical)
Your app will fail to start initially because it's missing the credentials (secrets.toml).
1.  On your app's dashboard in Streamlit Cloud, click names -> **Settings** -> **Secrets**.
2.  Copy the content of your local `.streamlit/secrets.toml` file.
3.  Paste it into the secrets text area.
4.  Click **Save**.

The app will reboot and should be live!
