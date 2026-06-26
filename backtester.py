
# backtester.py — Strategy backtester with equity curve
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date

TA_AVAILABLE = False

NSE_TICKERS = {
    "Nifty 50":"^NSEI","Nifty Midcap":"^NSMIDCP",
    "HDFC Bank":"HDFCBANK.NS","ICICI Bank":"ICICIBANK.NS",
    "TCS":"TCS.NS","Infosys":"INFY.NS","Reliance":"RELIANCE.NS",
    "HUL":"HINDUNILVR.NS","Maruti":"MARUTI.NS","ITC":"ITC.NS",
    "Sun Pharma":"SUNPHARMA.NS","Bajaj Finance":"BAJFINANCE.NS",
    "L&T":"LT.NS","Axis Bank":"AXISBANK.NS","Wipro":"WIPRO.NS",
    "Tata Motors":"TATAMOTORS.NS","NTPC":"NTPC.NS",
    "Tata Steel":"TATASTEEL.NS","JSW Steel":"JSWSTEEL.NS",
    "Zomato":"ZOMATO.NS","Dr. Reddys":"DRREDDY.NS",
}

@st.cache_data(ttl=86400)
def fetch_data(ticker, start, end):
    try:
        raw = yf.download(ticker, start=start, end=end,
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        return raw.dropna() if not raw.empty else None
    except Exception:
        return None

def run_backtest(df, strategy, params, initial_capital=100000):
    """
    Core backtesting engine.
    Returns: trades_df, equity_curve, metrics
    """
    close  = df["Close"].values
    high   = df["High"].values
    low    = df["Low"].values
    dates  = df.index

    # Generate signals based on strategy
    signals = np.zeros(len(close))

    if strategy == "MA Crossover":
        fast = int(params.get("fast_ma", 20))
        slow = int(params.get("slow_ma", 50))
        df2  = df.copy()
        if TA_AVAILABLE:
            fast_ma = ta.sma(df2["Close"], fast).values
            slow_ma = ta.sma(df2["Close"], slow).values
        else:
            fast_ma = df2["Close"].rolling(fast).mean().values
            slow_ma = df2["Close"].rolling(slow).mean().values

        for i in range(1, len(close)):
            if (fast_ma[i] > slow_ma[i] and
                    fast_ma[i-1] <= slow_ma[i-1]):
                signals[i] = 1   # Buy
            elif (fast_ma[i] < slow_ma[i] and
                      fast_ma[i-1] >= slow_ma[i-1]):
                signals[i] = -1  # Sell

    elif strategy == "RSI Mean Reversion":
        oversold  = params.get("oversold",  30)
        overbought= params.get("overbought", 70)
        if TA_AVAILABLE:
            rsi = ta.rsi(df["Close"], 14).values
        else:
            delta = df["Close"].diff()
            gain  = (delta.where(delta>0,0)).rolling(14).mean()
            loss  = (-delta.where(delta<0,0)).rolling(14).mean()
            rs    = gain/loss
            rsi   = (100 - 100/(1+rs)).values

        for i in range(1, len(close)):
            if rsi[i] < oversold  and rsi[i-1] >= oversold:
                signals[i] = 1
            elif rsi[i] > overbought and rsi[i-1] <= overbought:
                signals[i] = -1

    elif strategy == "Momentum":
        lookback = int(params.get("lookback", 20))
        threshold= params.get("threshold", 0.02)
        for i in range(lookback, len(close)):
            momentum = (close[i] - close[i-lookback]) / close[i-lookback]
            if momentum > threshold:
                signals[i] = 1
            elif momentum < -threshold:
                signals[i] = -1

    elif strategy == "Bollinger Band Breakout":
        period = int(params.get("period", 20))
        std_dev = params.get("std_dev", 2.0)
        if TA_AVAILABLE:
            bb = ta.bbands(df["Close"], period, std_dev)
            if bb is not None:
                upper = bb.iloc[:,0].values
                lower = bb.iloc[:,2].values
            else:
                sma   = df["Close"].rolling(period).mean()
                std   = df["Close"].rolling(period).std()
                upper = (sma + std_dev*std).values
                lower = (sma - std_dev*std).values
        else:
            sma   = df["Close"].rolling(period).mean()
            std   = df["Close"].rolling(period).std()
            upper = (sma + std_dev*std).values
            lower = (sma - std_dev*std).values

        for i in range(1, len(close)):
            if close[i] < lower[i] and close[i-1] >= lower[i-1]:
                signals[i] = 1
            elif close[i] > upper[i] and close[i-1] <= upper[i-1]:
                signals[i] = -1

    elif strategy == "MACD Signal":
        if TA_AVAILABLE:
            macd_df = ta.macd(df["Close"])
            if macd_df is not None:
                macd_line   = macd_df.iloc[:,0].values
                signal_line = macd_df.iloc[:,1].values
            else:
                macd_line = signal_line = np.zeros(len(close))
        else:
            ema12 = df["Close"].ewm(span=12).mean().values
            ema26 = df["Close"].ewm(span=26).mean().values
            macd_line = ema12 - ema26
            signal_line = pd.Series(macd_line).ewm(span=9).mean().values

        for i in range(1, len(close)):
            if (macd_line[i] > signal_line[i] and
                    macd_line[i-1] <= signal_line[i-1]):
                signals[i] = 1
            elif (macd_line[i] < signal_line[i] and
                      macd_line[i-1] >= signal_line[i-1]):
                signals[i] = -1

    # ── Simulate trades ────────────────────────────────────────────────────────
    capital    = float(initial_capital)
    position   = 0
    entry_price= 0
    entry_date = None
    trades     = []
    equity     = [capital]
    stop_loss  = params.get("stop_loss", 0.05)
    take_profit= params.get("take_profit", 0.10)

    for i in range(1, len(close)):
        price = close[i]

        # Check stop loss / take profit
        if position == 1 and entry_price > 0:
            pnl_pct = (price - entry_price) / entry_price
            if pnl_pct <= -stop_loss:
                signals[i] = -1   # Force exit
            elif pnl_pct >= take_profit:
                signals[i] = -1   # Force exit

        # Execute signals
        if signals[i] == 1 and position == 0:
            shares      = int(capital / price)
            position    = shares
            entry_price = price
            entry_date  = dates[i]
            capital    -= shares * price

        elif signals[i] == -1 and position > 0:
            exit_value = position * price
            pnl        = exit_value - position * entry_price
            pnl_pct    = pnl / (position * entry_price) * 100
            capital   += exit_value
            trades.append({
                "Entry Date":  entry_date.strftime("%Y-%m-%d"),
                "Exit Date":   dates[i].strftime("%Y-%m-%d"),
                "Entry Price": round(entry_price, 2),
                "Exit Price":  round(price, 2),
                "Shares":      position,
                "P&L (Rs.)":   round(pnl, 2),
                "P&L (%)":     round(pnl_pct, 2),
                "Result":      "Win" if pnl > 0 else "Loss",
            })
            position    = 0
            entry_price = 0

        # Mark-to-market equity
        mtm = capital + position * price
        equity.append(mtm)

    # Close any open position at end
    if position > 0:
        final_val = capital + position * close[-1]
        equity[-1] = final_val

    equity_series = pd.Series(equity, index=range(len(equity)))
    trades_df     = pd.DataFrame(trades)

    # ── Compute metrics ────────────────────────────────────────────────────────
    final_equity  = equity[-1]
    total_return  = (final_equity - initial_capital) / initial_capital * 100
    n_years       = len(close) / 252
    cagr          = ((final_equity/initial_capital)**(1/n_years)-1)*100 if n_years>0 else 0

    daily_ret     = pd.Series(equity).pct_change().dropna()
    sharpe        = (daily_ret.mean()*252 - 0.065) / (daily_ret.std()*np.sqrt(252))                     if daily_ret.std()>0 else 0

    # Drawdown
    eq_arr  = np.array(equity)
    peak    = np.maximum.accumulate(eq_arr)
    dd      = (eq_arr - peak) / peak * 100
    max_dd  = dd.min()

    # Buy and hold
    bh_return = (close[-1] - close[0]) / close[0] * 100
    bh_cagr   = ((close[-1]/close[0])**(1/n_years)-1)*100 if n_years>0 else 0

    # Trade stats
    if len(trades_df) > 0:
        wins     = (trades_df["P&L (Rs.)"] > 0).sum()
        losses   = (trades_df["P&L (Rs.)"] <= 0).sum()
        win_rate = wins / len(trades_df) * 100
        avg_win  = trades_df[trades_df["P&L (Rs.)"]>0]["P&L (Rs.)"].mean()                    if wins > 0 else 0
        avg_loss = trades_df[trades_df["P&L (Rs.)"]<=0]["P&L (Rs.)"].mean()                    if losses > 0 else 0
        profit_factor = abs(avg_win/avg_loss) if avg_loss != 0 else 999
    else:
        wins=losses=win_rate=avg_win=avg_loss=profit_factor = 0

    metrics = {
        "Total Return (%)":    round(total_return, 2),
        "CAGR (%)":            round(cagr, 2),
        "Sharpe Ratio":        round(sharpe, 3),
        "Max Drawdown (%)":    round(max_dd, 2),
        "Total Trades":        len(trades_df),
        "Win Rate (%)":        round(win_rate, 1),
        "Profit Factor":       round(profit_factor, 2),
        "Avg Win (Rs.)":       round(avg_win, 2),
        "Avg Loss (Rs.)":      round(avg_loss, 2),
        "B&H Return (%)":      round(bh_return, 2),
        "B&H CAGR (%)":        round(bh_cagr, 2),
        "Alpha vs B&H (%)":    round(cagr - bh_cagr, 2),
    }

    return trades_df, equity, dd, metrics, signals, close, dates

def render_backtester_tab():
    st.markdown("#### Strategy Backtester")
    st.caption(
        "Test rule-based trading strategies on historical NSE/BSE data. "
        "Includes equity curve, drawdown analysis, trade-by-trade breakdown, "
        "and comparison vs buy-and-hold benchmark."
    )

    # ── Strategy config ───────────────────────────────────────────────────────
    cfg1, cfg2, cfg3 = st.columns(3)

    with cfg1:
        selected_name = st.selectbox("Stock / Index",
                                      list(NSE_TICKERS.keys()),
                                      key="bt_stock")
        ticker = NSE_TICKERS[selected_name]

        start_date = st.date_input("From", value=date(2020,1,1), key="bt_start")
        end_date   = st.date_input("To",   value=date.today(),   key="bt_end")

    with cfg2:
        strategy = st.selectbox("Strategy", [
            "MA Crossover",
            "RSI Mean Reversion",
            "Momentum",
            "Bollinger Band Breakout",
            "MACD Signal",
        ], key="bt_strategy")

        capital = st.number_input("Starting Capital (Rs.)",
                                   10000, 10000000, 100000,
                                   step=10000, key="bt_capital")

    with cfg3:
        st.markdown("**Strategy Parameters**")

        params = {}
        if strategy == "MA Crossover":
            params["fast_ma"]  = st.slider("Fast MA period", 5,  50,  20, key="bt_fast")
            params["slow_ma"]  = st.slider("Slow MA period", 20, 200, 50, key="bt_slow")

        elif strategy == "RSI Mean Reversion":
            params["oversold"]   = st.slider("Oversold level",   10, 40, 30, key="bt_os")
            params["overbought"] = st.slider("Overbought level", 60, 90, 70, key="bt_ob")

        elif strategy == "Momentum":
            params["lookback"]  = st.slider("Lookback period", 5, 60, 20, key="bt_lb")
            params["threshold"] = st.slider("Threshold (%)", 1, 10, 2, key="bt_th") / 100

        elif strategy == "Bollinger Band Breakout":
            params["period"]  = st.slider("BB period",   10, 50, 20, key="bt_bbp")
            params["std_dev"] = st.slider("Std dev",      1,  3,  2, key="bt_bbs",
                                           step=1)

        elif strategy == "MACD Signal":
            st.caption("Uses standard MACD (12,26,9)")

        params["stop_loss"]   = st.slider("Stop Loss (%)",   1, 20, 5,  key="bt_sl") / 100
        params["take_profit"] = st.slider("Take Profit (%)", 1, 50, 10, key="bt_tp") / 100

    # ── Run backtest ──────────────────────────────────────────────────────────
    if st.button("▶ Run Backtest", type="primary", key="bt_run"):
        with st.spinner("Running backtest..."):
            df = fetch_data(ticker,
                            start_date.strftime("%Y-%m-%d"),
                            end_date.strftime("%Y-%m-%d"))

        if df is None or len(df) < 50:
            st.error("Not enough data. Try a longer date range.")
            return

        trades_df, equity, dd, metrics, signals, close, dates = run_backtest(
            df, strategy, params, capital)

        # ── Metrics dashboard ─────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**Backtest Results**")

        m1,m2,m3,m4,m5,m6 = st.columns(6)
        m1.metric("Total Return",   f"{metrics['Total Return (%)']:+.1f}%",
                  delta=f"{metrics['Alpha vs B&H (%)']:+.1f}% vs B&H")
        m2.metric("CAGR",           f"{metrics['CAGR (%)']:.1f}%")
        m3.metric("Sharpe Ratio",   f"{metrics['Sharpe Ratio']:.3f}")
        m4.metric("Max Drawdown",   f"{metrics['Max Drawdown (%)']:.1f}%")
        m5.metric("Win Rate",       f"{metrics['Win Rate (%)']:.1f}%")
        m6.metric("Total Trades",   f"{metrics['Total Trades']}")

        m7,m8,m9,m10,m11,m12 = st.columns(6)
        m7.metric("Profit Factor",  f"{metrics['Profit Factor']:.2f}")
        m8.metric("Avg Win",        f"Rs.{metrics['Avg Win (Rs.)']:,.0f}")
        m9.metric("Avg Loss",       f"Rs.{metrics['Avg Loss (Rs.)']:,.0f}")
        m10.metric("B&H Return",    f"{metrics['B&H Return (%)']:+.1f}%")
        m11.metric("B&H CAGR",      f"{metrics['B&H CAGR (%)']:.1f}%")
        m12.metric("Alpha vs B&H",  f"{metrics['Alpha vs B&H (%)']:+.1f}%",
                   delta="Outperform" if metrics['Alpha vs B&H (%)']>0 else "Underperform")

        # ── Equity curve ──────────────────────────────────────────────────────
        st.markdown("**Equity Curve vs Buy & Hold**")

        bh_equity = [capital * (p/close[0]) for p in close]

        fig_eq = go.Figure()
        fig_eq.add_trace(go.Scatter(
            x=list(range(len(equity))),
            y=equity,
            mode="lines", name=f"{strategy}",
            line=dict(color="#3fb950", width=2),
        ))
        fig_eq.add_trace(go.Scatter(
            x=list(range(len(bh_equity))),
            y=bh_equity,
            mode="lines", name="Buy & Hold",
            line=dict(color="#58a6ff", width=1.5, dash="dash"),
        ))
        fig_eq.add_hline(y=capital, line_color="#6e7681",
                         line_dash="dot", line_width=1,
                         annotation_text="Initial capital")
        fig_eq.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            font_color="#8b949e", height=350,
            margin=dict(t=20,b=40,l=60,r=20),
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
            yaxis_title="Portfolio Value (Rs.)",
            xaxis_title="Trading Days",
            hovermode="x unified",
        )
        fig_eq.update_xaxes(showgrid=True, gridcolor="#21262d")
        fig_eq.update_yaxes(showgrid=True, gridcolor="#21262d")
        st.plotly_chart(fig_eq, use_container_width=True)

        # ── Drawdown chart ────────────────────────────────────────────────────
        st.markdown("**Drawdown Chart**")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=list(range(len(dd))), y=dd,
            fill="tozeroy", fillcolor="rgba(248,81,73,0.15)",
            line=dict(color="#f85149", width=1),
            name="Drawdown",
        ))
        fig_dd.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            font_color="#8b949e", height=220,
            margin=dict(t=10,b=30,l=60,r=20),
            yaxis_title="Drawdown (%)",
            xaxis_title="Trading Days",
        )
        fig_dd.update_xaxes(showgrid=True, gridcolor="#21262d")
        fig_dd.update_yaxes(showgrid=True, gridcolor="#21262d")
        st.plotly_chart(fig_dd, use_container_width=True)

        # ── Trade list ────────────────────────────────────────────────────────
        if len(trades_df) > 0:
            st.markdown(f"**Trade Log — {len(trades_df)} trades**")
            st.dataframe(trades_df, hide_index=True,
                         use_container_width=True)

            # P&L distribution
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(
                x=trades_df["P&L (Rs.)"],
                nbinsx=20,
                marker_color=[
                    "#3fb950" if v>0 else "#f85149"
                    for v in trades_df["P&L (Rs.)"]
                ],
                name="Trade P&L",
            ))
            fig_dist.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font_color="#8b949e", height=250,
                margin=dict(t=20,b=30,l=60,r=20),
                title="P&L Distribution",
                title_font_color="#8b949e",
                xaxis_title="P&L per Trade (Rs.)",
                yaxis_title="Frequency",
            )
            fig_dist.update_xaxes(showgrid=True, gridcolor="#21262d")
            fig_dist.update_yaxes(showgrid=True, gridcolor="#21262d")
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.warning("No trades generated. Try adjusting strategy parameters.")

    else:
        st.info(
            "Configure your strategy above and click "
            "**▶ Run Backtest** to start."
        )
