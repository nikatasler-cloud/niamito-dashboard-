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

MARKET_COLORS = {"SI": BROWN, "HR": LAVEN, "DE": GREEN}
SKU_COLORS    = {
    "NIA-OG-250": BROWN,
    "NIA-VN-250": LAVEN,
    "NIA-CH-250": CORAL,
    "NIA-MP-500": YELLOW,
}

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
    background: #EDE3D8 !important;
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
# DEMO DATA
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def generate_demo_data():
    rng = np.random.default_rng(42)

    PRODUCTS = {
        "NIA-OG-250": {"name": "Original 250ml",    "price": 3.20, "bpc": 12},
        "NIA-VN-250": {"name": "Vanilla 250ml",     "price": 3.20, "bpc": 12},
        "NIA-CH-250": {"name": "Chocolate 250ml",   "price": 3.40, "bpc": 12},
        "NIA-MP-500": {"name": "Multipack 6x250ml", "price": 17.50, "bpc": 6},
    }

    weeks = pd.date_range("2026-01-05", "2026-05-11", freq="W-MON")

    BASE = {
        "SI": {"NIA-OG-250": 90,  "NIA-VN-250": 55, "NIA-CH-250": 42, "NIA-MP-500": 30},
        "HR": {"NIA-OG-250": 62,  "NIA-VN-250": 38, "NIA-CH-250": 30, "NIA-MP-500": 20},
        "DE": {"NIA-OG-250": 45,  "NIA-VN-250": 32, "NIA-CH-250": 25, "NIA-MP-500": 14},
    }

    CAMPAIGN_BOOSTS = {
        ("SI", 1): 1.22, ("SI", 2): 1.28, ("SI", 5): 1.35,
        ("HR", 2): 1.18, ("HR", 3): 1.24, ("HR", 4): 1.20,
        ("DE", 2): 1.15, ("DE", 4): 1.38, ("DE", 5): 1.42,
    }

    primary_rows = []
    for i, wk in enumerate(weeks):
        growth = 1 + i * 0.016
        for mkt, sku_dict in BASE.items():
            boost = CAMPAIGN_BOOSTS.get((mkt, wk.month), 1.0)
            for sku, base_cases in sku_dict.items():
                cases   = max(1, int(base_cases * growth * boost * rng.uniform(0.88, 1.16)))
                bottles = cases * PRODUCTS[sku]["bpc"]
                price   = PRODUCTS[sku]["price"]
                disc_pct = rng.uniform(0.06, 0.13)
                gross   = round(bottles * price, 2)
                disc    = round(gross * disc_pct, 2)
                primary_rows.append({
                    "week": wk, "market": mkt,
                    "sku_id": sku, "sku_name": PRODUCTS[sku]["name"],
                    "cases": cases, "bottles": bottles,
                    "list_price": price,
                    "gross_revenue": gross,
                    "trade_discount": disc,
                    "net_revenue": round(gross - disc, 2),
                    "funnel_type": "3-tier" if mkt in ["SI", "HR"] else "2-tier",
                })

    prim_df = pd.DataFrame(primary_rows)

    # ── Sell-out (Retailer → Consumer) ────────────────────
    sellout_rows = []
    RETAILER_MARGIN = 0.28
    for _, r in prim_df.iterrows():
        lag      = timedelta(weeks=2) if r["market"] in ["SI", "HR"] else timedelta(weeks=1)
        so_date  = r["week"] + lag
        if so_date > pd.Timestamp("2026-05-31"):
            continue
        so_ratio    = rng.uniform(0.84, 0.97)
        b_sold      = int(r["bottles"] * so_ratio)
        con_price   = round(r["list_price"] * (1 + RETAILER_MARGIN), 2)
        sellout_rows.append({
            "week": so_date, "market": r["market"],
            "sku_id": r["sku_id"], "sku_name": r["sku_name"],
            "bottles_sold": b_sold,
            "consumer_price": con_price,
            "sellout_revenue": round(b_sold * con_price, 2),
            "funnel_type": r["funnel_type"],
        })
    so_df = pd.DataFrame(sellout_rows)

    # ── Distributor stock (SI & HR) ───────────────────────
    stock_rows = []
    for mkt in ["SI", "HR"]:
        stock = 0
        for wk in weeks:
            c_in  = int(prim_df[(prim_df["market"] == mkt) & (prim_df["week"] == wk)]["cases"].sum())
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
    campaigns = [
        # scope: "Market" = influencers/events/ATL → market-wide lift by time window
        #        "Store"  = sampling/catalog/display → tag specific store rows
        {"id": "MKT-2026-001", "name": "Q1 Instore Sampling SI",
         "channel": "BTL - Sampling",         "market": "SI",  "start": "2026-01-15", "end": "2026-02-15",
         "media_spend": 2800,  "listing_fee": 0,    "trade_disc": 0,   "roas": 3.4,
         "influencer": None, "reach": None, "scope": "Store",  "window_days": 7},
        {"id": "MKT-2026-002", "name": "Valentine Digital DE",
         "channel": "BTL-Digital",             "market": "DE",  "start": "2026-02-01", "end": "2026-02-28",
         "media_spend": 1500,  "listing_fee": 0,    "trade_disc": 200, "roas": 2.1,
         "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-003", "name": "Spring OOH Billboard",
         "channel": "ATL - Out-of-Home",       "market": "ALL", "start": "2026-03-01", "end": "2026-04-30",
         "media_spend": 12000, "listing_fee": 0,    "trade_disc": 0,   "roas": 0.9,
         "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-004", "name": "Mercator Listing Fee",
         "channel": "Trade - Listing Fee",     "market": "SI",  "start": "2026-01-01", "end": "2026-01-01",
         "media_spend": 0,     "listing_fee": 3500, "trade_disc": 0,   "roas": None,
         "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2026-005", "name": "Konzum Shelf Push HR",
         "channel": "BTL - Trade Promo",       "market": "HR",  "start": "2026-02-15", "end": "2026-03-15",
         "media_spend": 1200,  "listing_fee": 1800, "trade_disc": 500, "roas": 2.0,
         "influencer": None, "reach": None, "scope": "Store",  "window_days": 0},
        {"id": "MKT-2026-006", "name": "@healthy.si.life Collab",
         "channel": "BTL-Digital - Influencer","market": "SI",  "start": "2026-03-10", "end": "2026-03-24",
         "media_spend": 600,   "listing_fee": 0,    "trade_disc": 0,   "roas": 3.1,
         "influencer": "@healthy.si.life", "reach": 28000,  "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-007", "name": "@fitnesswelt_de Collab",
         "channel": "BTL-Digital - Influencer","market": "DE",  "start": "2026-04-01", "end": "2026-04-21",
         "media_spend": 1800,  "listing_fee": 0,    "trade_disc": 0,   "roas": 2.7,
         "influencer": "@fitnesswelt_de", "reach": 112000, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-008", "name": "@jedihrvati Collab",
         "channel": "BTL-Digital - Influencer","market": "HR",  "start": "2026-04-10", "end": "2026-04-24",
         "media_spend": 900,   "listing_fee": 0,    "trade_disc": 0,   "roas": 2.3,
         "influencer": "@jedihrvati", "reach": 45000,  "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-009", "name": "Q2 Summer Sampling SI",
         "channel": "BTL - Sampling",         "market": "SI",  "start": "2026-05-01", "end": "2026-06-30",
         "media_spend": 3200,  "listing_fee": 0,    "trade_disc": 0,   "roas": 3.8,
         "influencer": None, "reach": None, "scope": "Store",  "window_days": 7},
        {"id": "MKT-2026-010", "name": "DE Summer Digital",
         "channel": "BTL-Digital",             "market": "DE",  "start": "2026-05-15", "end": "2026-06-30",
         "media_spend": 2400,  "listing_fee": 0,    "trade_disc": 300, "roas": 2.4,
         "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
        {"id": "MKT-2026-011", "name": "DM Tek - Social Coverage",
         "channel": "BTL-Digital - Event",     "market": "SI",  "start": "2026-05-30", "end": "2026-05-30",
         "media_spend": 0,     "listing_fee": 0,    "trade_disc": 0,   "roas": None,
         "influencer": None, "reach": None, "scope": "Market", "window_days": 14},
    ]
    mkt_df = pd.DataFrame(campaigns)
    mkt_df["total_spend"] = mkt_df["media_spend"] + mkt_df["listing_fee"] + mkt_df["trade_disc"]
    mkt_df["attributed_sales"] = mkt_df.apply(
        lambda r: round(r["total_spend"] * r["roas"], 0) if pd.notna(r["roas"]) else 0.0, axis=1
    )

    return prim_df, so_df, mkt_df, stock_df, PRODUCTS


# ──────────────────────────────────────────────────────────────────────────────
# EXCEL LOADER (for real uploads)
# ──────────────────────────────────────────────────────────────────────────────
def load_excel(file):
    """
    Try to load Primary Sales and Marketing Calendar from uploaded Master Tables.
    Returns (prim_df, mkt_df) or raises an error message.
    """
    xl = pd.ExcelFile(file, engine="openpyxl")
    sheets = xl.sheet_names

    def find_sheet(keywords):
        for s in sheets:
            if any(k.lower() in s.lower() for k in keywords):
                return s
        return None

    prim_sheet = find_sheet(["Primary", "Sales"])
    mkt_sheet  = find_sheet(["Marketing", "Calendar"])

    results = {}
    if prim_sheet:
        df = pd.read_excel(file, sheet_name=prim_sheet, header=2, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        results["primary"] = df
    if mkt_sheet:
        df = pd.read_excel(file, sheet_name=mkt_sheet, header=2, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        results["marketing"] = df

    return results


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
            value=(pd.Timestamp("2026-04-01").date(), pd.Timestamp("2026-05-19").date()),
            min_value=pd.Timestamp("2026-01-01").date(),
            max_value=pd.Timestamp("2026-12-31").date(),
            format="DD/MM/YYYY",
        )


# ──────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────────────────────
demo_mode = True
prim_df, so_df, mkt_df, stock_df, PRODUCTS = generate_demo_data()

if uploaded is not None:
    # Detect new file and clear cache so stale demo data doesn't persist
    file_id = f"{uploaded.name}_{uploaded.size}"
    if st.session_state.get("last_file_id") != file_id:
        st.cache_data.clear()
        st.session_state["last_file_id"] = file_id
        prim_df, so_df, mkt_df, stock_df, PRODUCTS = generate_demo_data()
    try:
        loaded = load_excel(uploaded)
        if loaded:
            demo_mode = False
            st.sidebar.success("✓ Data loaded from file")
        else:
            st.sidebar.warning("Could not read sheets — using demo data")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# ── Apply market filter ───────────────────────────────
if market_filter:
    prim_f  = prim_df[prim_df["market"].isin(market_filter)]
    so_f    = so_df[so_df["market"].isin(market_filter)]
    mkt_f   = mkt_df[mkt_df["market"].isin(market_filter) | (mkt_df["market"] == "ALL")]
    stock_f = stock_df[stock_df["market"].isin(market_filter)]
else:
    prim_f, so_f, mkt_f, stock_f = prim_df, so_df, mkt_df, stock_df

# ── Apply period filter ───────────────────────────────
today = pd.Timestamp("2026-05-19")
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
        f"{'⚠️ Demo data — upload your Master Tables to see live numbers' if demo_mode else '✓ Live data'}"
        f"  ·  Markets: {', '.join(market_filter) if market_filter else 'none'}"
        f"  ·  Period: {period}</p>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Sales Funnel",
    "Marketing ROI",
    "Value Leakage",
    "SKU Performance",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── KPI row ──────────────────────────────────────────
    total_so_rev  = so_f["sellout_revenue"].sum()
    total_mkt_spd = mkt_f["total_spend"].sum()
    blended_roas  = (mkt_f["attributed_sales"].sum() / max(mkt_f["total_spend"].sum(), 1))
    total_net_rev = prim_f["net_revenue"].sum()
    total_gross   = prim_f["gross_revenue"].sum()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sell-Out Revenue",     f"€{total_so_rev:,.0f}",  delta="vs prior period")
    k2.metric("Total Net Revenue",    f"€{total_net_rev:,.0f}", delta=f"Gross €{total_gross:,.0f}")
    k3.metric("Marketing Spend",      f"€{total_mkt_spd:,.0f}", delta="incl. listing fees")
    k4.metric("Blended ROAS",         f"{blended_roas:.1f}×",   delta="BTL campaigns only" if blended_roas > 0 else None)

    st.markdown("")

    # ── Sell-out trend by market ──────────────────────────
    c_left, c_right = st.columns([0.6, 0.4])

    with c_left:
        so_weekly = (
            so_f.groupby(["week", "market"])["sellout_revenue"]
            .sum().reset_index()
        )
        fig = go.Figure()
        for mkt in (market_filter or ["SI", "HR", "DE"]):
            d = so_weekly[so_weekly["market"] == mkt]
            fig.add_trace(go.Scatter(
                x=d["week"], y=d["sellout_revenue"],
                mode="lines+markers",
                name=mkt,
                line=dict(color=MARKET_COLORS.get(mkt, BROWN), width=2.5),
                marker=dict(size=5),
                hovertemplate=f"<b>{mkt}</b><br>Week: %{{x|%d %b}}<br>€%{{y:,.0f}}<extra></extra>",
            ))
        layout = base_layout("Sell-Out Revenue by Market (weekly)", height=320)
        layout["yaxis"]["tickprefix"] = "€"
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        # Spend by channel donut
        ch_spend = mkt_f.groupby("channel")["total_spend"].sum().reset_index()
        ch_spend = ch_spend[ch_spend["total_spend"] > 0].sort_values("total_spend", ascending=False)
        palette = [BROWN, LAVEN, GREEN, CORAL, YELLOW, MID, "#c8b89a"]

        fig2 = go.Figure(go.Pie(
            labels=ch_spend["channel"],
            values=ch_spend["total_spend"],
            hole=0.52,
            marker=dict(colors=palette[:len(ch_spend)], line=dict(color=CREAM, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<extra></extra>",
        ))
        layout2 = base_layout("Marketing Spend by Channel", height=320, legend_below=False)
        layout2["legend"]["orientation"] = "v"
        layout2["legend"]["x"] = 1.0
        layout2["legend"]["y"] = 0.5
        fig2.update_layout(**layout2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Primary revenue trend ─────────────────────────────
    prim_weekly = prim_f.groupby("week").agg(
        gross=("gross_revenue", "sum"),
        net=("net_revenue", "sum"),
    ).reset_index()

    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=prim_weekly["week"], y=prim_weekly["gross"],
        name="Gross Revenue", marker_color=LAVEN, opacity=0.7,
        hovertemplate="Gross: €%{y:,.0f}<extra></extra>",
    ))
    fig3.add_trace(go.Bar(
        x=prim_weekly["week"], y=prim_weekly["net"],
        name="Net Revenue", marker_color=BROWN,
        hovertemplate="Net: €%{y:,.0f}<extra></extra>",
    ))
    layout3 = base_layout("Primary Sales: Gross vs Net Revenue (weekly, all markets)", height=280)
    layout3["yaxis"]["tickprefix"] = "€"
    layout3["barmode"] = "overlay"
    fig3.update_layout(**layout3)
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · SALES FUNNEL
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    st.markdown("<h2>Sales Funnel by Market</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:12px; color:{MID};'>"
        "SI & HR use a <b>3-tier funnel</b> (Company → Distributor → Retailer → Consumer). "
        "DE uses a <b>2-tier funnel</b> (Company → Retailer → Consumer).</p>",
        unsafe_allow_html=True,
    )

    sel_mkt = st.radio(
        "Select market:",
        options=[m for m in ["SI", "HR", "DE"] if m in (market_filter or ["SI","HR","DE"])],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ── Funnel numbers ────────────────────────────────────
    prim_mkt = prim_f[prim_f["market"] == sel_mkt]
    so_mkt   = so_f[so_f["market"] == sel_mkt]

    p_rev  = prim_mkt["gross_revenue"].sum()
    n_rev  = prim_mkt["net_revenue"].sum()
    so_rev = so_mkt["sellout_revenue"].sum()
    fill_rate = (so_rev / p_rev * 100) if p_rev > 0 else 0

    funnel_type = "3-tier" if sel_mkt in ["SI", "HR"] else "2-tier"

    fl, fm, fr = st.columns(3)
    fl.metric("Primary Sales (Gross)", f"€{p_rev:,.0f}", help="Company invoices to distributor/retailer")
    fm.metric("Net Revenue (after discounts)", f"€{n_rev:,.0f}", delta=f"–{(p_rev - n_rev) / max(p_rev,1)*100:.1f}% trade disc.")
    fr.metric("Sell-Out Revenue (consumer)", f"€{so_rev:,.0f}", delta=f"{fill_rate:.0f}% sell-through")

    st.markdown("")

    # ── Funnel chart ──────────────────────────────────────
    if funnel_type == "3-tier":
        stock_mkt = stock_f[stock_f["market"] == sel_mkt]
        avg_stock = stock_mkt["stock_cases"].mean() if not stock_mkt.empty else 0

        stages = ["Primary (Gross)", "Net (after discounts)", "Sell-Out (consumer)"]
        values = [p_rev, n_rev, so_rev]
        colors = [LAVEN, BROWN, GREEN]
    else:
        stages = ["Primary Sales", "Net Revenue", "Sell-Out (consumer)"]
        values = [p_rev, n_rev, so_rev]
        colors = [LAVEN, BROWN, GREEN]

    fig_f = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        texttemplate="€%{value:,.0f}  (%{percentInitial:.0%})",
        marker=dict(color=colors, line=dict(color=CREAM, width=1.5)),
        connector=dict(line=dict(color=BROWN, width=1)),
    ))
    layout_f = base_layout(f"{sel_mkt} — {'3-Tier' if funnel_type=='3-tier' else '2-Tier'} Funnel", height=320)
    layout_f.pop("xaxis", None)
    layout_f.pop("yaxis", None)
    fig_f.update_layout(**layout_f)
    st.plotly_chart(fig_f, use_container_width=True)

    # ── Stock-to-Sales (SI & HR only) ─────────────────────
    if sel_mkt in ["SI", "HR"]:
        st.markdown("<h2>Distributor Stock Health</h2>", unsafe_allow_html=True)
        stock_mkt = stock_f[stock_f["market"] == sel_mkt]

        c_s1, c_s2 = st.columns([0.65, 0.35])
        with c_s1:
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(
                x=stock_mkt["week"], y=stock_mkt["stock_cases"],
                fill="tozeroy", mode="lines",
                line=dict(color=LAVEN, width=2),
                fillcolor="rgba(179, 184, 217, 0.33)",
                name="Stock (cases)",
                hovertemplate="Week: %{x|%d %b}<br>Stock: %{y:,} cases<extra></extra>",
            ))
            fig_s.add_hline(
                y=stock_mkt["stock_cases"].mean() * 1.5,
                line_dash="dash", line_color=CORAL, annotation_text="⚠ Overstock threshold",
                annotation_font_color=CORAL,
            )
            layout_s = base_layout(f"{sel_mkt} Distributor Stock (cases)", height=280)
            fig_s.update_layout(**layout_s)
            st.plotly_chart(fig_s, use_container_width=True)

        with c_s2:
            avg_s2s = stock_mkt["stock_to_sales"].mean()
            st.metric("Avg Stock-to-Sales Ratio", f"{avg_s2s:.1f}×",
                      help="Cases in stock ÷ cases shipped out. >2.0 = overstock risk")
            current = stock_mkt.iloc[-1]["stock_to_sales"] if not stock_mkt.empty else 0
            flag = "🟢 Healthy" if current < 2.0 else "🔴 Overstock risk"
            st.markdown(f"<p style='font-size:13px;'>Latest week: <b>{current:.1f}×</b> — {flag}</p>",
                        unsafe_allow_html=True)

            # Mini bar: in vs out
            fig_io = go.Figure()
            fig_io.add_trace(go.Bar(x=stock_mkt["week"], y=stock_mkt["cases_in"],
                                    name="In", marker_color=GREEN, opacity=0.8))
            fig_io.add_trace(go.Bar(x=stock_mkt["week"], y=stock_mkt["cases_out"],
                                    name="Out", marker_color=CORAL, opacity=0.8))
            layout_io = base_layout("Cases In vs Out", height=230)
            layout_io["margin"]["t"] = 30
            layout_io["barmode"] = "group"
            fig_io.update_layout(**layout_io)
            st.plotly_chart(fig_io, use_container_width=True)
    else:
        st.info("Germany uses a 2-tier funnel — no distributor stock to track. Products ship directly from Niamito to retailers.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · MARKETING ROI
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    # ── Attribution scope legend ──────────────────────────
    st.markdown(f"""
    <div style='display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap;'>
      <div style='background:{LAVEN}33; border:1.5px solid {LAVEN}; border-radius:10px;
                  padding:10px 16px; font-size:12px; flex:1; min-width:200px;'>
        <b style='color:{BROWN};'>🌍 Market-level attribution</b><br>
        <span style='color:{MID};'>Influencers, events, social, ATL — lift measured across the whole market
        for the window after the campaign ends. Tag: no store-specific tagging needed.</span>
      </div>
      <div style='background:{GREEN}33; border:1.5px solid {GREEN}; border-radius:10px;
                  padding:10px 16px; font-size:12px; flex:1; min-width:200px;'>
        <b style='color:{BROWN};'>🏪 Store-level attribution</b><br>
        <span style='color:{MID};'>In-store sampling, catalog promos, displays — tag specific store rows
        in the Sell-out Template with the Campaign ID during the exact promo dates.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Split campaigns by scope ──────────────────────────
    mkt_market = mkt_f[mkt_f.get("scope", pd.Series(["Store"]*len(mkt_f))) == "Market"] if "scope" in mkt_f.columns else mkt_f[mkt_f["channel"].str.contains("Influencer|ATL|Digital|Event|Social", case=False, na=False)]
    mkt_store  = mkt_f[mkt_f.get("scope", pd.Series(["Store"]*len(mkt_f))) == "Store"]  if "scope" in mkt_f.columns else mkt_f[~mkt_f["channel"].str.contains("Influencer|ATL|Digital|Event|Social", case=False, na=False)]

    # fallback if scope column missing: derive from channel
    if "scope" not in mkt_f.columns:
        def _scope(ch):
            ch = str(ch).lower()
            return "Market" if any(k in ch for k in ["influencer","atl","digital","event","social"]) else "Store"
        mkt_f2_scope = mkt_f.copy()
        mkt_f2_scope["scope"] = mkt_f2_scope["channel"].apply(_scope)
        mkt_market = mkt_f2_scope[mkt_f2_scope["scope"] == "Market"]
        mkt_store  = mkt_f2_scope[mkt_f2_scope["scope"] == "Store"]

    # ── ROAS charts side by side ──────────────────────────
    col_m, col_s = st.columns(2)

    def roas_bar(df, title, color_accent):
        df = df[df["roas"].notna()].sort_values("roas", ascending=True)
        if df.empty:
            return go.Figure()
        colors = [GREEN if r >= 2.0 else (YELLOW if r >= 1.0 else CORAL) for r in df["roas"]]
        fig = go.Figure(go.Bar(
            x=df["roas"], y=df["name"], orientation="h",
            marker=dict(color=colors, line=dict(color=CREAM, width=0.5)),
            text=[f"{r:.1f}×" for r in df["roas"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}×<extra></extra>",
        ))
        fig.add_vline(x=1.0, line_dash="dot", line_color=CORAL)
        fig.add_vline(x=2.0, line_dash="dot", line_color=GREEN)
        layout = base_layout(title, height=max(280, len(df) * 44 + 60))
        layout["xaxis"]["title"] = "ROAS"
        layout["margin"]["l"] = 190
        layout["plot_bgcolor"] = color_accent + "18"
        fig.update_layout(**layout)
        return fig

    with col_m:
        st.markdown(f"<h2 style='color:{BROWN};'>🌍 Market-Level Campaigns</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:11px;color:{MID};'>Influencers, events, ATL · ROAS = market sell-out lift ÷ spend</p>", unsafe_allow_html=True)
        fig_m = roas_bar(mkt_market, "ROAS — Market-Level", LAVEN)
        if not mkt_market[mkt_market["roas"].notna()].empty:
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info("No ROAS data yet for market-level campaigns.")

    with col_s:
        st.markdown(f"<h2 style='color:{BROWN};'>🏪 Store-Level Campaigns</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:11px;color:{MID};'>Sampling, catalog, display · ROAS = tagged store sell-out ÷ spend</p>", unsafe_allow_html=True)
        fig_s = roas_bar(mkt_store, "ROAS — Store-Level", GREEN)
        if not mkt_store[mkt_store["roas"].notna()].empty:
            st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.info("No ROAS data yet for store-level campaigns.")

    # ── Influencer cards ──────────────────────────────────
    inf_df = mkt_f[mkt_f["influencer"].notna()].copy()
    if not inf_df.empty:
        st.markdown("<h2>Influencer Tracker</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:11px;color:{MID};margin-top:-8px;'>Market-level · ROAS measured as market sell-out lift in the 14 days after post date</p>", unsafe_allow_html=True)
        max_cols = min(len(inf_df), 4)
        rows_needed = (len(inf_df) + max_cols - 1) // max_cols
        for row_i in range(rows_needed):
            row_data = inf_df.iloc[row_i*max_cols:(row_i+1)*max_cols]
            cols_inf = st.columns(len(row_data))
            for i, (_, row) in enumerate(row_data.iterrows()):
                with cols_inf[i]:
                    reach    = row.get("reach") or 0
                    cpm      = round(row["media_spend"] / max(reach, 1) * 1000, 2) if reach else 0
                    roas_val = row["roas"]
                    roas_str = f"{roas_val:.1f}×" if pd.notna(roas_val) else "pending"
                    roas_col = GREEN if (pd.notna(roas_val) and roas_val >= 2) else (YELLOW if pd.notna(roas_val) else MID)
                    st.markdown(f"""
                    <div style='background:{CREAM}; border:1.5px solid {LAVEN}; border-radius:12px; padding:14px; margin-bottom:8px;'>
                        <p style='font-size:13px; font-weight:700; margin:0; color:{BROWN};'>{row["influencer"]}</p>
                        <p style='font-size:10px; color:{MID}; margin:2px 0 8px; text-transform:uppercase; letter-spacing:0.5px;'>{row["market"]} · Market-level</p>
                        <p style='margin:3px 0; font-size:12px;'>👁 Reach: <b>{int(reach):,}</b></p>
                        <p style='margin:3px 0; font-size:12px;'>💶 Spend: <b>€{row["media_spend"]:,.0f}</b></p>
                        <p style='margin:3px 0; font-size:12px;'>📈 ROAS: <b style='color:{roas_col};'>{roas_str}</b></p>
                        <p style='margin:3px 0; font-size:12px;'>💡 CPM: <b>€{cpm:.2f}</b></p>
                        <p style='margin:3px 0; font-size:11px; color:{MID};'>{row["start"]} → +14 days</p>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Full campaign table ───────────────────────────────
    st.markdown("<h2>All Campaigns</h2>", unsafe_allow_html=True)

    def _scope_label(row):
        if "scope" in row and pd.notna(row["scope"]):
            return "🌍 Market" if row["scope"] == "Market" else "🏪 Store"
        ch = str(row.get("channel","")).lower()
        return "🌍 Market" if any(k in ch for k in ["influencer","atl","digital","event"]) else "🏪 Store"

    tbl = mkt_f[["id","name","channel","market","start","end","total_spend","roas","attributed_sales"]].copy()
    tbl["Attribution"] = mkt_f.apply(_scope_label, axis=1)
    tbl.columns = ["ID","Campaign","Channel","Mkt","Start","End","Spend (€)","ROAS","Attributed Sales (€)","Attribution"]
    tbl = tbl[["Attribution","ID","Campaign","Channel","Mkt","Start","End","Spend (€)","ROAS","Attributed Sales (€)"]]
    tbl["Spend (€)"]            = tbl["Spend (€)"].apply(lambda x: f"€{x:,.0f}")
    tbl["Attributed Sales (€)"] = tbl["Attributed Sales (€)"].apply(lambda x: f"€{x:,.0f}" if x else "—")
    tbl["ROAS"]                 = tbl["ROAS"].apply(lambda x: f"{x:.1f}×" if pd.notna(x) else "—")
    st.dataframe(tbl.sort_values("Attribution"), use_container_width=True, hide_index=True)

    # ── Spend mix ─────────────────────────────────────────
    st.markdown("<h2>Spend Mix</h2>", unsafe_allow_html=True)
    c_type, c_mkt = st.columns(2)

    def get_type(ch):
        ch = str(ch).lower()
        if "atl" in ch:                                        return "ATL"
        if "influencer" in ch:                                 return "BTL-Digital · Influencer"
        if "digital" in ch or "social" in ch or "event" in ch: return "BTL-Digital · Other"
        if "listing" in ch or "trade" in ch:                   return "Trade"
        return "BTL · In-store"

    mkt_typed = mkt_f.copy()
    mkt_typed["type"] = mkt_typed["channel"].apply(get_type)
    type_spend = mkt_typed.groupby("type")["total_spend"].sum().reset_index()
    type_spend = type_spend[type_spend["total_spend"] > 0]
    palette = [BROWN, LAVEN, GREEN, CORAL, YELLOW, MID]

    with c_type:
        fig_type = go.Figure(go.Pie(
            labels=type_spend["type"], values=type_spend["total_spend"],
            hole=0.5,
            marker=dict(colors=palette[:len(type_spend)], line=dict(color=CREAM, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>€%{value:,.0f}<extra></extra>",
        ))
        l_type = base_layout("Spend by Channel Type", height=300, legend_below=False)
        l_type["legend"] = dict(x=1.0, y=0.5, font=dict(size=10, color=BROWN), bgcolor="rgba(0,0,0,0)")
        fig_type.update_layout(**l_type)
        st.plotly_chart(fig_type, use_container_width=True)

    with c_mkt:
        mkt_spend = mkt_typed.groupby("market")["total_spend"].sum().reset_index()
        fig_mkt = go.Figure(go.Bar(
            x=mkt_spend["market"], y=mkt_spend["total_spend"],
            marker=dict(color=[MARKET_COLORS.get(m, BROWN) for m in mkt_spend["market"]]),
            text=[f"€{v:,.0f}" for v in mkt_spend["total_spend"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra></extra>",
        ))
        l_mkt = base_layout("Spend by Market", height=300)
        l_mkt["yaxis"]["tickprefix"] = "€"
        fig_mkt.update_layout(**l_mkt)
        st.plotly_chart(fig_mkt, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · VALUE LEAKAGE WATERFALL
# ══════════════════════════════════════════════════════════════════════════════
with tab4:

    st.markdown("<h2>Value Leakage — Where Revenue Goes</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:12px; color:{MID};'>"
        "Starting from gross sales, each deduction shows what's taken off before Niamito's net revenue. "
        "The smaller the leakage, the more efficient the go-to-market.</p>",
        unsafe_allow_html=True,
    )

    wf_mkt = st.radio("Market:", options=[m for m in ["ALL","SI","HR","DE"]
                                           if m == "ALL" or m in (market_filter or ["SI","HR","DE"])],
                       horizontal=True, key="wf_mkt")

    # Compute waterfall values
    if wf_mkt == "ALL":
        p_data = prim_f
        m_data = mkt_f
    else:
        p_data = prim_f[prim_f["market"] == wf_mkt]
        m_data = mkt_f[mkt_f["market"].isin([wf_mkt, "ALL"])]

    gross         = p_data["gross_revenue"].sum()
    trade_disc    = p_data["trade_discount"].sum()
    after_trade   = gross - trade_disc
    mkt_spend     = m_data["media_spend"].sum()
    after_mkt     = after_trade - mkt_spend
    listing_fees  = m_data["listing_fee"].sum()
    net_revenue   = after_mkt - listing_fees

    # Waterfall using Plotly
    wf_labels  = ["Gross Revenue", "– Trade Discounts", "– Marketing Spend", "– Listing Fees", "Net Revenue"]
    wf_measure = ["absolute", "relative", "relative", "relative", "total"]
    wf_values  = [gross, -trade_disc, -mkt_spend, -listing_fees, net_revenue]
    wf_colors  = [BROWN, CORAL, CORAL, CORAL, GREEN]

    fig_wf = go.Figure(go.Waterfall(
        name="Value Leakage",
        orientation="v",
        measure=wf_measure,
        x=wf_labels,
        y=wf_values,
        text=[f"€{abs(v):,.0f}" for v in wf_values],
        textposition="outside",
        connector=dict(line=dict(color=MID, width=1, dash="dot")),
        increasing=dict(marker=dict(color=GREEN)),
        decreasing=dict(marker=dict(color=CORAL)),
        totals=dict(marker=dict(color=BROWN)),
        hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra></extra>",
    ))
    layout_wf = base_layout(
        f"Value Leakage Waterfall — {wf_mkt}  "
        f"(Net margin: {net_revenue/max(gross,1)*100:.1f}%)",
        height=380,
    )
    layout_wf["yaxis"]["tickprefix"] = "€"
    fig_wf.update_layout(**layout_wf)
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Summary table ─────────────────────────────────────
    wf_tbl = pd.DataFrame({
        "Line": wf_labels,
        "Amount (€)": [f"€{abs(v):,.0f}" for v in wf_values],
        "% of Gross": [f"{abs(v)/max(gross,1)*100:.1f}%" for v in wf_values],
    })
    st.dataframe(wf_tbl, use_container_width=True, hide_index=True)

    # ── Per-market comparison ─────────────────────────────
    st.markdown("<h2>Net Margin by Market</h2>", unsafe_allow_html=True)
    margin_rows = []
    for mkt in ["SI", "HR", "DE"]:
        if mkt not in (market_filter or ["SI","HR","DE"]):
            continue
        pd_ = prim_f[prim_f["market"] == mkt]
        md_ = mkt_f[mkt_f["market"].isin([mkt, "ALL"])]
        g   = pd_["gross_revenue"].sum()
        td  = pd_["trade_discount"].sum()
        ms  = md_["media_spend"].sum()
        lf  = md_["listing_fee"].sum()
        nr  = g - td - ms - lf
        margin_rows.append({
            "Market": mkt, "Gross (€)": g, "Trade Disc (€)": td,
            "Mktg Spend (€)": ms, "Listing Fees (€)": lf,
            "Net Revenue (€)": nr, "Net Margin %": f"{nr/max(g,1)*100:.1f}%",
        })

    if margin_rows:
        margin_df = pd.DataFrame(margin_rows)
        for col in ["Gross (€)", "Trade Disc (€)", "Mktg Spend (€)", "Listing Fees (€)", "Net Revenue (€)"]:
            margin_df[col] = margin_df[col].apply(lambda x: f"€{x:,.0f}")
        st.dataframe(margin_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 · SKU PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab5:

    st.markdown("<h2>SKU Performance — Sell-Out</h2>", unsafe_allow_html=True)

    # ── Sell-out by SKU ───────────────────────────────────
    sku_so = so_f.groupby("sku_id").agg(
        sku_name=("sku_name", "first"),
        bottles=("bottles_sold", "sum"),
        revenue=("sellout_revenue", "sum"),
    ).reset_index().sort_values("revenue", ascending=False)

    c_sku1, c_sku2 = st.columns(2)

    with c_sku1:
        fig_sku = go.Figure(go.Bar(
            x=sku_so["sku_name"],
            y=sku_so["revenue"],
            marker=dict(color=[SKU_COLORS.get(s, BROWN) for s in sku_so["sku_id"]]),
            text=[f"€{v:,.0f}" for v in sku_so["revenue"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>€%{y:,.0f}<extra></extra>",
        ))
        layout_sku = base_layout("Sell-Out Revenue by SKU", height=320)
        layout_sku["yaxis"]["tickprefix"] = "€"
        layout_sku["xaxis"]["tickangle"] = -15
        fig_sku.update_layout(**layout_sku)
        st.plotly_chart(fig_sku, use_container_width=True)

    with c_sku2:
        fig_sku_p = go.Figure(go.Pie(
            labels=sku_so["sku_name"],
            values=sku_so["bottles"],
            hole=0.5,
            marker=dict(colors=[SKU_COLORS.get(s, BROWN) for s in sku_so["sku_id"]],
                        line=dict(color=CREAM, width=2)),
            textinfo="percent",
            hovertemplate="<b>%{label}</b><br>%{value:,} bottles<extra></extra>",
        ))
        l_sku_p = base_layout("Bottle Share by SKU", height=320, legend_below=False)
        l_sku_p["legend"]["x"] = 1.0
        l_sku_p["legend"]["y"] = 0.5
        fig_sku_p.update_layout(**l_sku_p)
        st.plotly_chart(fig_sku_p, use_container_width=True)

    # ── SKU × Market heatmap ──────────────────────────────
    st.markdown("<h2>Revenue by SKU × Market</h2>", unsafe_allow_html=True)

    pivot = so_f.groupby(["sku_name", "market"])["sellout_revenue"].sum().unstack(fill_value=0)
    pivot = pivot.round(0)

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0, CREAM], [0.4, LAVEN], [1.0, BROWN]],
        text=[[f"€{v:,.0f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
        showscale=True,
        colorbar=dict(tickprefix="€", tickfont=dict(color=BROWN, size=10)),
    ))
    layout_heat = base_layout("Sell-Out Revenue (€) — SKU × Market", height=280)
    layout_heat.pop("xaxis", None)
    layout_heat.pop("yaxis", None)
    layout_heat["margin"]["l"] = 160
    fig_heat.update_layout(**layout_heat)
    st.plotly_chart(fig_heat, use_container_width=True)

    # ── SKU trend lines ───────────────────────────────────
    st.markdown("<h2>Sell-Out Trend by SKU</h2>", unsafe_allow_html=True)

    sku_trend = so_f.groupby(["week", "sku_id"])["sellout_revenue"].sum().reset_index()
    fig_t = go.Figure()
    for sku in sku_so["sku_id"]:
        d = sku_trend[sku_trend["sku_id"] == sku]
        name = PRODUCTS.get(sku, {}).get("name", sku)
        fig_t.add_trace(go.Scatter(
            x=d["week"], y=d["sellout_revenue"],
            mode="lines",
            name=name,
            line=dict(color=SKU_COLORS.get(sku, BROWN), width=2),
            hovertemplate=f"<b>{name}</b><br>%{{x|%d %b}}: €%{{y:,.0f}}<extra></extra>",
        ))
    layout_t = base_layout("Weekly Sell-Out by SKU (all markets)", height=300)
    layout_t["yaxis"]["tickprefix"] = "€"
    fig_t.update_layout(**layout_t)
    st.plotly_chart(fig_t, use_container_width=True)

    # ── SKU summary table ─────────────────────────────────
    st.markdown("<h2>SKU Summary Table</h2>", unsafe_allow_html=True)

    prim_sku = prim_f.groupby(["sku_id"]).agg(
        sku_name=("sku_name", "first"),
        cases=("cases", "sum"),
        gross=("gross_revenue", "sum"),
        discount=("trade_discount", "sum"),
        net=("net_revenue", "sum"),
    ).reset_index()

    so_sku = so_f.groupby("sku_id")["sellout_revenue"].sum().rename("so_revenue")
    sku_tbl = prim_sku.merge(so_sku, on="sku_id", how="left")
    sku_tbl["disc_%"] = (sku_tbl["discount"] / sku_tbl["gross"] * 100).round(1)
    sku_tbl["so_revenue"] = sku_tbl["so_revenue"].fillna(0)

    out = sku_tbl[["sku_name", "cases", "gross", "discount", "disc_%", "net", "so_revenue"]].copy()
    out.columns = ["SKU", "Cases Sold", "Gross (€)", "Trade Disc (€)", "Disc %", "Net Rev (€)", "Sell-Out (€)"]
    for col in ["Gross (€)", "Trade Disc (€)", "Net Rev (€)", "Sell-Out (€)"]:
        out[col] = out[col].apply(lambda x: f"€{x:,.0f}")
    out["Disc %"] = out["Disc %"].apply(lambda x: f"{x:.1f}%")

    st.dataframe(out, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align:center; color:{MID}; font-size:10px;'>"
    "Niamito Business Intelligence · "
    "Data: Niamito_Master_Tables.xlsx · "
    "Built with Streamlit · "
    "{'Demo mode — upload real data via sidebar' if demo_mode else 'Live data'}"
    "</p>",
    unsafe_allow_html=True,
)
