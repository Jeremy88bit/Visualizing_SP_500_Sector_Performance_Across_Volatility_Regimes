"""
Viz 2: Sector Correlation Heatmap
DS4200 - Altair interactive visualization
Interaction: Buttons toggle correlation matrices for all / normal / high volatility periods

Run: pip install altair pandas numpy vl-convert-python
     python viz2_sector_correlation.py
"""

import altair as alt
import pandas as pd

alt.data_transformers.enable('default', max_rows=20000)

# Load data
try:
    df = pd.read_csv('data/web_dataset.csv', parse_dates=['date'])
except FileNotFoundError:
    df = pd.read_csv('web_dataset.csv', parse_dates=['date'])

# Keep needed columns only
corr_data = df[['date', 'ticker', 'returns', 'regime', 'regime_label']].dropna().copy()

# Order of ETFs
tickers = ['SPY', 'XLK', 'XLF', 'XLE', 'XLV', 'XLY']
sector_names = {
    'SPY': 'S&P 500',
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLV': 'Healthcare',
    'XLY': 'Consumer Discretionary'
}

# ── Helper: build correlation matrix for a subset ──
def build_corr_matrix(data, label):
    pivot = data.pivot(index='date', columns='ticker', values='returns')
    pivot = pivot[tickers].dropna()

    corr = pivot.corr()

    rows = []
    for row_ticker in tickers:
        for col_ticker in tickers:
            rows.append({
                'row': row_ticker,
                'col': col_ticker,
                'row_sector': sector_names[row_ticker],
                'col_sector': sector_names[col_ticker],
                'correlation': corr.loc[row_ticker, col_ticker],
                'period': label
            })

    return pd.DataFrame(rows)

# Build three states
corr_all = build_corr_matrix(corr_data, 'All periods')
corr_normal = build_corr_matrix(corr_data[corr_data['regime'] == 0], 'Normal volatility')
corr_high = build_corr_matrix(corr_data[corr_data['regime'] == 1], 'High volatility')

corr_df = pd.concat([corr_all, corr_normal, corr_high], ignore_index=True)

# ── Selection buttons ──
period_select = alt.selection_point(
    fields=['period'],
    bind=alt.binding_radio(
        options=['All periods', 'Normal volatility', 'High volatility'],
        name='Select period: '
    ),
    value='All periods'
)

# ── Heatmap ──
heatmap = alt.Chart(corr_df).mark_rect(stroke='white', strokeWidth=1.5).encode(
    x=alt.X(
        'col:N',
        title='',
        sort=tickers,
        axis=alt.Axis(labelAngle=0)
    ),
    y=alt.Y(
        'row:N',
        title='',
        sort=tickers
    ),
    color=alt.Color(
        'correlation:Q',
        title='Correlation (red = stronger positive, blue = weaker/negative)',
        scale=alt.Scale(
            domain=[-1, 0, 1],
            range=['#2c7bb6', '#f7f7f7', '#d7191c']
        )
    ),
    tooltip=[
        alt.Tooltip('row:N', title='ETF 1'),
        alt.Tooltip('row_sector:N', title='Sector 1'),
        alt.Tooltip('col:N', title='ETF 2'),
        alt.Tooltip('col_sector:N', title='Sector 2'),
        alt.Tooltip('correlation:Q', title='Correlation', format='.3f'),
        alt.Tooltip('period:N', title='Period')
    ]
).transform_filter(
    period_select
).properties(
    width=420,
    height=420
)

# ── Text labels on cells ──
labels = alt.Chart(corr_df).mark_text(fontSize=11, fontWeight='bold').encode(
    x=alt.X('col:N', sort=tickers),
    y=alt.Y('row:N', sort=tickers),
    text=alt.Text('correlation:Q', format='.2f'),
    color=alt.condition(
        'abs(datum.correlation) > 0.55',
        alt.value('white'),
        alt.value('#333333')
    )
).transform_filter(
    period_select
)

# ── Combine ──
chart = (heatmap + labels).add_params(
    period_select
).configure(
    font='Arial',
    title=alt.TitleConfig(fontSize=16, anchor='start'),
    axis=alt.AxisConfig(labelFontSize=11, titleFontSize=12),
    legend=alt.LegendConfig(titleFontSize=12, labelFontSize=11)
).properties(
    title=alt.Title(
        'Visualization 3: Cross-Sector Correlation by Volatility Regime',
        subtitle=[
            'This heatmap shows how similarly sector returns move in calm versus turbulent markets',
            'Use the selector above to compare all periods, normal volatility, and high volatility'
        ]
    )
)

chart.save('viz3_sector_correlation.html')
print("Saved: viz2_sector_correlation.html")