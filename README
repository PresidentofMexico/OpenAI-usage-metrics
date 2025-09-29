 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index b689373f5f50ad9ded576e6675828fe14ea98f0c..df5b9efb689d2ba15d1a4dba6dd5a6f2011fd8b4 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,29 @@
 # OpenAI usage metrics
-Automatically pull and update user metrics
+
+A lightweight Streamlit application for exploring OpenAI Enterprise workspace exports. Upload the monthly CSV metrics provided in the Workspace Settings panel to generate dashboards that highlight adoption trends, top users, and day-to-day activity.
+
+## Getting started
+
+1. Create and activate a Python 3.10+ virtual environment.
+2. Install dependencies:
+   ```bash
+   pip install -r requirements.txt
+   ```
+3. Launch the Streamlit dashboard:
+   ```bash
+   streamlit run streamlit_app.py
+   ```
+
+The app stores uploaded data in the current Streamlit session. Upload the latest monthly export at the end of each month to refresh the dashboards. Use the **Clear loaded data** button in the sidebar to reset the dashboard.
+
+## Features
+
+- Automatic normalisation of CSV exports with flexible column-name matching.
+- Month-over-month summaries of requests, tokens, cost and active user counts.
+- User-level breakdowns with active day counts per selected month.
+- Trend analysis that highlights the largest increases or decreases in usage.
+- Daily/weekly/monthly time-series visualisations with optional rolling averages.
+
+## Customising column aliases
+
+If your export uses different headings, you can provide additional aliases by editing `usage_metrics/data_ingestion.py` and extending the `DEFAULT_COLUMN_ALIASES` mapping.
 
EOF
)
