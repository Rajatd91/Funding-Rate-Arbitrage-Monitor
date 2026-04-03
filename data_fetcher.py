import requests
import pandas as pd
import time
from config import API_URLS, DEFAULT_SYMBOLS

def format_symbol(symbol, exchange):
    """Format base symbol to exchange-specific format."""
    if exchange == "Binance" or exchange == "Bybit":
        return f"{symbol}USDT"
    elif exchange == "OKX":
        return f"{symbol}-USDT-SWAP"
    elif exchange == "dYdX":
        return f"{symbol}-USD"
    return symbol

def fetch_binance_current(symbol):
    """Fetch current funding rate from Binance."""
    sym = format_symbol(symbol, "Binance")
    url = f"{API_URLS['Binance']}/premiumIndex" # Premium index has the current/next funding rate
    try:
        response = requests.get(url, params={"symbol": sym})
        response.raise_for_status()
        data = response.json()
        return float(data.get("lastFundingRate", 0))
    except Exception as e:
        print(f"Error fetching Binance current for {symbol}: {e}")
        return None

def fetch_bybit_current(symbol):
    """Fetch current funding rate from Bybit."""
    sym = format_symbol(symbol, "Bybit")
    url = f"{API_URLS['Bybit']}/tickers"
    try:
        response = requests.get(url, params={"category": "linear", "symbol": sym})
        response.raise_for_status()
        data = response.json()
        if data["retCode"] == 0 and len(data["result"]["list"]) > 0:
            return float(data["result"]["list"][0].get("fundingRate", 0))
        return None
    except Exception as e:
        print(f"Error fetching Bybit current for {symbol}: {e}")
        return None

def fetch_okx_current(symbol):
    """Fetch current funding rate from OKX."""
    sym = format_symbol(symbol, "OKX")
    url = f"{API_URLS['OKX']}/funding-rate"
    try:
        response = requests.get(url, params={"instId": sym})
        response.raise_for_status()
        data = response.json()
        if data["code"] == "0" and len(data["data"]) > 0:
            return float(data["data"][0].get("fundingRate", 0))
        return None
    except Exception as e:
        print(f"Error fetching OKX current for {symbol}: {e}")
        return None

def fetch_dydx_current(symbol):
    """Fetch current funding rate from dYdX."""
    sym = format_symbol(symbol, "dYdX")
    url = f"{API_URLS['dYdX']}/perpetualMarkets"
    try:
        # Note: dydx usually returns all markets, so we get all and filter
        response = requests.get(url, params={"ticker": sym}) 
        response.raise_for_status()
        data = response.json()
        markets = data.get("markets", {})
        if sym in markets:
            return float(markets[sym].get("nextFundingRate", 0))
        return None
    except Exception as e:
        print(f"Error fetching dYdX current for {symbol}: {e}")
        return None

def get_live_funding_rates(symbols=DEFAULT_SYMBOLS):
    """Get a DataFrame of current funding rates for all exchanges."""
    results = []
    for sym in symbols:
        results.append({
            "Symbol": sym,
            "Binance": fetch_binance_current(sym),
            "Bybit": fetch_bybit_current(sym),
            "OKX": fetch_okx_current(sym),
            "dYdX": fetch_dydx_current(sym)
        })
    df = pd.DataFrame(results)
    return df

# ----- HISTORICAL DATA -----

def fetch_binance_history(symbol, limit=500):
    sym = format_symbol(symbol, "Binance")
    url = f"{API_URLS['Binance']}/fundingRate"
    try:
        response = requests.get(url, params={"symbol": sym, "limit": limit})
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        if df.empty:
            return df
        
        df["timestamp"] = pd.to_datetime(df["fundingTime"], unit='ms')
        df["fundingRate"] = df["fundingRate"].astype(float)
        return df[["timestamp", "fundingRate"]].set_index("timestamp")
    except Exception as e:
        print(f"Error fetching Binance history: {e}")
        return pd.DataFrame()

def fetch_bybit_history(symbol, limit=200): # bybit max is 200
    sym = format_symbol(symbol, "Bybit")
    url = f"{API_URLS['Bybit']}/funding/history"
    try:
        response = requests.get(url, params={"category": "linear", "symbol": sym, "limit": limit})
        response.raise_for_status()
        data = response.json()
        if data["retCode"] == 0:
            df = pd.DataFrame(data["result"]["list"])
            if df.empty:
                return df
            df["timestamp"] = pd.to_datetime(df["fundingRateTimestamp"].astype(float), unit='ms')
            df["fundingRate"] = df["fundingRate"].astype(float)
            return df[["timestamp", "fundingRate"]].set_index("timestamp").sort_index()
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching Bybit history: {e}")
        return pd.DataFrame()

def fetch_okx_history(symbol, limit=100):
    sym = format_symbol(symbol, "OKX")
    url = f"{API_URLS['OKX']}/funding-rate-history"
    try:
        response = requests.get(url, params={"instId": sym, "limit": limit})
        response.raise_for_status()
        data = response.json()
        if data["code"] == "0":
            df = pd.DataFrame(data["data"])
            if df.empty:
                return df
            df["timestamp"] = pd.to_datetime(df["fundingTime"].astype(float), unit='ms')
            df["fundingRate"] = df["fundingRate"].astype(float)
            return df[["timestamp", "fundingRate"]].set_index("timestamp").sort_index()
        return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching OKX history: {e}")
        return pd.DataFrame()

def fetch_dydx_history(symbol, limit=100):
    sym = format_symbol(symbol, "dYdX")
    url = f"{API_URLS['dYdX']}/historicalFunding"
    try:
        response = requests.get(url, params={"ticker": sym, "limit": limit})
        response.raise_for_status()
        data = response.json()
        rates = data.get("historicalFunding", [])
        if not rates:
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df["timestamp"] = pd.to_datetime(df["effectiveAt"])
        # dYdX rates might come as a percentage string or float, need to handle
        df["fundingRate"] = df["rate"].astype(float)
        return df[["timestamp", "fundingRate"]].set_index("timestamp").sort_index()
    except Exception as e:
        # print(f"Error fetching dYdX history: {e}")
        return pd.DataFrame()

def get_historical_rates(symbol):
    """Fetch historical rates and align them into a single dataframe."""
    binance = fetch_binance_history(symbol).rename(columns={"fundingRate": "Binance"})
    bybit = fetch_bybit_history(symbol).rename(columns={"fundingRate": "Bybit"})
    okx = fetch_okx_history(symbol).rename(columns={"fundingRate": "OKX"})
    dydx = fetch_dydx_history(symbol).rename(columns={"fundingRate": "dYdX"})
    
    # Merge on timestamp. Due to slight time differences, we'll use a tolerance or round to nearest hour
    # Most funding rates are 8h or 1h. Let's round the index to the nearest hour before joining.
    for df in [binance, bybit, okx, dydx]:
        if not df.empty:
            df.index = df.index.round('h') # type: ignore
    
    df_merged = binance.join([bybit, okx, dydx], how='outer')
    return df_merged

if __name__ == "__main__":
    print("Testing live feed...")
    print(get_live_funding_rates(["BTC", "ETH"]))
    print("Testing history feed for BTC...")
    print(get_historical_rates("BTC").tail())
