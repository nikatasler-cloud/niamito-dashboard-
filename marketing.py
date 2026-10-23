"""Marketing analysis: one source expense per row, with transparent classifications."""
import re
import unicodedata
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dashboard_ui import PALETTE, PURPLE, GREEN, base_layout, chart, section, note, kpis, horizontal_bars, csv_bytes

UNASSIGNED = 'Unassigned'
FAMILIES = {'Niamito Oatmeal': 'Kaša', 'Niamito Fresh Meal': 'HPP', 'Niamito Meal in a Bottle': 'UHT'}


def text(value):
    return '' if value is None or pd.isna(value) or str(value).strip().lower() in ('nan', 'none') else str(value).strip()


def plain(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', text(value).lower()) if not unicodedata.combining(c))


def classify_family(value):
    s = plain(value)
    matches = []
    if re.search(r'\b(kas\w*|oatmeal|choco oat|peach oat|blueberry oat)\b', s): matches.append('Kaša')
    if re.search(r'\b(hpp|fresh meal|smoothie\w*)\b', s): matches.append('HPP')
    if re.search(r'\b(uht|meal in a bottle)\b', s): matches.append('UHT')
    return matches[0] if len(matches) == 1 else 'Multiple products' if matches else UNASSIGNED


def classify_segment(name, channel):
    s, c = plain(name), plain(channel)
    if re.search(r'\b(atl|tv|radio|ooh|billboard\w*|revija)\b', s+' '+c) or c == 'traditional':
        return 'ATL'
    if any(k in s for k in ('degust', 'sampling', 'promotork')): return 'BTL · Sampling'
    if any(k in s for k in ('wobbler', 'display', 'stojalo', 'letak', 'katalog', 'police', 'retail', 'oznaceval')):
        return 'BTL · Retail'
    if any(k in s for k in ('popust', 'akcija', 'kupon', 'listing')): return 'Trade promotions'
    if 'influenc' in c: return 'BTL · Influencers'
    if 'digital' in c or 'media buy' in c: return 'BTL · Digital'
    if 'event' in c or any(k in s for k in ('sponzor', 'tek', 'pedosana')): return 'BTL · Events'
    if 'material' in c: return 'BTL · Materials'
    if 'production' in c or 'produkcija' in c: return 'Creative & production'
    if 'team' in c: return 'Team & support'
    return UNASSIGNED


def classify_retailer(name):
    s = plain(name)
    found = [label for label, pattern in (
        ('SPAR', r'\bspar\b'), ('Mercator', r'\b(mercator|mercatro|merc|mer)\b'),
        ('Leclerc', r'\bleclerc\w*\b'), ('Jager', r'\bjager\b'),
        ('DM', r'\bdm\b'), ('Hofer', r'\bhofer\b'), ('Petrol', r'\bpetrol\b'),
        ('Amazon', r'\bamazon\b')) if re.search(pattern, s)]
    return found[0] if len(found) == 1 else 'Multiple retailers' if found else UNASSIGNED


def normalize_marketing(frame):
    """Never distribute a shared expense to several products, countries or stores."""
    data = frame.copy()
    defaults = {'id':'', 'name':'', 'channel':UNASSIGNED, 'market':UNASSIGNED, 'start':None, 'end':None,
                'total_spend':0.0, 'roas':None, 'attributed_sales':None, 'reach':None,
                'influencer':None, 'product_family':'', 'segment':'', 'retailer':'', 'source_row':None}
    for col, value in defaults.items():
        if col not in data: data[col] = value
    data['total_spend'] = pd.to_numeric(data.total_spend, errors='coerce').fillna(0)
    data['start_dt'] = pd.to_datetime(data.start, errors='coerce')
    data['end_dt'] = pd.to_datetime(data.end, errors='coerce')
    data['month'] = data.start_dt.dt.to_period('M').dt.to_timestamp()
    for field in ('product_family', 'segment', 'retailer', 'market'):
        data[field+'_basis'] = 'Recorded'
    for idx, row in data.iterrows():
        name = text(row['name'])
        family = text(row.product_family)
        if family:
            family = FAMILIES.get(family, family)
        else:
            family = classify_family(name)
            data.loc[idx, 'product_family_basis'] = 'Inferred from name' if family != UNASSIGNED else 'Missing'
        data.loc[idx, 'product_family'] = family
        if not text(row.segment):
            data.loc[idx, 'segment'] = classify_segment(name, text(row.get('source_type')) or row.channel)
            data.loc[idx, 'segment_basis'] = 'Inferred from type / name'
        if not text(row.retailer):
            retailer = classify_retailer(name)
            data.loc[idx, 'retailer'] = retailer
            data.loc[idx, 'retailer_basis'] = 'Inferred from name' if retailer != UNASSIGNED else 'Missing'
        market = text(row.market)
        if market in ('', 'Unassigned', 'ALL', 'None'):
            s = plain(name)
            hits = [code for code, pattern in (
                ('DE', r'\b(de|nemcij\w*|germany)\b'),
                ('SI', r'\b(si|slo|sloveni\w*)\b'),
                ('HR', r'\b(hr|hrvask\w*|croatia)\b'),
                ('AT', r'\b(at|avstrij\w*|austria)\b')) if re.search(pattern, s)]
            market = hits[0] if len(hits) == 1 else 'Multiple markets' if hits else UNASSIGNED
            data.loc[idx, 'market_basis'] = 'Inferred from name' if hits else 'Missing'
        data.loc[idx, 'market'] = market
    data['channel'] = data.channel.map(lambda x: text(x) or UNASSIGNED)
    # Duplicate-looking records stay in totals until reconciled against invoices.
    data['possible_duplicate'] = data.duplicated(['name', 'channel', 'start', 'total_spend'], keep=False)
    return data


def filter_marketing(data, markets=None, families=None, segments=None, channels=None, query=''):
    out = data.copy()
    for field, selected in (('market', markets), ('product_family', families), ('segment', segments), ('channel', channels)):
        if selected: out = out[out[field].isin(selected)]
    if query:
        out = out[out['name'].str.contains(query, case=False, regex=False, na=False)]
    return out


def monthly_spend(data):
    dated = data.dropna(subset=['month'])
    if dated.empty: return pd.DataFrame(columns=['month','total_spend','cumulative'])
    out = dated.groupby('month').total_spend.sum().reset_index().sort_values('month')
    out['cumulative'] = out.total_spend.cumsum()
    return out


def marketing_allocations(expenses, start=None, end=None):
    """Expenses are the existing 2026 allocation model, independent of campaign rows."""
    out = pd.DataFrame(columns=['month','product_family','total_spend'])
    if expenses.empty or 'marketing_promo' not in expenses:
        return out
    data = expenses.copy()
    months = {name: i+1 for i,name in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}
    data['month'] = pd.to_datetime(data['month'].map(lambda m: f'2026-{months[m]:02d}-01' if m in months else None), errors='coerce')
    if start is not None: data = data[data.month >= pd.Timestamp(start).to_period('M').to_timestamp()]
    if end is not None: data = data[data.month <= pd.Timestamp(end).to_period('M').to_timestamp()]
    data['product_family'] = data.product_line.map({'Niamito Fresh Meal':'HPP','Niamito Oatmeal':'Kaša','Niamito UHT Meal':'UHT'}).fillna(UNASSIGNED)
    data['total_spend'] = pd.to_numeric(data.marketing_promo,errors='coerce').fillna(0)
    return data.groupby(['month','product_family'],as_index=False).total_spend.sum()


def render_allocations(allocations, calendar):
    section('2026 expense model', 'Marketing by product family',
            'Existing workbook allocations by Kaša, HPP and UHT. Calendar classifications are shown separately.')
    total = allocations.total_spend.sum()
    calendar_total = calendar.total_spend.sum()
    kpis([('Allocated marketing costs',f'€{total:,.0f}','Expense-model amounts for selected months'),
          ('Detailed calendar spend',f'€{calendar_total:,.0f}','Dated calendar records in the selected period'),
          ('Difference to reconcile',f'€{total-calendar_total:,.0f}','Allocation model minus detailed calendar')])
    left,right=st.columns([1,1.6])
    with left:
        chart(horizontal_bars(allocations,'product_family','Allocated investment by product'),'allocation_family')
    with right:
        fig=go.Figure()
        for i,family in enumerate(['Kaša','HPP','UHT',UNASSIGNED]):
            d=allocations[(allocations.product_family==family) & (allocations.total_spend!=0)]
            if d.empty:continue
            fig.add_trace(go.Bar(x=d.month,y=d.total_spend,name=family,marker_color=PALETTE[i],
                hovertemplate='%{x|%b %Y}<br>€%{y:,.2f}<extra></extra>'))
        fig.update_layout(**base_layout('Monthly product allocation',330),barmode='stack')
        fig.update_xaxes(tickformat='%b %Y');fig.update_yaxes(tickprefix='€')
        chart(fig,'allocation_monthly')
    comparison=allocations.groupby('month').total_spend.sum().rename('Allocated costs (€)').to_frame()
    detail=monthly_spend(calendar)
    comparison=comparison.join(detail.set_index('month').total_spend.rename('Calendar detail (€)'),how='outer')
    # Absent calendar months stay missing instead of being silently treated as confirmed zero.
    comparison['Unreconciled (€)']=comparison['Allocated costs (€)']-comparison['Calendar detail (€)']
    comparison['Status']=['Calendar detail missing' if pd.isna(c) and a != 0 else
                          'No non-zero allocation recorded' if pd.notna(a) and a == 0 and pd.isna(c) else
                          'Allocation missing' if pd.isna(a) else
                          'Reconciled (within €0.05)' if abs(a-c)<=.05 else 'Review source difference'
                          for a,c in zip(comparison['Allocated costs (€)'],comparison['Calendar detail (€)'])]
    comparison=comparison.reset_index()
    st.dataframe(comparison,hide_index=True,width='stretch',column_config={
        'month':st.column_config.DateColumn('Month',format='MMM YYYY'),
        **{col:st.column_config.NumberColumn(format='€%.2f') for col in comparison if '(€)' in col}})
    st.caption('The two sources overlap and must not be added together. The expense model contains allocations, not campaign attribution. Calendar filters above do not change this reconciliation. Partial date selections include the whole allocation month; the calendar follows exact dates.')
    st.download_button('Download product allocations',csv_bytes(allocations),'niamito_marketing_allocations.csv','text/csv',key='download_allocations')


def render_marketing(data, primary, secondary, allocations=None):
    section('Marketing', 'Where the investment goes',
            'Explore spend by product, channel and retailer. Every amount traces back to a source record.')
    if allocations is None: allocations=marketing_allocations(pd.DataFrame())
    if data.empty:
        st.info('No marketing expenses are recorded in this period. Choose All data or upload an updated workbook.')
        if not allocations.empty and allocations.total_spend.sum() != 0:
            render_allocations(allocations,data)
        return
    with st.container(border=True):
        a,b,c,d = st.columns(4)
        markets = a.multiselect('Marketing market', sorted(data.market.unique()), key='mkt_market')
        families = b.multiselect('Marketing product', sorted(data.product_family.unique()), key='mkt_product')
        segments = c.multiselect('Marketing segment', sorted(data.segment.unique()), key='mkt_segment')
        channels = d.multiselect('Source channel', sorted(data.channel.unique()), key='mkt_channel')
        st.caption('These filters apply to marketing only. Empty selection includes all values. Sales category filters do not allocate shared marketing spend.')
    selected = filter_marketing(data, markets, families, segments, channels)
    if selected.empty:
        st.info('No expenses match these filters. Clear a marketing filter to widen the view.')
        return
    spend = selected.total_spend.sum()
    period_spend = data.total_spend.sum()
    months = selected.month.nunique()
    share = spend / period_spend if period_spend > 0 else None
    kpis([('Detailed calendar spend', f'€{spend:,.0f}', 'Recorded expenses in this selection'),
          ('Expense records', f'{len(selected):,}', 'Source rows, not unique campaigns'),
          ('Average / recorded month', f'€{spend/months:,.0f}' if months else '—', f'{months} months with dated records'),
          ('Share of period spend', f'{share:.1%}' if share is not None else '—', 'Of all marketing in this period')])
    top = selected.groupby('segment').total_spend.sum().sort_values(ascending=False)
    note('Investment focus', f'{top.index[0]} accounts for €{top.iloc[0]:,.0f}' +
         (f' ({top.iloc[0]/spend:.0%}) of this selection.' if spend > 0 else '.') +
         ' Open the breakdown to compare products, stores and source channels.')
    # Retain the original units-versus-investment analysis, ahead of the
    # detailed source views. A missing month stays missing in its own series.
    if not secondary.empty:
        monthly_units = secondary.groupby(secondary.week.dt.to_period('M').dt.to_timestamp())['bottles_sold'].sum()
        monthly_units.index.name = 'month'
        monthly_cost = monthly_spend(selected).set_index('month')['total_spend']
        context = monthly_units.rename('units').to_frame().join(monthly_cost, how='outer').sort_index()
        fig = go.Figure(go.Bar(
            x=context.index, y=context.units, name='Units sold · secondary',
            marker_color=GREEN, opacity=.88,
            hovertemplate='%{x|%b %Y}<br>%{y:,.0f} units<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=context.index, y=context.total_spend, name='Marketing spend',
            mode='lines+markers', yaxis='y2', connectgaps=False,
            line=dict(color=PURPLE, width=2.5),
            hovertemplate='%{x|%b %Y}<br>€%{y:,.2f}<extra></extra>',
        ))
        layout = base_layout('Secondary units sold vs marketing spend', 340)
        layout['yaxis']['title'] = 'Units sold'
        layout['yaxis2'] = dict(overlaying='y', side='right', showgrid=False,
                               tickprefix='€', title='Marketing spend (€)')
        layout['margin']['r'] = 70
        fig.update_layout(**layout)
        fig.update_xaxes(tickformat='%b %Y')
        chart(fig, 'mkt_units_vs_spend')
        st.caption('Units use reported consumer sell-out after the sidebar sales filters. Spend uses the marketing filters above. The axes have different units; this comparison shows timing and scale, not attribution. Missing expense months are not assumed to be zero.')
    # Keep every analysis in the Marketing page instead of concealing charts
    # and tables behind another layer of tabs.
    allocation_tab, spend_tab, breakdown_tab, impact_tab, records_tab = [st.container() for _ in range(5)]
    with allocation_tab:
        section('Product allocation', 'Recorded investment by product',
                'The existing allocation model and detailed calendar remain separate sources.')
        if allocations.empty: st.info('No expense-model allocations are available for this period.')
        else: render_allocations(allocations,data)
    with spend_tab:
        section('Spend trend', 'Investment over time',
                'Monthly, cumulative and channel views stay together in this page.')
        left, right = st.columns([1.6,1])
        dated = selected.dropna(subset=['month'])
        with left:
            fig = go.Figure()
            for i, channel in enumerate(sorted(dated.channel.unique())):
                d = dated[dated.channel == channel].groupby('month').total_spend.sum()
                fig.add_trace(go.Bar(x=d.index, y=d.values, name=channel,
                    marker_color=PALETTE[i%len(PALETTE)], hovertemplate='%{x|%b %Y}<br>€%{y:,.2f}<extra></extra>'))
            fig.update_layout(**base_layout('Monthly investment', height=370), barmode='stack')
            fig.update_xaxes(tickformat='%b %Y'); fig.update_yaxes(tickprefix='€')
            chart(fig, 'mkt_monthly')
        with right:
            chart(horizontal_bars(selected, 'segment', 'ATL, BTL & supporting costs', 370), 'mkt_segments')
        c1,c2 = st.columns(2)
        with c1:
            mo = monthly_spend(selected)
            fig = go.Figure(go.Scatter(x=mo.month, y=mo.cumulative, mode='lines+markers', fill='tozeroy',
                fillcolor='rgba(147,128,220,.12)', line=dict(color=PURPLE, width=3),
                hovertemplate='%{x|%b %Y}<br>€%{y:,.2f}<extra></extra>'))
            fig.update_layout(**base_layout('Cumulative recorded spend', 310)); fig.update_yaxes(tickprefix='€')
            chart(fig, 'mkt_cumulative')
        with c2:
            chart(horizontal_bars(selected, 'channel', 'Original source channels', 310), 'mkt_channels')
        # Preserve the original annotated channel analysis and the combined
        # monthly/cumulative view alongside the expanded marketing charts.
        channel_counts = selected.groupby('channel').agg(
            total_spend=('total_spend', 'sum'), records=('channel', 'size')
        ).reset_index().sort_values('total_spend')
        fig = go.Figure(go.Bar(
            x=channel_counts.total_spend, y=channel_counts.channel, orientation='h',
            marker_color=PURPLE,
            text=[f'€{value:,.0f} · {count:,} records' for value, count in
                  zip(channel_counts.total_spend, channel_counts.records)],
            textposition='auto', customdata=channel_counts.records,
            hovertemplate='%{y}<br>€%{x:,.2f}<br>%{customdata:,} expense records<extra></extra>',
        ))
        fig.update_layout(**base_layout('Spend & expense records by channel', 330))
        fig.update_xaxes(tickprefix='€')
        chart(fig, 'mkt_channel_records')
        fig = go.Figure(go.Bar(
            x=mo.month, y=mo.total_spend, name='Monthly spend', marker_color=PURPLE,
            opacity=.7, hovertemplate='%{x|%b %Y}<br>€%{y:,.2f}<extra></extra>',
        ))
        fig.add_trace(go.Scatter(
            x=mo.month, y=mo.cumulative, name='Cumulative spend', yaxis='y2',
            mode='lines+markers', line=dict(color=GREEN, width=2.5),
            hovertemplate='%{x|%b %Y}<br>Cumulative €%{y:,.2f}<extra></extra>',
        ))
        layout = base_layout('Monthly & cumulative marketing spend', 330)
        layout['yaxis']['tickprefix'] = '€'
        layout['yaxis2'] = dict(overlaying='y', side='right', showgrid=False,
                               tickprefix='€', title='Cumulative spend (€)')
        layout['margin']['r'] = 75
        fig.update_layout(**layout)
        fig.update_xaxes(tickformat='%b %Y')
        chart(fig, 'mkt_monthly_cumulative')
        undated = selected[selected.start_dt.isna()].total_spend.sum()
        st.caption('Amounts are booked to the recorded start month. Months without records are not confirmed zero-spend months. No budget target is supplied.' +
                   (f' €{undated:,.2f} has no date and is excluded from time charts.' if undated else ''))
    with breakdown_tab:
        section('Product & retail', 'Where activity is concentrated',
                'Product, segment and retailer detail from the selected expense records.')
        c1,c2 = st.columns(2)
        with c1: chart(horizontal_bars(selected, 'product_family', 'Product family'), 'mkt_families')
        with c2: chart(horizontal_bars(selected, 'retailer', 'Retailers & shared activity'), 'mkt_retailers')
        st.caption('Product and retailer tags are inferred only when names contain explicit clues. Unassigned is not allocated across Kaša, HPP and UHT. Multi-retailer expenses are counted once.')
        matrix = selected.pivot_table(index='segment', columns='product_family', values='total_spend', aggfunc='sum', fill_value=0)
        fig = go.Figure(go.Heatmap(z=matrix.values, x=matrix.columns.tolist(), y=matrix.index.tolist(),
            colorscale=[[0,'#F7F4FC'],[.5,'#C9BDEA'],[1,'#7C64B8']],
            text=[[f'€{v:,.0f}' for v in row] for row in matrix.values], texttemplate='%{text}',
            hovertemplate='%{y} · %{x}<br>€%{z:,.2f}<extra></extra>', showscale=False))
        fig.update_layout(**base_layout('Product × segment investment', max(330,len(matrix)*45+90)))
        chart(fig,'mkt_matrix')
        summary = selected.groupby(['product_family','segment','retailer'],dropna=False).agg(
            spend=('total_spend','sum'), records=('name','size')).reset_index().sort_values('spend', ascending=False)
        summary['share'] = summary.spend/spend if spend > 0 else np.nan
        st.dataframe(summary, width='stretch', hide_index=True, column_config={
            'product_family':'Product', 'segment':'Segment', 'retailer':'Retailer', 'records':'Records',
            'spend':st.column_config.NumberColumn('Spend (€)',format='€%.2f'),
            'share':st.column_config.NumberColumn('Share (0–1)',format='%.3f')})
        st.download_button('Download breakdown',csv_bytes(summary),'niamito_marketing_breakdown.csv','text/csv',key='download_mkt_summary')
    with impact_tab:
        section('Sales context', 'Sales alongside investment',
                'Keep reported sales and marketing costs visible without assuming attribution.')
        note('Spend and sales are context, not attribution',
             'The source does not link these expenses to incremental sales. Revenue divided by all spend is a blended ratio, not campaign ROAS. Sales below follow the sidebar category filter; marketing follows the filters above.', 'amber')
        mo = monthly_spend(selected)
        for source, value_col, title, key, color in (
            (primary,'gross_revenue','Primary invoiced revenue', 'primary',PURPLE),
            (secondary,'sellout_revenue','Secondary sell-out revenue','secondary',GREEN)):
            if source.empty: continue
            sales = source.copy(); sales['month'] = sales.week.dt.to_period('M').dt.to_timestamp()
            sales = sales.groupby('month')[value_col].sum().rename('revenue').reset_index()
            compare = sales.merge(mo[['month','total_spend']],on='month',how='outer').sort_values('month')
            fig = go.Figure(go.Bar(x=compare.month,y=compare.revenue,name=title,marker_color=color))
            fig.add_trace(go.Scatter(x=compare.month,y=compare.total_spend,name='Marketing investment',
                mode='lines+markers',line=dict(color='#D8876D',width=3),connectgaps=False))
            fig.update_layout(**base_layout(title+' & marketing investment',330)); fig.update_yaxes(tickprefix='€')
            chart(fig,'mkt_vs_'+key)
        attributed = pd.to_numeric(selected.attributed_sales,errors='coerce')
        measured = attributed.notna() & (selected.total_spend > 0)
        if measured.any():
            measured_spend = selected.loc[measured,'total_spend'].sum()
            st.metric('Reported attributed ROAS',f'{attributed[measured].sum()/measured_spend:.2f}×',
                      help='Attributed revenue divided by spend for records with attribution only.')
            st.caption(f'{measured.sum()} records contain attribution. This is a subset of total marketing spend.')
        else:
            st.info('Campaign ROAS is unavailable: no attributed revenue is recorded. Add attributed revenue and the attribution window to the source to enable it.')
        influencers = selected[selected.influencer.notna() | selected.channel.str.contains('Influencer',case=False)]
        if not influencers.empty:
            st.subheader('Influencer activity')
            st.dataframe(influencers[['name','start','total_spend','reach','influencer']],hide_index=True,width='stretch')
    with records_tab:
        section('Records & actions', 'The detail behind the view',
                'Complete source records, original register fields and reconciliation actions.')
        search = st.text_input('Search expense names',placeholder='Try SPAR, Meta, UHT…',key='mkt_search')
        records = filter_marketing(selected,query=search).sort_values('start_dt',ascending=False)
        st.caption(f'{len(records)} records · €{records.total_spend.sum():,.2f}. Classification basis is included in the export.')
        cols = ['source_row','name','channel','market','product_family','segment','retailer','start_dt','end_dt','total_spend','possible_duplicate']
        st.dataframe(records[cols],hide_index=True,width='stretch',height=430,column_config={
            'source_row':'Excel row','name':'Expense','channel':'Source channel','market':'Market',
            'product_family':'Product','segment':'Segment','retailer':'Retailer',
            'start_dt':st.column_config.DateColumn('Start',format='DD MMM YYYY'),
            'end_dt':st.column_config.DateColumn('End',format='DD MMM YYYY'),
            'total_spend':st.column_config.NumberColumn('Spend (€)',format='€%.2f'),
            'possible_duplicate':'Review duplicate'})
        st.download_button('Download selected records',csv_bytes(records),'niamito_marketing_records.csv','text/csv',key='download_mkt_records')
        # Keep the original source-register columns visible as well as the
        # expanded classification/reconciliation table above.
        st.subheader('Source expense register')
        register_cols = [col for col in ('id', 'name', 'channel', 'market', 'start', 'end',
                                        'total_spend', 'roas') if col in records]
        st.dataframe(records[register_cols], hide_index=True, width='stretch', column_config={
            'id': 'ID', 'name': 'Expense / campaign name', 'channel': 'Channel', 'market': 'Market',
            'start': 'Start', 'end': 'End',
            'total_spend': st.column_config.NumberColumn('Spend (€)', format='€%.2f'),
            'roas': st.column_config.NumberColumn('Source ROAS', format='%.2f×'),
        })
        st.caption('Original register fields are retained. An absent source ROAS stays blank; it is not inferred from overall sales.')
        actions = []
        for col,label,action in (
            ('product_family','Product allocation','Add the product family or a documented allocation key to the source.'),
            ('market','Market allocation','Confirm the country from the invoice or campaign brief.'),
            ('retailer','Retailer allocation','Add the retailer for store activity; leave brand-wide expenses unallocated.')):
            subset = selected[selected[col]==UNASSIGNED]
            if not subset.empty: actions.append({'Review':label,'Records':len(subset),'Spend (€)':subset.total_spend.sum(),'Next action':action})
        dup = selected[selected.possible_duplicate]
        if not dup.empty:
            actions.append({'Review':'Possible duplicate records','Records':len(dup),'Spend (€)':dup.total_spend.sum(),
                            'Next action':'Match invoice IDs before removing anything. These records remain in totals.'})
        if actions:
            st.subheader('Actions to improve reporting')
            st.dataframe(pd.DataFrame(actions),width='stretch',hide_index=True,
                         column_config={'Spend (€)':st.column_config.NumberColumn(format='€%.2f')})
        with st.expander('How classifications work'):
            st.write('Explicit product, segment, retailer and market columns take precedence. Otherwise, product and retailer tags use name clues. Segment uses the source type and activity name. Missing values remain Unassigned. Shared amounts are never copied into several groups. Source channels stay available alongside the inferred segment.')
            st.dataframe(selected[['name','product_family_basis','segment_basis','retailer_basis','market_basis']],hide_index=True,width='stretch')
