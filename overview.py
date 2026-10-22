"""Executive overview and transparent exports for the existing reporting tools."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dashboard_ui import PURPLE, GREEN, PALETTE, base_layout, chart, section, note, kpis, csv_bytes
from marketing import monthly_spend


def coverage(frame, date_col):
    dates = pd.to_datetime(frame[date_col],errors='coerce').dropna() if date_col in frame else pd.Series(dtype='datetime64[ns]')
    return dates.max().strftime('%b %Y') if not dates.empty else 'No dated records'


def render_overview(primary, secondary, marketing, full_primary, full_secondary, full_marketing, allocations):
    section('Business overview', 'The numbers. The bigger picture.',
            'Primary invoices measure our sales. Secondary sales measure sell-through. Each remains a separate view.')
    gross = primary.gross_revenue.sum()
    units = primary.bottles.sum()
    sellout = secondary.sellout_revenue.sum()
    spend = marketing.total_spend.sum()
    kpis([('Invoiced revenue',f'€{gross:,.0f}',f'{units:,.0f} units sold'),
          ('Consumer sell-out',f'€{sellout:,.0f}',f'{secondary.bottles_sold.sum():,.0f} units reported'),
          ('Allocated marketing costs',f'€{allocations.total_spend.sum():,.0f}' if not allocations.empty else '—',f'Calendar detail: €{spend:,.0f}'),
          ('Average invoiced price',f'€{gross/units:.2f}' if units > 0 else '—','Revenue / units in the selected scope')])
    c1,c2 = st.columns([1.7,1])
    with c1:
        fig = go.Figure()
        for frame,col,name,color in ((primary,'gross_revenue','Primary invoiced',PURPLE),(secondary,'sellout_revenue','Secondary sell-out',GREEN)):
            if frame.empty: continue
            monthly = frame.groupby(frame.week.dt.to_period('M'))[col].sum()
            fig.add_trace(go.Scatter(x=monthly.index.to_timestamp(),y=monthly.values,name=name,mode='lines+markers',
                line=dict(color=color,width=3),marker=dict(size=6),connectgaps=False,
                hovertemplate='%{x|%b %Y}<br>€%{y:,.0f}<extra></extra>'))
        fig.update_layout(**base_layout('Revenue over time',350)); fig.update_yaxes(tickprefix='€')
        chart(fig,'overview_revenue')
    with c2:
        cat = primary.groupby('category').gross_revenue.sum().sort_values(ascending=False)
        names = {'Niamito Oatmeal':'Kaša','Niamito Fresh Meal':'HPP','Niamito Meal in a Bottle':'UHT'}
        fig = go.Figure(go.Bar(x=cat.index.map(lambda x:names.get(x,x)),y=cat.values,
            marker_color=PALETTE[:len(cat)],text=[f'€{v:,.0f}' for v in cat],textposition='auto',
            hovertemplate='%{x}<br>€%{y:,.0f}<extra></extra>'))
        fig.update_layout(**base_layout('Revenue by product family',350)); fig.update_yaxes(tickprefix='€')
        chart(fig,'overview_products')
    c1,c2 = st.columns(2)
    with c1:
        section('Market performance','Where customers buy','Secondary sales are grouped by the market reported in the source.')
        markets = secondary.groupby('market').agg(units=('bottles_sold','sum'),revenue=('sellout_revenue','sum')).reset_index().sort_values('revenue',ascending=False)
        if markets.empty: st.info('No sell-out records in this period.')
        else:
            st.dataframe(markets,hide_index=True,width='stretch',column_config={
                'market':'Market','units':st.column_config.NumberColumn('Units',format='%d'),
                'revenue':st.column_config.NumberColumn('Sell-out revenue (€)',format='€%.0f')})
    with c2:
        section('Data coverage','Know what is included','Coverage is shown from the full loaded workbook, before filters.')
        st.dataframe(pd.DataFrame([
            {'Source':'Primary invoices','Latest records':coverage(full_primary,'week'),'Rows':len(full_primary)},
            {'Source':'Secondary sales','Latest records':coverage(full_secondary,'week'),'Rows':len(full_secondary)},
            {'Source':'Marketing expenses','Latest records':coverage(full_marketing,'start'),'Rows':len(full_marketing)},
        ]),hide_index=True,width='stretch')
    note('Read each sales stage separately',
         'Primary and secondary revenue are not added together. A gap between them is not an inventory balance because timing, prices and reporting coverage differ. Marketing comparisons use recorded spend only.')


def render_data(primary, secondary, marketing, expenses, demo_mode):
    section('Data & exports','From source to decision','Inspect the loaded records and download the current selection.')
    note('Demonstration data' if demo_mode else 'Workbook snapshot',
         'These are illustrative figures.' if demo_mode else 'The dashboard reads Niamito_Master_Tables.xlsx from GitHub, or your uploaded replacement. It is not a live Google Sheets connection. Uploading a file affects this browser session only.')
    a,b,c,d=st.tabs(['Primary sales','Secondary sales','Marketing','Expense model'])
    for container,frame,label,filename in ((a,primary,'Primary sales','primary'),(b,secondary,'Secondary sales','secondary'),
                                            (c,marketing,'Marketing','marketing'),(d,expenses,'Expense model','expenses')):
        with container:
            st.caption(f'{len(frame):,} records. '+('Original expense-model scope; see Profitability for category selection.' if filename=='expenses' else 'Period-filtered records; sales also follow the sidebar product selection.'))
            st.dataframe(frame,hide_index=True,width='stretch',height=420)
            st.download_button('Download '+label.lower(),csv_bytes(frame),'niamito_'+filename+'.csv','text/csv',key='export_'+filename)
    with st.expander('Definitions and reporting scope'):
        st.markdown('''
- **Primary sales:** invoiced revenue and units, including returns and revenue-only adjustments.
- **Secondary sales:** reported sell-out, kept separate from primary invoices.
- **Marketing:** one expense per source row. Blank-name total rows are excluded. Possible duplicates remain until reconciled.
- **Classification:** recorded values take priority. Name-based classifications and missing values are visible in marketing exports.
- **Profitability:** the original 2026 expense-model calculation is retained. Its annual costs and inventory assumptions are shown on that page; it is not an audited monthly P&L.
- **Missing data:** no attributed revenue means no campaign ROAS. Missing marketing months do not mean zero spend.
''')
