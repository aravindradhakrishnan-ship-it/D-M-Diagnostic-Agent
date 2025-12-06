# 📊 KPI Diagnostic Agent Dashboard

A Streamlit-based dashboard for analyzing KPI changes and diagnosing root causes. This tool helps you understand **why** your metrics changed, not just that they changed.

## ✨ Features

- **59 KPIs Tracked**: Demo includes comprehensive mock data simulating real-world maintenance and operational metrics
- **Period Comparison**: Compare any two time periods to understand changes
- **Visual Analytics**: Interactive charts with trend analysis and moving averages
- **Correlation Detection**: Automatically find related KPIs that might explain changes
- **Root Cause Analysis**: AI-powered (optional) or rule-based diagnostic insights
- **Statistical Deep Dive**: Comprehensive metrics including mean, median, variance, and more

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation & Running

1. **Navigate to the project directory:**
   ```bash
   cd /Users/aravindradhakrishnan/diagnostic-agent
   ```

2. **Run the dashboard:**
   ```bash
   bash run.sh
   ```

   The script will automatically:
   - Create a virtual environment (if needed)
   - Install all dependencies
   - Launch the Streamlit dashboard

3. **Access the dashboard:**
   - Open your browser to `http://localhost:8501`
   - The dashboard should open automatically

## 📖 How to Use

### Basic Workflow

1. **Select a KPI** from the dropdown in the sidebar (e.g., "Performed Intervention")
2. **Choose Period 1 (Baseline)** - your reference period
3. **Choose Period 2 (Comparison)** - the period you want to analyze
4. **Click "Analyze"** to generate insights

### Understanding the Results

The dashboard provides multiple views:

- **Key Metrics**: Quick overview of averages, trends, and volatility
- **Time Series Chart**: Visual representation with period highlighting
- **Statistical Comparison**: Bar charts comparing key statistics
- **Diagnostic Insights**: 
  - Summary of changes
  - Variability analysis
  - Correlation findings
  - Root cause hypotheses

## ⚙️ Configuration

### Demo Mode (Default)

The dashboard runs in demo mode by default, using mock data. This is perfect for:
- Testing the system
- Understanding the interface
- Demonstrating capabilities

### Production Mode (Google Sheets)

To connect to your actual Google Sheets data:

1. **Set up Google Sheets API credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Sheets API
   - Create service account credentials
   - Download JSON key file

2. **Update `.env` file:**
   ```bash
   USE_MOCK_DATA=false
   GOOGLE_SHEET_ID=your_sheet_id_here
   GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
   SHEET_NAME=KPIs
   DATE_COLUMN=Date
   ```

3. **Install additional dependencies:**
   ```bash
   source venv/bin/activate
   pip install gspread oauth2client google-auth
   ```

### AI-Powered Analysis (Optional)

Enable advanced AI analysis by adding an API key:

1. **Get an API key** from:
   - [OpenAI](https://platform.openai.com/) (GPT-4)
   - [Anthropic](https://www.anthropic.com/) (Claude)
   - [Google AI](https://ai.google.dev/) (Gemini)

2. **Add to `.env` file:**
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Restart the dashboard** to use AI-powered insights

## 📁 Project Structure

```
diagnostic-agent/
├── venv/                  # Virtual environment
├── src/
│   ├── app.py            # Main Streamlit dashboard
│   ├── data_loader.py    # Data loading and mock data generation
│   ├── analyzer.py       # KPI analysis engine
│   └── utils.py          # Helper functions
├── .env                  # Environment configuration
├── .env.template         # Template for environment variables
├── requirements.txt      # Python dependencies
├── run.sh               # Startup script
└── README.md            # This file
```

## 🔧 Troubleshooting

### Dashboard won't start
```bash
# Ensure you're in the project directory
cd /Users/aravindradhakrishnan/diagnostic-agent

# Manually create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Streamlit directly
streamlit run src/app.py
```

### Port already in use
```bash
# Use a different port
streamlit run src/app.py --server.port 8502
```

### Import errors
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

## 🎯 Use Cases

This dashboard is perfect for:

- **Operations Teams**: Understanding equipment performance changes
- **Maintenance Managers**: Diagnosing why maintenance KPIs shifted
- **Data Analysts**: Quick root cause analysis of metric variations
- **Executives**: Getting insights into operational trends

## 🔮 Future Enhancements

Planned features:
- Multi-KPI comparison view
- Automated anomaly detection alerts
- Export reports to PDF
- Historical trend predictions
- Custom KPI formula builder

## 📝 License

MIT License - feel free to use and modify as needed.

## 🤝 Support

For issues or questions, contact your development team.

---

**Built with**: Streamlit, Plotly, Pandas, and ❤️
