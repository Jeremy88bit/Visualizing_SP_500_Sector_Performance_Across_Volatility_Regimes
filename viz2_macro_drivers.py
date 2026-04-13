"""
Viz 3: Macro & Technical Driver Importance
DS4200 - Altair static visualization
Shows which features best distinguish high vs. normal volatility regimes

Run: pip install altair pandas scikit-learn vl-convert-python
     python viz3_macro_drivers.py
"""

import altair as alt
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

alt.data_transformers.enable('default', max_rows=20000)

# Load data
df = pd.read_csv('data/full_dataset.csv', parse_dates=['date'])

# Use SPY data for feature importance (benchmark index)
spy = df[df['ticker'] == 'SPY'].dropna(subset=['regime']).copy()

# Define features (same 28 as in DS2500, excluding macro if not available)
feature_cols = [
    'volatility_5d', 'volatility_10d', 'volatility_20d', 'volatility_50d',
    'volatility_ratio', 'volatility_term_structure',
    'ma10_distance', 'ma50_distance', 'price_to_ma200', 'ma_cross',
    'bb_width', 'bb_position', 'atr_ratio',
    'rsi', 'momentum_1m', 'momentum_3m', 'momentum_6m',
    'volume_ratio', 'volume_momentum',
    'market_breadth_proxy', 'high_low_ratio'
]

# Add FRED features if available
for col in ['vix', 'fed_funds_rate', 'unemployment_rate']:
    if col in spy.columns and spy[col].notna().sum() > 100:
        feature_cols.append(col)

# Clean
available_features = [f for f in feature_cols if f in spy.columns]
model_data = spy[available_features + ['regime']].dropna()

X = model_data[available_features]
y = model_data['regime']

# Train Random Forest to get feature importances
rf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=10)
rf.fit(X, y)

# Build importance DataFrame
importance_df = pd.DataFrame({
    'feature': available_features,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False).head(15)

# Categorize features for coloring
def categorize(feat):
    if 'volatility' in feat: return 'Volatility'
    if 'ma' in feat or 'price_to' in feat or 'cross' in feat or 'breadth' in feat: return 'Trend / Moving Avg'
    if 'bb_' in feat or 'atr' in feat: return 'Range / Bands'
    if 'rsi' in feat or 'momentum' in feat: return 'Momentum'
    if 'volume' in feat: return 'Volume'
    if feat in ['vix', 'fed_funds_rate', 'unemployment_rate']: return 'Macroeconomic'
    return 'Other'

importance_df['category'] = importance_df['feature'].apply(categorize)

# Readable feature names
name_map = {
    'fed_funds_rate': 'Fed Funds Rate',
    'vix': 'VIX Index',
    'unemployment_rate': 'Unemployment Rate',
    'volatility_5d': 'Volatility (5-day)',
    'volatility_10d': 'Volatility (10-day)',
    'volatility_20d': 'Volatility (20-day)',
    'volatility_50d': 'Volatility (50-day)',
    'volatility_ratio': 'Volatility Ratio (10d/50d)',
    'volatility_term_structure': 'Volatility Term Structure',
    'momentum_1m': 'Momentum (1-month)',
    'momentum_3m': 'Momentum (3-month)',
    'momentum_6m': 'Momentum (6-month)',
    'rsi': 'RSI (14-day)',
    'ma10_distance': 'Distance from 10-day MA',
    'ma50_distance': 'Distance from 50-day MA',
    'price_to_ma200': 'Price / 200-day MA',
    'ma_cross': 'MA Crossover Signal',
    'bb_width': 'Bollinger Band Width',
    'bb_position': 'Bollinger Band Position',
    'atr_ratio': 'ATR Ratio',
    'volume_ratio': 'Volume Ratio (10d/50d)',
    'volume_momentum': 'Volume Momentum',
    'market_breadth_proxy': 'Market Breadth Proxy',
    'high_low_ratio': 'High/Low Ratio'
}
importance_df['feature_name'] = importance_df['feature'].map(name_map).fillna(importance_df['feature'])

# Category colors
category_colors = {
    'Macroeconomic': '#c0392b',
    'Volatility': '#e67e22',
    'Momentum': '#2980b9',
    'Trend / Moving Avg': '#27ae60',
    'Range / Bands': '#8e44ad',
    'Volume': '#16a085',
    'Other': '#7f8c8d'
}

cat_scale = alt.Scale(
    domain=list(category_colors.keys()),
    range=list(category_colors.values())
)

# ── Build chart ──
bars = alt.Chart(importance_df).mark_bar(
    cornerRadiusEnd=4,
    height=18
).encode(
    x=alt.X('importance:Q',
            title='Feature Importance (Random Forest)',
            axis=alt.Axis(format='.0%')),
    y=alt.Y('feature_name:N',
            title='',
            sort=alt.EncodingSortField(field='importance', order='descending')),
    color=alt.Color('category:N',
                    scale=cat_scale,
                    title='Feature Category'),
    tooltip=[
        alt.Tooltip('feature_name:N', title='Feature'),
        alt.Tooltip('category:N', title='Category'),
        alt.Tooltip('importance:Q', title='Importance', format='.4f')
    ]
).properties(
    width=550,
    height=400,
    title=alt.Title(
        'Visualization 3: What Drives Volatility Regimes?',
        subtitle='Top 15 features ranked by Random Forest importance for classifying high vs. normal volatility',
        fontSize=16
    )
)

# Add value labels
labels = alt.Chart(importance_df).mark_text(
    align='left',
    dx=4,
    fontSize=11,
    color='#555'
).encode(
    x=alt.X('importance:Q'),
    y=alt.Y('feature_name:N',
            sort=alt.EncodingSortField(field='importance', order='descending')),
    text=alt.Text('importance:Q', format='.1%')
)

chart = (bars + labels).configure(
    font='Arial',
    axis=alt.AxisConfig(labelFontSize=11, titleFontSize=12),
    legend=alt.LegendConfig(
        titleFontSize=12, labelFontSize=11,
        orient='bottom', columns=3
    )
)

chart.save('viz2_macro_drivers.html')
print("Saved: viz3_macro_drivers.html")
print(f"\nTop 5 features:")
for _, row in importance_df.head(5).iterrows():
    print(f"  {row['feature_name']}: {row['importance']:.4f} ({row['category']})")
