"""
Niamito Business Intelligence Dashboard
app.py  ·  Streamlit Community Cloud deployment
GitHub repo: nikatasler-cloud/niamito-dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import timedelta
import warnings
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# BRAND
# ──────────────────────────────────────────────────────────────────────────────
BEIGE  = "#EDE3D8"
BROWN  = "#2C1A0E"
LAVEN  = "#B3B8D9"
GREEN  = "#A8D99A"
CORAL  = "#F07A72"
YELLOW = "#EDD96A"
CREAM  = "#F9F4EF"
MID    = "#6b4c30"

def hex_alpha(hex_color, alpha):
    """Convert a 6-digit hex color + float alpha to an rgba() string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

MARKET_COLORS = {"SI": BROWN, "HR": LAVEN, "DE": GREEN}
SKU_COLORS    = {
    "NIA-OG-250": BROWN,
    "NIA-VN-250": LAVEN,
    "NIA-CH-250": CORAL,
    "NIA-MP-500": YELLOW,
}

# ──────────────────────────────────────────────────────────────────────────────
# PRODUCT CATEGORIES
# ──────────────────────────────────────────────────────────────────────────────
ALL_CATEGORIES = ["Niamito Oatmeal", "Niamito Fresh Meal", "Niamito Meal in a Bottle"]

_CAT_KEYWORDS = {
    "Niamito Meal in a Bottle": ["uht", "470", "cocoa", "cookie", "vanilla", "meal in a bottle"],
    "Niamito Fresh Meal":       ["fresh meal", "fresh", "hpp", "390", "apple", "blueberry", "spinach", "strawberry", "jaffa", "borovn", "jagod", "\u0161pina\u010d", "jabolč", "jaffa"],
    # Oatmeal is default
}

CATEGORY_COLORS = {
    "Niamito Fresh Meal":         GREEN,
    "Niamito Oatmeal":            BROWN,
    "Niamito Meal in a Bottle":   LAVEN,
}

def get_product_category(sku_name: str) -> str:
    """Map a product name to one of three Niamito product categories."""
    name = str(sku_name).lower()
    for cat, keywords in _CAT_KEYWORDS.items():
        if any(k in name for k in keywords):
            return cat
    return "Niamito Oatmeal"

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Niamito · Business Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─────────────────────────────────────────────────
   BASE
───────────────────────────────────────────────── */
html, body, [class*="css"], .stApp, .stMarkdown, p, span, div, label, button, input {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Helvetica Neue", Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
}

/* ─────────────────────────────────────────────────
   APP BACKGROUND
───────────────────────────────────────────────── */
.stApp { background-color: #EEE6DC; }

/* ─────────────────────────────────────────────────
   SIDEBAR
───────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #1C1008 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: rgba(240,232,220,0.70) !important;
}
section[data-testid="stSidebar"] .stMarkdown small {
    color: rgba(240,232,220,0.40) !important;
    font-size: 10px !important;
}

/* hide sidebar collapse button */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarHeader"] { display: none !important; }

/* ── section labels ─────────────────────── */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-size: 9px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: rgba(240,232,220,0.35) !important;
    font-weight: 600 !important;
    margin-bottom: 6px !important;
}

/* ── upload drop zone ─────────────────────────────── */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px dashed rgba(240,232,220,0.18) !important;
    border-radius: 16px !important;
    transition: all 0.2s ease !important;
    padding: 20px 16px !important;
    text-align: center !important;
}
/* stretch the span wrapper so the button fills full width */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] > span {
    width: 100% !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
    border-color: rgba(240,232,220,0.40) !important;
    background: rgba(255,255,255,0.08) !important;
}
/* the browse button */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background: #FFFFFF !important;
    color: #111008 !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1px !important;
    padding: 9px 0 !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    display: block !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button:hover {
    background: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
}
/* hide the icon wrapper inside the button (hides icon + removes its flex gap) */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button span:has(> [data-testid="stIconMaterial"]) {
    display: none !important;
}
/* force button text dark — overrides the broad sidebar rgba text rule */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button p,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button span,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button div {
    color: #111008 !important;
    font-weight: 600 !important;
    font-size: 12px !important;
}
/* hide file size / format hint */
[data-testid="stFileUploaderDropzoneInstructions"],
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {
    display: none !important;
}

/* ── uploaded file card — force dark text on light background ── */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"],
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFileData"],
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [class*="uploadedFile"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] p,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] span,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] small,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] div,
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [class*="uploadedFile"] * {
    color: #1C1008 !important;
    opacity: 1 !important;
}
/* progress bar under uploaded file */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] [role="progressbar"] {
    display: none !important;
}

/* ── date range picker ───────────────────── */
section[data-testid="stSidebar"] [data-testid="stDateInput"] label {
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(240,232,220,0.15) !important;
    border-radius: 12px !important;
    padding: 2px 4px !important;
}
section[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    color: rgba(240,232,220,0.85) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    text-align: center !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] [data-testid="stDateInput"] input::placeholder {
    color: rgba(240,232,220,0.35) !important;
}

/* ── multiselect ──────────────────────────── */
section[data-testid="stSidebar"] span[data-baseweb="tag"] {
    background: rgba(240,232,220,0.12) !important;
    border: 1px solid rgba(240,232,220,0.20) !important;
    border-radius: 999px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    padding: 3px 10px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(240,232,220,0.12) !important;
    border-radius: 12px !important;
}

/* ── period radio → pill buttons ─────────── */
section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 3px !important;
    display: flex !important;
    flex-direction: column !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    padding: 8px 14px !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
    background: rgba(237,221,210,0.13) !important;
    border-color: rgba(240,232,220,0.22) !important;
}
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}

/* ─────────────────────────────────────────────────
   MAIN CONTENT
───────────────────────────────────────────────── */
.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

/* ── metric cards ─────────────────────────── */
div[data-testid="metric-container"] {
    background: #F9F4EF;
    border: 1px solid rgba(44,26,14,0.10);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 0 0 0.5px rgba(0,0,0,0.06), 0 2px 6px rgba(44,26,14,0.04), 0 8px 20px rgba(44,26,14,0.07);
}
div[data-testid="metric-container"] label {
    color: #6b4c30 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-weight: 600 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #1C1008 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ── tabs ─────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(44,26,14,0.07) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(44,26,14,0.55);
    border-radius: 8px !important;
    font-size: 13px;
    font-weight: 500;
    padding: 7px 16px;
    background: transparent !important;
    border: none !important;
    transition: all 0.15s ease !important;
}
.stTabs [aria-selected="true"] {
    color: #1C1008 !important;
    font-weight: 600 !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.10), 0 1px 1px rgba(0,0,0,0.06) !important;
}

/* ── iOS segmented control — main content radios ─ */
.stMain [data-testid="stRadio"] > div[role="radiogroup"] {
    display: inline-flex !important;
    flex-direction: row !important;
    background: rgba(44,26,14,0.07) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 2px !important;
}
.stMain label[data-baseweb="radio"] {
    border-radius: 8px !important;
    padding: 5px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: rgba(44,26,14,0.55) !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
    border: none !important;
    background: transparent !important;
}
.stMain label[data-baseweb="radio"]:has(input:checked) {
    background: #FFFFFF !important;
    color: #1C1008 !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.10), 0 1px 1px rgba(0,0,0,0.06) !important;
}
.stMain label[data-baseweb="radio"] > div:first-child { display: none !important; }

/* ── chart captions ───────────────────────── */
p.chart-caption {
    font-size: 12.5px;
    color: #8a6a4a;
    line-height: 1.55;
    margin-top: 6px;
    margin-bottom: 18px;
    max-width: 520px;
}

/* ── demo badge ───────────────────────────── */
.demo-badge {
    background: #EDD96A;
    color: #2C1A0E;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 999px;
    vertical-align: middle;
}

/* ── page header ──────────────────────────── */
.page-header {
    font-size: 22px;
    font-weight: 700;
    color: #1C1008;
    letter-spacing: -0.4px;
    margin-bottom: 2px;
}
.context-line {
    font-size: 12px;
    color: #8a6a4a;
    margin-bottom: 20px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CAPTION HELPER
# ──────────────────────────────────────────────────────────────────────────────
def caption(text):
    st.markdown(f"<p class='chart-caption'>{text}</p>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# CHART LAYOUT HELPER
# ──────────────────────────────────────────────────────────────────────────────
def base_layout(title="", height=340, legend_below=True):
    leg = dict(
        orientation="h", y=-0.20, x=0,
        font=dict(size=10, color=BROWN),
        bgcolor="rgba(0,0,0,0)",
    ) if legend_below else dict(font=dict(size=10, color=BROWN), bgcolor="rgba(0,0,0,0)")
    return dict(
        title=dict(text=title, font=dict(color=BROWN, size=13, family="Georgia"), x=0, pad=dict(l=6)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CREAM,
        font=dict(color=BROWN, size=11, family="Arial"),
        height=height,
        margin=dict(l=12, r=12, t=44, b=20),
        legend=leg,
        xaxis=dict(gridcolor="#e8ddd0", gridwidth=1, zeroline=False, linecolor="#c8b89a"),
        yaxis=dict(gridcolor="#e8ddd0", gridwidth=1, zeroline=False, linecolor="#c8b89a"),
        hoverlabel=dict(bgcolor=CREAM, bordercolor=BROWN, font=dict(color=BROWN, size=11)),
    )


# ──────────────────────────────────────────────────────────────────────────────
# DEMO DATA — Niamito realistic structure Jan 2024–Apr 2026
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def generate_demo_data():
    rng = np.random.default_rng(42)

    PRODUCTS = {
        # Fresh Meal (HPP 390g)
        "APL05": {"name": "Fresh Meal Apple 390g",       "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "BLU05": {"name": "Fresh Meal Blueberry 390g",   "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "SPN05": {"name": "Fresh Meal Spinach 390g",     "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        "STR05": {"name": "Fresh Meal Strawberry 390g",  "price": 4.20, "bpc": 1, "line": "Niamito Fresh Meal"},
        # Oatmeal
        "BLK05": {"name": "Blueberry Oat",               "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        "CHK05": {"name": "Choco Oat",                   "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        "PCK05": {"name": "Peach Oat",                   "price": 3.50, "bpc": 1, "line": "Niamito Oatmeal"},
        # Meal in a Bottle (UHT 470ml)
        "COU05-DE": {"name": "Meal in a Bottle Cocoa 470ml",   "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
        "CKU05-DE": {"name": "Meal in a Bottle Cookie 470ml",  "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
        "VAU05-DE": {"name": "Meal in a Bottle Vanilla 470ml", "price": 3.80, "bpc": 1, "line": "Niamito Meal in a Bottle"},
    }

    weeks = pd.date_range("2024-01-01", "2026-04-28", freq="W-MON")

    # Base weekly bottles per SKU per market
    BASE = {
        "SI": {
            "APL05": 120, "BLU05": 95, "SPN05": 60, "STR05": 80,
            "BLK05": 70, "CHK05": 55, "PCK05": 50,
            "COU05-DE": 0, "CKU05-DE": 0, "VAU05-DE": 0,
        },
        "HR": {
            "APL05": 50, "BLU05": 40, "SPN05": 25, "STR05": 35,
            "BLK05": 30, "CHK05": 25, "PCK05": 20,
            "COU05-DE": 0, "CKU05-DE": 0, "VAU05-DE": 0,
        },
        "DE": {
            "APL05": 0, "BLU05": 0, "SPN05": 0, "STR05": 0,
            "BLK05": 0, "CHK05": 0, "PCK05": 0,
            "COU05-DE": 80, "CKU05-DE": 65, "VAU05-DE": 55,
        },
    }

    primary_rows = []
    for i, wk in enumerate(weeks):
        growth = 1 + i * 0.008
        for mkt, sku_dict in BASE.items():
            for sku, base_bottles in sku_dict.items():
                if base_bottles == 0:
                    continue
                bottles = max(1, int(base_bottles * growth * rng.uniform(0.85, 1.18)))
                price = PRODUCTS[sku]["price"]
                gross = round(bottles * price, 2)
                primary_rows.append({
                    "week": wk,
                    "market": mkt,
                    "sku_id": sku,
                    "sku_name": PRODUCTS[sku]["name"],
                    "cases": 0,
                    "bottles": bottles,
                    "list_price": price,
                    "gross_revenue": gross,
                    "trade_discount": 0.0,
                    "net_revenue": gross,
                    "funnel_type": "3-tier" if mkt in ["SI", "HR"] else "2-tier",
                    "category": PRODUCTS[sku]["line"],
                })

    prim_df = pd.DataFrame(primary_rows)
    prim_df["category"] = prim_df["sku_name"].apply(get_product_category)

    # ── Secondary sales (retail sell-out, SI only, no revenue) ────────────────
    RETAILER_POOL = [f"Retailer_{i:03d}" for i in range(1, 224)]
    so_rows = []
    so_weeks = pd.date_range("2025-01-06", "2026-04-28", freq="W-MON")
    si_skus = [k for k, v in PRODUCTS.items() if v["line"] in ("Niamito Fresh Meal", "Niamito Oatmeal")]
    for wk in so_weeks:
        n_retailers = rng.integers(30, 80)
        chosen = rng.choice(RETAILER_POOL, size=n_retailers, replace=False)
        for ret in chosen:
            sku = rng.choice(si_skus)
            units = int(rng.integers(2, 25))
            so_rows.append({
                "week": wk,
                "market": "SI",
                "retailer": ret,
                "sku_id": sku,
                "sku_name": PRODUCTS[sku]["name"],
                "bottles_sold": units,
                "consumer_price": 0.0,
                "sellout_revenue": 0.0,
                "funnel_type": "3-tier",
                "category": PRODUCTS[sku]["line"],
            })
    so_df = pd.DataFrame(so_rows)
    so_df["category"] = so_df["sku_name"].apply(get_product_category)

    # ── Distributor stock (SI & HR) ───────────────────────
    stock_rows = []
    for mkt in ["SI", "HR"]:
        stock = 0
        for wk in weeks:
            c_in = int(prim_df[(prim_df["market"] == mkt) & (prim_df["week"] == wk)]["bottles"].sum() // 12)
            c_out = int(c_in * rng.uniform(0.72, 0.96))
            stock = max(0, stock + c_in - c_out)
            stock_rows.append({
                "week": wk, "market": mkt,
                "cases_in": c_in, "cases_out": c_out,
                "stock_cases": stock,
                "stock_to_sales": round(stock / max(c_out, 1), 2),
            })
    stock_df = pd.DataFrame(stock_rows)

    # ── Marketing Calendar ────────────────────────────────
    mkt_campaigns = [
        {"id": "MKT-2024-001", "name": "Q1 Digital SI",           "channel": "Digital",     "market": "SI",  "start": "2024-01-15", "end": "2024-02-28", "media_spend": 2500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-002", "name": "Spring Events SI",         "channel": "Events",      "market": "SI",  "start": "2024-03-01", "end": "2024-04-30", "media_spend": 3800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-003", "name": "Mercator Listing Q1",      "channel": "Team",        "market": "SI",  "start": "2024-01-01", "end": "2024-01-01", "media_spend": 0,    "listing_fee": 4500, "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2024-004", "name": "Production Campaign",      "channel": "Production",  "market": "SI",  "start": "2024-05-01", "end": "2024-05-31", "media_spend": 1800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-005", "name": "HR Market Launch",         "channel": "Events",      "market": "HR",  "start": "2024-06-01", "end": "2024-06-30", "media_spend": 3200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-006", "name": "DE Launch Digital",        "channel": "Digital-Intl","market": "DE",  "start": "2024-07-01", "end": "2024-08-31", "media_spend": 5500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-007", "name": "@healthysi Collab",        "channel": "Digital",     "market": "SI",  "start": "2024-09-10", "end": "2024-09-24", "media_spend": 700,  "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": "@healthysi", "reach": 32000, "scope": "Market", "window_days": 14},
        {"id": "MKT-2024-008", "name": "Q4 Traditional SI",        "channel": "Traditional", "market": "SI",  "start": "2024-10-01", "end": "2024-12-31", "media_spend": 4200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-001", "name": "Jan Digital Push",         "channel": "Digital",     "market": "SI",  "start": "2025-01-15", "end": "2025-02-15", "media_spend": 2800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-002", "name": "Spring Events HR",         "channel": "Events",      "market": "HR",  "start": "2025-03-01", "end": "2025-04-30", "media_spend": 3500, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-003", "name": "@fitnesswelt_de Collab",   "channel": "Digital-Intl","market": "DE",  "start": "2025-04-01", "end": "2025-04-21", "media_spend": 2000, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": "@fitnesswelt_de", "reach": 115000, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-004", "name": "Production 2025",          "channel": "Production",  "market": "SI",  "start": "2025-05-01", "end": "2025-05-31", "media_spend": 2100, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2025-005", "name": "Konzum Listing HR",        "channel": "Team",        "market": "HR",  "start": "2025-06-01", "end": "2025-06-01", "media_spend": 0,    "listing_fee": 3800, "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2025-006", "name": "Q4 Traditional SI",        "channel": "Traditional", "market": "SI",  "start": "2025-10-01", "end": "2025-12-31", "media_spend": 4800, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-001", "name": "Q1 Digital 2026",          "channel": "Digital",     "market": "SI",  "start": "2026-01-15", "end": "2026-02-28", "media_spend": 3200, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-002", "name": "Spring Events 2026",       "channel": "Events",      "market": "SI",  "start": "2026-03-01", "end": "2026-04-30", "media_spend": 4100, "listing_fee": 0,    "trade_disc": 0,   "roas": None, "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
    ]
    mkt_df = pd.DataFrame(mkt_campaigns)
    mkt_df["total_spend"] = mkt_df["media_spend"] + mkt_df["listing_fee"] + mkt_df["trade_disc"]
    mkt_df["attributed_sales"] = 0.0

    return prim_df, so_df, mkt_df, stock_df, PRODUCTS


# ──────────────────────────────────────────────────────────────────────────────
# EXCEL LOADER (for real uploads)
# ──────────────────────────────────────────────────────────────────────────────
def load_excel(file):
    """
    Load Niamito_Master_Tables.xlsx and map all sheets to the app's
    internal dataframe schema.
    Returns (prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df).
    """
    def to_float(val):
        """Safely convert a cell value to float, treating '-', '', None as 0."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    CHANNEL_TYPE_MAP = {
        "Ekipa": "Team",
        "Produkcija": "Production",
        "Digitalni marketing": "Digital",
        "Digitalni marketing AT": "Digital-Intl",
        "Dogodki & promocije": "Events",
        "Tradicionalni marketing": "Traditional",
    }

    import openpyxl as _opxl
    _wb = _opxl.load_workbook(file, data_only=True)

    # Read sheets with row-3 headers (standard sheets)
    raw = {}
    for s in _wb.sheetnames:
        try:
            ws = _wb[s]
            headers = [
                str(cell.value).replace("\n", " ").strip() if cell.value else f"_col{i}"
                for i, cell in enumerate(ws[3])
            ]
            rows = []
            for row in ws.iter_rows(min_row=4, values_only=True):
                if any(v is not None for v in row):
                    rows.append(dict(zip(headers, row)))
            if rows:
                df = pd.DataFrame(rows).dropna(how="all")
                raw[s] = df
        except Exception:
            pass

    # Read Expenses sheet with row-1 headers
    exp_raw = None
    for s in _wb.sheetnames:
        if "expense" in s.lower() or "Expense" in s:
            try:
                ws = _wb[s]
                headers = [
                    str(cell.value).replace("\n", " ").strip() if cell.value else f"_col{i}"
                    for i, cell in enumerate(ws[1])
                ]
                rows = []
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if any(v is not None for v in row):
                        rows.append(dict(zip(headers, row)))
                if rows:
                    exp_raw = pd.DataFrame(rows).dropna(how="all")
            except Exception:
                pass
            break

    def find(keywords):
        for name, df in raw.items():
            if any(k.lower() in name.lower() for k in keywords):
                return df, name
        return None, None

    prod_raw_df, _ = find(["Product"])
    mkt_raw_df, _  = find(["Marketing", "Calendar"])
    prim_raw_df, _ = find(["Primary", "Sales"])

    # Find Secondary Sales sheet
    sec_raw_df = None
    sec_name = None
    for name, df in raw.items():
        if "secondary" in name.lower():
            sec_raw_df = df
            sec_name = name
            break

    # Find Sell-out Template sheet
    sot_raw_df = None
    for name, df in raw.items():
        if "sell" in name.lower() and "template" in name.lower():
            sot_raw_df = df
            break
        if "sell" in name.lower() and name != sec_name:
            sot_raw_df = df
            break

    # ── PRODUCTS dict ─────────────────────────────────────────────────────────
    PRODUCTS = {}
    prod_by_ret_name = {}
    if prod_raw_df is not None:
        ret_name_col = next((c for c in prod_raw_df.columns if "Retailer SKU Name" in c), None)
        sku_col      = next((c for c in prod_raw_df.columns if "Internal SKU" in c), None)
        name_col     = next((c for c in prod_raw_df.columns if "Product Name" in c), None)
        for _, r in prod_raw_df.iterrows():
            if pd.isna(r.get(sku_col, None)):
                continue
            sku = str(r[sku_col]).strip()
            prd_name = str(r[name_col]).strip() if name_col else sku
            PRODUCTS[sku] = {"name": prd_name, "price": 0.0, "bpc": 1}
            if ret_name_col and pd.notna(r.get(ret_name_col)):
                key = str(r[ret_name_col]).strip().lower()
                prod_by_ret_name[key] = {"sku_id": sku, "sku_name": prd_name}

    if not PRODUCTS:
        PRODUCTS = {
            "APL05": {"name": "Fresh Meal Apple 390g",       "price": 4.20, "bpc": 1},
            "BLU05": {"name": "Fresh Meal Blueberry 390g",   "price": 4.20, "bpc": 1},
            "SPN05": {"name": "Fresh Meal Spinach 390g",     "price": 4.20, "bpc": 1},
            "STR05": {"name": "Fresh Meal Strawberry 390g",  "price": 4.20, "bpc": 1},
            "BLK05": {"name": "Blueberry Oat",               "price": 3.50, "bpc": 1},
            "CHK05": {"name": "Choco Oat",                   "price": 3.50, "bpc": 1},
            "PCK05": {"name": "Peach Oat",                   "price": 3.50, "bpc": 1},
            "COU05-DE": {"name": "Meal in a Bottle Cocoa 470ml",   "price": 3.80, "bpc": 1},
            "CKU05-DE": {"name": "Meal in a Bottle Cookie 470ml",  "price": 3.80, "bpc": 1},
            "VAU05-DE": {"name": "Meal in a Bottle Vanilla 470ml", "price": 3.80, "bpc": 1},
        }

    # ── Primary Sales → prim_df ───────────────────────────────────────────────
    prim_rows = []
    if prim_raw_df is not None:
        date_col_p = next((c for c in prim_raw_df.columns if "Invoice Date" in c or "Date" in c), None)
        mkt_col_p  = next((c for c in prim_raw_df.columns if "Market" in c), None)
        tier_col_p = next((c for c in prim_raw_df.columns if "Tier" in c), None)
        sku_col_p  = next((c for c in prim_raw_df.columns if "Internal SKU Code" in c or "Internal SKU" in c), None)
        name_col_p = next((c for c in prim_raw_df.columns if "Product Name" in c), None)
        btl_col_p  = next((c for c in prim_raw_df.columns if "Bottles sold" in c or "Bottles Sold" in c or "Bottles" in c), None)
        gross_col  = next((c for c in prim_raw_df.columns if "Gross Revenue" in c), None)

        for _, r in prim_raw_df.iterrows():
            if pd.isna(r.get(sku_col_p)):
                continue
            raw_date = r.get(date_col_p)
            try:
                dt   = pd.to_datetime(str(raw_date), dayfirst=True, errors="coerce")
                week = dt - pd.Timedelta(days=dt.weekday())
            except Exception:
                week = pd.NaT
            mkt = str(r.get(mkt_col_p, "SI")).strip() if mkt_col_p else "SI"
            # Normalise SLO → SI
            if mkt.upper() in ("SLO", "SLOVENIJA"):
                mkt = "SI"
            if mkt not in ("SI", "HR", "DE"):
                mkt = "SI"
            sku   = str(r.get(sku_col_p, "")).strip()
            name  = str(r.get(name_col_p, sku)).strip() if name_col_p else sku
            bottles = int(to_float(r.get(btl_col_p)))
            gross   = to_float(r.get(gross_col))
            prim_rows.append({
                "week":           week,
                "market":         mkt,
                "sku_id":         sku,
                "sku_name":       name,
                "cases":          0,
                "bottles":        bottles,
                "list_price":     round(gross / max(bottles, 1), 4),
                "gross_revenue":  gross,
                "trade_discount": 0.0,
                "net_revenue":    gross,
                "funnel_type":    "3-tier",
            })

    prim_df = pd.DataFrame(prim_rows) if prim_rows else pd.DataFrame(
        columns=["week","market","sku_id","sku_name","cases","bottles",
                 "list_price","gross_revenue","trade_discount","net_revenue","funnel_type"])
    prim_df["category"] = prim_df["sku_name"].apply(get_product_category)

    stock_df = pd.DataFrame(
        columns=["week","market","cases_in","cases_out","stock_cases","stock_to_sales"])

    # ── Secondary Sales → so_df ───────────────────────────────────────────────
    so_rows = []

    def _parse_secondary_row(r, date_col, retail_col, sku_col_s, pcs_col):
        raw_date = r.get(date_col)
        try:
            dt   = pd.to_datetime(str(raw_date), dayfirst=True, errors="coerce")
            week = dt - pd.Timedelta(days=dt.weekday())
        except Exception:
            week = pd.NaT
        retailer = str(r.get(retail_col, "")).strip() if retail_col else ""
        sku_raw  = str(r.get(sku_col_s, "")).strip() if sku_col_s else ""
        prod_info = prod_by_ret_name.get(sku_raw.lower(), {"sku_id": sku_raw, "sku_name": sku_raw})
        units = int(to_float(r.get(pcs_col)))
        return {
            "week":            week,
            "market":          "SI",
            "retailer":        retailer,
            "sku_id":          prod_info["sku_id"],
            "sku_name":        prod_info["sku_name"],
            "bottles_sold":    units,
            "consumer_price":  0.0,
            "sellout_revenue": 0.0,
            "funnel_type":     "3-tier",
        }

    if sec_raw_df is not None:
        date_col_s   = next((c for c in sec_raw_df.columns if "DATE" in c.upper() or "Date" in c), None)
        retail_col_s = next((c for c in sec_raw_df.columns if "RETAIL" in c.upper() or "Store" in c or "Retail" in c), None)
        sku_col_s    = next((c for c in sec_raw_df.columns if c.upper() == "SKU" or "SKU" in c), None)
        pcs_col_s    = next((c for c in sec_raw_df.columns if c.upper() == "PCS" or "PCS" in c or "Units" in c), None)
        for _, r in sec_raw_df.iterrows():
            if pd.isna(r.get(pcs_col_s)):
                continue
            row_data = _parse_secondary_row(r, date_col_s, retail_col_s, sku_col_s, pcs_col_s)
            if row_data["bottles_sold"] > 0:
                so_rows.append(row_data)

    # Sell-out Template — merge additional rows
    if sot_raw_df is not None:
        date_col_t  = next((c for c in sot_raw_df.columns if "Date" in c), None)
        store_col_t = next((c for c in sot_raw_df.columns if "Store" in c or "Retail" in c), None)
        mkt_col_t   = next((c for c in sot_raw_df.columns if "Market" in c), None)
        name_col_t  = next((c for c in sot_raw_df.columns if "Product Name" in c), None)
        units_col_t = next((c for c in sot_raw_df.columns if "Units" in c), None)
        rev_col_t   = next((c for c in sot_raw_df.columns if "Revenue" in c), None)
        for _, r in sot_raw_df.iterrows():
            if pd.isna(r.get(units_col_t)):
                continue
            raw_date = r.get(date_col_t)
            try:
                dt   = pd.to_datetime(str(raw_date), dayfirst=True, errors="coerce")
                week = dt - pd.Timedelta(days=dt.weekday())
            except Exception:
                week = pd.NaT
            mkt = str(r.get(mkt_col_t, "SI")).strip() if mkt_col_t else "SI"
            if mkt.upper() in ("SLO", "SLOVENIJA"):
                mkt = "SI"
            if mkt not in ("SI", "HR", "DE"):
                mkt = "SI"
            prd_raw = str(r.get(name_col_t, "")).strip() if name_col_t else ""
            prod_info = prod_by_ret_name.get(prd_raw.lower(), {"sku_id": prd_raw, "sku_name": prd_raw})
            units = int(to_float(r.get(units_col_t)))
            rev   = to_float(r.get(rev_col_t)) if rev_col_t else 0.0
            if units > 0:
                so_rows.append({
                    "week":            week,
                    "market":          mkt,
                    "retailer":        str(r.get(store_col_t, "")).strip() if store_col_t else "",
                    "sku_id":          prod_info["sku_id"],
                    "sku_name":        prod_info["sku_name"],
                    "bottles_sold":    units,
                    "consumer_price":  round(rev / units, 2) if units > 0 and rev > 0 else 0.0,
                    "sellout_revenue": round(rev, 2),
                    "funnel_type":     "3-tier" if mkt in ("SI", "HR") else "2-tier",
                })

    so_df = pd.DataFrame(so_rows) if so_rows else pd.DataFrame(
        columns=["week","market","retailer","sku_id","sku_name","bottles_sold",
                 "consumer_price","sellout_revenue","funnel_type"])
    if not so_df.empty:
        so_df["category"] = so_df["sku_name"].apply(get_product_category)
    else:
        so_df["category"] = pd.Series(dtype=str)

    # ── Marketing Calendar → mkt_df ───────────────────────────────────────────
    mkt_rows = []
    if mkt_raw_df is not None:
        cid_col   = next((c for c in mkt_raw_df.columns if "Campaign ID" in c), None)
        name_col  = next((c for c in mkt_raw_df.columns if "Campaign Name" in c), None)
        type_col  = next((c for c in mkt_raw_df.columns if "Type" in c), None)
        mkt_col   = next((c for c in mkt_raw_df.columns if "Market" in c), None)
        start_col = next((c for c in mkt_raw_df.columns if "Start" in c), None)
        end_col   = next((c for c in mkt_raw_df.columns if "End" in c), None)
        inf_col   = next((c for c in mkt_raw_df.columns if "Influencer" in c), None)
        reach_col = next((c for c in mkt_raw_df.columns if "Reach" in c), None)
        scope_col = next((c for c in mkt_raw_df.columns if "Attribution Scope" in c), None)
        window_col= next((c for c in mkt_raw_df.columns if "Attribution Window" in c), None)
        # Spend is col index 6 = "TOTAL Spend (€)"
        spend_col = mkt_raw_df.columns[6] if len(mkt_raw_df.columns) > 6 else None

        for _, r in mkt_raw_df.iterrows():
            if pd.isna(r.get(cid_col)):
                continue
            total = to_float(r.get(spend_col)) if spend_col else 0.0
            raw_type = str(r.get(type_col, "")).strip() if type_col else ""
            channel  = CHANNEL_TYPE_MAP.get(raw_type, raw_type)
            mkt_val  = str(r.get(mkt_col, "")).strip() if mkt_col else "SI"
            if mkt_val.upper() in ("SLO", "SLOVENIJA"):
                mkt_val = "SI"
            # Derive scope from channel type
            if scope_col and pd.notna(r.get(scope_col)):
                raw_scope = str(r.get(scope_col, "")).strip()
                scope = "Market" if "market" in raw_scope.lower() else "Store"
            else:
                scope = "Market" if channel in ("Digital", "Digital-Intl", "Events", "Traditional") else "Store"
            mkt_rows.append({
                "id":               str(r.get(cid_col, "")).strip(),
                "name":             str(r.get(name_col, "")).strip() if name_col else "",
                "channel":          channel,
                "market":           mkt_val,
                "start":            str(r.get(start_col, "")).strip() if start_col else "",
                "end":              str(r.get(end_col, "")).strip() if end_col else "",
                "media_spend":      total,
                "listing_fee":      0.0,
                "trade_disc":       0.0,
                "total_spend":      total,
                "roas":             None,
                "attributed_sales": 0.0,
                "influencer":       str(r[inf_col]).strip() if inf_col and pd.notna(r.get(inf_col)) else None,
                "reach":            to_float(r.get(reach_col)) or None,
                "scope":            scope,
                "window_days":      int(to_float(r.get(window_col)) or 14),
            })

    mkt_df = pd.DataFrame(mkt_rows) if mkt_rows else pd.DataFrame(
        columns=["id","name","channel","market","start","end","media_spend",
                 "listing_fee","trade_disc","total_spend","roas","attributed_sales",
                 "influencer","reach","scope","window_days"])

    # ── Expenses → exp_df ────────────────────────────────────────────────────
    exp_rows = []
    if exp_raw is not None:
        pl_col   = next((c for c in exp_raw.columns if "Product Line" in c), None)
        sku_col_e= next((c for c in exp_raw.columns if c.strip() == "SKU"), None)
        mon_col  = next((c for c in exp_raw.columns if "Month" in c), None)
        prod_col = next((c for c in exp_raw.columns if "Production cost" in c), None)
        log_col  = next((c for c in exp_raw.columns if "Logistics" in c), None)
        mktg_col = next((c for c in exp_raw.columns if "Marketing" in c and "Promo" in c), None)
        if mktg_col is None:
            mktg_col = next((c for c in exp_raw.columns if "Marketing" in c), None)
        for _, r in exp_raw.iterrows():
            if pd.isna(r.get(pl_col)):
                continue
            exp_rows.append({
                "product_line":    str(r.get(pl_col, "")).strip(),
                "sku":             str(r.get(sku_col_e, "")).strip() if sku_col_e else "",
                "month":           str(r.get(mon_col, "")).strip() if mon_col else "",
                "production_cost": to_float(r.get(prod_col)),
                "logistics":       to_float(r.get(log_col)),
                "marketing_promo": to_float(r.get(mktg_col)),
            })

    exp_df = pd.DataFrame(exp_rows) if exp_rows else pd.DataFrame(
        columns=["product_line","sku","month","production_cost","logistics","marketing_promo"])

    return prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='padding: 32px 4px 24px; text-align:center;'>
            <div style='font-family:Georgia,serif; font-size:22px; font-weight:700;
                        color:#EDE3D8; letter-spacing:-0.4px; line-height:1;'>Niamito</div>
            <div style='font-size:9px; color:rgba(237,227,216,0.28); letter-spacing:3px;
                        text-transform:uppercase; margin-top:6px; font-weight:500;'>Business Intelligence</div>
        </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Data source",
        type=["xlsx"],
        help="Upload Niamito_Master_Tables.xlsx from Google Drive",
        key="file_uploader",
    )

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    market_filter = st.multiselect(
        "Markets",
        options=["SI", "HR", "DE"],
        default=["SI", "HR", "DE"],
    )

    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

    period = st.radio(
        "Period",
        options=["All data", "Last month", "Last quarter", "Custom range"],
        index=0,
    )

    custom_range = None
    if period == "Custom range":
        custom_range = st.date_input(
            "Date range",
            value=(pd.Timestamp("2026-01-01").date(), pd.Timestamp("2026-04-28").date()),
            min_value=pd.Timestamp("2024-01-01").date(),
            max_value=pd.Timestamp("2026-12-31").date(),
            format="DD/MM/YYYY",
        )

    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

    category_filter = st.multiselect(
        "Product Category",
        options=ALL_CATEGORIES,
        default=ALL_CATEGORIES,
    )

    st.markdown(
        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:10px 0 8px;'>",
        unsafe_allow_html=True,
    )

    metric_mode = st.radio(
        "View as",
        options=["Bottles sold", "Revenue (€)"],
        index=0,
    )


# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
demo_mode = True
PRODUCTS = {
    "APL05": {"name": "Fresh Meal Apple 390g",       "price": 4.20, "bpc": 1},
    "BLU05": {"name": "Fresh Meal Blueberry 390g",   "price": 4.20, "bpc": 1},
    "SPN05": {"name": "Fresh Meal Spinach 390g",     "price": 4.20, "bpc": 1},
    "STR05": {"name": "Fresh Meal Strawberry 390g",  "price": 4.20, "bpc": 1},
    "BLK05": {"name": "Blueberry Oat",               "price": 3.50, "bpc": 1},
    "CHK05": {"name": "Choco Oat",                   "price": 3.50, "bpc": 1},
    "PCK05": {"name": "Peach Oat",                   "price": 3.50, "bpc": 1},
    "COU05-DE": {"name": "Meal in a Bottle Cocoa 470ml",   "price": 3.80, "bpc": 1},
    "CKU05-DE": {"name": "Meal in a Bottle Cookie 470ml",  "price": 3.80, "bpc": 1},
    "VAU05-DE": {"name": "Meal in a Bottle Vanilla 470ml", "price": 3.80, "bpc": 1},
}
prim_df  = pd.DataFrame(columns=["week","market","sku_id","sku_name","cases","bottles",
                                  "list_price","gross_revenue","trade_discount","net_revenue","funnel_type","category"])
so_df    = pd.DataFrame(columns=["week","market","retailer","sku_id","sku_name","bottles_sold",
                                  "consumer_price","sellout_revenue","funnel_type","category"])
mkt_df   = pd.DataFrame(columns=["id","name","channel","market","start","end","media_spend",
                                  "listing_fee","trade_disc","total_spend","roas","attributed_sales",
                                  "influencer","reach","scope","window_days"])
stock_df = pd.DataFrame(columns=["week","market","cases_in","cases_out","stock_cases","stock_to_sales"])
exp_df   = pd.DataFrame(columns=["product_line","sku","month","production_cost","logistics","marketing_promo"])

if uploaded is not None:
    try:
        prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df = load_excel(uploaded)
        demo_mode = False
        st.sidebar.success("Data loaded")
        # Show data freshness note
        if not prim_df.empty and "week" in prim_df.columns:
            latest_prim = prim_df["week"].max()
            if pd.notna(latest_prim):
                st.sidebar.caption(
                    f"📦 Primary Sales data: up to {latest_prim.strftime('%b %Y')}. "
                    "Add new invoices to the Excel to extend the timeline."
                )
    except Exception as e:
        st.sidebar.error(f"Could not read file: {e}")

if demo_mode:
    prim_df, so_df, mkt_df, stock_df, PRODUCTS = generate_demo_data()

# ── Apply market filter ───────────────────────────────
if market_filter:
    prim_f  = prim_df[prim_df["market"].isin(market_filter)]
    so_f    = so_df[so_df["market"].isin(market_filter)]
    mkt_f   = mkt_df[mkt_df["market"].isin(market_filter) | (mkt_df["market"] == "ALL")]
    stock_f = stock_df[stock_df["market"].isin(market_filter)]
else:
    prim_f, so_f, mkt_f, stock_f = prim_df, so_df, mkt_df, stock_df

# Snapshot before category filter — used in SKU Performance to show all products
prim_f_nokcat = prim_f.copy()

# ── Apply category filter ─────────────────────────────
if category_filter and len(category_filter) < len(ALL_CATEGORIES):
    if "category" in prim_f.columns:
        prim_f = prim_f[prim_f["category"].isin(category_filter)]
    if "category" in so_f.columns:
        so_f   = so_f[so_f["category"].isin(category_filter)]

# ── Apply period filter ───────────────────────────────
today = pd.Timestamp("2026-05-25")
cutoff_map = {
    "Last month":   (today.replace(day=1) - pd.DateOffset(months=1)),
    "Last quarter": (today - pd.DateOffset(months=3)),
}
if period == "Custom range":
    if custom_range and len(custom_range) == 2:
        start_ts, end_ts = pd.Timestamp(custom_range[0]), pd.Timestamp(custom_range[1])
        prim_f  = prim_f[(prim_f["week"] >= start_ts) & (prim_f["week"] <= end_ts)]
        so_f    = so_f[(so_f["week"] >= start_ts) & (so_f["week"] <= end_ts)]
        stock_f = stock_f[(stock_f["week"] >= start_ts) & (stock_f["week"] <= end_ts)]
elif period != "All data":
    cutoff  = cutoff_map[period]
    prim_f  = prim_f[prim_f["week"] >= cutoff]
    so_f    = so_f[so_f["week"] >= cutoff]
    stock_f = stock_f[stock_f["week"] >= cutoff]


# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([0.06, 0.94])
with col_title:
    st.markdown("<h1>Niamito · Business Intelligence</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:{MID}; font-size:12px; margin-top:-6px;'>"
        f"{'Demo data — upload your Master Tables to see live numbers' if demo_mode else 'Live data'}"
        f"  ·  Markets: {', '.join(market_filter) if market_filter else 'none'}"
        f"  ·  Period: {period}</p>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Marketing",
    "Value Leakage",
    "SKU Performance",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── KPI row ───────────────────────────────────────────
    total_so_units = so_f["bottles_sold"].sum() if not so_f.empty and "bottles_sold" in so_f.columns else 0
    total_mkt_spd  = mkt_f["total_spend"].sum() if not mkt_f.empty else 0
    blended_roas   = (mkt_f["attributed_sales"].sum() / max(mkt_f["total_spend"].sum(), 1)) if not mkt_f.empty else 0
    total_gross    = prim_f["gross_revenue"].sum() if not prim_f.empty else 0
    total_net_rev  = prim_f["net_revenue"].sum() if not prim_f.empty else 0
    prim_bottles   = prim_f["bottles"].sum() if not prim_f.empty else 0
    sellthrough_pct = total_so_units / max(prim_bottles, 1) * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Retail Units Sold (sell-out)", f"{total_so_units:,.0f}",
              delta=f"{sellthrough_pct:.0f}% sell-through rate")
    k2.metric("Gross Revenue (sell-in)",      f"\u20ac{total_gross:,.0f}",
              delta=f"Net \u20ac{total_net_rev:,.0f}")
    k3.metric("Marketing Spend",              f"\u20ac{total_mkt_spd:,.0f}")
    k4.metric("Blended ROAS",                 f"{blended_roas:.1f}\u00d7",
              delta="No ROAS data in real file" if not demo_mode and blended_roas == 0 else None)

    st.markdown("")

    # ── YTD Bottles cards (secondary sell-out) ────────────────
    today_ts   = pd.Timestamp("today").normalize()
    jan1_2026  = pd.Timestamp("2026-01-01")
    jan1_2025  = pd.Timestamp("2025-01-01")
    # Same calendar date in 2025
    same_day_2025 = today_ts.replace(year=2025)

    if not so_df.empty and "bottles_sold" in so_df.columns and "week" in so_df.columns:
        ytd_2026 = int(so_df[
            (so_df["week"] >= jan1_2026) & (so_df["week"] <= today_ts)
        ]["bottles_sold"].sum())
        ytd_2025 = int(so_df[
            (so_df["week"] >= jan1_2025) & (so_df["week"] <= same_day_2025)
        ]["bottles_sold"].sum())
        yoy_delta = ytd_2026 - ytd_2025
        yoy_pct   = f"{yoy_delta/max(ytd_2025,1)*100:+.1f}% vs same period 2025"

        kytd1, kytd2, kytd3 = st.columns([1, 1, 2])
        kytd1.metric(
            "🛒 Retail Bottles YTD 2026",
            f"{ytd_2026:,}",
            delta=yoy_pct,
        )
        kytd2.metric(
            "🛒 Retail Bottles YTD 2025",
            f"{ytd_2025:,}",
        )
        # Mini sparkline of weekly retail units this year
        with kytd3:
            weekly_ytd = so_df[
                (so_df["week"] >= jan1_2026) & (so_df["week"] <= today_ts)
            ].groupby("week")["bottles_sold"].sum().reset_index()
            if not weekly_ytd.empty:
                fig_ytd = go.Figure(go.Scatter(
                    x=weekly_ytd["week"], y=weekly_ytd["bottles_sold"],
                    fill="tozeroy", mode="lines",
                    line=dict(color=GREEN, width=2),
                    fillcolor=hex_alpha(GREEN, 0.25),
                ))
                fig_ytd.update_layout(
                    height=80, margin=dict(l=0,r=0,t=4,b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                )
                st.plotly_chart(fig_ytd, use_container_width=True)
    st.markdown("")

    # ── Primary sales trend by product category (stacked area) ───────────────
    c_left, c_right = st.columns([0.6, 0.4])

    with c_left:
        if not prim_f.empty and "category" in prim_f.columns:
            cat_weekly = prim_f.groupby(["week", "category"]).agg(
                bottles=("bottles", "sum"),
                revenue=("gross_revenue", "sum"),
            ).reset_index()
            y_col = "bottles" if metric_mode == "Bottles sold" else "revenue"
            chart_title = (
                "Primary Sales by Product Category (weekly)"
                if metric_mode == "Bottles sold"
                else "Primary Revenue by Product Category (weekly)"
            )
            fig = go.Figure()
            for cat in ALL_CATEGORIES:
                d = cat_weekly[cat_weekly["category"] == cat]
                if d.empty:
                    continue
                color = CATEGORY_COLORS.get(cat, BROWN)
                hover = (
                    f"<b>{cat}</b><br>Week: %{{x|%d %b}}<br>%{{y:,}} bottles<extra></extra>"
                    if metric_mode == "Bottles sold"
                    else f"<b>{cat}</b><br>Week: %{{x|%d %b}}<br>\u20ac%{{y:,.0f}}<extra></extra>"
                )
                fig.add_trace(go.Scatter(
                    x=d["week"], y=d[y_col],
                    mode="lines",
                    name=cat,
                    stackgroup="one",
                    line=dict(color=color, width=1.5),
                    fillcolor=hex_alpha(color, 0.55),
                    hovertemplate=hover,
                ))
            layout = base_layout(chart_title, height=320)
            if metric_mode != "Bottles sold":
                layout["yaxis"]["tickprefix"] = "\u20ac"
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No primary sales data to display.")

    with c_right:
        # Spend by channel donut
        ch_spend = mkt_f.groupby("channel")["total_spend"].sum().reset_index() if not mkt_f.empty else pd.DataFrame()
        if not ch_spend.empty:
            ch_spend = ch_spend[ch_spend["total_spend"] > 0].sort_values("total_spend", ascending=False)
        palette = [BROWN, LAVEN, GREEN, CORAL, YELLOW, MID, "#c8b89a"]

        fig2 = go.Figure(go.Pie(
            labels=ch_spend["channel"] if not ch_spend.empty else [],
            values=ch_spend["total_spend"] if not ch_spend.empty else [],
            hole=0.52,
            marker=dict(colors=palette[:len(ch_spend)], line=dict(color=CREAM, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>\u20ac%{value:,.0f}<extra></extra>",
        ))
        layout2 = base_layout("Marketing Spend by Channel", height=320, legend_below=False)
        layout2["legend"]["orientation"] = "v"
        layout2["legend"]["x"] = 1.0
        layout2["legend"]["y"] = 0.5
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Primary revenue / bottles trend ──────────────────
    if not prim_f.empty:
        prim_weekly = prim_f.groupby("week").agg(
            gross=("gross_revenue", "sum"),
            net=("net_revenue", "sum"),
            bottles=("bottles", "sum"),
        ).reset_index()

        fig3 = go.Figure()
        if metric_mode == "Bottles sold":
            fig3.add_trace(go.Bar(
                x=prim_weekly["week"], y=prim_weekly["bottles"],
                name="Bottles Shipped", marker_color=LAVEN,
                hovertemplate="Bottles shipped: %{y:,}<extra></extra>",
            ))
            layout3 = base_layout("Primary Sales: Bottles Shipped (weekly, all markets)", height=280)
        else:
            fig3.add_trace(go.Bar(
                x=prim_weekly["week"], y=prim_weekly["gross"],
                name="Gross Revenue", marker_color=LAVEN, opacity=0.7,
                hovertemplate="Gross: \u20ac%{y:,.0f}<extra></extra>",
            ))
            fig3.add_trace(go.Bar(
                x=prim_weekly["week"], y=prim_weekly["net"],
                name="Net Revenue", marker_color=BROWN,
                hovertemplate="Net: \u20ac%{y:,.0f}<extra></extra>",
            ))
            layout3 = base_layout("Primary Sales: Gross vs Net Revenue (weekly, all markets)", height=280)
            layout3["yaxis"]["tickprefix"] = "\u20ac"
            layout3["barmode"] = "overlay"
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · MARKETING
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    # ── KPI row ───────────────────────────────────────────────────────────────
    total_spend_mkt   = mkt_f["total_spend"].sum() if not mkt_f.empty else 0
    n_campaigns       = len(mkt_f) if not mkt_f.empty else 0
    top_channel       = (mkt_f.groupby("channel")["total_spend"].sum().idxmax()
                         if not mkt_f.empty and mkt_f["total_spend"].sum() > 0 else "—")
    n_influencers     = mkt_f["influencer"].notna().sum() if not mkt_f.empty and "influencer" in mkt_f.columns else 0
    avg_cpm           = total_spend_mkt / max(
        mkt_f["reach"].sum() if not mkt_f.empty and "reach" in mkt_f.columns else 0, 1
    ) * 1000

    mk1, mk2, mk3, mk4, mk5 = st.columns(5)
    mk1.metric("Total Marketing Spend", f"\u20ac{total_spend_mkt:,.0f}")
    mk2.metric("Campaigns Tracked",     f"{n_campaigns}")
    mk3.metric("Top Channel",           top_channel)
    mk4.metric("Influencer Activations", f"{n_influencers}")
    mk5.metric("Est. CPM",              f"\u20ac{avg_cpm:.2f}" if avg_cpm < 1000 else "—",
               help="Cost per 1,000 estimated impressions (influencer reach only)")

    st.markdown("<hr style='margin:8px 0 16px'>", unsafe_allow_html=True)

    if mkt_f.empty:
        st.info("No marketing data available.")
    else:
        # ── Row 1: Spend by channel + Monthly spend trend ─────────────────────
        col_ch, col_mo = st.columns(2)

        with col_ch:
            ch_spend = mkt_f.groupby("channel")["total_spend"].sum().reset_index()
            ch_spend = ch_spend[ch_spend["total_spend"] > 0].sort_values("total_spend", ascending=True)
            ch_palette = [BROWN, LAVEN, GREEN, CORAL, YELLOW, MID, "#c8b89a"]
            fig_ch = go.Figure(go.Bar(
                x=ch_spend["total_spend"],
                y=ch_spend["channel"],
                orientation="h",
                marker=dict(color=ch_palette[:len(ch_spend)],
                            line=dict(color=CREAM, width=1)),
                text=[f"\u20ac{v:,.0f}" for v in ch_spend["total_spend"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>\u20ac%{x:,.0f}<extra></extra>",
            ))
            l_ch = base_layout("Spend by Channel", height=300)
            l_ch["xaxis"]["tickprefix"] = "\u20ac"
            l_ch["margin"]["l"] = 130
            fig_ch.update_layout(**l_ch)
            st.plotly_chart(fig_ch, use_container_width=True)

        with col_mo:
            mkt_f2 = mkt_f.copy()
            mkt_f2["month_dt"] = pd.to_datetime(mkt_f2["start"], errors="coerce").dt.to_period("M")
            monthly = mkt_f2.groupby(["month_dt","channel"])["total_spend"].sum().reset_index()
            monthly["month_str"] = monthly["month_dt"].astype(str)
            monthly = monthly.sort_values("month_str")

            fig_mo = go.Figure()
            for idx, ch in enumerate(monthly["channel"].unique()):
                d = monthly[monthly["channel"] == ch]
                fig_mo.add_trace(go.Bar(
                    x=d["month_str"], y=d["total_spend"],
                    name=ch,
                    marker_color=ch_palette[idx % len(ch_palette)],
                    hovertemplate=f"<b>{ch}</b><br>%{{x}}<br>\u20ac%{{y:,.0f}}<extra></extra>",
                ))
            l_mo = base_layout("Monthly Spend by Channel", height=300)
            l_mo["barmode"] = "stack"
            l_mo["yaxis"]["tickprefix"] = "\u20ac"
            l_mo["xaxis"]["tickangle"] = -30
            fig_mo.update_layout(**l_mo)
            st.plotly_chart(fig_mo, use_container_width=True)

        # ── Row 2: Channel mix donut + Campaign count heatmap ─────────────────
        col_donut, col_heat = st.columns(2)

        with col_donut:
            fig_donut = go.Figure(go.Pie(
                labels=ch_spend["channel"],
                values=ch_spend["total_spend"],
                hole=0.55,
                marker=dict(colors=ch_palette[:len(ch_spend)],
                            line=dict(color=CREAM, width=2)),
                textinfo="percent+label",
                hovertemplate="<b>%{label}</b><br>\u20ac%{value:,.0f}  (%{percent})<extra></extra>",
            ))
            l_donut = base_layout("Spend Mix", height=300, legend_below=False)
            l_donut["showlegend"] = False
            fig_donut.update_layout(**l_donut)
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_heat:
            # Campaign count heatmap: month × channel
            mkt_f3 = mkt_f.copy()
            mkt_f3["month_str"] = pd.to_datetime(mkt_f3["start"], errors="coerce").dt.to_period("M").astype(str)
            heat_data = mkt_f3.groupby(["channel","month_str"]).size().unstack(fill_value=0)
            heat_data = heat_data.sort_index()
            if not heat_data.empty:
                fig_heat = go.Figure(go.Heatmap(
                    z=heat_data.values,
                    x=heat_data.columns.tolist(),
                    y=heat_data.index.tolist(),
                    colorscale=[[0, CREAM], [0.3, LAVEN], [1.0, BROWN]],
                    text=[[str(v) if v > 0 else "" for v in row] for row in heat_data.values],
                    texttemplate="%{text}",
                    hovertemplate="<b>%{y}</b><br>%{x}: %{z} campaigns<extra></extra>",
                    showscale=False,
                ))
                l_heat = base_layout("Campaign Activity (count by month)", height=300)
                l_heat.pop("xaxis", None)
                l_heat.pop("yaxis", None)
                l_heat["margin"]["l"] = 130
                l_heat["margin"]["b"] = 60
                fig_heat.update_layout(**l_heat)
                st.plotly_chart(fig_heat, use_container_width=True)

        # ── Influencer tracker ────────────────────────────────────────────────
        if "influencer" in mkt_f.columns:
            inf_df = mkt_f[mkt_f["influencer"].notna()].copy()
            if not inf_df.empty:
                st.markdown("<h2>Influencer Activations</h2>", unsafe_allow_html=True)
                st.markdown(
                    f"<p style='font-size:11px;color:{MID};margin-top:-8px;'>"
                    f"{len(inf_df)} activations · ROAS pending sell-out linkage</p>",
                    unsafe_allow_html=True,
                )
                max_cols = min(len(inf_df), 4)
                rows_needed = (len(inf_df) + max_cols - 1) // max_cols
                for row_i in range(rows_needed):
                    row_data = inf_df.iloc[row_i*max_cols:(row_i+1)*max_cols]
                    cols_inf = st.columns(len(row_data))
                    for i, (_, row) in enumerate(row_data.iterrows()):
                        with cols_inf[i]:
                            reach    = row.get("reach") or 0
                            cpm      = round(row["media_spend"] / max(reach, 1) * 1000, 2) if reach else 0
                            roas_val = row.get("roas")
                            roas_str = f"{roas_val:.1f}\u00d7" if pd.notna(roas_val) else "pending"
                            roas_col = GREEN if (pd.notna(roas_val) and roas_val >= 2) else (YELLOW if pd.notna(roas_val) else MID)
                            reach_str = f"{int(reach):,}" if reach else "—"
                            spend = row["media_spend"]
                            # Colour band based on spend size
                            border_col = BROWN if spend > 500 else LAVEN
                            st.markdown(f"""
                            <div style='background:{CREAM}; border-left:4px solid {border_col};
                                        border-radius:10px; padding:12px 14px; margin-bottom:8px;
                                        box-shadow:0 1px 4px rgba(0,0,0,0.07);'>
                                <p style='font-size:13px; font-weight:700; margin:0 0 2px; color:{BROWN};'>
                                    {row["influencer"]}</p>
                                <p style='font-size:10px; color:{MID}; margin:0 0 8px;
                                   text-transform:uppercase; letter-spacing:0.5px;'>
                                   {row["market"]} · {row.get("channel","—")}</p>
                                <div style='display:grid; grid-template-columns:1fr 1fr; gap:2px 10px; font-size:12px;'>
                                  <span>👁 Reach</span><b>{reach_str}</b>
                                  <span>💶 Spend</span><b>\u20ac{spend:,.0f}</b>
                                  <span>📈 ROAS</span><b style='color:{roas_col}'>{roas_str}</b>
                                  <span>📊 CPM</span><b>\u20ac{cpm:.2f}</b>
                                </div>
                                <p style='margin:8px 0 0; font-size:10px; color:{MID};'>
                                   {row["start"]} → {row["end"]}</p>
                            </div>
                            """, unsafe_allow_html=True)

        # ── Campaign timeline (Gantt-style) ───────────────────────────────────
        st.markdown("<h2>Campaign Timeline</h2>", unsafe_allow_html=True)

        mkt_gant = mkt_f.copy()
        mkt_gant["start_dt"] = pd.to_datetime(mkt_gant["start"], errors="coerce")
        mkt_gant["end_dt"]   = pd.to_datetime(mkt_gant["end"],   errors="coerce")
        mkt_gant = mkt_gant.dropna(subset=["start_dt","end_dt"])

        if not mkt_gant.empty:
            # Group by channel and show one bar per campaign coloured by channel
            ch_color_map = dict(zip(
                mkt_gant["channel"].unique(),
                ch_palette[:mkt_gant["channel"].nunique()]
            ))
            # Aggregate monthly campaign counts per channel for a simple bar Gantt substitute
            mkt_gant["month_str"] = mkt_gant["start_dt"].dt.to_period("M").astype(str)
            gantt_monthly = (mkt_gant.groupby(["month_str","channel"])
                             .agg(count=("name","count"), spend=("total_spend","sum"))
                             .reset_index().sort_values("month_str"))

            fig_gantt = go.Figure()
            for ch in gantt_monthly["channel"].unique():
                d = gantt_monthly[gantt_monthly["channel"] == ch]
                fig_gantt.add_trace(go.Scatter(
                    x=d["month_str"],
                    y=d["spend"],
                    mode="lines+markers",
                    name=ch,
                    line=dict(color=ch_color_map.get(ch, BROWN), width=2),
                    marker=dict(size=d["count"]*3, sizemode="diameter",
                                color=ch_color_map.get(ch, BROWN)),
                    hovertemplate=(f"<b>{ch}</b><br>%{{x}}<br>"
                                   "Campaigns: %{marker.size:.0f}<br>"
                                   "Spend: \u20ac%{y:,.0f}<extra></extra>"),
                ))
            l_gantt = base_layout("Monthly Spend Pulse by Channel (bubble = # campaigns)", height=320)
            l_gantt["yaxis"]["tickprefix"] = "\u20ac"
            l_gantt["xaxis"]["tickangle"] = -30
            fig_gantt.update_layout(**l_gantt)
            st.plotly_chart(fig_gantt, use_container_width=True)

        # ── All campaigns table ───────────────────────────────────────────────
        st.markdown("<h2>All Campaigns</h2>", unsafe_allow_html=True)
        tbl_cols = [c for c in ["id","name","channel","market","start","end","total_spend","roas"] if c in mkt_f.columns]
        tbl = mkt_f[tbl_cols].copy()
        rename_map = {
            "id": "ID", "name": "Campaign", "channel": "Channel",
            "market": "Mkt", "start": "Start", "end": "End",
            "total_spend": "Spend (\u20ac)", "roas": "ROAS",
        }
        tbl = tbl.rename(columns=rename_map)
        if "Spend (\u20ac)" in tbl.columns:
            tbl["Spend (\u20ac)"] = tbl["Spend (\u20ac)"].apply(lambda x: f"\u20ac{x:,.0f}")
        if "ROAS" in tbl.columns:
            tbl["ROAS"] = tbl["ROAS"].apply(lambda x: f"{x:.1f}\u00d7" if pd.notna(x) else "—")
        st.dataframe(tbl, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · VALUE LEAKAGE WATERFALL
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<h2>Value Leakage — Revenue to Gross Margin</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:12px; color:{MID};'>"
        "Gross revenue minus costs gives the gross margin. "
        "Each bar below shows how much of the top line survives after each deduction.</p>",
        unsafe_allow_html=True,
    )

    wf_mkt = st.radio("Market:", options=[m for m in ["ALL","SI","HR","DE"]
                                           if m == "ALL" or m in (market_filter or ["SI","HR","DE"])],
                       horizontal=True, key="wf_mkt")

    p_data = prim_f if wf_mkt == "ALL" else (
        prim_f[prim_f["market"] == wf_mkt] if not prim_f.empty else prim_f)
    m_data = mkt_f if wf_mkt == "ALL" else (
        mkt_f[mkt_f["market"].isin([wf_mkt, "ALL"])] if not mkt_f.empty else mkt_f)

    gross      = p_data["gross_revenue"].sum() if not p_data.empty else 0
    trade_disc = p_data["trade_discount"].sum() if not p_data.empty else 0
    mkt_spend  = m_data["total_spend"].sum() if not m_data.empty else 0

    # Pull expense totals
    prod_cost = exp_df["production_cost"].sum() if not exp_df.empty else 0
    logistics = exp_df["logistics"].sum()        if not exp_df.empty else 0
    mktg_promo= exp_df["marketing_promo"].sum()  if not exp_df.empty else 0
    total_exp = prod_cost + logistics + mktg_promo

    # Net = gross minus all deductions
    gross_margin = gross - prod_cost - logistics - mktg_promo - trade_disc

    # ── Waterfall ─────────────────────────────────────────────────────────────
    if total_exp > 0:
        wf_labels  = ["Gross Revenue", "Production Cost", "Logistics", "Mktg & Promo", "Trade Discounts", "Gross Margin"]
        wf_measure = ["absolute",       "relative",        "relative",  "relative",      "relative",        "total"]
        wf_values  = [gross,            -prod_cost,        -logistics,  -mktg_promo,     -trade_disc,       gross_margin]
    else:
        wf_labels  = ["Gross Revenue", "Trade Discounts", "Marketing Spend", "Gross Margin"]
        wf_measure = ["absolute",       "relative",        "relative",        "total"]
        wf_values  = [gross,            -trade_disc,       -mkt_spend,        gross - trade_disc - mkt_spend]
        gross_margin = gross - trade_disc - mkt_spend

    fig_wf = go.Figure(go.Waterfall(
        name="Value Leakage",
        orientation="v",
        measure=wf_measure,
        x=wf_labels,
        y=wf_values,
        text=[f"\u20ac{abs(v):,.0f}" for v in wf_values],
        textposition="outside",
        connector=dict(line=dict(color=MID, width=1, dash="dot")),
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=CORAL)),
        totals=dict(marker=dict(color=BROWN)),
        hovertemplate="<b>%{x}</b><br>\u20ac%{y:,.0f}<extra></extra>",
    ))
    margin_pct = gross_margin / max(gross, 1) * 100
    layout_wf = base_layout(
        f"P&L Waterfall — {wf_mkt}  (Gross Margin: {margin_pct:.1f}%)",
        height=400,
    )
    layout_wf["yaxis"]["tickprefix"] = "\u20ac"
    fig_wf.update_layout(**layout_wf)
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Summary table ─────────────────────────────────────────────────────────
    wf_tbl = pd.DataFrame({
        "Line": wf_labels,
        "Amount (\u20ac)": [f"\u20ac{abs(v):,.0f}" for v in wf_values],
        "% of Gross":  [f"{abs(v)/max(gross,1)*100:.1f}%" for v in wf_values],
        "Cumulative (\u20ac)": [
            f"\u20ac{(gross + sum(wf_values[1:i+1])):,.0f}" if i > 0 else f"\u20ac{gross:,.0f}"
            for i in range(len(wf_values))
        ],
    })
    st.dataframe(wf_tbl, use_container_width=True, hide_index=True)

    # ── Monthly P&L timeline (only if Expenses data exists) ───────────────────
    if not exp_df.empty:
        st.markdown("<h2>Monthly Cost vs Revenue Timeline</h2>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='font-size:12px; color:{MID};'>"
            "Stacked cost bars vs primary revenue. Shows where costs are heaviest relative to revenue.</p>",
            unsafe_allow_html=True,
        )

        MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        cost_monthly = exp_df.groupby("month").agg(
            production_cost=("production_cost","sum"),
            logistics=("logistics","sum"),
            marketing_promo=("marketing_promo","sum"),
        ).reset_index()
        # Sort months correctly
        cost_monthly["month_idx"] = cost_monthly["month"].apply(
            lambda m: MONTH_ORDER.index(m[:3]) if m[:3] in MONTH_ORDER else 99
        )
        cost_monthly = cost_monthly.sort_values("month_idx")
        cost_monthly["total_cost"] = (
            cost_monthly["production_cost"] + cost_monthly["logistics"] + cost_monthly["marketing_promo"]
        )

        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Bar(
            x=cost_monthly["month"], y=cost_monthly["production_cost"],
            name="Production", marker_color=BROWN, opacity=0.85,
            hovertemplate="Production: \u20ac%{y:,.0f}<extra></extra>",
        ))
        fig_pnl.add_trace(go.Bar(
            x=cost_monthly["month"], y=cost_monthly["logistics"],
            name="Logistics", marker_color=LAVEN, opacity=0.85,
            hovertemplate="Logistics: \u20ac%{y:,.0f}<extra></extra>",
        ))
        fig_pnl.add_trace(go.Bar(
            x=cost_monthly["month"], y=cost_monthly["marketing_promo"],
            name="Mktg & Promo", marker_color=GREEN, opacity=0.85,
            hovertemplate="Mktg & Promo: \u20ac%{y:,.0f}<extra></extra>",
        ))
        fig_pnl.add_trace(go.Scatter(
            x=cost_monthly["month"], y=cost_monthly["total_cost"],
            name="Total Cost", mode="lines+markers",
            line=dict(color=CORAL, width=2, dash="dot"),
            marker=dict(size=7, color=CORAL),
            hovertemplate="Total Cost: \u20ac%{y:,.0f}<extra></extra>",
        ))
        l_pnl = base_layout("Monthly Cost Breakdown (Expenses sheet)", height=360)
        l_pnl["barmode"] = "stack"
        l_pnl["yaxis"]["tickprefix"] = "\u20ac"
        fig_pnl.update_layout(**l_pnl)
        st.plotly_chart(fig_pnl, use_container_width=True)

        # Cost by product line
        st.markdown("<h2>Cost Structure by Product Line</h2>", unsafe_allow_html=True)
        cost_by_line = exp_df.groupby("product_line").agg(
            production_cost=("production_cost","sum"),
            logistics=("logistics","sum"),
            marketing_promo=("marketing_promo","sum"),
        ).reset_index()
        cost_by_line["total_cost"] = (
            cost_by_line["production_cost"] + cost_by_line["logistics"] + cost_by_line["marketing_promo"]
        )

        fig_pl = go.Figure()
        fig_pl.add_trace(go.Bar(x=cost_by_line["product_line"], y=cost_by_line["production_cost"],
                                name="Production", marker_color=BROWN,
                                hovertemplate="<b>%{x}</b><br>Production: \u20ac%{y:,.0f}<extra></extra>"))
        fig_pl.add_trace(go.Bar(x=cost_by_line["product_line"], y=cost_by_line["logistics"],
                                name="Logistics", marker_color=LAVEN,
                                hovertemplate="<b>%{x}</b><br>Logistics: \u20ac%{y:,.0f}<extra></extra>"))
        fig_pl.add_trace(go.Bar(x=cost_by_line["product_line"], y=cost_by_line["marketing_promo"],
                                name="Mktg & Promo", marker_color=GREEN,
                                hovertemplate="<b>%{x}</b><br>Mktg & Promo: \u20ac%{y:,.0f}<extra></extra>"))
        l_pl = base_layout("Cost by Product Line", height=340)
        l_pl["barmode"] = "group"
        l_pl["yaxis"]["tickprefix"] = "\u20ac"
        fig_pl.update_layout(**l_pl)
        st.plotly_chart(fig_pl, use_container_width=True)

        st.dataframe(cost_by_line.rename(columns={
            "product_line":"Product Line",
            "production_cost":"Production (\u20ac)",
            "logistics":"Logistics (\u20ac)",
            "marketing_promo":"Mktg & Promo (\u20ac)",
            "total_cost":"Total Cost (\u20ac)",
        }), use_container_width=True, hide_index=True)

    # ── Net Margin by Market table ────────────────────────────────────────────
    st.markdown("<h2>Net Margin by Market</h2>", unsafe_allow_html=True)
    margin_rows = []
    for mkt in ["SI", "HR", "DE"]:
        if mkt not in (market_filter or ["SI","HR","DE"]):
            continue
        pd_ = prim_f[prim_f["market"] == mkt] if not prim_f.empty else pd.DataFrame()
        md_ = mkt_f[mkt_f["market"].isin([mkt, "ALL"])] if not mkt_f.empty else pd.DataFrame()
        g   = pd_["gross_revenue"].sum() if not pd_.empty else 0
        td  = pd_["trade_discount"].sum() if not pd_.empty else 0
        ms  = md_["total_spend"].sum() if not md_.empty else 0
        nr  = g - td - ms
        margin_rows.append({
            "Market":        mkt,
            "Gross (\u20ac)":     g,
            "Trade Disc (\u20ac)":td,
            "Mktg Spend (\u20ac)":ms,
            "Net Rev (\u20ac)":   nr,
            "Net Margin %":  f"{nr/max(g,1)*100:.1f}%",
        })
    if margin_rows:
        margin_df = pd.DataFrame(margin_rows)
        for col in ["Gross (\u20ac)","Trade Disc (\u20ac)","Mktg Spend (\u20ac)","Net Rev (\u20ac)"]:
            margin_df[col] = margin_df[col].apply(lambda x: f"\u20ac{x:,.0f}")
        st.dataframe(margin_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · SKU PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab4:

    # ────────────────────────────────────────────────────────────────────────
    # SECTION A: Primary Sell-In
    # ────────────────────────────────────────────────────────────────────────
    st.markdown("<h2>Primary Sell-In Performance</h2>", unsafe_allow_html=True)
    if len(category_filter) < len(ALL_CATEGORIES):
        st.caption("ℹ️ Showing all categories here — category filter applies to Overview charts only.")

    if not prim_f_nokcat.empty:
        _sort_col_p = "bottles" if metric_mode == "Bottles sold" else "gross"
        sku_prim = prim_f_nokcat.groupby("sku_id").agg(
            sku_name=("sku_name", "first"),
            bottles=("bottles", "sum"),
            gross=("gross_revenue", "sum"),
            net=("net_revenue", "sum"),
        ).reset_index().sort_values(_sort_col_p, ascending=False)

        c_sku1, c_sku2 = st.columns(2)

        with c_sku1:
            _sku_y     = "bottles" if metric_mode == "Bottles sold" else "gross"
            _sku_fmt   = (lambda v: f"{v:,.0f}") if metric_mode == "Bottles sold" else (lambda v: f"\u20ac{v:,.0f}")
            _sku_hover = ("<b>%{x}</b><br>%{y:,} bottles<extra></extra>"
                          if metric_mode == "Bottles sold"
                          else "<b>%{x}</b><br>\u20ac%{y:,.0f}<extra></extra>")
            _sku_title = ("Bottles by SKU (primary)" if metric_mode == "Bottles sold"
                          else "Gross Revenue by SKU (primary)")
            sku_colors_p = [CATEGORY_COLORS.get(get_product_category(n), BROWN) for n in sku_prim["sku_name"]]
            fig_sku = go.Figure(go.Bar(
                x=sku_prim["sku_name"],
                y=sku_prim[_sku_y],
                marker=dict(color=sku_colors_p),
                text=[_sku_fmt(v) for v in sku_prim[_sku_y]],
                textposition="outside",
                hovertemplate=_sku_hover,
            ))
            layout_sku = base_layout(_sku_title, height=340)
            layout_sku["xaxis"]["tickangle"] = -20
            if metric_mode != "Bottles sold":
                layout_sku["yaxis"]["tickprefix"] = "\u20ac"
            fig_sku.update_layout(**layout_sku)
            st.plotly_chart(fig_sku, use_container_width=True)

        with c_sku2:
            _pie_vals  = sku_prim["bottles"] if metric_mode == "Bottles sold" else sku_prim["gross"]
            _pie_hover = ("<b>%{label}</b><br>%{value:,} bottles<extra></extra>"
                          if metric_mode == "Bottles sold"
                          else "<b>%{label}</b><br>\u20ac%{value:,.0f}<extra></extra>")
            _pie_title = "Bottle Share (primary)" if metric_mode == "Bottles sold" else "Revenue Share (primary)"
            fig_sku_p = go.Figure(go.Pie(
                labels=sku_prim["sku_name"],
                values=_pie_vals,
                hole=0.5,
                marker=dict(colors=sku_colors_p, line=dict(color=CREAM, width=2)),
                textinfo="percent",
                hovertemplate=_pie_hover,
            ))
            l_sku_p = base_layout(_pie_title, height=340, legend_below=False)
            l_sku_p["legend"]["x"] = 1.0
            l_sku_p["legend"]["y"] = 0.5
            fig_sku_p.update_layout(**l_sku_p)
            st.plotly_chart(fig_sku_p, use_container_width=True)

        # Primary SKU trend
        _trend_col_p = "bottles"
        _trend_title_p = "Weekly Primary Sales by SKU — Bottles (all markets)"
        sku_trend_p = prim_f_nokcat.groupby(["week", "sku_id"])["bottles"].sum().reset_index()
        fig_tp = go.Figure()
        for sku in sku_prim["sku_id"]:
            d    = sku_trend_p[sku_trend_p["sku_id"] == sku]
            name = sku_prim.loc[sku_prim["sku_id"] == sku, "sku_name"].iloc[0] if not sku_prim[sku_prim["sku_id"]==sku].empty else sku
            clr  = CATEGORY_COLORS.get(get_product_category(name), BROWN)
            fig_tp.add_trace(go.Scatter(
                x=d["week"], y=d["bottles"],
                mode="lines",
                name=name,
                line=dict(color=clr, width=2),
                hovertemplate=f"<b>{name}</b><br>%{{x|%d %b}}: %{{y:,}} bottles<extra></extra>",
            ))
        layout_tp = base_layout(_trend_title_p, height=300)
        fig_tp.update_layout(**layout_tp)
        st.plotly_chart(fig_tp, use_container_width=True)

        # Primary SKU summary table
        st.markdown("<h2>Primary SKU Summary</h2>", unsafe_allow_html=True)
        out_p = sku_prim[["sku_name","bottles","gross","net"]].copy()
        out_p.columns = ["SKU", "Bottles (primary)", "Gross (\u20ac)", "Net (\u20ac)"]
        for col in ["Gross (\u20ac)", "Net (\u20ac)"]:
            out_p[col] = out_p[col].apply(lambda x: f"\u20ac{x:,.0f}")
        out_p["Bottles (primary)"] = out_p["Bottles (primary)"].apply(lambda x: f"{int(x):,}")
        st.dataframe(out_p, use_container_width=True, hide_index=True)
    else:
        st.info("No primary sales data available.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # SECTION B: Retail Sell-Out

    # ────────────────────────────────────────────────────────────────────────
    st.markdown("<h2>Retail Sell-Out</h2>", unsafe_allow_html=True)

    if so_f.empty or "bottles_sold" not in so_f.columns or so_f["bottles_sold"].sum() == 0:
        st.info("No retail sell-out data available. Upload the Master Tables file with Secondary Sales to see retail data.")
    else:
        # Top 20 retailers by units
        if "retailer" in so_f.columns:
            top_ret = so_f.groupby("retailer")["bottles_sold"].sum().reset_index()
            top_ret = top_ret.sort_values("bottles_sold", ascending=False).head(20)
            fig_ret = go.Figure(go.Bar(
                x=top_ret["bottles_sold"],
                y=top_ret["retailer"],
                orientation="h",
                marker_color=GREEN,
                text=[f"{v:,}" for v in top_ret["bottles_sold"]],
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x:,} units<extra></extra>",
            ))
            l_ret = base_layout("Top 20 Retailers by Units Sold", height=max(300, len(top_ret) * 32 + 80))
            l_ret["margin"]["l"] = 140
            fig_ret.update_layout(**l_ret)
            st.plotly_chart(fig_ret, use_container_width=True)

        # Secondary sales trend by product
        so_sku_weekly = so_f.groupby(["week", "sku_name"])["bottles_sold"].sum().reset_index()
        top_so_skus = so_f.groupby("sku_name")["bottles_sold"].sum().sort_values(ascending=False).index.tolist()

        fig_so_t = go.Figure()
        for sku_nm in top_so_skus:
            d = so_sku_weekly[so_sku_weekly["sku_name"] == sku_nm]
            clr = CATEGORY_COLORS.get(get_product_category(sku_nm), BROWN)
            fig_so_t.add_trace(go.Scatter(
                x=d["week"], y=d["bottles_sold"],
                mode="lines",
                name=sku_nm,
                line=dict(color=clr, width=2),
                hovertemplate=f"<b>{sku_nm}</b><br>%{{x|%d %b}}: %{{y:,}} units<extra></extra>",
            ))
        layout_so_t = base_layout("Weekly Retail Units by SKU (Secondary Sales)", height=320)
        fig_so_t.update_layout(**layout_so_t)
        st.plotly_chart(fig_so_t, use_container_width=True)

        # SKU x Market heatmap (secondary)
        st.markdown("<h2>Retail Units by SKU and Market</h2>", unsafe_allow_html=True)
        pivot_so = so_f.groupby(["sku_name", "market"])["bottles_sold"].sum().unstack(fill_value=0)
        pivot_so = pivot_so.round(0)
        fig_heat_so = go.Figure(go.Heatmap(
            z=pivot_so.values,
            x=pivot_so.columns.tolist(),
            y=pivot_so.index.tolist(),
            colorscale=[[0, CREAM], [0.4, LAVEN], [1.0, BROWN]],
            text=[[f"{v:,.0f}" for v in row] for row in pivot_so.values],
            texttemplate="%{text}",
            hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
            showscale=True,
            colorbar=dict(tickfont=dict(color=BROWN, size=10)),
        ))
        layout_heat_so = base_layout("Retail Units — SKU x Market", height=max(250, len(pivot_so) * 28 + 80))
        layout_heat_so.pop("xaxis", None)
        layout_heat_so.pop("yaxis", None)
        layout_heat_so["margin"]["l"] = 200
        fig_heat_so.update_layout(**layout_heat_so)
        st.plotly_chart(fig_heat_so, use_container_width=True)

        # Summary table
        so_sku_tbl = so_f.groupby("sku_name").agg(
            total_units=("bottles_sold", "sum"),
            weeks_with_data=("week", "nunique"),
        ).reset_index().sort_values("total_units", ascending=False)
        so_sku_tbl["avg_per_week"] = (so_sku_tbl["total_units"] / so_sku_tbl["weeks_with_data"].clip(lower=1)).round(1)
        so_sku_tbl.columns = ["SKU Name", "Total Units", "Weeks", "Avg Units/Week"]
        so_sku_tbl["Total Units"] = so_sku_tbl["Total Units"].apply(lambda x: f"{int(x):,}")
        st.markdown("<h2>Retail SKU Summary</h2>", unsafe_allow_html=True)
        st.dataframe(so_sku_tbl, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center; color:{MID}; font-size:10px;'>"
    "Niamito Business Intelligence · "
    "Data: Niamito_Master_Tables.xlsx · "
    "Built with Streamlit"
    "</p>",
    unsafe_allow_html=True,
)
