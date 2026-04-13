"""
Viz 4: Portfolio Strategy Comparison Across Sectors
DS4200 - Altair interactive visualization
Interaction: Dropdown to select ETF, showing dynamic strategy vs buy-and-hold

Run: pip install altair pandas vl-convert-python
     python viz4_portfolio_strategy.py
"""

import altair as alt
import pandas as pd

alt.data_transformers.enable('default', max_rows=20000)

# Load data
try:
    df = pd.read_csv('data/web_dataset.csv', parse_dates=['date'])
except FileNotFoundError:
    df = pd.read_csv('web_dataset.csv', parse_dates=['date'])

# ── Backtest a simple volatility-based strategy per ETF ──
def backtest_strategy(etf_data, normal_alloc=0.8, high_alloc=0.4):
    """
    Dynamic allocation: invest normal_alloc in stocks during normal volatility,
    high_alloc during high volatility. The rest is held in cash.
    """
    data = etf_data.sort_values('date').copy()
    data = data.dropna(subset=['returns', 'regime'])

    data['allocation'] = data['regime'].map({0: normal_alloc, 1: high_alloc})
    data['strategy_return'] = data['returns'] * data['allocation']
    data['buyhold_return'] = data['returns']

    data['strategy_cumulative'] = (1 + data['strategy_return']).cumprod()
    data['buyhold_cumulative'] = (1 + data['buyhold_return']).cumprod()

    return data

results = []
for ticker in df['ticker'].unique():
    etf = df[df['ticker'] == ticker].copy()
    bt = backtest_strategy(etf)
    bt_long = pd.melt(
        bt[['date', 'ticker', 'sector', 'strategy_cumulative', 'buyhold_cumulative', 'regime_label']],
        id_vars=['date', 'ticker', 'sector', 'regime_label'],
        value_vars=['strategy_cumulative', 'buyhold_cumulative'],
        var_name='approach',
        value_name='cumulative_return'
    )
    bt_long['approach'] = bt_long['approach'].map({
        'strategy_cumulative': 'Dynamic Strategy',
        'buyhold_cumulative': 'Buy & Hold'
    })
    results.append(bt_long)

all_results = pd.concat(results, ignore_index=True)

# ── Dropdown binding for ETF selection ──
ticker_options = ['XLE', None, 'SPY', 'XLK', 'XLF', 'XLV', 'XLY']
ticker_labels = ['XLE', 'All ETFs', 'SPY', 'XLK', 'XLF', 'XLV', 'XLY']

ticker_dropdown = alt.binding_select(
    options=ticker_options,
    labels=ticker_labels,
    name='Select ETF: '
)

ticker_param = alt.param(
    name='ticker_sel',
    bind=ticker_dropdown,
    value='XLE'
)

approach_colors = alt.Scale(
    domain=['Dynamic Strategy', 'Buy & Hold'],
    range=['#2980b9', '#95a5a6']
)

# ── Line chart ──
lines = alt.Chart(all_results).mark_line(strokeWidth=1.8).encode(
    x=alt.X('date:T', title='Date'),
    y=alt.Y(
        'cumulative_return:Q',
        title='Cumulative Return (Growth of $1)',
        scale=alt.Scale(zero=False)
    ),
    color=alt.Color('approach:N', scale=approach_colors, title='Strategy'),
    strokeDash=alt.StrokeDash(
        'approach:N',
        scale=alt.Scale(
            domain=['Dynamic Strategy', 'Buy & Hold'],
            range=[[1, 0], [6, 3]]
        ),
        legend=None
    ),
    detail='ticker:N',
    opacity=alt.condition(
        'ticker_sel == null || datum.ticker == ticker_sel',
        alt.value(0.9),
        alt.value(0.08)
    ),
    tooltip=[
        alt.Tooltip('date:T', title='Date', format='%b %d, %Y'),
        alt.Tooltip('ticker:N', title='ETF'),
        alt.Tooltip('sector:N', title='Sector'),
        alt.Tooltip('approach:N', title='Strategy'),
        alt.Tooltip('cumulative_return:Q', title='Cumulative Return', format=',.3f'),
        alt.Tooltip('regime_label:N', title='Current Regime')
    ]
).add_params(
    ticker_param
).properties(
    width=760,
    height=360,
    title=alt.Title(
        'Visualization 4: Dynamic Volatility Strategy vs. Buy & Hold',
        subtitle=[
            'This chart compares cumulative performance for a regime-aware strategy versus buy-and-hold',
            'Strategy: 80% stocks in normal volatility, 40% stocks in high volatility, rest in cash'
        ],
        fontSize=16
    )
)

# ── Reference line at 1.0 ──
rule = alt.Chart(pd.DataFrame({'y': [1.0]})).mark_rule(
    strokeDash=[4, 4],
    color='#333',
    strokeWidth=0.8
).encode(
    y='y:Q'
)

chart = (rule + lines).configure(
    font='Arial',
    axis=alt.AxisConfig(labelFontSize=11, titleFontSize=12),
    legend=alt.LegendConfig(titleFontSize=12, labelFontSize=11, orient='top')
)

chart.save('viz4_portfolio_strategy.html')
print("Saved: viz4_portfolio_strategy.html")