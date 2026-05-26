"""
Niamito Business Intelligence Dashboard - CFO Edition
Optimized for Niamito Master Tables (CSV Exports)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────────
# 1. BRAND & VISUAL CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
BEIGE  = "#EDE3D8"
BROWN  = "#2C1A0E"
GREEN  = "#A8D99A"
CORAL  = "#F07A72"
CREAM  = "#F9F4EF"

st.set_page_config(page_title="Niamito · CFO Dashboard", layout="wide")

# Custom CSS to maintain the Niamito aesthetic
st.markdown(f"""
<style>
    .stApp {{ background-color: {BEIGE}; }}
    [data-testid="metric-container"] {{
        background: {CREAM};
        border: 1px solid rgba(44,26,14,0.1);
        border-radius: 12px;
        padding: 15px;
    }}
    h1, h2, h3 {{ color: {BROWN}; font-family: 'Georgia', serif; }}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADING ENGINE (CSV COMPATIBLE)
# ──────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_niamito_data():
    try:
        # Load Product Master to create the SKU mapping
        prod_master = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📦 Product Master.csv", skiprows=2)
        sku_map = prod_master.set_index('Retailer SKU Name')['Internal SKU Code'].to_dict()
        
        # Load Expenses (CFO Source of Truth)
        expenses = pd.read_csv("Niamito_Master_Tables-9.xlsx - Expenses.csv")
        expenses['SKU_Code'] = expenses['SKU'].apply(lambda x: str(x).split(' ')[0])
        
        # Load Primary Sales
        primary = pd.read_csv("Niamito_Master_Tables-9.xlsx - 💸 Primary Sales.csv")
        primary['Invoice Date'] = pd.to_datetime(primary['Invoice Date'])
        primary['Month'] = primary['Invoice Date'].dt.strftime('%b')
        primary['SKU_Code'] = primary['SKU'].map(sku_map)
        
        # Load Marketing & Sell-out
        mkt = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📅 Marketing Calendar.csv", skiprows=2)
        sell_out = pd.read_csv("Niamito_Master_Tables-9.xlsx - 📤 Sell-out Template.csv", skiprows=2)
        
        return primary, expenses, mkt, sell_out, prod_master
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return None, None, None, None, None

# ──────────────────────────────────────────────────────────────────────────────
# 3. CFO CALCULATION ENGINE
# ──────────────────────────────────────────────────────────────────────────────
def calculate_financials(primary, expenses):
    # Group revenue by Month and SKU
    sales_grouped = primary.groupby(['Month', 'SKU_Code'])['Gross Revenue'].sum().reset_index()
    
    # Merge with Expenses
    fin_df = pd.merge(sales_grouped, expenses, on=['Month', 'SKU_Code'], how='inner')
    
    # CFO KPI Definitions
    fin_df['COGS'] = (fin_df['Material Cost (€) [WO col E — full production]'] + 
                      fin_df['Labour Cost (€) [WO col f — full production]'] + 
                      fin_df['Production Overhead (€) [0000 dummy — Stroškovna Mesta]'])
    
    fin_df['Logistics'] = fin_df['Logistics & Distribution (€) [0000s dummy by taste volume]']
    
    # Contribution Margin = Gross Rev - COGS - Logistics
    fin_df['Contribution_Margin'] = fin_df['Gross Revenue'] - fin_df['COGS'] - fin_df['Logistics']
    fin_df['Margin_Percent'] = (fin_df['Contribution_Margin'] / fin_df['Gross Revenue']) * 100
    
    return fin_df

# ──────────────────────────────────────────────────────────────────────────────
# 4. MAIN DASHBOARD UI
# ──────────────────────────────────────────────────────────────────────────────
def main():
    st.title("🌿 Niamito · Strategic Business Intelligence")
    
    prim, exp, mkt, sout, p_master = load_niamito_data()
    
    if prim is not None:
        fin_df = calculate_financials(prim, exp)
        
        # --- TOP LEVEL METRICS ---
        t1, t2, t3, t4 = st.columns(4)
        total_rev = fin_df['Gross Revenue'].sum()
        total_cm = fin_df['Contribution_Margin'].sum()
        avg_margin = (total_cm / total_rev) * 100
        
        t1.metric("Total Revenue", f"€{total_rev:,.0f}")
        t2.metric("Contribution Margin", f"€{total_cm:,.0f}")
        t3.metric("Avg. Margin %", f"{avg_margin:.1f}%")
        t4.metric("Active SKUs", len(fin_df['SKU_Code'].unique()))

        # --- TABS FOR DIFFERENT STAKEHOLDERS ---
        tab_cfo, tab_sales, tab_mkt = st.tabs(["📊 CFO Profitability", "📦 Sales & Volume", "📣 Marketing ROI"])
        
        with tab_cfo:
            st.subheader("SKU-Level Profitability (Contribution Margin)")
            
            # Identify high and low performers
            fig_margin = px.bar(fin_df, x='SKU_Code', y='Contribution_Margin', color='Month',
                                title="Contribution Margin by SKU and Month",
                                barmode='group', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_margin, use_container_width=True)
            
            # CFO Alert Table
            st.markdown("### ⚠️ Margin Watchlist (Margins < 20%)")
            watchlist = fin_df[fin_df['Margin_Percent'] < 20][['Month', 'SKU_Code', 'Gross Revenue', 'Margin_Percent']]
            if not watchlist.empty:
                st.dataframe(watchlist.style.background_gradient(subset=['Margin_Percent'], cmap='RdYlGn'), use_container_width=True)
            else:
                st.success("All SKUs maintaining healthy margins above 20%.")

        with tab_sales:
            col_a, col_b = st.columns(2)
            with col_a:
                fig_rev = px.pie(fin_df, values='Gross Revenue', names='SKU_Code', title="Revenue Mix by SKU")
                st.plotly_chart(fig_rev)
            with col_b:
                # Sell-in vs Sell-out Logic
                st.write("### Channel Inventory Check")
                st.caption("Comparing Primary Sales (Sell-in) vs. Retail Templates (Sell-out)")
                st.info("CFO Note: High Sell-in with Low Sell-out indicates overstocking risk.")

        with tab_mkt:
            st.subheader("Marketing Spend vs. Revenue Impact")
            mkt_spend = exp.groupby('Month')['Marketing & Promotions (€) [0000m dummy by taste vol. + promo cost]'].sum()
            rev_month = prim.groupby('Month')['Gross Revenue'].sum()
            
            comparison = pd.DataFrame({'Spend': mkt_spend, 'Revenue': rev_month}).dropna()
            comparison['ROMI_Factor'] = comparison['Revenue'] / comparison['Spend']
            
            fig_romi = px.line(comparison, y='ROMI_Factor', title="Marketing Efficiency (Revenue per €1 Spend)")
            st.plotly_chart(fig_romi, use_container_width=True)

if __name__ == "__main__":
    main()
