
# walkforward.py — Walk-forward optimisation
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date
from itertools import product

TA_AVAILABLE = False

NSE_TICKERS = {
    "Nifty 50":"^NSEI","Nifty Midcap":"^NSMIDCP",
    "HDFC Bank":"HDFCBANK.NS","ICICI Bank":"ICICIBANK.NS",
    "TCS":"TCS.NS","Reliance":"RELIANCE.NS","Infosys":"INFY.NS",
}

@st.cache_data(ttl=86400)
def fetch_wf_data(ticker, start, end):
    try:
        raw = yf.download(ticker, start=start, end=end,
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        return raw.dropna() if not raw.empty else None
    except Exception:
        return None

def simple_ma_backtest(close_arr, fast, slow, stop=0.05, tp=0.10):
    """Lightweight MA crossover for optimisation."""
    n = len(close_arr)
    if fast >= slow or slow >= n:
        return -999

    close_s = pd.Series(close_arr)
    fast_ma = close_s.rolling(fast).mean().values
    slow_ma = close_s.rolling(slow).mean().values

    capital = 100000.0
    position = 0; entry = 0
    equity = [capital]

    for i in range(1, n):
        p = close_arr[i]
        if position > 0:
            pct = (p - entry) / entry
            if pct <= -stop or pct >= tp:
                capital  += position * p
                position  = 0

        if (fast_ma[i] > slow_ma[i] and
                fast_ma[i-1] <= slow_ma[i-1] and position == 0):
            shares   = int(capital / p)
            position = shares
            entry    = p
            capital -= shares * p

        elif (fast_ma[i] < slow_ma[i] and
                  fast_ma[i-1] >= slow_ma[i-1] and position > 0):
            capital  += position * p
            position  = 0

        equity.append(capital + position * p)

    final = equity[-1]
    ret   = (final - 100000) / 100000

    # Sharpe
    eq_s  = pd.Series(equity)
    dr    = eq_s.pct_change().dropna()
    sharpe = (dr.mean()*252 - 0.065)/(dr.std()*np.sqrt(252)) if dr.std()>0 else 0

    return sharpe

def render_walkforward_tab():
    st.markdown("#### Walk-Forward Optimisation")
    st.info(
        "Walk-forward optimisation splits historical data into rolling "
        "in-sample (training) and out-of-sample (testing) windows. "
        "Parameters are optimised on training data and validated on unseen "
        "test data — the only reliable way to avoid curve-fitting."
    )

    st.markdown("""
    <div style="background:#161b22; border:1px solid #21262d; border-radius:8px;
                padding:14px 16px; margin-bottom:16px; font-size:12px;
                color:#8b949e; line-height:1.8;">
    <b style="color:#f0f6fc;">How Walk-Forward Works:</b><br>
    1. Take full historical data (e.g. 3 years)<br>
    2. Split into windows: e.g. 6-month train + 2-month test<br>
    3. Optimise MA parameters on the 6-month train window<br>
    4. Apply best parameters to the 2-month test window — record result<br>
    5. Roll forward by 2 months and repeat<br>
    6. Final result = concatenation of all out-of-sample test periods<br>
    <b style="color:#3fb950;">If OOS performance is close to IS performance — strategy is robust.</b>
    </div>
    """, unsafe_allow_html=True)

    # ── Config ────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    selected   = c1.selectbox("Stock / Index",
                               list(NSE_TICKERS.keys()), key="wf_stock")
    ticker     = NSE_TICKERS[selected]
    start_date = c2.date_input("From", value=date(2019,1,1), key="wf_start")
    end_date   = c3.date_input("To",   value=date.today(),   key="wf_end")

    w1, w2, w3 = st.columns(3)
    train_months = w1.slider("Training window (months)", 3, 18, 6, key="wf_train")
    test_months  = w2.slider("Test window (months)",     1,  6, 2, key="wf_test")
    n_windows    = w3.number_input("Max windows to run", 3, 20, 8, key="wf_nwin")

    st.markdown("**Parameter Search Space**")
    ps1, ps2 = st.columns(2)
    fast_range = ps1.multiselect("Fast MA options",
                                  [5,10,15,20,25,30],
                                  default=[5,10,15,20], key="wf_fast")
    slow_range = ps2.multiselect("Slow MA options",
                                  [20,30,40,50,60,80,100],
                                  default=[30,50,80], key="wf_slow")

    if st.button("▶ Run Walk-Forward Optimisation",
                 type="primary", key="wf_run"):
        if not fast_range or not slow_range:
            st.error("Select at least 1 option for each MA range.")
            return

        with st.spinner("Loading data..."):
            df = fetch_wf_data(ticker,
                               start_date.strftime("%Y-%m-%d"),
                               end_date.strftime("%Y-%m-%d"))

        if df is None or len(df) < 100:
            st.error("Not enough data.")
            return

        close    = df["Close"].values
        n_bars   = len(close)
        bars_per_month = 21

        train_bars = train_months * bars_per_month
        test_bars  = test_months  * bars_per_month

        if train_bars + test_bars > n_bars:
            st.error("Not enough data for these window sizes.")
            return

        # ── Walk-forward loop ─────────────────────────────────────────────────
        wf_results   = []
        is_sharpes   = []
        oos_sharpes  = []
        best_params_list = []

        progress = st.progress(0)
        status   = st.empty()
        max_starts = min(int(n_windows),
                         (n_bars - train_bars - test_bars) // test_bars + 1)

        for w_idx in range(max_starts):
            start_idx = w_idx * test_bars
            train_end = start_idx + train_bars
            test_end  = train_end + test_bars

            if test_end > n_bars:
                break

            status.text(f"Optimising window {w_idx+1}/{max_starts}...")
            progress.progress((w_idx+1)/max_starts)

            # In-sample optimisation
            train_close = close[start_idx:train_end]
            best_sharpe = -999
            best_f = fast_range[0]; best_s = slow_range[0]

            for f, s in product(fast_range, slow_range):
                if f >= s:
                    continue
                sharpe = simple_ma_backtest(train_close, f, s)
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_f = f; best_s = s

            # Out-of-sample validation
            test_close  = close[train_end:test_end]
            oos_sharpe  = simple_ma_backtest(test_close, best_f, best_s)

            is_sharpes.append(best_sharpe)
            oos_sharpes.append(oos_sharpe)
            best_params_list.append((best_f, best_s))

            wf_results.append({
                "Window":      w_idx+1,
                "IS Period":   f"{df.index[start_idx].date()} → {df.index[train_end-1].date()}",
                "OOS Period":  f"{df.index[train_end].date()} → {df.index[test_end-1].date()}",
                "Best Fast MA":best_f,
                "Best Slow MA":best_s,
                "IS Sharpe":   round(best_sharpe,3),
                "OOS Sharpe":  round(oos_sharpe,3),
                "IS→OOS Decay":f"{((oos_sharpe-best_sharpe)/abs(best_sharpe)*100):.1f}%"                                if best_sharpe!=0 else "N/A",
            })

        progress.empty(); status.empty()

        if not wf_results:
            st.error("No windows completed. Try shorter window sizes.")
            return

        results_df = pd.DataFrame(wf_results)

        # ── Summary metrics ───────────────────────────────────────────────────
        avg_is  = np.mean(is_sharpes)
        avg_oos = np.mean(oos_sharpes)
        robust  = avg_oos / avg_is if avg_is != 0 else 0
        consistency = sum(1 for o in oos_sharpes if o > 0) / len(oos_sharpes) * 100

        r1,r2,r3,r4 = st.columns(4)
        r1.metric("Avg IS Sharpe",   f"{avg_is:.3f}")
        r2.metric("Avg OOS Sharpe",  f"{avg_oos:.3f}",
                  delta=f"{avg_oos-avg_is:+.3f} vs IS")
        r3.metric("Robustness Ratio",f"{robust:.2f}",
                  delta="Good" if robust>0.5 else "Weak")
        r4.metric("OOS Win Rate",    f"{consistency:.0f}%",
                  delta="Robust" if consistency>=60 else "Curve-fitted")

        # ── IS vs OOS chart ───────────────────────────────────────────────────
        windows = [r["Window"] for r in wf_results]

        fig_wf = go.Figure()
        fig_wf.add_trace(go.Bar(
            x=windows, y=is_sharpes,
            name="In-Sample Sharpe", marker_color="#58a6ff", opacity=0.7,
        ))
        fig_wf.add_trace(go.Bar(
            x=windows, y=oos_sharpes,
            name="Out-of-Sample Sharpe",
            marker_color=[
                "#3fb950" if v > 0 else "#f85149"
                for v in oos_sharpes
            ],
            opacity=0.85,
        ))
        fig_wf.add_hline(y=0, line_color="#6e7681", line_width=1)
        fig_wf.add_hline(y=avg_oos, line_color="#ffa657",
                         line_dash="dash", line_width=1.2,
                         annotation_text=f"Avg OOS: {avg_oos:.2f}")
        fig_wf.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            font_color="#8b949e", height=380, barmode="group",
            margin=dict(t=20,b=40,l=60,r=20),
            title="In-Sample vs Out-of-Sample Sharpe Ratio per Window",
            title_font_color="#8b949e",
            xaxis_title="Window Number",
            yaxis_title="Sharpe Ratio",
            legend=dict(bgcolor="rgba(0,0,0,0)", font_size=10),
        )
        fig_wf.update_xaxes(showgrid=True, gridcolor="#21262d")
        fig_wf.update_yaxes(showgrid=True, gridcolor="#21262d")
        st.plotly_chart(fig_wf, use_container_width=True)

        # ── Parameter stability heatmap ───────────────────────────────────────
        st.markdown("**Parameter Stability — Best MA Pairs Across Windows**")
        param_counts = {}
        for f, s in best_params_list:
            key = f"F{f}/S{s}"
            param_counts[key] = param_counts.get(key, 0) + 1

        sorted_params = sorted(param_counts.items(),
                               key=lambda x: x[1], reverse=True)
        p_labels = [p[0] for p in sorted_params]
        p_counts = [p[1] for p in sorted_params]

        fig_param = go.Figure(go.Bar(
            x=p_labels, y=p_counts,
            marker_color="#d2a8ff", opacity=0.85,
        ))
        fig_param.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
            font_color="#8b949e", height=280,
            margin=dict(t=20,b=40,l=60,r=20),
            title="Parameter frequency — most selected = most stable",
            title_font_color="#8b949e",
            xaxis_title="MA Parameter Pair",
            yaxis_title="Times selected as best",
        )
        fig_param.update_xaxes(showgrid=True, gridcolor="#21262d")
        fig_param.update_yaxes(showgrid=True, gridcolor="#21262d")
        st.plotly_chart(fig_param, use_container_width=True)

        # ── Interpretation ────────────────────────────────────────────────────
        if robust > 0.6 and consistency >= 60:
            st.success(
                f"Strategy appears ROBUST. OOS Sharpe averages {avg_oos:.2f} "
                f"({consistency:.0f}% of windows positive). "
                f"Robustness ratio {robust:.2f} > 0.6 — strategy generalises well."
            )
        elif robust > 0.3:
            st.warning(
                f"Strategy shows MODERATE robustness. "
                f"OOS Sharpe {avg_oos:.2f}, robustness ratio {robust:.2f}. "
                f"Consider testing more parameter combinations."
            )
        else:
            st.error(
                f"Strategy appears CURVE-FITTED. "
                f"IS Sharpe {avg_is:.2f} degrades to OOS {avg_oos:.2f}. "
                f"This strategy is over-optimised — it works on past data but "
                f"unlikely to work in live trading."
            )

        # ── Detailed results table ─────────────────────────────────────────────
        st.markdown("**Detailed Window Results**")
        st.dataframe(results_df, hide_index=True, use_container_width=True)
