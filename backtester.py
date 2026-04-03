import pandas as pd
import numpy as np

def run_backtest(df_apr, entry_threshold=0.15, exit_threshold=0.05, trading_fee=0.001):
    """
    Simulate a basic funding rate carry strategy.
    
    df_apr: DataFrame carrying "Spread" and underlying exchange APRs. Indexed by datetime.
    entry_threshold: APR at which to enter spread position.
    exit_threshold: APR at which to exit spread position.
    trading_fee: 0.1% fee * 2 legs = 0.2% cost to enter, 0.2% cost to exit.
    
    Returns:
       DataFrame with backtest results including Equity Curve.
    """
    if "Spread" not in df_apr.columns:
        raise ValueError("DataFrame must contain 'Spread' column")
        
    df = df_apr.copy()
    
    # Pre-compute time delta in years for accurate return calculation per step
    # We use difference between consecutive times to know how long a rate was held.
    # Default to 1 hour if first row or missing
    df['TimeDelta_Hours'] = df.index.to_series().diff().dt.total_seconds().fillna(3600) / 3600
    df['TimeDelta_Years'] = df['TimeDelta_Hours'] / (24 * 365)
    
    position = 0 # 1 if in trade, 0 otherwise
    returns = []
    
    for _, row in df.iterrows():
        spread = row["Spread"]
        dt_years = row["TimeDelta_Years"]
        
        step_return = 0
        
        if position == 0:
            if spread >= entry_threshold:
                # Enter position
                position = 1
                # Pay trading fee for 2 legs (Long and Short)
                step_return -= (trading_fee * 2)
        else:
            if spread <= exit_threshold:
                # Exit position
                position = 0
                step_return -= (trading_fee * 2)
            else:
                # Accrue funding spread
                # The spread is already annualized. So return for this timestep is spread * dt_years
                # Capital required is 2 (e.g., $1 long, $1 short). 
                # So relative to total capital, return is (spread * dt_years) / 2
                step_return += (spread * dt_years) / 2
                
        returns.append(step_return)
        
    df['Strategy_Return'] = returns
    df['Cumulative_Return'] = (1 + df['Strategy_Return']).cumprod() - 1
    
    return df

def calculate_metrics(df_backtest):
    """Calculate basic performance metrics from the backtest."""
    cum_ret = df_backtest['Cumulative_Return'].iloc[-1] if not df_backtest.empty else 0
    max_dd = 0
    
    if not df_backtest.empty:
        rolling_max = (1 + df_backtest['Cumulative_Return']).cummax()
        drawdowns = (1 + df_backtest['Cumulative_Return']) / rolling_max - 1
        max_dd = drawdowns.min()
        
    return {
        "Total Return": cum_ret,
        "Max Drawdown": max_dd,
        "Trade Periods Executed": (df_backtest['Strategy_Return'] > 0).sum()
    }
