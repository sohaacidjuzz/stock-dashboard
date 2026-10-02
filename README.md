# Stock Dashboard

A Python-based stock dashboard using Streamlit and yFinance for viewing price trends, volume, RSI, and multi-stock comparison.

## Features
- Multi-stock watchlist
- Interactive candlestick chart
- Moving averages
- RSI indicator
- Trading volume chart
- Correlation matrix across stocks
- Portfolio overview table

## Setup
1. Clone the project
2. Create a virtual environment
3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app
```bash
streamlit run app.py
```

## Notes
- Some stock symbols may not be available in all markets or may have limited historical data.
- Yahoo Finance is used for market data and may occasionally rate-limit requests.
