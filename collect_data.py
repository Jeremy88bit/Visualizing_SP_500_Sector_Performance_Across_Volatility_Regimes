"""
DS4200 Project - Data Collection Script
Collects sector ETF data from Yahoo Finance and FRED macro data.
Run: pip install yfinance pandas numpy
Then: python collect_data.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

ETFS = {
    'SPY': 'S&P 500 (Benchmark)',
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLV': 'Healthcare',
    'XLY': 'Consumer Discretionary'
}

START_DATE = '2015-01-01'
END_DATE = datetime.today().strftime('%Y-%m-%d')

OUTPUT_DIR = 'data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 1. COLLECT ETF PRICE DATA
# ============================================================

print("=" * 60)
print("DS4200 PROJECT - DATA COLLECTION")
print("=" * 60)

print(f"\nFetching ETF data from {START_DATE} to {END_DATE}...")
print(f"ETFs: {', '.join(ETFS.keys())}\n")

all_etf_data = {}

for ticker, name in ETFS.items():
    print(f"  Downloading {ticker} ({name})...", end=" ")
    try:
        data = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False)
        # Flatten multi-level columns if present (newer yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index = pd.to_datetime(data.index).normalize()
        all_etf_data[ticker] = data
        print(f"OK - {len(data):,} days")
    except Exception as e:
        print(f"FAILED - {e}")

# Combine into a single DataFrame with ticker column
frames = []
for ticker, data in all_etf_data.items():
    df = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df['ticker'] = ticker
    df['sector'] = ETFS[ticker]
    df.index.name = 'date'
    frames.append(df)

combined = pd.concat(frames).reset_index()
combined = combined.sort_values(['ticker', 'date']).reset_index(drop=True)

print(f"\nCombined dataset: {len(combined):,} rows × {len(combined.columns)} columns")
print(f"Tickers: {combined['ticker'].nunique()}")
print(f"Date range: {combined['date'].min().strftime('%Y-%m-%d')} to {combined['date'].max().strftime('%Y-%m-%d')}")
print(f"Days per ticker: ~{len(combined) // combined['ticker'].nunique():,}")

# ============================================================
# 2. FEATURE ENGINEERING (PER ETF)
# ============================================================

print("\nEngineering features per ETF...")

def engineer_features(df):
    """Create 28 features for a single ETF's price data."""
    df = df.copy().sort_values('date').set_index('date')
    
    df['returns'] = df['close'].pct_change()
    
    # --- Volatility features (6) ---
    df['volatility_5d'] = df['returns'].rolling(5).std() * np.sqrt(252)
    df['volatility_10d'] = df['returns'].rolling(10).std() * np.sqrt(252)
    df['volatility_20d'] = df['returns'].rolling(20).std() * np.sqrt(252)
    df['volatility_50d'] = df['returns'].rolling(50).std() * np.sqrt(252)
    df['volatility_ratio'] = df['volatility_10d'] / df['volatility_50d']
    df['volatility_term_structure'] = df['volatility_5d'] / df['volatility_20d']
    
    # --- Moving averages & distance (7) ---
    df['ma_10'] = df['close'].rolling(10).mean()
    df['ma_50'] = df['close'].rolling(50).mean()
    df['ma_200'] = df['close'].rolling(200).mean()
    df['ma10_distance'] = (df['close'] - df['ma_10']) / df['ma_10'] * 100
    df['ma50_distance'] = (df['close'] - df['ma_50']) / df['ma_50'] * 100
    df['price_to_ma200'] = df['close'] / df['ma_200']
    df['ma_cross'] = (df['ma_10'] > df['ma_50']).astype(int)
    
    # --- Bollinger Bands (2) ---
    bb_mid = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_width'] = (2 * bb_std * 2) / bb_mid  # band width relative to price
    df['bb_position'] = (df['close'] - (bb_mid - bb_std * 2)) / (bb_std * 4)
    
    # --- ATR (1) ---
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr_ratio'] = true_range.rolling(14).mean() / df['close']
    
    # --- Momentum (4) ---
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['momentum_1m'] = df['close'].pct_change(21) * 100
    df['momentum_3m'] = df['close'].pct_change(63) * 100
    df['momentum_6m'] = df['close'].pct_change(126) * 100
    
    # --- Volume (3) ---
    df['volume_10d_avg'] = df['volume'].rolling(10).mean()
    df['volume_50d_avg'] = df['volume'].rolling(50).mean()
    df['volume_ratio'] = df['volume_10d_avg'] / df['volume_50d_avg']
    
    # --- Market structure (2) ---
    df['market_breadth_proxy'] = (df['close'] > df['ma_200']).rolling(20).mean() * 100
    df['high_low_ratio'] = df['high'] / df['low']
    
    # --- Forward volatility target (for regime classification) ---
    df['forward_volatility'] = df['returns'].shift(-20).rolling(20).std() * np.sqrt(252)
    
    return df.reset_index()

featured_frames = []
for ticker in ETFS.keys():
    print(f"  Processing {ticker}...", end=" ")
    etf_df = combined[combined['ticker'] == ticker].copy()
    featured = engineer_features(etf_df)
    featured['ticker'] = ticker
    featured['sector'] = ETFS[ticker]
    featured_frames.append(featured)
    print(f"OK - {len(featured.columns)} columns")

full_dataset = pd.concat(featured_frames, ignore_index=True)

# ============================================================
# 3. REGIME CLASSIFICATION
# ============================================================

print("\nClassifying volatility regimes...")

# Use SPY's median forward volatility as the universal threshold
spy_data = full_dataset[full_dataset['ticker'] == 'SPY']
median_vol = spy_data['forward_volatility'].dropna().median()
print(f"  SPY median forward volatility: {median_vol:.4f} ({median_vol*100:.2f}%)")

full_dataset['regime'] = (full_dataset['forward_volatility'] > median_vol).astype(int)
full_dataset['regime_label'] = full_dataset['regime'].map({0: 'Normal', 1: 'High'})

# ============================================================
# 4. LOAD FRED MACRO DATA (if CSVs are available)
# ============================================================

print("\nLooking for FRED macro data CSVs...")

fred_loaded = False
for fred_file, col_name in [('VIXCLS.csv', 'vix'), ('DFF.csv', 'fed_funds_rate'), ('UNRATE.csv', 'unemployment_rate')]:
    if os.path.exists(fred_file):
        print(f"  Found {fred_file}")
        fred_df = pd.read_csv(fred_file)
        fred_df['observation_date'] = pd.to_datetime(fred_df['observation_date'])
        fred_df = fred_df.set_index('observation_date')
        fred_df.columns = [col_name]
        fred_df[col_name] = pd.to_numeric(fred_df[col_name], errors='coerce')
        fred_df = fred_df.dropna()
        if col_name == 'unemployment_rate':
            fred_df = fred_df.resample('D').ffill()
        
        # Merge with full dataset
        fred_df.index = fred_df.index.normalize()
        fred_df.index.name = 'date'
        full_dataset = full_dataset.merge(
            fred_df.reset_index(), on='date', how='left'
        )
        full_dataset[col_name] = full_dataset[col_name].ffill().bfill()
        fred_loaded = True
    else:
        print(f"  {fred_file} not found - download from FRED:")
        print(f"    https://fred.stlouisfed.org/series/{fred_file.replace('.csv', '')}")

if not fred_loaded:
    print("\n  NOTE: FRED CSVs not found in current directory.")
    print("  Download these 3 files from FRED and place them here:")
    print("    - VIXCLS.csv  (VIX Index)")
    print("    - DFF.csv     (Fed Funds Rate)")
    print("    - UNRATE.csv  (Unemployment Rate)")
    print("  Then re-run this script to include macro features.")

# ============================================================
# 5. CLEAN AND SAVE
# ============================================================

print("\nCleaning and saving...")

# Drop rows with NaN in key feature columns (from rolling windows)
feature_cols = [c for c in full_dataset.columns if c not in 
                ['date', 'ticker', 'sector', 'regime', 'regime_label',
                 'open', 'high', 'low', 'close', 'volume', 'returns',
                 'ma_10', 'ma_50', 'ma_200', 'volume_10d_avg', 'volume_50d_avg',
                 'forward_volatility']]
clean = full_dataset.dropna(subset=['volatility_50d', 'momentum_6m', 'ma_200'])

# Save files
clean.to_csv(f'{OUTPUT_DIR}/full_dataset.csv', index=False)
print(f"  Saved: {OUTPUT_DIR}/full_dataset.csv ({len(clean):,} rows × {len(clean.columns)} cols)")

# Also save a lightweight version for the website (smaller file for GitHub)
web_cols = ['date', 'ticker', 'sector', 'close', 'returns', 'volume',
            'volatility_20d', 'volatility_50d', 'rsi', 'momentum_1m', 'momentum_3m',
            'momentum_6m', 'volume_ratio', 'bb_width', 'atr_ratio',
            'forward_volatility', 'regime', 'regime_label']
# Add FRED columns if they exist
for col in ['vix', 'fed_funds_rate', 'unemployment_rate']:
    if col in clean.columns:
        web_cols.append(col)

web_data = clean[web_cols].copy()
web_data.to_csv(f'{OUTPUT_DIR}/web_dataset.csv', index=False)
print(f"  Saved: {OUTPUT_DIR}/web_dataset.csv ({len(web_data):,} rows × {len(web_data.columns)} cols)")

# Save per-ETF files (useful for individual Altair charts)
for ticker in ETFS.keys():
    etf_slice = clean[clean['ticker'] == ticker]
    etf_slice.to_csv(f'{OUTPUT_DIR}/{ticker}_features.csv', index=False)
    print(f"  Saved: {OUTPUT_DIR}/{ticker}_features.csv ({len(etf_slice):,} rows)")

# ============================================================
# 6. SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DATA COLLECTION COMPLETE")
print("=" * 60)
print(f"\nTotal observations: {len(clean):,}")
print(f"Features per observation: {len(clean.columns)}")
print(f"ETFs: {', '.join(ETFS.keys())} ({len(ETFS)} sectors)")
print(f"Date range: {clean['date'].min()} to {clean['date'].max()}")
print(f"\nRegime distribution (across all ETFs):")
print(clean['regime_label'].value_counts().to_string())
print(f"\nPer-ETF row counts:")
print(clean.groupby('ticker').size().to_string())
print(f"\nFiles saved to '{OUTPUT_DIR}/' directory:")
print(f"  full_dataset.csv    - Complete dataset with all features")
print(f"  web_dataset.csv     - Lightweight version for GitHub/website")
print(f"  [TICKER]_features.csv - Individual ETF files")
print(f"\nNext step: Run the visualization scripts!")
