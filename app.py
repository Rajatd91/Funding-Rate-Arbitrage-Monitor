import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import EXCHANGES, DEFAULT_SYMBOLS, MIN_APR_THRESHOLD, APP_TITLE
from data_fetcher import get_live_funding_rates, get_historical_rates
from arbitrage_engine import find_opportunities, annualize_rate, calculate_historical_spreads
from backtester import run_backtest, calculate_metrics

st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="💹")

st.title(f"💹 {APP_TITLE}")

# Sidebar
st.sidebar.header("Strategy & Fee Configuration")
st.sidebar.markdown("Configure the conditions for the arbitrage strategy.")
active_symbols = st.sidebar.multiselect("Active Symbols", DEFAULT_SYMBOLS, default=DEFAULT_SYMBOLS)
entry_threshold = st.sidebar.slider("Entry APR (%): Min spread to open position", 1.0, 50.0, MIN_APR_THRESHOLD * 100, 1.0) / 100
exit_threshold = st.sidebar.slider("Exit APR (%): Spread to close position", 0.0, 20.0, 2.0, 0.5) / 100
trading_fee = st.sidebar.slider("Trading Fee & Slippage per leg (%)", 0.0, 0.5, 0.1, 0.01) / 100

tab1, tab2 = st.tabs(["Live Scanner", "Backtester"])

with tab1:
    st.header("Live Funding Rate Monitor")
    st.write("Fetching real-time data from Exchange APIs...")
    
    if st.button("Refresh Live Data"):
        st.cache_data.clear()
        
    @st.cache_data(ttl=60)
    def load_live_data(symbols):
        df_live = get_live_funding_rates(symbols)
        # Convert raw rates to APR for display
        df_apr = df_live.copy()
        for ex in EXCHANGES:
            df_apr[ex] = df_apr[ex].apply(lambda r: annualize_rate(r, ex))
        return df_live, df_apr

    df_live, df_apr = load_live_data(active_symbols)
    
    # Heatmap Visualization
    st.subheader("Funding Rate Heatmap (APR)")
    if not df_apr.empty:
        # Melt dataframe for Plotly format
        df_melted = df_apr.melt(id_vars=["Symbol"], value_vars=EXCHANGES, var_name="Exchange", value_name="APR")
        fig = px.density_heatmap(
            df_melted, x="Exchange", y="Symbol", z="APR", 
            text_auto=".2%", color_continuous_scale="RdYlGn",
            title="Cross-Exchange Annualized Funding Rates"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Active Arbitrage Opportunities")
        df_opps = find_opportunities(df_live)
        if not df_opps.empty:
            # Filter based on slider
            df_opps = df_opps[df_opps["Spread APR"] >= entry_threshold]
            st.dataframe(df_opps.style.format({"Long APR": "{:.2%}", "Short APR": "{:.2%}", "Spread APR": "{:.2%}"}))
        else:
            st.success("No current opportunities exceed the threshold.")

with tab2:
    st.header("Historical Backtesting")
    st.write("Note: Historical data fetching can take some time due to API rate limits.")
    
    selected_sym = st.selectbox("Select Symbol for Backtest", active_symbols)
    
    if st.button("Run Backtest"):
        with st.spinner("Fetching historical data... This may take a minute."):
            df_hist = get_historical_rates(selected_sym)
            
            if not df_hist.empty:
                df_spreads = calculate_historical_spreads(df_hist)
                df_bt = run_backtest(df_spreads, entry_threshold=entry_threshold, exit_threshold=exit_threshold, trading_fee=trading_fee)
                
                metrics = calculate_metrics(df_bt)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Return", f"{metrics['Total Return']:.2%}")
                col2.metric("Max Drawdown", f"{metrics['Max Drawdown']:.2%}")
                col3.metric("Trade Periods Executed", metrics['Trade Periods Executed'])
                
                # Equity Curve
                st.subheader("Strategy Equity Curve")
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=df_bt.index, y=df_bt['Cumulative_Return'], mode='lines', name='Cumulative Return'))
                fig_eq.update_layout(yaxis_tickformat='.2%', title=f"Backtest Equity Curve for {selected_sym}")
                st.plotly_chart(fig_eq, use_container_width=True)
                
                # Spread History
                st.subheader("Spread History")
                fig_sp = go.Figure()
                fig_sp.add_trace(go.Scatter(x=df_bt.index, y=df_bt['Spread'], mode='lines', name='Spread APR'))
                fig_sp.add_hline(y=entry_threshold, line_dash="dash", line_color="green", annotation_text="Entry Threshold")
                fig_sp.add_hline(y=exit_threshold, line_dash="dash", line_color="red", annotation_text="Exit Threshold")
                fig_sp.update_layout(yaxis_tickformat='.2%', title=f"Historical Max Spread for {selected_sym}")
                st.plotly_chart(fig_sp, use_container_width=True)
            else:
                st.error("Could not fetch sufficient historical data.")
