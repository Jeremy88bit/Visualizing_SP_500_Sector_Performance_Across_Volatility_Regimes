# Visualizing S&P 500 Volatility Regimes
### DS4200 — Information Presentation & Data Visualization

---

## How to View the Website

### Requirements
- **Python 3** (any version — only needed to run a local file server, no packages required)
- **Google Chrome** (recommended) or any modern web browser

### Instructions

1. **Unzip** the project folder and open it

2. **Open a terminal / command prompt inside the project folder**
   - **Windows:** Open File Explorer, navigate into the unzipped folder so you can see `index.html`. Then click the address bar at the top, type `cmd`, and press Enter.
   - **Mac:** Right-click the folder in Finder → "New Terminal at Folder"
   - **Linux:** Open a terminal and `cd` into the folder

3. **Verify you're in the right place.** You should see this structure:
   ```
   DS4200_Project/
   ├── index.html          ← main website
   ├── data/
   │   ├── web_dataset.csv
   │   └── feature_importance.csv
   ├── design_rationale.docx
   ├── collect_data.py
   ├── viz1_sector_timeline.py
   ├── viz3_macro_drivers.py
   ├── viz4_portfolio_strategy.py
   └── README.md
   ```

4. **Start a local web server** by running:
   ```
   python -m http.server 8000
   ```
   You should see: `Serving HTTP on :: port 8000`

   > If `python` doesn't work, try `python3 -m http.server 8000`

5. **Open Google Chrome** and go to:
   ```
   http://localhost:8000
   ```

6. **That's it!** The website will load with all 5 interactive visualizations. Scroll down to explore each one.

7. **When finished**, go back to the terminal and press `Ctrl + C` to stop the server.

---

## Interacting with the Visualizations

| # | Visualization | How to Interact |
|---|---|---|
| 1 | Sector Volatility Timeline | **Drag** on the small overview chart at the bottom to zoom into a date range. **Hover** over lines for details. |
| 2 | Sector Correlation Heatmap | **Click** the "All periods" / "Normal volatility" / "High volatility" buttons to see how correlations change. **Hover** cells for values. |
| 3 | Volatility Regime Drivers | Static chart — **hover** bars for exact importance values. |
| 4 | Portfolio Strategy Comparison | Use the **dropdown** to select a specific ETF or view all. **Hover** for details. |
| 5 | Return Distribution by Regime | Use the **sector dropdown** and **year dropdown** to filter. Bars animate between selections. **Hover** for bin details. |

---

## Troubleshooting

**"The page is blank / charts don't show"**
- Make sure you started the server from inside the project folder (where `index.html` is), not from a parent folder.
- Check that the `data/` folder with CSV files is in the same directory as `index.html`.

**"python is not recognized"**
- Try `python3` instead of `python`.
- On Windows, you may need to install Python from [python.org](https://www.python.org/downloads/).

**Charts load but show no data**
- Open Chrome DevTools (press F12 → Console tab) and check for errors.
- The most common issue is running the server from the wrong directory.

---

## Project Files

| [viz3[viz3_macro_drivers.py](viz3_macro_drivers.py)_macro_drivers.html](viz3_macro_drivers.html)File | De[viz1_sector_timeline.py](viz1_sector_timeline.py)scription |
|---|---|
| `index.html`[viz4_portfolio_strategy.py](viz4_portfolio_strategy.py) | Main website with all visualizations (HTML/CSS/JS) |
| `data/web_dataset.csv` | Dataset: 15,822 observations, 6 ETFs, 32 features |
| `data/feature_importance.csv` | Feature ranking data for Visualization 3 |
| `design_rationale.docx` | Design rationale document explaining each visualization |
| `collect_data.py` | Python script used to collect and engineer the data |
| `viz1_sector_timeline.py` | Altair source code for Visualization 1 |
| `viz3_macro_drivers.py` | Altair source code for Visualization 3 |
| `viz4_portfolio_strategy.py` | Altair source code for Visualization 4 |

---

## Data Sources

- **Yahoo Finance** — Daily OHLCV price data for SPY, XLK, XLF, XLE, XLV, XLY (2015–2025)
- **Federal Reserve Economic Data (FRED)** — VIX Index, Federal Funds Rate, Unemployment Rate
