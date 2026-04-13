"""
Viz 1: Sector Volatility Timeline
DS4200 - Altair interactive visualization
Interaction: Interval brush selection on bottom chart filters top chart + tooltips on hover

Run: pip install altair pandas vl-convert-python
     python viz1_sector_timeline.py
"""

import altair as alt
import pandas as pd

alt.data_transformers.enable('default', max_rows=20000)

# Load data
try:
    df = pd.read_csv('data/web_dataset.csv', parse_dates=['date'])
except FileNotFoundError:
    df = pd.read_csv('web_dataset.csv', parse_dates=['date'])

# Prepare data for visualization
viz_data = df[['date', 'ticker', 'sector', 'close', 'volatility_20d', 'regime_label']].dropna().copy()

# Normalize prices to 100 at start for comparison
for ticker in viz_data['ticker'].unique():
    mask = viz_data['ticker'] == ticker
    first_price = viz_data.loc[mask, 'close'].iloc[0]
    viz_data.loc[mask, 'price_normalized'] = viz_data.loc[mask, 'close'] / first_price * 100

# Color scheme
sector_colors = {
    'SPY': '#1a5276',
    'XLK': '#6c3483',
    'XLF': '#1e8449',
    'XLE': '#b9770e',
    'XLV': '#c0392b',
    'XLY': '#2874a6'
}
color_scale = alt.Scale(
    domain=list(sector_colors.keys()),
    range=list(sector_colors.values())
)

# Brush selection
brush = alt.selection_interval(encodings=['x'])

# Top chart
detail_base = alt.Chart(viz_data).mark_line(strokeWidth=1.5).encode(
    x=alt.X('date:T', title='', scale=alt.Scale(domain=brush)),
    y=alt.Y(
        'price_normalized:Q',
        title='Normalized price (base = 100)',
        scale=alt.Scale(zero=False)
    ),
    color=alt.Color('ticker:N', scale=color_scale, title='ETF'),
    tooltip=[
        alt.Tooltip('date:T', title='Date', format='%b %d, %Y'),
        alt.Tooltip('ticker:N', title='ETF'),
        alt.Tooltip('sector:N', title='Sector'),
        alt.Tooltip('close:Q', title='Price ($)', format=',.2f'),
        alt.Tooltip('volatility_20d:Q', title='20-day Volatility', format='.2%'),
        alt.Tooltip('regime_label:N', title='Volatility Regime')
    ]
).properties(
    width=760,
    height=260,
    title=alt.Title(
        'Sector ETF Performance During Volatility Regimes',
        subtitle='This chart shows how sector prices and volatility change across calm and turbulent market periods'
    )
)

# Background shading using SPY regime
spy_regimes = viz_data[viz_data['ticker'] == 'SPY'][['date', 'regime_label']].copy()

regime_bg = alt.Chart(spy_regimes).mark_rect(opacity=0.08).encode(
    x='date:T',
    x2=alt.X2('date:T'),
    color=alt.condition(
        alt.datum.regime_label == 'High',
        alt.value('#e74c3c'),
        alt.value('transparent')
    )
).transform_filter(
    brush
)

detail_chart = (regime_bg + detail_base).properties(
    width=760,
    height=260
)

# Volatility subplot
vol_chart = alt.Chart(viz_data).mark_line(strokeWidth=1, opacity=0.8).encode(
    x=alt.X('date:T', title='', scale=alt.Scale(domain=brush)),
    y=alt.Y(
        'volatility_20d:Q',
        title='20-day rolling volatility',
        axis=alt.Axis(format='.0%')
    ),
    color=alt.Color('ticker:N', scale=color_scale, legend=None),
    tooltip=[
        alt.Tooltip('date:T', title='Date', format='%b %d, %Y'),
        alt.Tooltip('ticker:N', title='ETF'),
        alt.Tooltip('volatility_20d:Q', title='Volatility', format='.2%')
    ]
).properties(
    width=760,
    height=140,
    title='Rolling 20-Day Volatility by Sector (higher = larger price swings)'
)

# Overview chart
overview = alt.Chart(viz_data).mark_line(strokeWidth=0.8, opacity=0.7).encode(
    x=alt.X('date:T', title='Date'),
    y=alt.Y('price_normalized:Q', title='', scale=alt.Scale(zero=False)),
    color=alt.Color('ticker:N', scale=color_scale, legend=None)
).properties(
    width=760,
    height=60,
    title='Overview — drag to select a date range'
).add_params(brush)

# Combine
chart = alt.vconcat(
    detail_chart,
    vol_chart,
    overview
).resolve_scale(
    color='shared'
).configure(
    font='Arial',
    title=alt.TitleConfig(fontSize=16, anchor='start'),
    axis=alt.AxisConfig(labelFontSize=11, titleFontSize=12),
    legend=alt.LegendConfig(titleFontSize=12, labelFontSize=11)
).properties(
    title=alt.Title(
        'Visualization 1: Sector Volatility Timeline',
        subtitle='When do volatility regimes form, and how do sector prices respond over time?',
        fontSize=18
    )
)

chart.save('viz1_sector_timeline.html')
print("Saved: viz1_sector_timeline.html")