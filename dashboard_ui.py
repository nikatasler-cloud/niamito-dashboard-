"""Shared visual language for Niamito's reporting workspace."""
from html import escape
from pathlib import Path
import base64
import streamlit as st
import plotly.graph_objects as go

INK = '#3F2111'
MUTED = '#725B4B'
PURPLE = '#6B83C1'
GREEN = '#47814A'
CORAL = '#D9665A'
PALETTE = [PURPLE, GREEN, CORAL, '#CB9D37', '#8D6C9D', '#AA7C5C', '#9AB38B']


def install_theme():
    root = Path(__file__).parent
    fonts = []
    for filename, weight in (('right-grotesk-regular.ttf', 400), ('right-grotesk-medium.ttf', 600)):
        font_path = root / 'assets' / 'brand' / filename
        if font_path.exists():
            encoded = base64.b64encode(font_path.read_bytes()).decode('ascii')
            fonts.append("@font-face{font-family:'Niamito Right Grotesk';src:url(data:font/ttf;base64," +
                         encoded + ") format('truetype');font-weight:" + str(weight) +
                         ";font-style:normal;font-display:swap;}")
    st.markdown('<style>' + ''.join(fonts) + root.joinpath('dashboard.css').read_text() + '</style>', unsafe_allow_html=True)


def base_layout(title='', height=340, legend_below=True):
    return dict(
        title=dict(text=title, font=dict(size=17, color=INK, family='Niamito Right Grotesk, Arial, sans-serif'), x=0),
        height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Niamito Right Grotesk, Arial, sans-serif', size=12, color=MUTED),
        colorway=PALETTE, margin=dict(l=12, r=20, t=54, b=45),
        legend=dict(orientation='h' if legend_below else 'v', y=-0.23 if legend_below else 1,
                    x=0, font=dict(size=11, color=INK), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(showgrid=False, zeroline=False, linecolor='#DCCEB6', automargin=True),
        yaxis=dict(gridcolor='#ECE5D7', zeroline=False, linecolor='#DCCEB6', automargin=True),
        hoverlabel=dict(bgcolor='#F8F5F0', bordercolor='#DCCEB6', font=dict(color=INK, size=13)),
        hovermode='x unified',
    )


def chart(fig, key=None):
    st.plotly_chart(fig, width='stretch', theme=None, key=key,
                    config={'displaylogo': False, 'scrollZoom': False,
                            'toImageButtonOptions': {'format': 'png', 'scale': 2}})


def section(kicker, title, description=''):
    st.markdown(f'<div class="section-intro"><div class="eyebrow">{escape(kicker)}</div>'
                f'<h2>{escape(title)}</h2><p>{escape(description)}</p></div>', unsafe_allow_html=True)


def note(title, body, tone='neutral'):
    st.markdown(f'<div class="insight {escape(tone)}"><strong>{escape(title)}</strong>'
                f'<p>{escape(body)}</p></div>', unsafe_allow_html=True)


def kpis(items):
    cols = st.columns(len(items))
    for col, (label, value, detail) in zip(cols, items):
        with col:
            st.markdown(f'<div class="kpi-card"><span>{escape(label)}</span>'
                        f'<div class="kpi-value">{escape(str(value))}</div>'
                        f'<small>{escape(detail)}</small></div>', unsafe_allow_html=True)


def horizontal_bars(frame, dimension, title, height=330):
    values = frame.groupby(dimension, dropna=False)['total_spend'].sum().sort_values()
    fig = go.Figure(go.Bar(x=values.values, y=values.index, orientation='h',
        marker_color=[PALETTE[i % len(PALETTE)] for i in range(len(values))],
        text=[f'€{v:,.0f}' for v in values.values], textposition='auto',
        hovertemplate='%{y}<br>€%{x:,.2f}<extra></extra>'))
    fig.update_layout(**base_layout(title, height=max(height, len(values)*32+90)))
    fig.update_xaxes(tickprefix='€')
    return fig


def csv_bytes(frame):
    """Neutralize formula-like source strings in spreadsheet-bound CSV exports."""
    data = frame.copy()
    for col in data.select_dtypes(include=['object', 'string']).columns:
        data[col] = data[col].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
    return data.to_csv(index=False).encode('utf-8-sig')
