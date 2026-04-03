import os

# Configuration Settings

# Exchanges to monitor
EXCHANGES = ["Binance", "Bybit", "OKX", "dYdX"]

# Default assets to monitor
DEFAULT_SYMBOLS = ["BTC", "ETH", "SOL", "DOGE"]

# API Endpoints
API_URLS = {
    "Binance": "https://fapi.binance.com/fapi/v1",
    "Bybit": "https://api.bybit.com/v5/market",
    "OKX": "https://www.okx.com/api/v5/public",
    "dYdX": "https://indexer.dydx.trade/v4"
}

# Arbitrage Engine Settings
# The threshold (Annualized) to flag an opportunity (e.g. 0.15 = 15% APR)
MIN_APR_THRESHOLD = 0.15

# Number of historical records fetched per underlying limit requests
HISTORICAL_LIMIT = 500

# Streamlit App Configurations
APP_TITLE = "Funding Rate Arbitrage Monitor"
UPDATE_INTERVAL = 30  # seconds for live refresh rate in the app
