"""Niamito's own product imagery and workbook-backed product shelf."""
import base64
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).with_name('assets') / 'brand'
FAMILIES = [
    ('UHT', 'Niamito Meal in a Bottle', 'Meal in a bottle', 'cookie.webp', '#f0be8b'),
    ('HPP', 'Niamito Fresh Meal', 'Fresh meal', 'blueberry.webp', '#afb7de'),
    ('Kaša', 'Niamito Oatmeal', 'Oatmeal', 'oatmeal.webp', '#c8e9ae'),
]
PRODUCTS = [
    ('CKU05', 'Cookie', 'UHT', 'cookie.webp', '#f0be8b'),
    ('COU05', 'Cocoa', 'UHT', 'cocoa.webp', '#dcceb6'),
    ('VAU05', 'Vanilla', 'UHT', 'vanilla.webp', '#f0dd78'),
    ('BLU05', 'Blueberry', 'HPP', 'blueberry.webp', '#afb7de'),
    ('APL05', 'Apple', 'HPP', 'apple.webp', '#f0dd78'),
    ('STR05', 'Strawberry', 'HPP', 'strawberry.webp', '#edb0aa'),
    ('SPN05', 'Spinach', 'HPP', 'spinach.webp', '#c8e9ae'),
    ('BLK05', 'Blueberry oatmeal', 'Kaša', 'oatmeal.webp', '#afb7de'),
    ('CHK05', 'Choco oatmeal', 'Kaša', None, '#dcceb6'),
    ('PCK05', 'Peach oatmeal', 'Kaša', None, '#f0be8b'),
]


@lru_cache(maxsize=16)
def asset_uri(filename):
    """Bundle assets with the app; rendering needs no third-party requests."""
    path = ASSETS / filename
    mime = 'image/svg+xml' if path.suffix == '.svg' else 'image/webp'
    return 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode()


def logo_html():
    return f'<img class="brand-logo" src="{asset_uri("logo.svg")}" alt="Niamito"/>'


def render_brand_hero(period, demo_mode=False):
    status = 'Demonstration data' if demo_mode else 'Workbook snapshot'
    st.markdown(
        '<div class="brand-hero"><div class="brand-hero-copy">'
        '<div class="brand-eyebrow">NIAMITO / BUSINESS WORKSPACE</div>'
        '<h1>Sales intelligence</h1>'
        '<p>Units sold, market performance and the investment behind them.</p></div>'
        f'<div class="brand-hero-meta"><span class="brand-tag">{escape(period)}</span>'
        f'<small>{escape(status)}</small></div></div>',
        unsafe_allow_html=True,
    )


def _value(data, column):
    return float(data[column].sum()) if column in data else 0.0


def _stat(label, value):
    return f'<div class="product-stat"><strong>{escape(value)}</strong><small>{escape(label)}</small></div>'


def _card(kicker, title, filename, tint, primary, secondary):
    photo = (f'<img src="{asset_uri(filename)}" alt="Niamito {escape(title)}" loading="lazy"/>'
             if filename else '<div class="product-family">kaša.<span>OATMEAL</span></div>')
    stats = (_stat('Primary units sold', f'{_value(primary,"bottles"):,.0f}') +
             _stat('Consumer units sold', f'{_value(secondary,"bottles_sold"):,.0f}') +
             _stat('Invoiced revenue', f'€{_value(primary,"gross_revenue"):,.0f}') +
             _stat('Sell-out revenue', f'€{_value(secondary,"sellout_revenue"):,.0f}'))
    return (f'<article class="product-card" style="--product-tint:{tint}">'
            f'<div class="product-photo">{photo}</div><div class="product-info">'
            f'<div class="product-kicker">{escape(kicker)}</div><div class="product-name">{escape(title)}</div>'
            f'<div class="product-stats">{stats}</div></div></article>')


def render_product_gallery(primary, secondary):
    cards = []
    for family, category, title, photo, tint in FAMILIES:
        p = primary[primary.category == category]
        s = secondary[secondary.category == category]
        if p.empty and s.empty:
            continue
        cards.append(_card(family, title, photo, tint, p, s))
    if cards:
        st.markdown('<div class="product-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)


def render_flavour_gallery(primary, secondary):
    st.markdown('<div class="section-intro"><div class="eyebrow">THE PRODUCT SHELF</div>'
                '<h2>Product performance</h2></div>', unsafe_allow_html=True)
    family = st.radio('Product family', ['UHT', 'HPP', 'Kaša'], horizontal=True, key='product_shelf_family')
    cards = []
    for prefix, name, product_family, photo, tint in PRODUCTS:
        if product_family != family:
            continue
        p = primary[primary.sku_id.astype(str).str.startswith(prefix)]
        s = secondary[secondary.sku_id.astype(str).str.startswith(prefix)]
        if p.empty and s.empty:
            continue
        cards.append(_card(product_family, name, photo, tint, p, s))
    if cards:
        st.markdown('<div class="product-grid">' + ''.join(cards) + '</div>', unsafe_allow_html=True)
    else:
        st.info('No records for these bottles in the current reporting selection.')
    st.caption('Figures follow the selected period and product category. Primary units and consumer sell-out are separate stages. The oatmeal photograph identifies Blueberry; photographs for Choco and Peach are not supplied. Historical products remain in the detailed tables below.')
