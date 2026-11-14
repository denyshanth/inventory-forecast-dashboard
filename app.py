import streamlit as st
import pandas as pd
import numpy as np
import joblib
import re
import plotly.express as px
from datetime import date, timedelta
from pathlib import Path

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Inventory Forecast Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

SAFETY_STOCK_PERCENT = 0.10

STATUS_COLORS = {
    "Shortage": "#dc2626",
    "Balanced": "#16a34a",
    "Overstock": "#d97706",
    "Other": "#64748b",
}

# =========================================================
# 2. DESIGN SYSTEM
#    Ink navy + one blue accent. Red / green / amber are used
#    only to show inventory status, nowhere else.
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --ink: #0f172a;
    --text: #334155;
    --muted: #64748b;
    --line: #e2e8f0;
    --bg: #f6f8fb;
    --surface: #ffffff;
    --accent: #1d4ed8;
    --accent-soft: #eff4ff;
}

html, body, .stApp, [data-testid="stMarkdownContainer"], [data-testid="stMetric"],
button, input, label, textarea, table {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}

.stApp { background: var(--bg); }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--line);
}
.side-brand {
    font-size: 17px; font-weight: 700; color: var(--ink);
    padding-bottom: 14px; margin-bottom: 18px;
    border-bottom: 1px solid var(--line);
}
.side-brand span { display: block; font-size: 12px; font-weight: 400; color: var(--muted); margin-top: 3px; }
.side-label { font-size: 13px; font-weight: 600; color: var(--ink); margin: 4px 0 8px 0; }
.side-card {
    background: var(--accent-soft); border: 1px solid #dbe6ff;
    border-radius: 10px; padding: 12px 14px; margin: 12px 0 18px 0;
}
.side-card-title { font-size: 12px; color: var(--muted); }
.side-card-value { font-size: 15px; font-weight: 700; color: var(--ink); margin-top: 2px; }
.side-card-note { font-size: 12px; color: var(--muted); margin-top: 2px; line-height: 1.45; }

/* ---------- Page header ---------- */
.page-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    gap: 16px; flex-wrap: wrap;
    padding-bottom: 18px; margin-bottom: 8px;
    border-bottom: 1px solid var(--line);
}
.page-title { font-size: 28px; font-weight: 700; color: var(--ink); letter-spacing: -0.4px; }
.page-sub { font-size: 14px; color: var(--muted); margin-top: 4px; }
.period-chip {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 8px; padding: 8px 14px;
    font-size: 13px; font-weight: 600; color: var(--ink);
}
.period-chip span { color: var(--muted); font-weight: 500; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] {
    height: 46px; padding: 0 2px; background: transparent;
    font-size: 14px; font-weight: 600; color: var(--muted);
}
.stTabs [aria-selected="true"] { color: var(--ink); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ---------- Section headings ---------- */
.section-head { margin: 26px 0 14px 0; }
.section-title { font-size: 18px; font-weight: 700; color: var(--ink); }
.section-sub { font-size: 13px; color: var(--muted); margin-top: 3px; }

/* ---------- KPI cards ---------- */
.kpi {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 16px 18px; min-height: 108px;
}
.kpi-label { font-size: 13px; font-weight: 500; color: var(--muted); }
.kpi-value {
    font-size: 28px; font-weight: 700; color: var(--ink);
    margin-top: 6px; letter-spacing: -0.5px; font-variant-numeric: tabular-nums;
}
.kpi-note { font-size: 12px; color: var(--muted); margin-top: 2px; }
.kpi-shortage  { border-left: 4px solid #dc2626; }
.kpi-balanced  { border-left: 4px solid #16a34a; }
.kpi-overstock { border-left: 4px solid #d97706; }

/* ---------- Panels, charts, tables ---------- */
.panel {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 18px 22px; min-height: 318px;
}
.panel-title { font-size: 14px; font-weight: 600; color: var(--ink); margin-bottom: 4px; }
.bar-row { margin-top: 16px; }
.bar-top { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
.bar-name { color: var(--text); font-weight: 500; }
.bar-count { color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }
.bar-count span { color: var(--muted); font-weight: 400; }
.bar-track { height: 8px; background: #eef2f7; border-radius: 8px; overflow: hidden; }
.bar-fill { height: 8px; border-radius: 8px; }

[data-testid="stPlotlyChart"] {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 8px;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
}

/* ---------- Inputs and buttons ---------- */
[data-testid="stSelectbox"] label, [data-testid="stDateInput"] label {
    font-size: 13px; font-weight: 600; color: var(--ink);
}
.stDownloadButton button, .stButton button {
    border-radius: 8px; font-weight: 600; padding: 0.5rem 1.1rem;
}
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
    background: var(--accent); border-color: var(--accent); color: #ffffff;
}
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
    background: #1e40af; border-color: #1e40af; color: #ffffff;
}

/* ---------- Methodology ---------- */
.method-card {
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 20px 24px; margin-bottom: 14px;
}
.method-card h4 { margin: 0 0 8px 0; font-size: 15px; color: var(--ink); }
.method-card p, .method-card li { font-size: 14px; color: var(--text); line-height: 1.7; }
.method-card ul { margin: 6px 0 0 18px; padding: 0; }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. UI HELPERS
# =========================================================

def kpi_card(label, value, note="", tone="neutral"):
    return (
        f'<div class="kpi kpi-{tone}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-note">{note}</div>'
        f'</div>'
    )


def section_head(title, subtitle=""):
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="section-head"><div class="section-title">{title}</div>{sub}</div>',
        unsafe_allow_html=True
    )


def status_summary(df):
    """Return (counts per status, total records) for a result dataframe."""
    series = (
        df["predicted_inventory_status"]
        .fillna("unknown").astype(str).str.strip().str.lower()
    )
    counts = series.value_counts()
    total = int(counts.sum())
    known = {
        "Shortage": int(counts.get("shortage", 0)),
        "Balanced": int(counts.get("balanced", 0)),
        "Overstock": int(counts.get("overstock", 0)),
    }
    other = total - sum(known.values())
    if other > 0:
        known["Other"] = other
    return known, total


def render_status_block(df, key):
    """Donut chart on the left, share-of-records bars on the right."""
    counts, total = status_summary(df)

    if total == 0:
        st.info("No inventory records are available for this selection.")
        return

    left, right = st.columns(2, gap="medium")

    with left:
        chart_df = pd.DataFrame({
            "Status": list(counts.keys()),
            "Records": list(counts.values())
        })
        chart_df = chart_df[chart_df["Records"] > 0]

        fig = px.pie(
            chart_df, names="Status", values="Records", hole=0.72,
            color="Status", color_discrete_map=STATUS_COLORS
        )
        fig.update_traces(
            sort=False,
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>Records: %{value:,}<br>Share: %{percent}<extra></extra>",
            marker=dict(line=dict(color="#ffffff", width=3))
        )
        fig.update_layout(
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#334155"),
            annotations=[dict(
                text=f"<b style='font-size:26px;color:#0f172a'>{total:,}</b><br>"
                     f"<span style='font-size:12px;color:#64748b'>records</span>",
                x=0.5, y=0.5, showarrow=False
            )]
        )
        st.plotly_chart(
            fig, use_container_width=True,
            config={"displayModeBar": False}, key=f"donut_{key}"
        )

    with right:
        rows = ""
        for label, count in counts.items():
            share = count / total * 100 if total else 0
            rows += (
                f'<div class="bar-row">'
                f'<div class="bar-top"><span class="bar-name">{label}</span>'
                f'<span class="bar-count">{count:,} <span>({share:.1f}%)</span></span></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{share:.2f}%;background:{STATUS_COLORS[label]};"></div></div>'
                f'</div>'
            )
        st.markdown(
            f'<div class="panel"><div class="panel-title">Share of product-store records</div>{rows}</div>',
            unsafe_allow_html=True
        )


DISPLAY_COLUMNS = [
    "product_id", "product_category", "stock_level", "sales_units",
    "predicted_demand_7d", "estimated_demand_period",
    "predicted_inventory_status", "supplier_lead_time_days",
    "reorder_point", "recommended_order_quantity", "recommended_action"
]

COLUMN_NAMES = {
    "product_id": "Product ID",
    "product_category": "Category",
    "stock_level": "Current Stock",
    "sales_units": "Recent Sales",
    "predicted_demand_7d": "7-Day Demand",
    "estimated_demand_period": "Period Demand",
    "predicted_inventory_status": "Inventory Status",
    "supplier_lead_time_days": "Lead Time (Days)",
    "reorder_point": "Reorder Point",
    "recommended_order_quantity": "Suggested Order",
    "recommended_action": "Recommended Action"
}

NUMERIC_COLUMNS = [
    "Current Stock", "Recent Sales", "7-Day Demand", "Period Demand",
    "Lead Time (Days)", "Reorder Point", "Suggested Order"
]

TABLE_CONFIG = {
    name: st.column_config.NumberColumn(name, format="%d")
    for name in NUMERIC_COLUMNS
}


def prepare_table(df):
    table = df[DISPLAY_COLUMNS].rename(columns=COLUMN_NAMES)
    table["Inventory Status"] = table["Inventory Status"].astype(str).str.title()
    table["Recommended Action"] = table["Recommended Action"].astype(str).str.capitalize()
    return table


# =========================================================
# 4. LOAD SAVED MODEL BUNDLE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "inventory_model_bundle.joblib"


@st.cache_resource
def load_model_bundle(model_path):
    return joblib.load(model_path)


if not MODEL_PATH.exists():
    st.error(
        "Model file not found. Place inventory_model_bundle.joblib "
        "in the same folder as app.py."
    )
    st.stop()

try:
    bundle = load_model_bundle(str(MODEL_PATH))

    required_keys = [
        "regression_model",
        "classification_model",
        "preprocessor",
        "feature_columns",
        "product_store_catalog"
    ]

    missing_keys = [key for key in required_keys if key not in bundle]

    if missing_keys:
        st.error(
            "Your saved model file is the older version and does not "
            "contain the product-store inventory catalog. "
            f"Missing key(s): {', '.join(missing_keys)}"
        )
        st.info(
            "Go back to Google Colab and run the updated model-saving "
            "cell that creates product_store_catalog. Download the new "
            "inventory_model_bundle.joblib and replace the old file "
            "beside app.py."
        )
        st.stop()

    regression_model = bundle["regression_model"]
    classification_model = bundle["classification_model"]
    preprocessor = bundle["preprocessor"]
    feature_columns = bundle["feature_columns"]
    catalog = bundle["product_store_catalog"].copy()

    if catalog.empty:
        st.error("The saved product-store catalog is empty.")
        st.stop()

    required_catalog_columns = set(feature_columns + ["date"])
    missing_catalog_columns = required_catalog_columns - set(catalog.columns)

    if missing_catalog_columns:
        st.error(
            "The product-store catalog is missing required columns: "
            + ", ".join(sorted(missing_catalog_columns))
        )
        st.stop()

except Exception as error:
    st.error(f"Unable to load model bundle: {error}")
    st.stop()


# =========================================================
# 5. SIDEBAR - FORECAST SETTINGS
# =========================================================

st.sidebar.markdown(
    '<div class="side-brand">Inventory Forecast'
    '<span>Demand and replenishment planning</span></div>',
    unsafe_allow_html=True
)

st.sidebar.markdown('<div class="side-label">Forecast period</div>', unsafe_allow_html=True)

default_start = date.today()
default_end = default_start + timedelta(days=6)

selected_range = st.sidebar.date_input(
    "Select start and end date",
    value=(default_start, default_end),
    format="DD/MM/YYYY",
    key="forecast_date_range",
    help="Pick the start date, then the end date. Minimum period is 7 days.",
    label_visibility="collapsed"
)

range_ready = isinstance(selected_range, (tuple, list)) and len(selected_range) == 2
period_text = ""

if range_ready:
    start_date, end_date = selected_range
    forecast_days = (end_date - start_date).days + 1
    period_text = (
        f"{start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')}"
        f" <span>&nbsp;|&nbsp; {forecast_days} days</span>"
    )


# =========================================================
# 6. PAGE HEADER
# =========================================================

chip = f'<div class="period-chip">{period_text}</div>' if period_text else ""

st.markdown(
    '<div class="page-header"><div>'
    '<div class="page-title">Inventory Intelligence &amp; Forecasting</div>'
    '<div class="page-sub">Multi-store inventory monitoring, demand forecasting '
    'and stock replenishment planning</div>'
    f'</div>{chip}</div>',
    unsafe_allow_html=True
)

if not range_ready:
    st.info("Select both a start date and an end date in the sidebar to generate the forecast.")
    st.stop()

if end_date < start_date:
    st.error("End date must be on or after the start date.")
    st.stop()

if forecast_days < 7:
    st.warning(
        f"The selected period is {forecast_days} days. "
        "Please choose at least 7 days."
    )
    st.stop()

st.sidebar.markdown(
    f"""<div class="side-card">
<div class="side-card-title">Selected period</div>
<div class="side-card-value">{forecast_days} days</div>
<div class="side-card-note">{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}</div>
</div>""",
    unsafe_allow_html=True
)

st.sidebar.markdown('<div class="side-label">Planning parameters</div>', unsafe_allow_html=True)
st.sidebar.markdown(
    f"""<div class="side-card">
<div class="side-card-title">Safety stock buffer</div>
<div class="side-card-value">{SAFETY_STOCK_PERCENT:.0%}</div>
<div class="side-card-note">Applied to lead-time demand. This is an illustrative
assumption and needs business approval.</div>
</div>""",
    unsafe_allow_html=True
)
st.sidebar.caption("Settings apply to all product-store combinations.")


# =========================================================
# 7. PREPARE ALL PRODUCT-STORE RECORDS
# =========================================================

forecast_input = catalog.copy()

if forecast_input.empty:
    st.error("No product-store inventory records found in the model bundle.")
    st.stop()

# Use selected forecast start date for date features
forecast_input["year"] = start_date.year
forecast_input["month"] = start_date.month
forecast_input["day"] = start_date.day
forecast_input["day_of_week"] = start_date.weekday()

# Keep exact training feature order
forecast_input = forecast_input[feature_columns]


# =========================================================
# 8. RUN BOTH SAVED ML MODELS
# =========================================================

try:
    encoded_input = preprocessor.transform(forecast_input)

    # Model 1: demand for the next 7 days
    predicted_7d_demand = regression_model.predict(encoded_input)
    predicted_7d_demand = np.maximum(0, np.rint(predicted_7d_demand)).astype(int)

    # Model 2: inventory status on a 7-day basis
    predicted_status = classification_model.predict(encoded_input)

except Exception as error:
    st.error(f"Prediction failed: {error}")
    st.stop()


# =========================================================
# 9. BUILD FORECAST RESULT TABLE
# =========================================================

result_df = catalog.copy()

result_df["predicted_demand_7d"] = predicted_7d_demand
result_df["predicted_inventory_status"] = predicted_status

# For periods longer than 7 days, constant average daily demand is assumed.
result_df["estimated_demand_period"] = np.ceil(
    result_df["predicted_demand_7d"] * forecast_days / 7
).astype(int)

result_df["estimated_daily_demand"] = result_df["predicted_demand_7d"] / 7

# Replenishment calculation
result_df["lead_time_demand"] = (
    result_df["estimated_daily_demand"] * result_df["supplier_lead_time_days"]
)

result_df["safety_stock"] = np.ceil(
    result_df["lead_time_demand"] * SAFETY_STOCK_PERCENT
).astype(int)

result_df["reorder_point"] = np.ceil(
    result_df["lead_time_demand"] + result_df["safety_stock"]
).astype(int)

result_df["recommended_order_quantity"] = np.maximum(
    0, result_df["reorder_point"] - result_df["stock_level"]
).astype(int)


def get_recommended_action(row):
    status = row["predicted_inventory_status"]
    quantity = row["recommended_order_quantity"]

    if status == "shortage":
        return "REORDER STOCK" if quantity > 0 else "MONITOR STOCK"
    elif status == "overstock":
        return "OVERSTOCK ALERT"
    elif status == "balanced":
        return "REPLENISHMENT REVIEW" if quantity > 0 else "STOCK BALANCED"
    return "REVIEW REQUIRED"


result_df["recommended_action"] = result_df.apply(get_recommended_action, axis=1)


# =========================================================
# 10. DASHBOARD TABS
# =========================================================

tab_overview, tab_store, tab_export, tab_method = st.tabs(
    ["Overview", "Store analysis", "Data export", "Methodology"]
)

# ---------------------------------------------------------
# TAB 1 - OVERVIEW
# ---------------------------------------------------------
with tab_overview:
    section_head(
        "Executive summary",
        "Inventory position across all stores for the selected forecast period."
    )

    overall_counts, overall_total = status_summary(result_df)
    total_order_quantity = int(result_df["recommended_order_quantity"].sum())

    cols = st.columns(5, gap="small")
    cols[0].markdown(
        kpi_card("Products", f"{result_df['product_id'].nunique():,}", "Unique product IDs"),
        unsafe_allow_html=True
    )
    cols[1].markdown(
        kpi_card("Stores", f"{result_df['store_id'].nunique():,}", "Locations covered"),
        unsafe_allow_html=True
    )
    cols[2].markdown(
        kpi_card(
            "Shortage", f"{overall_counts['Shortage']:,}",
            f"{overall_counts['Shortage'] / overall_total:.1%} of records" if overall_total else "",
            "shortage"
        ),
        unsafe_allow_html=True
    )
    cols[3].markdown(
        kpi_card(
            "Overstock", f"{overall_counts['Overstock']:,}",
            f"{overall_counts['Overstock'] / overall_total:.1%} of records" if overall_total else "",
            "overstock"
        ),
        unsafe_allow_html=True
    )
    cols[4].markdown(
        kpi_card("Units to order", f"{total_order_quantity:,}", "Total suggested order"),
        unsafe_allow_html=True
    )

    section_head(
        "Inventory status",
        "Predicted stock condition for every product-store record."
    )
    render_status_block(result_df, "overview")

# ---------------------------------------------------------
# TAB 2 - STORE ANALYSIS
# ---------------------------------------------------------
with tab_store:
    section_head(
        "Store-level analysis",
        "Review inventory health, replenishment needs and product forecasts for one store or all stores."
    )

    store_ids = sorted(result_df["store_id"].dropna().unique().tolist())
    store_options = ["All stores"] + [str(store) for store in store_ids]

    select_col, _spacer = st.columns([1, 2])
    selected_store = select_col.selectbox(
        "Store", options=store_options, key="professional_store_selector"
    )

    if selected_store == "All stores":
        store_view_df = result_df.copy()
    else:
        store_view_df = result_df[
            result_df["store_id"].astype(str) == selected_store
        ].copy()

    store_counts, store_total = status_summary(store_view_df)
    store_units = int(
        pd.to_numeric(store_view_df["recommended_order_quantity"], errors="coerce")
        .fillna(0).clip(lower=0).sum()
    )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    k = st.columns(5, gap="small")
    k[0].markdown(kpi_card("Products", f"{store_total:,}", "In this view"), unsafe_allow_html=True)
    k[1].markdown(kpi_card("Shortage", f"{store_counts['Shortage']:,}", "", "shortage"), unsafe_allow_html=True)
    k[2].markdown(kpi_card("Balanced", f"{store_counts['Balanced']:,}", "", "balanced"), unsafe_allow_html=True)
    k[3].markdown(kpi_card("Overstock", f"{store_counts['Overstock']:,}", "", "overstock"), unsafe_allow_html=True)
    k[4].markdown(kpi_card("Units to order", f"{store_units:,}", "Suggested order"), unsafe_allow_html=True)

    section_head("Inventory distribution")
    render_status_block(store_view_df, f"store_{selected_store}")

    section_head(
        "Product-level forecast",
        "Demand, stock position, supplier lead time and the recommended action for each product."
    )

    if not store_view_df.empty:
        store_table = prepare_table(store_view_df)

        st.dataframe(
            store_table,
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config=TABLE_CONFIG
        )

        safe_store_name = (
            "all_stores"
            if selected_store == "All stores"
            else re.sub(r"[^A-Za-z0-9_-]+", "_", str(selected_store))
        )
        st.download_button(
            label="Download store forecast (CSV)",
            data=store_table.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{safe_store_name}_inventory_forecast.csv",
            mime="text/csv",
            key="download_professional_store_forecast",
            type="primary"
        )
    else:
        st.warning("No product records are available for the selected store.")

# ---------------------------------------------------------
# TAB 3 - DATA EXPORT
# ---------------------------------------------------------
with tab_export:
    section_head(
        "Forecast data export",
        f"Complete forecast for {len(result_df):,} product-store records, "
        f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}."
    )

    download_df = prepare_table(result_df)

    st.download_button(
        label="Download all stores forecast (CSV)",
        data=download_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="complete_inventory_forecast.csv",
        mime="text/csv",
        type="primary"
    )

    section_head("Data preview", "First 200 rows of the exported file.")
    st.dataframe(
        download_df.head(200),
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config=TABLE_CONFIG
    )

# ---------------------------------------------------------
# TAB 4 - METHODOLOGY
# ---------------------------------------------------------
with tab_method:
    section_head(
        "How the forecast is produced",
        "Assumptions and calculations behind the numbers in this dashboard."
    )

    st.markdown(
        f"""<div class="method-card">
<h4>Prediction models</h4>
<ul>
<li>A Random Forest model predicts product demand for the next 7 days.</li>
<li>A Decision Tree model classifies each product-store record as shortage, balanced or overstock.</li>
<li>Both models use the 7-day target they were trained on.</li>
</ul>
</div>
<div class="method-card">
<h4>Replenishment calculation</h4>
<ul>
<li>Average daily demand = 7-day predicted demand / 7</li>
<li>Lead-time demand = average daily demand x supplier lead time (days)</li>
<li>Safety stock = {SAFETY_STOCK_PERCENT:.0%} of lead-time demand</li>
<li>Reorder point = lead-time demand + safety stock</li>
<li>Suggested order = reorder point - current stock (never below zero)</li>
</ul>
</div>
<div class="method-card">
<h4>Assumptions</h4>
<ul>
<li>For periods longer than 7 days, demand is scaled using the average daily demand.</li>
<li>The {SAFETY_STOCK_PERCENT:.0%} safety-stock buffer is illustrative and needs business approval.</li>
<li>Each product-store pair uses its latest available historical record.</li>
<li>The dashboard does not create new daily time-series forecasts.</li>
</ul>
</div>""",
        unsafe_allow_html=True
    )
