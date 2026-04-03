# Funding Rate Arbitrage Monitor

A Python-based tool and Streamlit dashboard that pulls real-time perpetual funding rates from major quantitative exchanges (Binance, Bybit, OKX, and dYdX). It computes cross-exchange spreads, flags arbitrage opportunities based on a configurable APR threshold, and backtests historical funding rate carry strategies.

## Features
- **Live Scanning**: Monitors funding rates natively by interacting with exchange REST APIs.
- **Arbitrage Engine**: Flags trading pairs where the funding rate spread (annualized) exceeds a defined safe threshold (e.g., >15% APR).
- **Backtesting Tool**: Simulates historical entry/exit models utilizing funding periods and associated funding costs, taking into account basic fee structures.
- **Interactive Dashboard**: A sleek Streamlit UI with a live heatmap of cross-exchange funding rates, spread histories, and backtested P&L equity curves.

## Installation

```bash
# Optional but recommended: create a virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

## Usage

To start the local Streamlit dashboard:

```bash
streamlit run app.py
```

## CV Highlights / Draft Bullets
- Developed a cross-exchange funding rate arbitrage scanner pulling real-time perpetual contract rates from Binance, Bybit, OKX, and dYdX; computed annualised carry spreads and flagged opportunities exceeding configurable APR thresholds.
- Backtested funding rate carry strategies across 12 months of historical data, analysing entry/exit timing, holding costs, and net carry returns; deployed as a live Streamlit dashboard with heatmap visualisation.
