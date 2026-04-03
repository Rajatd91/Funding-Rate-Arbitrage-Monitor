import pandas as pd
import numpy as np
from config import MIN_APR_THRESHOLD, EXCHANGES

# Funding rate intervals (in hours) - simplified defaults
FUNDING_INTERVALS = {
    "Binance": 8,
    "Bybit": 8,
    "OKX": 8,
    "dYdX": 1  # dYdX v4 actually applies funding every block but reports hourly
}

def annualize_rate(rate, exchange):
    """Convert per-interval funding rate to Annualized Percentage Rate (APR)."""
    if pd.isna(rate):
        return pd.NA
    interval = FUNDING_INTERVALS.get(exchange, 8)
    periods_per_day = 24 / interval
    periods_per_year = periods_per_day * 365
    return rate * periods_per_year

def find_opportunities(df):
    """
    Find arbitrage opportunities in a dataframe of live rates.
    Expects df with columns: Symbol, Binance, Bybit, OKX, dYdX
    Returns a dataframe of identified spreads > threshold.
    """
    opportunities = []
    
    for _, row in df.iterrows():
        symbol = row["Symbol"]
        # Convert all to APR for fair comparison
        rates_apr = {}
        for ex in EXCHANGES:
            r = row.get(ex)
            if r is not None and not pd.isna(r):
                rates_apr[ex] = annualize_rate(r, ex)
        
        if len(rates_apr) < 2:
            continue
            
        # Find max and min
        max_ex = max(rates_apr, key=rates_apr.get) # type: ignore
        min_ex = min(rates_apr, key=rates_apr.get) # type: ignore
        
        max_rate = rates_apr[max_ex]
        min_rate = rates_apr[min_ex]
        
        # Spread
        spread = max_rate - min_rate
        
        if spread >= MIN_APR_THRESHOLD:
            opportunities.append({
                "Symbol": symbol,
                "Long Exchange": min_ex,  # We long perps where funding is lower/negative
                "Short Exchange": max_ex,  # We short perps where funding is higher/positive
                "Long APR": min_rate,
                "Short APR": max_rate,
                "Spread APR": spread
            })
            
    df_opps = pd.DataFrame(opportunities)
    if not df_opps.empty:
        df_opps = df_opps.sort_values(by="Spread APR", ascending=False)
    return df_opps

def calculate_historical_spreads(df_history):
    """
    Calculate max spreads at each timestamp from historical data.
    Input df_history is indexed by timestamp, columns are exchanges.
    """
    # Create an APR dataframe
    df_apr = pd.DataFrame(index=df_history.index)
    for ex in EXCHANGES:
        if ex in df_history.columns:
            df_apr[ex] = df_history[ex].apply(lambda r: annualize_rate(r, ex))
            
    # Calculate max and min across rows
    available_exchanges = [ex for ex in EXCHANGES if ex in df_apr.columns]
    if not available_exchanges:
        df_apr["Max_APR"] = np.nan
        df_apr["Min_APR"] = np.nan
        df_apr["Spread"] = np.nan
        return df_apr
        
    df_apr["Max_APR"] = df_apr[available_exchanges].max(axis=1)
    df_apr["Min_APR"] = df_apr[available_exchanges].min(axis=1)
    df_apr["Spread"] = df_apr["Max_APR"] - df_apr["Min_APR"]
    
    return df_apr
