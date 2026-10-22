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
import os
import pathlib
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# BRAND
# ──────────────────────────────────────────────────────────────────────────────
BEIGE  = "#F8F7F5"
BROWN  = "#292322"
LAVEN  = "#9380DC"
GREEN  = "#497864"
CORAL  = "#D8876D"
YELLOW = "#C8A84B"
CREAM  = "#FFFFFF"
MID    = "#817875"

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
    # Oatmeal MUST be checked first — its products also contain "hpp" and flavour words
    # that appear in Fresh Meal keywords, so order matters.
    "Niamito Oatmeal":          ["oatmeal", "oat"],
    "Niamito Meal in a Bottle": ["uht", "470", "cocoa", "cookie", "vanilla", "meal in a bottle"],
    "Niamito Fresh Meal":       ["fresh meal", "fresh", "hpp", "390", "apple", "blueberry",
                                  "spinach", "strawberry", "jaffa", "borovn", "jagod",
                                  "\u0161pina\u010d", "jabolč"],
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
    return "Niamito Fresh Meal"  # safe fallback; Oatmeal is now matched explicitly above

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Niamito · Business Intelligence",
    page_icon=":seedling:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard_ui import install_theme, base_layout, section, note
from dashboard_data import load_excel_cached, generate_demo_data
from marketing import normalize_marketing, render_marketing, marketing_allocations
from overview import render_overview, render_data
from html import escape
install_theme()

def caption(text):
    st.markdown(f"<p class='chart-caption'>{escape(text)}</p>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand"><b>niamito.</b><span>BUSINESS WORKSPACE</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Reporting scope</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Data source",
        type=["xlsx"],
        help="Upload Niamito_Master_Tables.xlsx from Google Drive",
        key="file_uploader",
    )

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    period = st.sidebar.selectbox(
        "Period",
        ["This year (YTD)", "Last 3 months", "Last 6 months", "All data", "Custom range"],
        index=0,
    )

    custom_range = None
    if period == "Custom range":
        custom_range = st.date_input(
            "Date range",
            value=(pd.Timestamp.today().replace(month=1, day=1).date(), pd.Timestamp.today().date()),
            min_value=pd.Timestamp("2024-01-01").date(),
            max_value=pd.Timestamp.today().replace(month=12, day=31).date(),
            format="DD/MM/YYYY",
        )

    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)

    category_filter = st.multiselect(
        "Product Category",
        options=ALL_CATEGORIES,
        default=ALL_CATEGORIES,
        help="Clear the selection to include all product categories. Marketing has its own filters.",
    )

    st.markdown(
        "<hr style='border:none; border-top:1px solid rgba(255,255,255,0.06); margin:10px 0 8px;'>",
        unsafe_allow_html=True,
    )

    metric_mode = st.radio(
        "View as",
        options=["Pieces sold", "Revenue (€)"],
        index=0,
        key="metric_mode",
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
exp_df   = pd.DataFrame(columns=["product_line","sku","month","material_cost","labour_overhead","production_cost","logistics","marketing_promo"])
xl_stock_val    = 0.0  # Active stock value (€) — from Excel Cost Allocation section
xl_promo_val    = 0.0  # Promo & External cost (€)
xl_internal_val = 0.0  # Internal Consumption cost (€)

# ── Auto-load from same folder first, then fall back to uploader ──────────
_AUTO_PATH = pathlib.Path(__file__).parent / "Niamito_Master_Tables.xlsx"
_data_source = None
if uploaded is not None:
    _data_source = uploaded
elif _AUTO_PATH.exists():
    _data_source = str(_AUTO_PATH)

if _data_source is not None:
    try:
        payload = uploaded.getvalue() if uploaded is not None else pathlib.Path(_data_source).read_bytes()
        prim_df, so_df, mkt_df, stock_df, PRODUCTS, exp_df, xl_stock_val, xl_promo_val, xl_internal_val = load_excel_cached(payload)
        demo_mode = False
        _src_label = "auto-loaded from folder" if uploaded is None else "uploaded"
        st.sidebar.caption("Workbook loaded · " + ("uploaded file" if uploaded is not None else "GitHub snapshot"))
        if not prim_df.empty and "week" in prim_df.columns:
            latest_prim = prim_df["week"].max()
            if pd.notna(latest_prim):
                st.sidebar.caption(
                    f"Primary Sales: up to {latest_prim.strftime('%b %Y')}. "
                    "Replace the Excel file to update."
                )
    except Exception as e:
        st.error(f"Could not read the workbook: {e}")
        st.info("Upload a valid master workbook to continue.")
        st.stop()

if demo_mode:
    st.warning("Demonstration mode: no master workbook was found. Upload your workbook to see actual figures.")
    prim_df, so_df, mkt_df, stock_df, PRODUCTS = generate_demo_data()

mkt_df = normalize_marketing(mkt_df)

prim_f  = prim_df.copy()
so_f    = so_df.copy()
mkt_f   = mkt_df.copy()
stock_f = stock_df.copy()

# ── Apply category filter ─────────────────────────────
if category_filter and len(category_filter) < len(ALL_CATEGORIES):
    if "category" in prim_f.columns:
        prim_f = prim_f[prim_f["category"].isin(category_filter)]
    if "category" in so_f.columns:
        so_f   = so_f[so_f["category"].isin(category_filter)]

# ── Apply period filter ───────────────────────────────
today = pd.Timestamp.now(tz="Europe/Ljubljana").tz_localize(None).normalize()
if period == "Custom range" and (not custom_range or len(custom_range) != 2):
    st.info("Select both a start and end date to apply the range.")
    st.stop()
jan1_this_year = pd.Timestamp(f"{today.year}-01-01")

if period == "Custom range":
    if custom_range and len(custom_range) == 2:
        start_ts, end_ts = pd.Timestamp(custom_range[0]), pd.Timestamp(custom_range[1])
        prim_f  = prim_f[(prim_f["week"] >= start_ts) & (prim_f["week"] <= end_ts)]
        so_f    = so_f[(so_f["week"] >= start_ts) & (so_f["week"] <= end_ts)]
        stock_f = stock_f[(stock_f["week"] >= start_ts) & (stock_f["week"] <= end_ts)]
elif period == "This year (YTD)":
    prim_f  = prim_f[prim_f["week"] >= jan1_this_year]
    so_f    = so_f[so_f["week"] >= jan1_this_year]
    stock_f = stock_f[stock_f["week"] >= jan1_this_year]
elif period == "Last 3 months":
    cutoff = today - pd.DateOffset(months=3)
    prim_f  = prim_f[prim_f["week"] >= cutoff]
    so_f    = so_f[so_f["week"] >= cutoff]
    stock_f = stock_f[stock_f["week"] >= cutoff]
elif period == "Last 6 months":
    cutoff = today - pd.DateOffset(months=6)
    prim_f  = prim_f[prim_f["week"] >= cutoff]
    so_f    = so_f[so_f["week"] >= cutoff]
    stock_f = stock_f[stock_f["week"] >= cutoff]
# "All data" → no filter

if period in ("This year (YTD)", "Last 3 months", "Last 6 months"):
    prim_f = prim_f[prim_f["week"] <= today]
    so_f = so_f[so_f["week"] <= today]
    stock_f = stock_f[stock_f["week"] <= today]

# Snapshot after period filter but before category filter — SKU tab shows all categories
prim_f_nokcat = prim_f.copy()

# ── Apply period filter to marketing calendar ─────────────────────────────
_mkt_start = pd.to_datetime(mkt_f["start"], errors="coerce") if not mkt_f.empty else pd.Series(dtype="datetime64[ns]")
if period == "Custom range" and custom_range and len(custom_range) == 2:
    _ms, _me = pd.Timestamp(custom_range[0]), pd.Timestamp(custom_range[1])
    mkt_f = mkt_f[(_mkt_start >= _ms) & (_mkt_start <= _me)]
elif period == "This year (YTD)":
    mkt_f = mkt_f[_mkt_start >= jan1_this_year]
elif period == "Last 3 months":
    mkt_f = mkt_f[_mkt_start >= (today - pd.DateOffset(months=3))]
elif period == "Last 6 months":
    mkt_f = mkt_f[_mkt_start >= (today - pd.DateOffset(months=6))]
# "All data" → no filter


if period in ("This year (YTD)", "Last 3 months", "Last 6 months"):
    mkt_f = mkt_f[pd.to_datetime(mkt_f["start"], errors="coerce") <= today]

# ── Sidebar: market jump nav (always visible, regardless of active tab) ───────
_nav_flags  = {"SI": "🇸🇮", "HR": "🇭🇷", "ME": "🇲🇪", "DE": "🇩🇪", "PL": "🇵🇱", "CH": "🇨🇭", "AT": "🇦🇹"}
_MARKET_ORDER = ["SI", "HR", "DE", "PL", "CH", "ME", "AT"]
_nav_markets = [m for m in _MARKET_ORDER if not so_df.empty and "market" in so_df.columns and m in so_df["market"].values] if not so_df.empty else []
if _nav_markets:
    with st.sidebar:
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(237,227,216,0.18);margin:12px 0 10px;'>"
            "<p style='font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
            "color:rgba(237,227,216,0.55);margin:0 0 6px;'>Jump to market</p>",
            unsafe_allow_html=True,
        )
        if st.button("🌍  All Markets", key="jnav___all__", width="stretch"):
            st.session_state["_scroll_target"] = "so-__all__"
        for _nm in _nav_markets:
            _nlabel = f"{_nav_flags.get(_nm,'')}  {_nm}"
            if st.button(_nlabel, key=f"jnav_{_nm}", width="stretch"):
                st.session_state["_scroll_target"] = f"so-{_nm}"

# ──────────────────────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero"><div><div class="eyebrow">NIAMITO / ANALYTICS</div>'
    '<h1>Business, in focus.</h1><p>Sales, marketing and product performance. One clear view.</p></div>'
    f'<div class="source-pill">{"Demonstration data" if demo_mode else "Workbook snapshot"} · {escape(period)}</div></div>',
    unsafe_allow_html=True,
)

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", "Sales", "Marketing", "Profitability", "Products", "Data & exports",
])
_allocation_start = (start_ts if period == "Custom range" else jan1_this_year if period == "This year (YTD)"
                     else today - pd.DateOffset(months=3) if period == "Last 3 months"
                     else today - pd.DateOffset(months=6) if period == "Last 6 months" else None)
_allocation_end = end_ts if period == "Custom range" else today if period != "All data" else None
_marketing_allocations = marketing_allocations(exp_df, _allocation_start, _allocation_end)
with tab0:
    render_overview(prim_f, so_f, mkt_f, prim_df, so_df, mkt_df, _marketing_allocations)
with tab5:
    render_data(prim_f, so_f, mkt_f, exp_df, demo_mode)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · SALES  (Level 1 Sell-In  +  Level 2 Sell-Out)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # Section header — clearly Level 1
    st.markdown(
        f"<div style='background:rgba(44,26,14,0.06);border-left:4px solid {BROWN};"
        f"border-radius:6px;padding:10px 16px;margin-bottom:10px;'>"
        f"<span style='font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
        f"color:{MID};'>Level 1 — Sell-In</span>"
        f"<h2 style='margin:2px 0 2px;font-size:20px;color:#1C1008;'>Invoiced Sales Command Center</h2>"
        f"<p style='font-size:12px;color:{MID};margin:0;'>"
        f"Factory invoices to distributor/retailer. These are your billed revenues — "
        f"what you have actually charged, regardless of what has sold through to consumers.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── KPI calculations ─────────────────────────────────────────────────────
    total_gross   = prim_f["gross_revenue"].sum() if not prim_f.empty else 0
    prim_pieces   = prim_f["bottles"].sum() if not prim_f.empty else 0
    avg_price_pc  = total_gross / max(prim_pieces, 1)

    # YoY comparison: same calendar window one year back
    def _prior_year_prim(pf_full, period_name, jan1_ty, today_ts, custom_range_val):
        if period_name == "This year (YTD)":
            py_start = jan1_ty - pd.DateOffset(years=1)
            py_end   = today_ts - pd.DateOffset(years=1)
        elif period_name == "Last 3 months":
            py_start = today_ts - pd.DateOffset(months=3) - pd.DateOffset(years=1)
            py_end   = today_ts - pd.DateOffset(years=1)
        elif period_name == "Last 6 months":
            py_start = today_ts - pd.DateOffset(months=6) - pd.DateOffset(years=1)
            py_end   = today_ts - pd.DateOffset(years=1)
        elif period_name == "Custom range" and custom_range_val and len(custom_range_val) == 2:
            py_start = pd.Timestamp(custom_range_val[0]) - pd.DateOffset(years=1)
            py_end   = pd.Timestamp(custom_range_val[1]) - pd.DateOffset(years=1)
        else:
            return pd.DataFrame()
        if pf_full.empty:
            return pd.DataFrame()
        return pf_full[(pf_full["week"] >= py_start) & (pf_full["week"] <= py_end)]

    # Apply same category filter to prior-year baseline so the comparison is apples-to-apples.
    # If the selected category didn't exist last year, py_df will be empty → no delta shown.
    _prim_df_cmp = prim_df.copy()
    if category_filter and len(category_filter) < len(ALL_CATEGORIES) and "category" in _prim_df_cmp.columns:
        _prim_df_cmp = _prim_df_cmp[_prim_df_cmp["category"].isin(category_filter)]
    py_df     = _prior_year_prim(_prim_df_cmp, period, jan1_this_year, today,
                                  custom_range if period == "Custom range" else None)
    py_pieces = py_df["bottles"].sum() if not py_df.empty else 0
    py_gross  = py_df["gross_revenue"].sum() if not py_df.empty else 0

    def _delta_str(curr, prev, is_currency=False):
        if prev == 0:
            return None
        diff = curr - prev
        pct  = diff / prev * 100
        sign = "+" if diff >= 0 else "-"
        if is_currency:
            return f"{sign}€{abs(diff):,.0f}  ({sign}{abs(pct):.1f}% vs same period last yr)"
        return f"{sign}{abs(diff):,.0f}  ({sign}{abs(pct):.1f}% vs same period last yr)"

    pieces_delta = _delta_str(prim_pieces, py_pieces)
    gross_delta  = _delta_str(total_gross, py_gross, is_currency=True)

    # ── 2026 run rate ─────────────────────────────────────────────────────────
    _pf_2026_all = prim_f[prim_f["week"].dt.year == 2026] if not prim_f.empty else prim_f
    if not _pf_2026_all.empty:
        _2026_mo_grp = (_pf_2026_all.copy()
                        .assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str))
                        .groupby("_mkey").agg(pieces=("bottles","sum"), revenue=("gross_revenue","sum"))
                        .reset_index())
        _n_actual_mo = len(_2026_mo_grp)
        _run_rate_pcs = int(_2026_mo_grp["pieces"].mean() * 12)
        _run_rate_rev = _2026_mo_grp["revenue"].mean() * 12
    else:
        _n_actual_mo = 0
        _run_rate_pcs = 0
        _run_rate_rev = 0.0

    # ── KPI row ───────────────────────────────────────────────────────────────
    ANNUAL_GOAL = 300_000
    _ytd_2026 = int(prim_f[prim_f["week"].dt.year == 2026]["bottles"].sum()) if not prim_f.empty else 0
    _goal_pct  = min(_ytd_2026 / ANNUAL_GOAL * 100, 100) if ANNUAL_GOAL > 0 else 0.0
    _remaining = max(ANNUAL_GOAL - _ytd_2026, 0)

    def _kpi_card(label, value, delta_str=None, color=GREEN, delta_good=True):
        return (
            f"<div class='kpi-card' style='border-top:3px solid {color};'>"
            f"<span>{escape(label)}</span><div class='kpi-value'>{escape(value)}</div>"
            f"<small>{escape(delta_str or '')}</small></div>"
        )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(_kpi_card("Pieces Sold", f"{prim_pieces:,.0f}", pieces_delta, color=GREEN,
                           delta_good=not pieces_delta.startswith("-") if pieces_delta else True),
                unsafe_allow_html=True)
    k2.markdown(_kpi_card("Gross Revenue", f"€{total_gross:,.0f}", gross_delta, color=CORAL,
                           delta_good=not gross_delta.startswith("-") if gross_delta else True),
                unsafe_allow_html=True)
    k3.markdown(_kpi_card("Avg Price / Piece", f"€{avg_price_pc:.2f}", color=YELLOW),
                unsafe_allow_html=True)
    if _run_rate_rev > 0:
        _rr_label = f"€{_run_rate_rev:,.0f}" if metric_mode != "Pieces sold" else f"{_run_rate_pcs:,}"
        k4.markdown(_kpi_card("Run Rate 2026", _rr_label, color=LAVEN), unsafe_allow_html=True)
    _goal_delta = f"−{_remaining:,} to go" if _remaining > 0 else "Goal reached"
    k5.markdown(_kpi_card("Goal Progress (300k)", f"{_goal_pct:.1f}%", _goal_delta,
                           color=BROWN if _goal_pct < 50 else (YELLOW if _goal_pct < 85 else GREEN),
                           delta_good=False),
                unsafe_allow_html=True)

    st.markdown("")


    # ── Monthly sales by category (full width) ───────────────────────────────
    if not prim_f.empty:
        _pf_mo = prim_f.copy()
        _pf_mo["_mkey"] = _pf_mo["week"].dt.to_period("M").astype(str)
        _pf_mo["month"] = _pf_mo["week"].dt.strftime("%b %Y")
        cat_monthly = _pf_mo.groupby(["_mkey", "month", "category"]).agg(
            pieces=("bottles","sum"),
            revenue=("gross_revenue","sum"),
        ).reset_index().sort_values("_mkey")
        y_col   = "pieces" if metric_mode == "Pieces sold" else "revenue"
        y_label = "Pieces" if metric_mode == "Pieces sold" else "Revenue (\u20ac)"
        fig_sw = go.Figure()
        for cat in ALL_CATEGORIES:
            d = cat_monthly[cat_monthly["category"] == cat]
            if d.empty:
                continue
            fig_sw.add_trace(go.Bar(
                x=d["month"], y=d[y_col],
                name=cat,
                marker_color=CATEGORY_COLORS.get(cat, BROWN),
                hovertemplate=f"<b>{cat}</b><br>%{{x}}: %{{y:,}}<extra></extra>",
            ))
        _months_ordered = (cat_monthly[["_mkey","month"]].drop_duplicates()
                           .sort_values("_mkey")["month"].tolist())
        l_sw = base_layout(f"Monthly Sales by Category ({y_label})", height=300)
        l_sw["barmode"] = "stack"
        l_sw["xaxis"]["tickangle"] = -30
        l_sw["xaxis"]["categoryorder"] = "array"
        l_sw["xaxis"]["categoryarray"] = _months_ordered
        if metric_mode != "Pieces sold":
            l_sw["yaxis"]["tickprefix"] = "\u20ac"
        fig_sw.update_layout(**l_sw)
        st.plotly_chart(fig_sw, width="stretch", theme=None, config={"displaylogo": False})
    else:
        st.info("No primary sales data.")

    # ── 2026 Forecast (full width) ────────────────────────────────────────────
    _fc_y   = "pieces" if metric_mode == "Pieces sold" else "revenue"
    _fc_lbl = "Pieces" if metric_mode == "Pieces sold" else "Revenue (\u20ac)"

    if not _pf_2026_all.empty and _n_actual_mo > 0:
        _fc_act = (_pf_2026_all.copy()
                   .assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str),
                           month=lambda d: d["week"].dt.strftime("%b %Y"))
                   .groupby(["_mkey","month"]).agg(
                       pieces=("bottles","sum"), revenue=("gross_revenue","sum"))
                   .reset_index().sort_values("_mkey"))

        _actual_mkeys = set(_fc_act["_mkey"])
        _all_2026_mkeys = [f"2026-{m:02d}" for m in range(1, 13)]
        _fc_mkeys = [mk for mk in _all_2026_mkeys if mk not in _actual_mkeys]
        _fc_labels = [pd.Period(mk).strftime("%b %Y") for mk in _fc_mkeys]

        # Forecast controls
        _fc_ctrl1, _fc_ctrl2, _fc_ctrl3 = st.columns([0.28, 0.28, 0.44])
        with _fc_ctrl1:
            _fc_type = st.selectbox(
                "Forecast method",
                ["Seasonal (prior year)", "Growth rate %", "Linear trend",
                 "ETS (exp. smoothing)", "Flat (last month)", "Goal-paced (300k)"],
                key="fc_type_sel",
            )
        with _fc_ctrl2:
            _fc_scenario = st.selectbox(
                "Scenario",
                ["Base", "Optimistic (+20%)", "Conservative (−20%)"],
                key="fc_scenario_sel",
            )

        _last_actual = float(_fc_act[_fc_y].iloc[-1]) if not _fc_act.empty else 0.0
        _growth_pct  = 0    # overwritten if method is "Growth rate %"
        _yoy         = None # overwritten if method is "Seasonal (prior year)"

        # Compute forecast values by method
        if _fc_type == "Growth rate %":
            with _fc_ctrl3:
                _growth_pct = st.slider(
                    "Monthly growth (%)",
                    min_value=-10, max_value=30, value=5, step=1,
                    key="fc_growth_slider",
                    help="Compounded month-over-month from the last actual month.",
                )
            _growth_rate = _growth_pct / 100.0
            _fc_values = [_last_actual * ((1 + _growth_rate) ** (i + 1))
                          for i in range(len(_fc_labels))]

        elif _fc_type == "Linear trend":
            import numpy as _np
            _x = list(range(len(_fc_act)))
            _y = _fc_act[_fc_y].tolist()
            if len(_x) >= 2:
                _coeffs = _np.polyfit(_x, _y, 1)
                _fc_values = [max(0.0, _np.polyval(_coeffs, len(_x) + i))
                              for i in range(len(_fc_labels))]
            else:
                _fc_values = [_last_actual] * len(_fc_labels)

        elif _fc_type == "Seasonal (prior year)":
            # Use same calendar month from prior year, scaled by observed YoY growth
            import numpy as _np
            _all_hist = (prim_df.copy()
                         .assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str))
                         .groupby("_mkey").agg(pieces=("bottles","sum"),
                                                revenue=("gross_revenue","sum"))
                         .reset_index())
            _all_hist["year"]  = _all_hist["_mkey"].str[:4].astype(int)
            _all_hist["mo"]    = _all_hist["_mkey"].str[5:].astype(int)
            _py_tbl = _all_hist[_all_hist["year"] == _fc_act["_mkey"].str[:4].astype(int).max() - 1].set_index("mo")
            # YoY growth factor from overlapping months (current year vs prior year)
            _act_mo = _fc_act.copy()
            _act_mo["mo"] = _act_mo["_mkey"].str[5:].astype(int)
            _overlap = set(_py_tbl.index) & set(_act_mo["mo"])
            if _overlap and not _py_tbl.empty:
                _cur_sum = _act_mo[_act_mo["mo"].isin(_overlap)][_fc_y].sum()
                _pyr_sum = _py_tbl.loc[list(_overlap), _fc_y].sum()
                _yoy     = _cur_sum / _pyr_sum if _pyr_sum > 0 else 1.15
            else:
                _yoy = 1.15  # assume +15% growth if no overlap
            _fc_values = []
            for _mk in _fc_mkeys:
                _mn = int(_mk[5:])
                if _mn in _py_tbl.index:
                    _fc_values.append(float(_py_tbl.loc[_mn, _fc_y]) * _yoy)
                else:
                    _fc_values.append(_last_actual * _yoy)

        elif _fc_type == "ETS (exp. smoothing)":
            # Holt's double exponential smoothing (level + trend)
            # L[t] = α·y[t] + (1−α)·(L[t−1]+T[t−1])
            # T[t] = β·(L[t]−L[t−1]) + (1−β)·T[t−1]
            # Forecast h steps ahead = L[n] + h·T[n]
            _hist_vals = _fc_act[_fc_y].tolist()
            if len(_hist_vals) >= 2:
                _alpha, _beta = 0.4, 0.2
                _L = _hist_vals[0]
                _T = _hist_vals[1] - _hist_vals[0]
                for _v in _hist_vals[1:]:
                    _L_prev, _T_prev = _L, _T
                    _L = _alpha * _v + (1 - _alpha) * (_L_prev + _T_prev)
                    _T = _beta  * (_L - _L_prev) + (1 - _beta) * _T_prev
                _fc_values = [max(0.0, _L + (i + 1) * _T)
                              for i in range(len(_fc_labels))]
            else:
                _fc_values = [_last_actual] * len(_fc_labels)

        elif _fc_type == "Flat (last month)":
            _fc_values = [_last_actual] * len(_fc_labels)

        else:  # Goal-paced (300k)
            _ytd_val = float(_fc_act[_fc_y].sum())
            _mo_left = len(_fc_labels)
            _goal_val = 300_000 if _fc_y == "pieces" else (_ytd_val / max(float(_fc_act["pieces"].sum()), 1) * 300_000)
            _needed = max(_goal_val - _ytd_val, 0)
            _mo_target = _needed / _mo_left if _mo_left > 0 else 0.0
            _fc_values = [_mo_target] * len(_fc_labels)

        # Apply scenario multiplier
        _sc_mult = {"Base": 1.0, "Optimistic (+20%)": 1.20, "Conservative (−20%)": 0.80}
        _mult = _sc_mult.get(_fc_scenario, 1.0)
        _fc_values = [v * _mult for v in _fc_values]

        _fc_prefix = "€" if _fc_y == "revenue" else ""
        _fc_total  = _fc_act[_fc_y].sum() + sum(_fc_values)

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Bar(
            x=_fc_act["month"], y=_fc_act[_fc_y],
            name="Actual", marker_color=BROWN, opacity=0.92,
            hovertemplate=f"%{{x}}: %{{y:,.0f}} {_fc_lbl} (actual)<extra></extra>",
        ))
        _fc_legend_label = {
            "Growth rate %":        f"Forecast ({'+' if _growth_pct >= 0 else ''}{_growth_pct}%/mo)",
            "Linear trend":         "Forecast (linear trend)",
            "Flat (last month)":    "Forecast (flat)",
            "Goal-paced (300k)":    "Forecast (goal-paced)",
            "Seasonal (prior year)": f"Forecast (seasonal ×{_yoy:.2f} YoY)" if _yoy else "Forecast (seasonal)",
            "ETS (exp. smoothing)": "Forecast (ETS smoothing)",
        }.get(_fc_type, "Forecast")
        if _fc_labels:
            fig_fc.add_trace(go.Bar(
                x=_fc_labels, y=_fc_values,
                name=_fc_legend_label,
                marker_color=LAVEN, opacity=0.65,
                hovertemplate=f"%{{x}}: %{{y:,.0f}} {_fc_lbl} (projected)<extra></extra>",
            ))
        l_fc = base_layout(
            f"2026 Actuals + Forecast  ·  Full-year estimate: {_fc_prefix}{int(_fc_total):,}",
            height=280,
        )
        l_fc["barmode"] = "overlay"
        l_fc["xaxis"]["tickangle"] = -30
        l_fc["legend"]["orientation"] = "h"
        l_fc["legend"]["y"] = -0.28
        if _fc_y == "revenue":
            l_fc["yaxis"]["tickprefix"] = "\u20ac"
        fig_fc.update_layout(**l_fc)
        st.plotly_chart(fig_fc, width="stretch", theme=None, config={"displaylogo": False})

    # ── Monthly performance table ─────────────────────────────────────────────
    if not prim_f.empty:
        _mo_tbl = (prim_f.copy()
                   .assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str),
                           month=lambda d: d["week"].dt.strftime("%b %Y"))
                   .groupby(["_mkey","month"]).agg(
                       pieces=("bottles","sum"), revenue=("gross_revenue","sum"))
                   .reset_index().sort_values("_mkey"))
        _mo_tbl["MoM %"] = _mo_tbl["revenue"].pct_change() * 100
        _mo_tbl = _mo_tbl.sort_values("_mkey", ascending=False)
        _mo_tbl_out = _mo_tbl[["month","pieces","revenue","MoM %"]].copy()
        _mo_tbl_out.columns = ["Month","Pieces","Revenue (€)","MoM %"]
        _mo_tbl_out["Pieces"]      = _mo_tbl_out["Pieces"].apply(lambda x: f"{int(x):,}")
        _mo_tbl_out["Revenue (€)"] = _mo_tbl_out["Revenue (€)"].apply(lambda x: f"€{x:,.0f}")
        _mo_tbl_out["MoM %"]       = _mo_tbl_out["MoM %"].apply(
            lambda x: f"+{x:.1f}%" if pd.notna(x) and x >= 0 else (f"{x:.1f}%" if pd.notna(x) else "—"))
        st.markdown(
            f"<p style='font-size:12px; color:{MID}; margin:4px 0 6px;'>"
            "<b>Monthly Performance</b></p>",
            unsafe_allow_html=True,
        )
        st.dataframe(_mo_tbl_out, width="stretch", hide_index=True)

    # ── Sales by category summary table ──────────────────────────────────────
    if not prim_f.empty:
        _cat_summary = prim_f.groupby("category").agg(
            pieces=("bottles", "sum"),
            revenue=("gross_revenue", "sum"),
        ).reset_index().sort_values("revenue", ascending=False)
        _cat_summary["Avg price/pc (€)"] = (_cat_summary["revenue"] / _cat_summary["pieces"].clip(lower=1)).round(2)
        _cat_summary.columns = ["Category", "Pieces", "Revenue (€)", "Avg price/pc (€)"]
        _cat_summary["Pieces"] = _cat_summary["Pieces"].apply(lambda x: f"{int(x):,}")
        _cat_summary["Revenue (€)"] = _cat_summary["Revenue (€)"].apply(lambda x: f"€{x:,.0f}")
        _cat_summary["Avg price/pc (€)"] = _cat_summary["Avg price/pc (€)"].apply(lambda x: f"€{x:.2f}")
        st.markdown(
            f"<p style='font-size:12px; color:{MID}; margin:4px 0 6px;'>"
            "<b>Sales by Product Category</b></p>",
            unsafe_allow_html=True,
        )
        st.dataframe(_cat_summary, width="stretch", hide_index=True)

    # ── divider between Level 1 and Level 2 ──────────────────────────────────
    st.markdown(
        f"<div style='margin:32px 0 24px;border-top:2px solid {BROWN}33;'></div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 2 — SELL-OUT: MARKET SHELF VELOCITY
    # ══════════════════════════════════════════════════════════════════════════
    # Section header — clearly Level 2
    st.markdown(
        f"<div style='background:rgba(168,217,154,0.15);border-left:4px solid {GREEN};"
        f"border-radius:6px;padding:10px 16px;margin-bottom:10px;'>"
        f"<span style='font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;"
        f"color:{MID};'>Level 2 — Sell-In to Retail</span>"
        f"<h2 style='margin:2px 0 2px;font-size:20px;color:#1C1008;'>Market Shelf Velocity</h2>"
        f"<p style='font-size:12px;color:{MID};margin:0;'>"
        f"Sell-In to retail — either through a distributor or direct. "
        f"Numbers reflect what physically moved into store shelves in the selected period.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    def _country_gap_data(market_code):
        """Return (gap_df, cum_si, cum_so, cover_days) for a market (or all markets).
        Uses period-filtered so_f / prim_f so charts match the selected period."""
        _so_src = so_f if market_code == "All" else (
            so_f[so_f["market"] == market_code] if not so_f.empty else so_f)
        _pi_src = prim_f if market_code == "All" else (
            prim_f[prim_f["market"] == market_code] if not prim_f.empty else prim_f)

        _pf_mo = pd.DataFrame()
        if not _pi_src.empty and "week" in _pi_src.columns:
            _pf_mo = (_pi_src.assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str))
                      .groupby("_mkey")["bottles"].sum().reset_index())
            _pf_mo["month"] = _pf_mo["_mkey"].apply(lambda m: pd.Period(m).strftime("%b %Y"))

        _so_mo = pd.DataFrame()
        if not _so_src.empty and "week" in _so_src.columns:
            _so_mo = (_so_src.assign(_mkey=lambda d: d["week"].dt.to_period("M").astype(str))
                      .groupby("_mkey")["bottles_sold"].sum().reset_index())
            _so_mo["month"] = _so_mo["_mkey"].apply(lambda m: pd.Period(m).strftime("%b %Y"))

        _si_ready = _pf_mo if not _pf_mo.empty else pd.DataFrame(columns=["_mkey", "bottles", "month"])
        _so_ready = _so_mo if not _so_mo.empty else pd.DataFrame(columns=["_mkey", "bottles_sold", "month"])
        gap = (_si_ready.rename(columns={"bottles": "sell_in"})
               .merge(_so_ready.rename(columns={"bottles_sold": "sell_out"}), on="_mkey", how="outer")
               .sort_values("_mkey").fillna(0))
        gap["month"] = gap.apply(
            lambda r: r.get("month_x") or r.get("month_y") or
            pd.Period(r["_mkey"]).strftime("%b %Y"), axis=1)

        cum_si = gap["sell_in"].sum()
        cum_so = gap["sell_out"].sum()
        implied = cum_si - cum_so

        _last_3mo = today - pd.DateOffset(months=3)
        _rec = _so_src[_so_src["week"] >= _last_3mo] if not _so_src.empty else _so_src
        _rec_units = _rec["bottles_sold"].sum() if not _rec.empty else 0
        _rec_days = max((_so_src["week"].max() - _last_3mo).days
                        if not _so_src.empty and pd.notna(_so_src["week"].max()) else 90, 1)
        _vel = _rec_units / _rec_days
        cover = int(implied / _vel) if _vel > 0 and implied > 0 else 0

        return gap, int(cum_si), int(cum_so), cover

    if not so_f.empty:
        _MARKET_ORDER_SO = ["SI", "HR", "DE", "PL", "CH", "ME", "AT"]
        _so_mkts_available = so_df["market"].unique().tolist() if "market" in so_df.columns else ["SI"]
        _so_markets_all = [m for m in _MARKET_ORDER_SO if m in _so_mkts_available] + \
                          [m for m in _so_mkts_available if m not in _MARKET_ORDER_SO]
        _country_flags  = {"SI": "🇸🇮", "HR": "🇭🇷", "ME": "🇲🇪", "DE": "🇩🇪", "PL": "🇵🇱", "CH": "🇨🇭", "AT": "🇦🇹"}

        # ── JS scroll injection ───────────────────────────────────────────────
        if st.session_state.get("_scroll_target"):
            _anchor = st.session_state["_scroll_target"]
            import streamlit.components.v1 as _stc
            _stc.html(
                f"""<script>
                    var el = window.parent.document.getElementById('{_anchor}');
                    if (el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
                </script>""",
                height=0,
            )
            st.session_state["_scroll_target"] = None

        # ── ALL MARKETS overview ──────────────────────────────────────────────
        st.markdown(
            '<div id="so-__all__"></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='font-size:12px;color:{MID};margin-bottom:8px;'>"
            "Cross-country inventory health at a glance. Scroll down for the full breakdown per market.</p>",
            unsafe_allow_html=True,
        )

        # Build comparison matrix
        _matrix_rows = []
        for _m in _so_markets_all:
            _so_m   = so_f[so_f["market"] == _m] if "market" in so_f.columns else so_df
            _pi_m   = prim_f[prim_f["market"] == _m] if not prim_f.empty and "market" in prim_f.columns else pd.DataFrame()
            _stores = int(_so_m["retailer"].nunique()) if "retailer" in _so_m.columns else 0
            _so_btl = int(_so_m["bottles_sold"].sum())
            _si_btl = int(_pi_m["bottles"].sum()) if not _pi_m.empty else 0
            _so_rev = _so_m["sellout_revenue"].sum() if "sellout_revenue" in _so_m.columns else 0
            _matrix_rows.append({
                "Country":         f"{_country_flags.get(_m, '')} {_m}",
                "Sell-In (btl)":   f"{_so_btl:,}",
                "Sell-In Rev (€)": f"€{_so_rev:,.0f}" if _so_rev > 0 else "—",
            })
        _mx_df = pd.DataFrame(_matrix_rows)
        st.dataframe(_mx_df, width="stretch", hide_index=True)

        # Summary bar: Sell-In (to retail) by country
        if len(_so_markets_all) > 1:
            _sum_so = [int(so_f[so_f["market"] == m]["bottles_sold"].sum())
                       if "market" in so_f.columns else 0
                       for m in _so_markets_all]
            _sum_labels = [f"{_country_flags.get(m,'')} {m}" for m in _so_markets_all]
            fig_sum = go.Figure()
            fig_sum.add_trace(go.Bar(
                x=_sum_labels, y=_sum_so, name="Sell-In (to retail)",
                marker_color=GREEN, opacity=0.88,
                hovertemplate="%{x}<br>Sell-In: %{y:,} btl<extra></extra>",
            ))
            l_sum = base_layout("Sell-In to Retail by Country (selected period)", height=280)
            l_sum["barmode"] = "group"
            fig_sum.update_layout(**l_sum)
            st.plotly_chart(fig_sum, width="stretch", key="fig_sum_all")

        # ── PER-COUNTRY sections (long scroll) ───────────────────────────────
        for _mkt in _so_markets_all:
            # Country section anchor + divider
            st.markdown(
                f'<div id="so-{_mkt}" style="padding-top:4px;"></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='margin:28px 0 14px;border-top:1px solid {BROWN}28;'></div>"
                f"<h3 style='font-size:16px;font-weight:700;color:#1C1008;margin:0 0 12px;'>"
                f"{_country_flags.get(_mkt, '')} {_mkt}</h3>",
                unsafe_allow_html=True,
            )

            _so2 = so_f[so_f["market"] == _mkt].copy() if "market" in so_f.columns else so_f.copy()
            _pf2 = prim_f[prim_f["market"] == _mkt].copy() if not prim_f.empty and "market" in prim_f.columns else prim_f.copy()

            _gap_c, _cum_si_c, _cum_so_c, _cover_c = _country_gap_data(_mkt)
            _so2_units  = int(_so2["bottles_sold"].sum())
            _so2_stores = int(_so2["retailer"].nunique()) if "retailer" in _so2.columns else 0
            _so2_rev    = _so2["sellout_revenue"].sum() if "sellout_revenue" in _so2.columns else 0.0
            _si_units   = int(_pf2["bottles"].sum()) if not _pf2.empty else 0

            # ── KPIs ─────────────────────────────────────────────────────────
            # Prior-year secondary sales for this market → YoY deltas
            _so_full_mkt = (so_df[so_df["market"] == _mkt].copy()
                            if not so_df.empty and "market" in so_df.columns else pd.DataFrame())
            _so_py = _prior_year_prim(
                _so_full_mkt, period, jan1_this_year, today,
                custom_range if period == "Custom range" else None)
            _py_so_units = (int(_so_py["bottles_sold"].sum())
                            if not _so_py.empty and "bottles_sold" in _so_py.columns else 0)
            _py_so_rev   = (_so_py["sellout_revenue"].sum()
                            if not _so_py.empty and "sellout_revenue" in _so_py.columns else 0.0)
            _so2_delta_u = _delta_str(_so2_units, _py_so_units) if _py_so_units > 0 else None
            _so2_delta_r = _delta_str(_so2_rev, _py_so_rev, is_currency=True) if _py_so_rev > 0 else None
            _avg_btl_price = round(_so2_rev / _so2_units, 2) if _so2_units > 0 and _so2_rev > 0 else 0.0
            _n_skus = _so2["sku_id"].nunique() if "sku_id" in _so2.columns and not _so2.empty else 0

            ck1, ck2, ck3, ck4 = st.columns(4)
            ck1.markdown(_kpi_card("Sell-In (to retail)", f"{_so2_units:,} btl",
                                   _so2_delta_u, color=GREEN),
                         unsafe_allow_html=True)
            if _so2_rev > 0:
                ck2.markdown(_kpi_card("Sell-In Revenue", f"€{_so2_rev:,.0f}",
                                       _so2_delta_r, color=CORAL),
                             unsafe_allow_html=True)
            if _avg_btl_price > 0:
                ck3.markdown(_kpi_card("Avg Price / Bottle", f"€{_avg_btl_price:.2f}",
                                       color=YELLOW),
                             unsafe_allow_html=True)
            if _n_skus > 0:
                ck4.markdown(_kpi_card("Active SKUs", str(_n_skus), color=LAVEN),
                             unsafe_allow_html=True)

            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

            # ── Sell-In monthly trend (stacked by product category) ──────────
            _so2_chart = _so2.copy() if not _so2.empty else pd.DataFrame()
            if not _so2_chart.empty and "week" in _so2_chart.columns and "bottles_sold" in _so2_chart.columns:
                _so2_chart["_mkey"] = _so2_chart["week"].dt.to_period("M").astype(str)
                _so2_chart["_month_lbl"] = _so2_chart["_mkey"].apply(
                    lambda m: pd.Period(m).strftime("%b %Y"))
                _cat_col = "category" if "category" in _so2_chart.columns else None
                _CAT_COLORS = {
                    "Niamito Fresh Meal":       GREEN,
                    "Niamito Oatmeal":          BROWN,
                    "Niamito Meal in a Bottle": LAVEN,
                }
                if _cat_col:
                    _si_pivot = (_so2_chart
                                 .groupby(["_mkey", "_month_lbl", _cat_col])["bottles_sold"]
                                 .sum().reset_index()
                                 .pivot(index=["_mkey","_month_lbl"], columns=_cat_col,
                                        values="bottles_sold")
                                 .fillna(0).reset_index()
                                 .sort_values("_mkey"))
                    _cats_present = [c for c in ALL_CATEGORIES if c in _si_pivot.columns]
                    fig_gap = go.Figure()
                    for _ci, _cat in enumerate(_cats_present):
                        fig_gap.add_trace(go.Bar(
                            x=_si_pivot["_month_lbl"],
                            y=_si_pivot[_cat],
                            name=_cat.replace("Niamito ", ""),
                            marker_color=_CAT_COLORS.get(_cat, CORAL),
                            opacity=0.92,
                            hovertemplate=f"<b>{_cat.replace('Niamito ','')}</b><br>"
                                          "%{x}<br>%{y:,} btl<extra></extra>",
                        ))
                else:
                    _si_mo = (_so2_chart.groupby(["_mkey","_month_lbl"])["bottles_sold"]
                              .sum().reset_index().sort_values("_mkey"))
                    fig_gap = go.Figure(go.Bar(
                        x=_si_mo["_month_lbl"], y=_si_mo["bottles_sold"],
                        name="Sell-In", marker_color=GREEN, opacity=0.92,
                        hovertemplate="%{x}<br>%{y:,} btl<extra></extra>",
                    ))
                l_gap = base_layout(
                    f"Monthly Sell-In — {_country_flags.get(_mkt,'')} {_mkt}",
                    height=280)
                l_gap["xaxis"]["tickangle"] = -35
                l_gap["barmode"] = "stack"
                fig_gap.update_layout(**l_gap)
                st.plotly_chart(fig_gap, width="stretch", key=f"fig_gap_{_mkt}")

            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

            # ── Top Retailers ─────────────────────────────────────────────────
            if not _so2.empty and "retailer" in _so2.columns and _so2["retailer"].notna().any():
                col_ret, col_mix = st.columns([0.60, 0.40])

                with col_ret:
                    _top_ret = (_so2.groupby("retailer")["bottles_sold"].sum()
                                .reset_index().sort_values("bottles_sold", ascending=True).tail(15))
                    _ret_colors = [BROWN if i % 2 == 0 else LAVEN for i in range(len(_top_ret))]
                    fig_ret = go.Figure(go.Bar(
                        x=_top_ret["bottles_sold"], y=_top_ret["retailer"],
                        orientation="h",
                        marker=dict(color=_ret_colors, line=dict(color=CREAM, width=0.5)),
                        text=[f"{int(v):,}" for v in _top_ret["bottles_sold"]],
                        textposition="outside",
                        hovertemplate="<b>%{y}</b><br>%{x:,} btl<extra></extra>",
                    ))
                    l_ret = base_layout(f"Top Retailer Accounts — {_country_flags.get(_mkt,'')} {_mkt}",
                                        height=max(300, len(_top_ret) * 26))
                    l_ret["xaxis"]["title"] = "Bottles Sold"
                    l_ret["margin"]["l"] = 230
                    l_ret["margin"]["r"] = 70
                    fig_ret.update_layout(**l_ret)
                    st.plotly_chart(fig_ret, width="stretch", key=f"fig_ret_{_mkt}")

                with col_mix:
                    _cat_mix = (_so2.groupby("sku_name")["bottles_sold"].sum()
                                .reset_index().sort_values("bottles_sold", ascending=False))
                    if not _cat_mix.empty:
                        _mix_colors = [CATEGORY_COLORS.get(get_product_category(n), BROWN)
                                       for n in _cat_mix["sku_name"]]
                        fig_mix = go.Figure(go.Pie(
                            labels=_cat_mix["sku_name"], values=_cat_mix["bottles_sold"],
                            hole=0.50,
                            marker=dict(colors=_mix_colors, line=dict(color=CREAM, width=2)),
                            textinfo="percent",
                            hovertemplate="<b>%{label}</b><br>%{value:,} btl  (%{percent})<extra></extra>",
                        ))
                        l_mix = base_layout("Product Mix", height=300, legend_below=False)
                        l_mix["legend"] = dict(orientation="v", x=1.02, y=0.5,
                                               font=dict(size=9, color=BROWN), bgcolor="rgba(0,0,0,0)")
                        fig_mix.update_layout(**l_mix)
                        st.plotly_chart(fig_mix, width="stretch", key=f"fig_mix_{_mkt}")

                # Retailer detail table
                st.markdown(
                    f"<p style='font-size:12px;font-weight:600;color:{BROWN};margin:8px 0 4px;'>"
                    f"All Stores — {_country_flags.get(_mkt,'')} {_mkt}</p>",
                    unsafe_allow_html=True,
                )
                _agg_kw = {"units": ("bottles_sold", "sum"), "skus": ("sku_name", "nunique")}
                if "sellout_revenue" in _so2.columns and _so2["sellout_revenue"].sum() > 0:
                    _rtbl = (_so2.groupby("retailer").agg(**_agg_kw, revenue=("sellout_revenue", "sum"))
                             .reset_index().sort_values("units", ascending=False))
                    _rtbl.columns = ["Store", "Units Sold", "SKUs", "Revenue (€)"]
                    _rtbl["Revenue (€)"] = _rtbl["Revenue (€)"].apply(lambda x: f"€{x:,.0f}")
                else:
                    _rtbl = (_so2.groupby("retailer").agg(**_agg_kw)
                             .reset_index().sort_values("units", ascending=False))
                    _rtbl.columns = ["Store", "Units Sold", "SKUs"]
                _rtbl["Units Sold"] = _rtbl["Units Sold"].apply(lambda x: f"{int(x):,}")
                st.dataframe(_rtbl, width="stretch", hide_index=True)

            elif _so2.empty:
                st.info(f"No sell-out data for {_mkt} in the selected period.")

    else:
        st.info("No secondary sales data available. Upload a file with a Secondary Sales sheet.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · MARKETING
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    render_marketing(mkt_f, prim_f, so_f, _marketing_allocations)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · PROFITABILITY
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    note("2026 expense model", "This view retains the existing annual cost and inventory model. Sales filters change revenue; expenses remain the full 2026 model for the selected products. Costs have no market allocation, so a single-market selection is not a market P&L.", "amber")

    st.markdown("<h2>Profitability — From Revenue to Gross Margin</h2>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:12px; color:{MID};'>"
        "Gross revenue minus costs gives the gross margin. "
        "Each bar below shows how much of the top line survives after each deduction.</p>",
        unsafe_allow_html=True,
    )

    # ── Context banner ────────────────────────────────────────────────────────
    if not demo_mode:
        _MO_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        _exp_months_raw = exp_df["month"].unique().tolist() if not exp_df.empty else []
        _exp_months_sorted = sorted(_exp_months_raw, key=lambda m: _MO_ORDER.index(m[:3]) if m[:3] in _MO_ORDER else 99)
        _exp_range = (f"{_exp_months_sorted[0]} – {_exp_months_sorted[-1]}"
                      if len(_exp_months_sorted) >= 2
                      else (_exp_months_sorted[0] if _exp_months_sorted else "n/a"))
        _prim_2026_pieces = prim_f[prim_f["week"].dt.year == 2026]["bottles"].sum() if not prim_f.empty else 0
        _raw_prod_cost = exp_df["production_cost"].sum() if not exp_df.empty else 0
        _cost_per_pc = (_raw_prod_cost / max(_prim_2026_pieces, 1)) if not exp_df.empty else 0
        st.markdown(
            f"""<div style='background:#efebf7;border-left:4px solid {BROWN};padding:10px 16px;
            border-radius:6px;margin-bottom:12px;font-size:13px;color:#51495b;line-height:1.9;'>
            <b>Revenue:</b> 2026 primary invoices only &nbsp;·&nbsp;
            <b>Costs:</b> Expenses {_exp_range} 2026 (all 12 months of annual cost plan) &nbsp;·&nbsp;
            <b>Units sold (2026):</b> {int(_prim_2026_pieces):,} pcs &nbsp;·&nbsp;
            <b>Full-year prod. cost/pc:</b> €{_cost_per_pc:.2f}<br>
            <b>Formula:</b> Gross Revenue − Material Cost − Labour &amp; Overhead + Active Stock + Internal Usage − Logistics − Mktg &amp; Promo − Promotional Units = Gross Margin
            </div>""",
            unsafe_allow_html=True,
        )

    _avail_mkt = sorted(prim_f["market"].unique().tolist()) if not prim_f.empty else []
    _wf_opts = ["All markets"] + _avail_mkt
    wf_mkt = st.radio("Market:", options=_wf_opts, horizontal=True, key="wf_mkt")

    # Profitability uses 2026 revenue only (expenses are 2026-only; mixing years distorts margins)
    _prim_2026 = prim_f[prim_f["week"].dt.year == 2026] if not prim_f.empty else prim_f
    p_data = _prim_2026 if wf_mkt == "All markets" else (
        _prim_2026[_prim_2026["market"] == wf_mkt] if not _prim_2026.empty else _prim_2026)
    m_data = mkt_f if wf_mkt == "All markets" else (
        mkt_f[mkt_f["market"].isin([wf_mkt, "ALL"])] if not mkt_f.empty else mkt_f)

    gross      = p_data["gross_revenue"].sum() if not p_data.empty else 0
    trade_disc = p_data["trade_discount"].sum() if not p_data.empty else 0
    mkt_spend  = m_data["total_spend"].sum() if not m_data.empty else 0

    # ── Filter expenses by product category ──────────────────────────────────
    _CAT_PL_KW = {
        "Niamito Fresh Meal":         ["fresh meal", "fresh"],
        "Niamito Oatmeal":            ["oatmeal", "oat"],
        "Niamito Meal in a Bottle":   ["uht meal", "uht"],
    }
    if not exp_df.empty and category_filter and len(category_filter) < len(ALL_CATEGORIES):
        _kws = [kw for cat in category_filter for kw in _CAT_PL_KW.get(cat, [])]
        _pl_mask = exp_df["product_line"].str.lower().str.contains("|".join(_kws), na=False)
        exp_df_pf = exp_df[_pl_mask]
    else:
        exp_df_pf = exp_df

    def _exp_sum(col):
        return exp_df_pf[col].sum() if not exp_df_pf.empty and col in exp_df_pf.columns else 0.0

    # Pull expense totals from per-row columns
    mat_cost     = _exp_sum("material_cost")
    lab_cost     = _exp_sum("labour_overhead")
    prod_cost    = _exp_sum("production_cost")
    logistics    = _exp_sum("logistics")
    mktg_promo   = _exp_sum("marketing_promo")
    promo_units  = _exp_sum("promo_units")    # outflow — separate bar next to Mktg
    internal_val = _exp_sum("internal_usage") # always positive — sold at production cost

    # Active Stock is a running balance (ending inventory value) per SKU, not a monthly flow.
    # Take the last value from months where production actually happened (production_cost > 0)
    # to avoid formula-error months in the Excel.
    if not exp_df_pf.empty and "active_stock" in exp_df_pf.columns and "production_cost" in exp_df_pf.columns:
        _prod_rows = exp_df_pf[exp_df_pf["production_cost"] > 0]
        if not _prod_rows.empty and "sku" in _prod_rows.columns:
            _mon_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            _prod_rows = _prod_rows.copy()
            _prod_rows["_mon_idx"] = _prod_rows["month"].map(
                lambda m: _mon_order.index(m) if m in _mon_order else 99)
            _last_stock = (_prod_rows.sort_values("_mon_idx")
                           .groupby(["product_line","sku"])["active_stock"].last())
            active_stock = float(_last_stock.sum())
        else:
            active_stock = 0.0
    else:
        active_stock = 0.0

    # Fallback: if dedicated columns absent, split production_cost 50/50
    if mat_cost == 0 and lab_cost == 0 and prod_cost > 0:
        mat_cost = prod_cost * 0.5
        lab_cost = prod_cost - mat_cost

    # ── P&L ───────────────────────────────────────────────────────────────────
    # active_stock: production cost that becomes inventory → adds back to margin
    # internal_val: sold to ourselves at production cost → adds back to margin
    # promo_units / mktg_promo / logistics: outflows → reduce margin
    gross_margin = (gross
                    - mat_cost - lab_cost
                    + active_stock + internal_val
                    - logistics - mktg_promo - promo_units)
    total_exp    = (mat_cost + lab_cost
                    + logistics + mktg_promo + promo_units
                    - active_stock - internal_val)

    # ── Waterfall ─────────────────────────────────────────────────────────────
    if prod_cost > 0 or logistics > 0 or mktg_promo > 0:
        wf_labels  = ["Gross Revenue", "Material Cost", "Labour & Overhead",
                      "Active Stock", "Internal Usage",
                      "Logistics", "Mktg & Promo", "Promotional Units"]
        wf_measure = ["absolute",      "relative",          "relative",
                      "relative",      "relative",
                      "relative",      "relative",          "relative"]
        wf_values  = [gross,           -mat_cost,           -lab_cost,
                      +active_stock,   +internal_val,
                      -logistics,      -mktg_promo,         -promo_units]
        wf_labels.append("Gross Margin")
        wf_measure.append("total")
        wf_values.append(gross_margin)
    else:
        wf_labels  = ["Gross Revenue", "Marketing Spend", "Gross Margin"]
        wf_measure = ["absolute",       "relative",        "total"]
        gross_margin = gross - mkt_spend
        wf_values  = [gross,            -mkt_spend,        gross_margin]

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
        totals=dict(marker=dict(color=CORAL if gross_margin < 0 else GREEN)),
        hovertemplate="<b>%{x}</b><br>\u20ac%{y:,.0f}<extra></extra>",
    ))
    margin_pct = gross_margin / max(gross, 1) * 100
    layout_wf = base_layout(
        f"Profitability Waterfall — {wf_mkt}  ·  Gross Margin: {margin_pct:.1f}%",
        height=400,
    )
    layout_wf["yaxis"]["tickprefix"] = "\u20ac"
    # Ensure the y-axis always shows negative territory when gross_margin < 0
    _wf_y_min = min(gross_margin, 0) * 1.25
    _wf_y_max = gross * 1.15
    if _wf_y_min < 0:
        layout_wf["yaxis"]["range"] = [_wf_y_min, _wf_y_max]
        layout_wf["yaxis"]["zeroline"] = True
        layout_wf["yaxis"]["zerolinecolor"] = BROWN
        layout_wf["yaxis"]["zerolinewidth"] = 2
        # Add a visible zero-baseline annotation
        fig_wf.add_hline(y=0, line_dash="solid", line_color=BROWN, line_width=2, opacity=0.6)
    fig_wf.update_layout(**layout_wf)
    st.plotly_chart(fig_wf, width="stretch", theme=None, config={"displaylogo": False})

    # ── Summary table ─────────────────────────────────────────────────────────
    wf_tbl = pd.DataFrame({
        "Line": wf_labels,
        "Amount (\u20ac)": [f"\u20ac{abs(v):,.0f}" for v in wf_values],
        "% of Gross":  [f"{abs(v)/max(gross,1)*100:.1f}%" for v in wf_values],
    })
    st.dataframe(wf_tbl, width="stretch", hide_index=True)

    # ── Revenue vs Cost summary ───────────────────────────────────────────────
    if not prim_f.empty or not exp_df.empty:
        _pf_summ_gross = prim_f["gross_revenue"].sum() if not prim_f.empty else 0
        _pf_summ_pcs   = prim_f["bottles"].sum() if not prim_f.empty else 0
        _pf4_k1, _pf4_k2, _pf4_k3, _pf4_k4 = st.columns(4)
        _pf4_k1.metric("Gross Revenue", f"€{_pf_summ_gross:,.0f}")
        _pf4_k2.metric("Net Cost Charge",
                        f"€{total_exp:,.0f}",
                        help="Material Cost + Labour & Overhead − Active Stock − Internal Usage + Logistics + Mktg & Promo + Promotional Units")
        _pf4_k3.metric("Gross Margin",  f"€{gross_margin:,.0f}")
        _pf4_k4.metric("Margin %",      f"{gross_margin/max(gross,1)*100:.1f}%")
        st.markdown("")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 · SKU PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab4:

    st.markdown("<h2>SKU Performance</h2>", unsafe_allow_html=True)

    if not prim_f_nokcat.empty:
        sku_prim = prim_f_nokcat.groupby("sku_id").agg(
            sku_name=("sku_name","first"),
            bottles=("bottles","sum"),
            gross=("gross_revenue","sum"),
            net=("net_revenue","sum"),
        ).reset_index().sort_values("gross", ascending=False)

        # ── Gross Revenue by SKU — horizontal ranked bar ───────────────────────
        _sku_rev_sorted = sku_prim.sort_values("gross", ascending=True)
        _sku_rev_colors = [CATEGORY_COLORS.get(get_product_category(n), BROWN)
                           for n in _sku_rev_sorted["sku_name"]]
        fig_rev = go.Figure(go.Bar(
            x=_sku_rev_sorted["gross"],
            y=_sku_rev_sorted["sku_name"],
            orientation="h",
            marker=dict(color=_sku_rev_colors),
            text=[f"\u20ac{v:,.0f}" for v in _sku_rev_sorted["gross"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>\u20ac%{x:,.0f} gross revenue<extra></extra>",
        ))
        l_rev = base_layout("Gross Revenue by SKU", height=max(300, len(sku_prim) * 36))
        l_rev["xaxis"]["tickprefix"] = "\u20ac"
        l_rev["margin"]["r"] = 80
        l_rev["margin"]["l"] = 220
        fig_rev.update_layout(**l_rev)
        st.plotly_chart(fig_rev, width="stretch", theme=None, config={"displaylogo": False})

        # ── SKU summary table ─────────────────────────────────────────────────
        _sku_simple = sku_prim[["sku_name","bottles","gross"]].copy()
        _sku_simple.columns = ["SKU","Pieces","Gross Revenue (\u20ac)"]
        _sku_simple["Pieces"]               = _sku_simple["Pieces"].apply(lambda x: f"{int(x):,}")
        _sku_simple["Gross Revenue (\u20ac)"] = _sku_simple["Gross Revenue (\u20ac)"].apply(lambda x: f"\u20ac{x:,.0f}")
        st.dataframe(_sku_simple, width="stretch", hide_index=True)
    else:
        st.info("No primary sales data available.")




st.markdown('<div class="footer">niamito. &nbsp; Business workspace · Workbook-backed reporting</div>', unsafe_allow_html=True)
