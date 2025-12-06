# 🚀 Running the KPI Diagnostic Dashboard

## Quick Start

### 1. Start the Dashboard

```bash
cd /Users/aravindradhakrishnan/diagnostic-agent
source venv/bin/activate
streamlit run src/dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

### 2. Using the Dashboard

#### **Step 1: Select Country**
- Use the dropdown in the left sidebar
- Choose from: FR🇫🇷, ES🇪🇸, NL🇳🇱, DE🇩🇪, UK🇬🇧, PT🇵🇹, BEL🇧🇪, IT🇮🇹

#### **Step 2: View KPI Overview**
- See all 9 KPIs calculated in real-time
- Each row shows:
  - KPI name
  - Current value
  - "Analyze" button

#### **Step 3: Drill Down (Click "Analyze")**
- Click any "Analyze" button to see:
  - **KPI Value** - Current metric
  - **Source Table** - Where data comes from
  - **Record Count** - Number of records
  - **Root Cause Breakdown** - Charts showing drivers
  - **Detailed Tables** - Breakdowns by dimension

#### **Step 4: Explore Root Causes**
- View bar charts and pie charts
- See top contributors
- Understand "why behind the numbers"

---

## Features

### ✅ Real-Time Calculation
- No pre-calculated values
- Fresh data from Google Sheets
- Applies all filters dynamically

### ✅ Interactive Drill-Down
- Click any KPI to investigate
- Multiple visualization types
- Drill down by root cause dimensions

### ✅ Root Cause Analysis
- Automatic breakdown by:
  - Highest Priority
  - Reporting Categories
  - Maintenance Cluster
  - And more...

### ✅ Multi-Country Support
- Instant switching between countries
- Consistent calculations across regions

---

## Dashboard Structure

```
┌─────────────────────────────────────────┐
│  Sidebar                                │
│  ├─ Country Selector                    │
│  └─ Current Selection Info              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Main View                              │
│                                         │
│  When NO KPI selected:                  │
│  ├─ KPI Table                           │
│  │  ├─ KPI Name                         │
│  │  ├─ Value                            │
│  │  └─ [Analyze] button                 │
│                                         │
│  When KPI selected:                     │
│  ├─ Metrics Row                         │
│  │  ├─ KPI Value                        │
│  │  ├─ Aggregation Type                 │
│  │  ├─ Source Table                     │
│  │  └─ Record Count                     │
│  ├─ Ratio Details (if applicable)       │
│  ├─ Root Cause Charts                   │
│  │  ├─ Bar Chart (breakdown)            │
│  │  └─ Pie Chart (distribution)         │
│  ├─ Detailed Breakdown Tables           │
│  └─ [← Back] button                     │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

### Dashboard won't start
```bash
# Check if port is in use
lsof -i :8501

# Kill existing process if needed
kill -9 <PID>

# Restart dashboard
streamlit run src/dashboard.py
```

### No KPIs showing
- Check Google Sheets connection
- Verify country filters match data
- Ensure .env is configured correctly

### Charts not displaying
- Refresh the page
- Check browser console for errors
- Try a different browser

---

## Next Steps

### Phase 4: Enhancements (Optional)
- [ ] Week-over-week comparison
- [ ] Multi-week trends
- [ ] Export to PDF
- [ ] AI-powered insights
- [ ] Email alerts

---

**Ready to explore your KPIs!** 🎉
