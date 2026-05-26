import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import timedelta
import warnings
import os

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# BRAND & STYLING (Retained from your original design)
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

# Custom CSS Injection (Identical to your original high-end aesthetic)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif !important; }}
.stApp {{ background-color: #EEE6DC; }}
section[data-testid="stSidebar"] {{ background: #1C1008 !important; }}
div[data-testid="metric-container"] {{
    background: #F9F4EF;
    border: 1px solid rgba(44,26,14,0.10);
    border-radius: 16px;
    padding: 16px 20px;
    box-shadow: 0 8px 20px rgba(44,26,14,0.07);
}}
/* iOS Segmented Control Styling */
.stMain [data-testid="stRadio"] > div[role="radiogroup"] {{
    display: inline-flex !important; flex-direction: row !important;
    background: rgba(44,26,14,0.07) !important; border-radius: 10px !important; padding: 3px !important;
}}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# DATA LOADING ENGINE (Updated for CSV compatibility & CFO Logic)
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data
def load_niamito_csv_suite():
    """
    Loads all 6 CSV files with appropriate metadata row skips and 
    performs the SKU mapping required for financial analysis.
    """
    # 1. Product Master (Key for reconciliation)
    pm = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📦 Product Master.csv", skiprows=2)
    sku_map = pm.set_index('Retailer SKU Name')['Internal SKU Code'].to_dict()
    
    # 2. Expenses (CFO Source of Truth)
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
