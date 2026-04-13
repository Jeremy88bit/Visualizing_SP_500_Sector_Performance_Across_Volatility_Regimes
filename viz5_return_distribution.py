"""
Viz 5: Return Distribution by Regime
DS4200 - Altair interactive visualization
Interaction: sector dropdown + year dropdown to compare return histograms

Run: pip install altair pandas vl-convert-python
     python viz5_return_distribution.py
"""

import altair as alt
import pandas as pd

alt.data_transformers.enable('default', max_rows=30000)

# Load data
try:
    df = pd.read_csv('data/web_dataset.csv', parse_dates=['date'])
except FileNotFoundError:
    df = pd.read_csv('web_dataset.csv', parse_dates=['date'])

# Prepare fields
viz = df[['date', 'ticker', 'sector', 'returns', 'regime_label']].dropna().copy()
viz['year'] = viz['date'].dt.year.astype(str)
viz['return_pct'] = viz['returns'] * 100

# Add an "All years" option
all_years = viz.copy()
all_years['year'] = 'All years'
viz = pd.concat([viz, all_years], ignore_index=True)

# Dropdown parameters
sector_options = ['XLE', 'SPY', 'XLK', 'XLF', 'XLV', 'XLY']
sector_labels = [
    'XLE — Energy',
    'SPY — S&P 500',
    'XLK — Technology',
    'XLF — Financials',
    'XLV — Healthcare',
    'XLY — Consumer Disc.'
]
year_options = ['All years'] + sorted(df['date'].dt.year.astype(str).unique().tolist())

ticker_param = alt.param(
    name='ticker_sel',
    value='XLE',
    bind=alt.binding_select(options=sector_options, labels=sector_labels, name='Sector: ')
)

year_param = alt.param(
    name='year_sel',
    value='All years',
    bind=alt.binding_select(options=year_options, name='Year: ')
)

flt = '(datum.ticker == ticker_sel) && (datum.year == year_sel)'

color_scale = alt.Scale(
    domain=['Normal', 'High'],
    range=['#2980b9', '#c0392b']
)

base = alt.Chart(viz).transform_filter(flt)

hist = base.mark_bar(opacity=0.5).encode(
    x=alt.X(
        'return_pct:Q',
        bin=alt.Bin(maxbins=45),
        title='Daily Return (%)'
    ),
    y=alt.Y('count():Q', title='Frequency'),
    color=alt.Color(
        'regime_label:N',
        title='Volatility Regime',
        scale=color_scale
    ),
    tooltip=[
        alt.Tooltip('regime_label:N', title='Volatility Regime'),
        alt.Tooltip('count():Q', title='Days'),
        alt.Tooltip('mean(return_pct):Q', title='Avg. return in bin', format='.2f')
    ]
).properties(
    width=720,
    height=360,
    title=alt.Title(
        'Visualization 5: Return Distribution by Volatility Regime',
        subtitle=[
            'This histogram compares daily return distributions under normal and high volatility',
            'Blue represents normal volatility and red represents high volatility; use the dropdowns to filter by sector and year'
        ],
        fontSize=16
    )
)

stats = base.transform_aggregate(
    mean_return='mean(return_pct)',
    std_return='stdev(return_pct)',
    observations='count()',
    groupby=['regime_label']
).transform_calculate(
    label="datum.regime_label + ' | mean: ' + format(datum.mean_return, '.3f') + '% | std: ' + format(datum.std_return, '.3f') + '% | n=' + datum.observations"
).mark_text(
    align='left',
    fontSize=12,
    dx=5
).encode(
    y=alt.Y('regime_label:N', axis=None, sort=['Normal', 'High']),
    text='label:N',
    color=alt.Color('regime_label:N', scale=color_scale, legend=None)
).properties(
    width=720,
    height=40
)

chart = alt.vconcat(
    hist,
    stats,
    spacing=8
).add_params(
    ticker_param,
    year_param
).configure(
    font='Arial',
    axis=alt.AxisConfig(labelFontSize=11, titleFontSize=12),
    legend=alt.LegendConfig(titleFontSize=11, labelFontSize=11, orient='top')
)

chart.save('viz5_return_distribution.html')
print('Saved: viz5_return_distribution.html')