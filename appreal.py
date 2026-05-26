import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import timedelta
import warnings
import os
import openpyxl as _opxl
import re as _re

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# BRAND & STYLING (Preserving your original aesthetic)
# ──────────────────────────────────────────────────────────────────────────────
BEIGE  = "#EDE3D8"
BROWN  = "#2C1A0E"
LAVEN  = "#B3B8D9"
GREEN  = "#A8D99A"
CORAL  = "#F07A72"
YELLOW = "#EDD96A"
CREAM  = "#F9F4EF"
MID    = "#6b4c30"

st.set_page_config(page_title="Niamito · Business Intelligence", page_icon="🌿", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif !important; }}
.stApp {{ background-color: #EEE6DC; }}
section[data-testid="stSidebar"] {{ background: #1C1008 !important; }}
div[data-testid="metric-container"] {{
    background: #F9F4EF; border: 1px solid rgba(44,26,14,0.10);
    border-radius: 16px; padding: 16px 20px; box-shadow: 0 8px 20px rgba(44,26,14,0.07);
}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CFO LOGIC: CATEGORY & SKU MAPPING
# ──────────────────────────────────────────────────────────────────────────────
def get_product_category(sku_name: str) -> str:
    name = str(sku_name).lower()
    if any(k in name for k in ["fresh meal", "hpp", "390"]): return "Niamito Fresh Meal"
    if any(k in name for k in ["uht", "470", "bottle"]): return "Niamito Meal in a Bottle"
    return "Niamito Oatmeal"

# ──────────────────────────────────────────────────────────────────────────────
# THE EXCEL LOADER (Updated for CFO compatibility)
# ──────────────────────────────────────────────────────────────────────────────
def load_excel(file):
    def _cell_val(v):
        if v is None: return None
        s = str(v)
        if not s.startswith("="): return v
        m = _re.search(r',\s*("([^"]*)"|([-]?\d+(?:\.\d+)?))\s*\)\s*$', s)
        if m:
            if m.group(2) is not None: return m.group(2)
            try: return float(m.group(3))
            except: pass
        return None

    _wb = _opxl.load_workbook(file, data_only=False)

    def _read_ws_rows(ws, header_row: int, data_start: int):
        headers = [(str(_cell_val(cell.value)).strip() if _cell_val(cell.value) else f"_col{i}")
                   for i, cell in enumerate(ws[header_row])]
        rows = []
        for row in ws.iter_rows(min_row=data_start, values_only=False):
            extracted = [_cell_val(cell.value) for cell in row]
            if any(v is not None for v in extracted): rows.append(dict(zip(headers, extracted)))
        return pd.DataFrame(rows)

    # 1. Load Product Master & Create CFO SKU Map
    ws_prod = next(s for s in _wb.sheetnames if "Product" in s)
    prod_master = _read_ws_rows(_wb[ws_prod], header_row=3, data_start=4)
    sku_map = prod_master.set_index('Retailer SKU Name')['Internal SKU Code'].to_dict()

    # 2. Load Expenses (Material, Labour, Overhead)
    ws_exp = next(s for s in _wb.sheetnames if "Expense" in s)
    exp_df = _read_ws_rows(_wb[ws_exp], header_row=1, data_start=2)
    # Reconcile SKU format: "APL05 (Apple)" -> "APL05"
    exp_df['Internal_SKU'] = exp_df['SKU'].apply(lambda x: str(x).split(' ')[0])

    # 3. Load Primary Sales
    ws_prim = next(s for s in _wb.sheetnames if "Primary" in s)
    prim_df = _read_ws_rows(_wb[ws_prim], header_row=3, data_start=4)
    prim_df['week'] = pd.to_datetime(prim_df['Invoice Date'])
    prim_df['Internal_SKU'] = prim_df['SKU'].map(sku_map)
    prim_df['Month'] = prim_df['week'].dt.strftime('%b')

    # 4. Load Marketing
    ws_mkt = next(s for s in _wb.sheetnames if "Marketing" in s)
    mkt_df = _read_ws_rows(_wb[ws_mkt], header_row=3, data_start=4)

    # 5. Load Sell-out Template (Secondary)
    ws_so = next(s for s in _wb.sheetnames if "Sell-out" in s or "Secondary" in s)
    so_df = _read_ws_rows(_wb[ws_so], header_row=3, data_start=4)

    return prim_df, so_df, mkt_df, exp_df, sku_map

# ──────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD LOGIC
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📥 Strategic Ingestion")
    uploaded = st.file_uploader("Niamito Master Tables", type=["xlsx"])

if uploaded:
    prim_df, so_df, mkt_df, exp_df, sku_map = load_excel(uploaded)
    
    # ── CFO METRIC CALCULATION ──
    # Merging Sales and Expenses for the P&L view
    total_rev = prim_df['Gross Revenue'].sum()
    total_cogs = exp_df['Production cost (€)'].sum() + exp_df['Logistics & Distribution (€)'].sum()
    gross_margin = total_rev - total_cogs
    
    # ── TABS ──
    tab1, tab2, tab3 = st.tabs(["Overview", "Marketing", "Profitability"])

    with tab1:
        st.markdown("<h2>Niamito · Business Overview</h2>", unsafe_allow_html=True)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Pieces Sold", f"{prim_df['Quantity (PCS)'].sum():,.0f}")
        k2.metric("Gross Revenue", f"€{total_rev:,.0f}")
        k3.metric("Gross Margin", f"€{gross_margin:,.0f}", delta=f"{(gross_margin/total_rev)*100:.1f}%")
        k4.metric("Rev per € Mkt", f"€{total_rev/max(mkt_df['TOTAL Spend (€)'].sum(), 1):.2f}")

        # Graph: Revenue vs Category
        prim_df['Category'] = prim_df['SKU'].apply(get_product_category)
        cat_data = prim_df.groupby('Category')['Gross Revenue'].sum().reset_index()
        fig = px.bar(cat_data, x='Category', y='Gross Revenue', color_discrete_sequence=[BROWN])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=CREAM)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### CFO Waterfall: Revenue to Net Margin")
        # Waterfall visualizing value leakage
        wf_fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Revenue", "Expenses", "Gross Margin"],
            y=[total_rev, -total_cogs, gross_margin],
            connector={"line":{"color":MID}},
            decreasing={"marker":{"color":CORAL}},
            increasing={"marker":{"color":GREEN}}
        ))
        st.plotly_chart(wf_fig, use_container_width=True)
else:
    st.info("Please upload the Niamito Master Tables Excel file to begin.")    # 2. Expenses (CFO Source of Truth)
    exp = pd.read_csv("Niamito_Master_Tables-9.xlsx - Expenses.csv")
    exp['SKU_Code'] = exp['SKU'].apply(lambda x: str(x).split(' ')[0])
    
    # 3. Primary Sales
    prim = pd.read_csv("Niamito_Master_Tables-9.xlsx - 💸 Primary Sales.csv")
    prim['date'] = pd.to_datetime(prim['Invoice Date'])
    prim['Month'] = prim['date'].dt.strftime('%b')
    prim['SKU_Code'] = prim['SKU'].map(sku_map)
    
    # 4. Secondary Sales & Marketing
    mkt = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📅 Marketing Calendar.csv", skiprows=2)
    s_out = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📤 Sell-out Template.csv", skiprows=2)
    s_out['date'] = pd.to_datetime(s_out['Date (DD/MM/YYYY)'])
    
    return prim, exp, mkt, s_out, sku_map

def get_product_category(sku_name):
    name = str(sku_name).lower()
    if any(k in name for k in ["hpp", "fresh"]): return "Niamito Fresh Meal"
    if any(k in name for k in ["uht", "bottle", "cocoa"]): return "Niamito Meal in a Bottle"
    return "Niamito Oatmeal"

# ──────────────────────────────────────────────────────────────────────────────
# CFO CALCULATION ENGINE
# ──────────────────────────────────────────────────────────────────────────────
def run_cfo_analysis(prim, exp):
    # Aggregate sales by Month and SKU to match expense sheet
    sales_mo = prim.groupby(['Month', 'SKU_Code'])['Gross Revenue'].sum().reset_index()
    
    # Merge Financials
    fin = pd.merge(sales_mo, exp, on=['Month', 'SKU_Code'], how='left').fillna(0)
    
    # KPIs: Contribution Margin
    fin['COGS'] = (fin['Material Cost (€) [WO col E — full production]'] + 
                   fin['Labour Cost (€) [WO col F — full production]'] + 
                   fin['Production Overhead (€) [0000 dummy — Stroškovna Mesta]'])
    
    fin['Gross_Margin'] = fin['Gross Revenue'] - fin['COGS'] - fin['Logistics & Distribution (€) [0000s dummy by taste volume]']
    fin['Margin_Pct'] = (fin['Gross_Margin'] / fin['Gross Revenue']) * 100
    return fin

# ──────────────────────────────────────────────────────────────────────────────
# DASHBOARD TABS
# ──────────────────────────────────────────────────────────────────────────────
def main():
    st.markdown("<h1 style='color:#1C1008;'>Niamito · Business Intelligence</h1>", unsafe_allow_html=True)
    
    # Load Data
    prim, exp, mkt, s_out, sku_map = load_niamito_csv_suite()
    fin_df = run_cfo_analysis(prim, exp)
    
    tab1, tab2, tab3 = st.tabs(["📊 CFO Overview", "📦 Sales Performance", "📣 Marketing ROI"])
    
    with tab1:
        # High-level Financial Metrics
        m1, m2, m3, m4 = st.columns(4)
        total_rev = fin_df['Gross Revenue'].sum()
        total_gm = fin_df['Gross_Margin'].sum()
        avg_margin = (total_gm / total_rev) * 100
        
        m1.metric("Gross Revenue", f"€{total_rev:,.0f}")
        m2.metric("Contribution Margin", f"€{total_gm:,.0f}")
        m3.metric("Margin %", f"{avg_margin:.1f}%")
        m4.metric("COGS % of Rev", f"{(fin_df['COGS'].sum()/total_rev)*100:.1f}%")

        st.markdown("### Profitability Waterfall (CFO View)")
        # Waterfall data preparation
        wf_data = {
            "Measure": ["Revenue", "COGS", "Logistics", "Net Margin"],
            "Amount": [total_rev, -fin_df['COGS'].sum(), -exp['Logistics & Distribution (€) [0000s dummy by taste volume]'].sum(), total_gm]
        }
        fig_wf = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "relative", "total"],
            x=wf_data["Measure"], y=wf_data["Amount"],
            connector={"line": {"color": BROWN}},
            increasing={"marker": {"color": GREEN}},
            decreasing={"marker": {"color": CORAL}}
        ))
        fig_wf.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor=CREAM, height=400)
        st.plotly_chart(fig_wf, use_container_width=True)

        # Critical Alert for CFO
        underperformers = fin_df[fin_df['Margin_Pct'] < 15]
        if not underperformers.empty:
            st.warning(f"⚠️ {len(underperformers)} SKU/Month combinations are below the 15% margin threshold.")

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Revenue by Category")
            prim['Category'] = prim['SKU'].apply(get_product_category)
            cat_rev = prim.groupby('Category')['Gross Revenue'].sum().reset_index()
            fig_cat = px.pie(cat_rev, values='Gross Revenue', names='Category', color_discrete_sequence=[BROWN, GREEN, LAVEN])
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with col_b:
            st.markdown("### Channel Stock Health (Sell-in vs Sell-out)")
            # Linking Primary (Sell-in) to Sell-out Template
            st.caption("A CFO looks for 'Stock Bloat' where Sell-in exceeds Sell-out.")
            # Simplified comparison for visual
            monthly_in = prim.groupby('Month')['Gross Revenue'].sum()
            st.bar_chart(monthly_in)

    with tab3:
        st.markdown("### Marketing Efficiency (ROMI)")
        mkt_spend = exp.groupby('Month')['Marketing & Promotions (€) [0000m dummy by taste vol. + promo cost]'].sum()
        # Revenue per Euro spent
        romi = (monthly_in / mkt_spend).reset_index()
        romi.columns = ['Month', 'Revenue_per_Euro']
        fig_romi = px.line(romi, x='Month', y='Revenue_per_Euro', title="Return on Marketing Spend", markers=True)
        fig_romi.update_traces(line_color=CORAL)
        st.plotly_chart(fig_romi, use_container_width=True)

if __name__ == "__main__":
    main()
