"""Alternative, reconciled views of the same Niamito business records.

Sales stages and marketing sources are grouped independently before joining.
This keeps returns and revenue-only adjustments without multiplying source rows.
"""
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_ui import (
    PURPLE, GREEN, base_layout, chart, section, note, kpis, csv_bytes,
)

FAMILIES = {
    'Niamito Oatmeal': 'Kaša',
    'Niamito Fresh Meal': 'HPP',
    'Niamito Meal in a Bottle': 'UHT',
}
FLAVOURS = {
    'APL05': 'HPP · Apple', 'BLU05': 'HPP · Blueberry',
    'SPN05': 'HPP · Spinach', 'STR05': 'HPP · Strawberry',
    'JAF05': 'HPP · Jaffa Cake', 'BLK05': 'Kaša · Blueberry',
    'CHK05': 'Kaša · Choco', 'PCK05': 'Kaša · Peach',
    'CKU05': 'UHT · Cookie', 'COU05': 'UHT · Cocoa',
    'VAU05': 'UHT · Vanilla',
}
LENSES = ['Product families', 'Flavours', 'Markets', 'Retailers', 'Marketing mix']


def _labels(series):
    return series.fillna('Unassigned').astype(str).str.strip().replace('', 'Unassigned')


def flavour_label(sku_id, sku_name=''):
    """Known SKU prefixes unify harmless name/market suffix variations."""
    code = re.sub(r'[^A-Z0-9]', '', str(sku_id).upper())
    for prefix, label in FLAVOURS.items():
        if code.startswith(prefix):
            return label
    name = '' if pd.isna(sku_name) else str(sku_name).strip()
    return name or (str(sku_id).strip() if pd.notna(sku_id) else '') or 'Unassigned'


def aggregate_sales(frame, dimension, stage='primary'):
    """One row per dimension; missing groups remain visible and negatives stay."""
    if stage not in ('primary', 'secondary'):
        raise ValueError('stage must be primary or secondary')
    units_col, revenue_col = (
        ('bottles', 'gross_revenue') if stage == 'primary'
        else ('bottles_sold', 'sellout_revenue')
    )
    columns = [dimension, stage + '_units', stage + '_revenue', stage + '_records']
    if frame.empty:
        return pd.DataFrame(columns=columns)
    data = frame.copy()
    if dimension == 'product_family':
        categories = data.get('category', pd.Series('Unassigned', index=data.index))
        data[dimension] = _labels(categories.map(lambda value: FAMILIES.get(value, value)))
    elif dimension == 'flavour':
        ids = data.get('sku_id', pd.Series('', index=data.index))
        names = data.get('sku_name', pd.Series('', index=data.index))
        data[dimension] = [flavour_label(code, name) for code, name in zip(ids, names)]
    elif dimension not in data:
        data[dimension] = 'Unassigned'
    data[dimension] = _labels(data[dimension])
    for col in (units_col, revenue_col):
        values = data.get(col, pd.Series(0, index=data.index))
        data[col] = pd.to_numeric(values, errors='coerce').fillna(0)
    return data.groupby(dimension, as_index=False, dropna=False).agg(**{
        stage + '_units': (units_col, 'sum'),
        stage + '_revenue': (revenue_col, 'sum'),
        stage + '_records': (revenue_col, 'size'),
    }).sort_values(stage + '_revenue', ascending=False).reset_index(drop=True)


def compare_sales(primary, secondary, dimension):
    """Keep each stage in separate columns; absent stage values stay missing."""
    first = aggregate_sales(primary, dimension, 'primary')
    second = aggregate_sales(secondary, dimension, 'secondary')
    return first.merge(second, on=dimension, how='outer', validate='one_to_one')


def aggregate_marketing(marketing, allocations, source, dimension):
    """Select one overlapping source, then group every expense once."""
    if source not in ('Calendar detail', 'Product allocations'):
        raise ValueError('Unknown marketing source')
    data = marketing.copy() if source == 'Calendar detail' else allocations.copy()
    if data.empty:
        return pd.DataFrame(columns=[dimension, 'total_spend', 'records'])
    if dimension not in data:
        data[dimension] = 'Unassigned'
    data[dimension] = _labels(data[dimension])
    data['total_spend'] = pd.to_numeric(data['total_spend'], errors='coerce').fillna(0)
    return data.groupby(dimension, as_index=False, dropna=False).agg(
        total_spend=('total_spend', 'sum'), records=('total_spend', 'size'),
    ).sort_values('total_spend', ascending=False).reset_index(drop=True)


def _bar(data, dimension, value_col, title, color=PURPLE, units=False, limit=None):
    display = data.dropna(subset=[value_col]).sort_values(value_col, ascending=False)
    if limit is not None:
        display = display.head(limit)
    display = display.sort_values(value_col)
    fig = go.Figure(go.Bar(
        x=display[value_col], y=display[dimension], orientation='h',
        marker_color=color,
        text=[f'{value:,.0f}' if units else f'€{value:,.0f}' for value in display[value_col]],
        textposition='auto',
        hovertemplate='%{y}<br>' + ('' if units else '€') + '%{x:,.2f}<extra></extra>',
    ))
    fig.update_layout(**base_layout(title, height=max(290, min(620, 35 * len(display) + 100))))
    fig.update_xaxes(tickprefix='' if units else '€')
    fig.update_layout(hovermode='closest')
    return fig


def _table(data, dimension):
    config = {dimension: dimension.replace('_', ' ').title()}
    for col in data:
        if col.endswith('_revenue') or col == 'total_spend':
            config[col] = st.column_config.NumberColumn(
                col.replace('_', ' ').title() + ' (€)', format='€%.2f')
        elif col.endswith('_units') or col.endswith('_records') or col == 'records':
            config[col] = st.column_config.NumberColumn(col.replace('_', ' ').title(), format='%d')
    st.dataframe(data, hide_index=True, width='stretch', column_config=config)


def _sales_lens(primary, secondary, dimension, title):
    comparison = compare_sales(primary, secondary, dimension)
    if comparison.empty:
        st.info('No sales records in this selection. Widen the period or product filter.')
        return
    measure = st.radio('Compare by', ['Revenue (€)', 'Units'], horizontal=True,
                       key='perspective_measure')
    suffix = 'units' if measure == 'Units' else 'revenue'
    a, b = st.columns(2)
    with a:
        chart(_bar(comparison, dimension, 'primary_' + suffix, 'Invoiced sales', units=suffix == 'units'),
              'perspective_primary')
    with b:
        chart(_bar(comparison, dimension, 'secondary_' + suffix, 'Consumer sell-out',
                   color=GREEN, units=suffix == 'units'), 'perspective_secondary')
    _table(comparison, dimension)
    st.download_button('Download ' + title.lower(), csv_bytes(comparison),
                       'niamito_' + dimension + '_perspective.csv', 'text/csv',
                       key='perspective_sales_export')
    st.caption('Primary and secondary are independent sales stages. Missing values indicate no records in that stage; they are not inventory, conversion or confirmed zero sales. Returns and revenue-only adjustments remain included.')


def render_perspectives(primary, secondary, marketing, allocations):
    section('Different angles. Same Niamito.', 'Pick your point of view.',
            'Move from the whole business to the products, places and activity behind it. All views follow the reporting period.')
    lens = st.radio('Explore the business through', LENSES, horizontal=True,
                    key='perspective_lens')
    if lens in ('Product families', 'Flavours', 'Markets'):
        dimension = {'Product families': 'product_family', 'Flavours': 'flavour', 'Markets': 'market'}[lens]
        _sales_lens(primary, secondary, dimension, lens)
        if lens == 'Flavours':
            st.caption('Flavours are matched by known SKU prefixes, so Cookie/Cocoa/Vanilla and country suffixes compare consistently. Historical products stay visible when present in the source.')
    elif lens == 'Retailers':
        data = aggregate_sales(secondary, 'retailer', 'secondary')
        if data.empty:
            st.info('No retailer sell-out records in this selection.')
            return
        nonzero = data[data.secondary_revenue != 0]
        leading = nonzero.iloc[0] if not nonzero.empty else None
        kpis([
            ('Reporting retailer labels', f'{len(data):,}', 'Names as reported in the source'),
            ('Consumer sell-out', f'€{data.secondary_revenue.sum():,.0f}', 'Secondary revenue only'),
            ('Largest recorded retailer', str(leading.retailer) if leading is not None else '—',
             f'€{leading.secondary_revenue:,.0f} sell-out' if leading is not None else 'No non-zero revenue'),
        ])
        chart(_bar(data, 'retailer', 'secondary_revenue', 'Top 15 reported retailers', GREEN, limit=15),
              'perspective_retailers')
        _table(data, 'retailer')
        st.download_button('Download all retailers', csv_bytes(data), 'niamito_retailer_perspective.csv',
                           'text/csv', key='perspective_retailers_export')
        st.caption('Retailer labels may identify stores or distribution centres. They are not assumed to be unique physical shops. The chart shows the top 15; the table and export contain every label, including returns.')
    else:
        source = st.radio('Marketing source', ['Calendar detail', 'Product allocations'],
                          horizontal=True, key='perspective_marketing_source')
        options = ['Segment', 'Source channel', 'Retailer', 'Product family', 'Market'] if source == 'Calendar detail' else ['Product family']
        by = st.selectbox('Break down investment by', options, key='perspective_marketing_dimension')
        dimension = {'Segment': 'segment', 'Source channel': 'channel', 'Retailer': 'retailer',
                     'Product family': 'product_family', 'Market': 'market'}[by]
        data = aggregate_marketing(marketing, allocations, source, dimension)
        if data.empty:
            st.info('No marketing records in this selection for this source.')
            return
        kpis([
            ('Selected-source spend', f'€{data.total_spend.sum():,.0f}', source),
            ('Reporting groups', f'{len(data):,}', 'Shared / unassigned stays visible'),
            ('Source rows', f'{int(data.records.sum()):,}', 'Expenses' if source == 'Calendar detail' else 'Monthly family allocations'),
        ])
        chart(_bar(data, dimension, 'total_spend', 'Investment by ' + by.lower()), 'perspective_marketing_mix')
        _table(data, dimension)
        st.download_button('Download investment view', csv_bytes(data), 'niamito_marketing_mix.csv',
                           'text/csv', key='perspective_marketing_export')
        note('One investment. Two source views.',
             'Calendar detail contains individual expenses. Product allocations come from the existing expense model. The sources overlap and are never added. Calendar classification may be inferred from names; attribution and ROAS are not assumed.')
