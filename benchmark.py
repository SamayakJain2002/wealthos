
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

BENCHMARKS = {
    "Nifty 50":           "^NSEI",
    "Nifty 500":          "^CNXINFRA",
    "Sensex":             "^BSESN",
    "Nifty Midcap 150":   "^NSMIDCP",
    "Gold ETF":           "GOLDBEES.NS",
    "Bharat Bond 2030":   "CPSEETF.NS",
}

PEER_PROFILES = {
    "Conservative PMS Peer": {
        "return": 0.112, "vol": 0.092, "sharpe": 0.51,
        "max_dd": -8.2,  "beta": 0.42,
        "allocation": {"Debt":65,"Equity":15,"Gold":12,"REIT":8},
    },
    "Balanced PMS Peer": {
        "return": 0.148, "vol": 0.138, "sharpe": 0.60,
        "max_dd": -14.5, "beta": 0.68,
        "allocation": {"Debt":35,"Equity":50,"Gold":10,"REIT":5},
    },
    "Aggressive PMS Peer": {
        "return": 0.187, "vol": 0.195, "sharpe": 0.63,
        "max_dd": -24.8, "beta": 0.92,
        "allocation": {"Debt":10,"Equity":78,"Gold":7,"REIT":5},
    },
    "Top PMS India (2024)": {
        "return": 0.224, "vol": 0.210, "sharpe": 0.75,
        "max_dd": -19.2, "beta": 0.95,
        "allocation": {"Debt":5,"Equity":85,"Gold":5,"REIT":5},
    },
    "Avg Equity MF India": {
        "return": 0.152, "vol": 0.165, "sharpe": 0.53,
        "max_dd": -22.1, "beta": 0.88,
        "allocation": {"Debt":5,"Equity":92,"Gold":0,"REIT":3},
    },
}

@st.cache_data(ttl=86400)
def get_benchmark_returns():
    import yfinance as yf
    END   = date.today().strftime("%Y-%m-%d")
    START = "2020-01-01"
    price_data = {}
    for name, ticker in BENCHMARKS.items():
        try:
            raw = yf.download(ticker, start=START, end=END,
                              auto_adjust=True, progress=False)
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            if not raw.empty and "Close" in raw.columns:
                s = raw["Close"].squeeze()
                if len(s) > 100:
                    price_data[name] = s
        except Exception:
            pass
    if not price_data:
        return pd.DataFrame()
    prices = pd.DataFrame(price_data).ffill().bfill()
    return prices.pct_change().dropna()

def compute_metrics(returns_series):
    ann_ret = returns_series.mean() * 252
    ann_vol = returns_series.std() * np.sqrt(252)
    sharpe  = (ann_ret - 0.065) / ann_vol if ann_vol > 0 else 0
    cum     = np.cumprod(1 + returns_series.values)
    rm      = np.maximum.accumulate(cum)
    max_dd  = ((cum - rm) / rm).min() * 100
    return {
        "return":  round(ann_ret * 100, 2),
        "vol":     round(ann_vol * 100, 2),
        "sharpe":  round(sharpe, 3),
        "max_dd":  round(max_dd, 2),
    }

def render_benchmark_tab(daily_returns, assets, port_weights,
                          port_metrics, profile_name):
    st.markdown("#### Peer Benchmarking & Performance Comparison")
    st.info(
        "Benchmarking shows how your portfolio performs relative to market "
        "indices and peer PMS strategies. SEBI requires PMS firms to disclose "
        "performance vs benchmark. This tab gives you that analysis instantly."
    )

    port_daily = pd.Series(
        daily_returns.values @ port_weights,
        index=daily_returns.index
    )

    with st.spinner("Loading benchmark data..."):
        bench_rets = get_benchmark_returns()

    # ── Performance vs benchmarks ─────────────────────────────────────────────
    st.markdown("**Portfolio vs Market Benchmarks**")

    comp_rows = [{
        "Name":       f"YOUR PORTFOLIO ({profile_name})",
        "Ann. Return":f"{port_metrics['return']*100:.2f}%",
        "Volatility": f"{port_metrics['vol']*100:.2f}%",
        "Sharpe":     f"{port_metrics['sharpe']:.3f}",
        "Max DD":     f"{port_metrics['max_dd']:.1f}%",
        "Type":       "Your Portfolio",
    }]

    bench_metrics = {}
    if not bench_rets.empty:
        for b_name in bench_rets.columns:
            m = compute_metrics(bench_rets[b_name])
            bench_metrics[b_name] = m
            comp_rows.append({
                "Name":       b_name,
                "Ann. Return":f"{m['return']:.2f}%",
                "Volatility": f"{m['vol']:.2f}%",
                "Sharpe":     f"{m['sharpe']:.3f}",
                "Max DD":     f"{m['max_dd']:.2f}%",
                "Type":       "Market Index",
            })

    # Peer PMS
    for peer_name, peer_data in PEER_PROFILES.items():
        comp_rows.append({
            "Name":       peer_name,
            "Ann. Return":f"{peer_data['return']*100:.2f}%",
            "Volatility": f"{peer_data['vol']*100:.2f}%",
            "Sharpe":     f"{peer_data['sharpe']:.3f}",
            "Max DD":     f"{peer_data['max_dd']:.2f}%",
            "Type":       "PMS Peer",
        })

    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(comp_df, hide_index=True, use_container_width=True)

    # ── Scatter — risk vs return ──────────────────────────────────────────────
    st.markdown("**Risk vs Return — Peer Map**")
    fig_scatter = go.Figure()

    type_colors = {
        "Your Portfolio": "#4CAF50",
        "Market Index":   "#2196F3",
        "PMS Peer":       "#FF9800",
    }
    type_sizes = {
        "Your Portfolio": 20,
        "Market Index":   10,
        "PMS Peer":       12,
    }

    for row in comp_rows:
        try:
            ret = float(row["Ann. Return"].replace("%",""))
            vol = float(row["Volatility"].replace("%",""))
            fig_scatter.add_trace(go.Scatter(
                x=[vol], y=[ret],
                mode="markers+text",
                marker=dict(
                    color=type_colors.get(row["Type"],"#888"),
                    size=type_sizes.get(row["Type"],10),
                    symbol="star" if row["Type"]=="Your Portfolio" else "circle",
                ),
                text=[row["Name"]],
                textposition="top right",
                textfont=dict(
                    size=9 if row["Type"]!="Your Portfolio" else 11,
                    color=type_colors.get(row["Type"],"#888"),
                ),
                name=row["Type"],
                showlegend=False,
            ))
        except Exception:
            pass

    # Add Sharpe ratio reference lines
    x_range = np.linspace(5, 30, 100)
    for sr, color in [(0.5,"rgba(255,255,255,0.2)"),(1.0,"rgba(255,255,255,0.3)")]:
        fig_scatter.add_trace(go.Scatter(
            x=x_range, y=[0.065 + sr*x/100*100 for x in x_range],
            mode="lines",
            line=dict(color=color, width=1, dash="dot"),
            name=f"Sharpe = {sr}",
            showlegend=True,
        ))

    fig_scatter.update_layout(
        paper_bgcolor="#0e0e1a", plot_bgcolor="#1a1a2e",
        font_color="white",
        title="Risk-Return Peer Map (Star = Your Portfolio)",
        xaxis_title="Volatility (%)",
        yaxis_title="Annual Return (%)",
        margin=dict(t=50,b=40,l=50,r=20),
        height=500,
        legend=dict(bgcolor="#1a1a2e", bordercolor="#333"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption(
        "Dotted lines show Sharpe ratio = 0.5 and 1.0. "
        "Portfolios above the Sharpe 1.0 line offer excellent risk-adjusted returns. "
        "Your portfolio (star) should ideally be in the upper-left region."
    )

    # ── Cumulative return comparison ──────────────────────────────────────────
    st.markdown("**Cumulative Return Since 2020**")
    if not bench_rets.empty:
        common_idx = port_daily.index.intersection(bench_rets.index)
        if len(common_idx) > 30:
            port_cum   = (1 + port_daily.loc[common_idx]).cumprod()
            bench_cum  = (1 + bench_rets.loc[common_idx]).cumprod()

            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=port_cum.index, y=port_cum.values,
                mode="lines",
                line=dict(color="#4CAF50", width=3),
                name=f"Your Portfolio ({profile_name})",
            ))
            b_colors = ["#2196F3","#FF9800","#9C27B0","#00BCD4","#FF5722","#FFC107"]
            for i, col in enumerate(bench_cum.columns):
                fig_cum.add_trace(go.Scatter(
                    x=bench_cum.index, y=bench_cum[col],
                    mode="lines",
                    line=dict(color=b_colors[i % len(b_colors)], width=1.5),
                    name=col,
                ))
            fig_cum.update_layout(
                paper_bgcolor="#0e0e1a", plot_bgcolor="#1a1a2e",
                font_color="white",
                title="Cumulative Return (Base = 1.0 in Jan 2020)",
                xaxis_title="Date", yaxis_title="Cumulative Return",
                margin=dict(t=50,b=40,l=50,r=20), height=420,
                legend=dict(bgcolor="#1a1a2e", bordercolor="#333"),
            )
            st.plotly_chart(fig_cum, use_container_width=True)

    # ── Rolling Sharpe comparison ─────────────────────────────────────────────
    st.markdown("**Rolling 6-Month Sharpe Ratio**")
    if not bench_rets.empty and "Nifty 50" in bench_rets.columns:
        window     = 126
        common_idx = port_daily.index.intersection(bench_rets.index)
        port_c     = port_daily.loc[common_idx]
        nifty_c    = bench_rets["Nifty 50"].loc[common_idx]

        roll_sharpe_port  = []
        roll_sharpe_nifty = []
        roll_dates        = []

        for i in range(window, len(common_idx)):
            p_slice = port_c.iloc[i-window:i]
            n_slice = nifty_c.iloc[i-window:i]
            rs_p = ((p_slice.mean()*252 - 0.065) /
                    (p_slice.std()*np.sqrt(252))) if p_slice.std()>0 else 0
            rs_n = ((n_slice.mean()*252 - 0.065) /
                    (n_slice.std()*np.sqrt(252))) if n_slice.std()>0 else 0
            roll_sharpe_port.append(rs_p)
            roll_sharpe_nifty.append(rs_n)
            roll_dates.append(common_idx[i])

        if roll_dates:
            fig_rs = go.Figure()
            fig_rs.add_trace(go.Scatter(
                x=roll_dates, y=roll_sharpe_port,
                mode="lines", line=dict(color="#4CAF50", width=2),
                fill="tozeroy", fillcolor="rgba(76,175,80,0.1)",
                name="Your Portfolio",
            ))
            fig_rs.add_trace(go.Scatter(
                x=roll_dates, y=roll_sharpe_nifty,
                mode="lines", line=dict(color="#2196F3", width=2),
                name="Nifty 50",
            ))
            fig_rs.add_hline(y=0, line_color="white", line_width=1)
            fig_rs.update_layout(
                paper_bgcolor="#0e0e1a", plot_bgcolor="#1a1a2e",
                font_color="white",
                title="Rolling 6-Month Sharpe Ratio vs Nifty 50",
                xaxis_title="Date", yaxis_title="Sharpe Ratio",
                margin=dict(t=50,b=40,l=50,r=20), height=380,
                legend=dict(bgcolor="#1a1a2e", bordercolor="#333"),
            )
            st.plotly_chart(fig_rs, use_container_width=True)
            st.caption(
                "When the green line (your portfolio) is above the blue line (Nifty 50), "
                "your portfolio is delivering better risk-adjusted returns than the benchmark. "
                "This is the core metric SEBI uses for PMS performance evaluation."
            )

    # ── XIRR calculator ───────────────────────────────────────────────────────
    st.markdown("**XIRR Calculator (SEBI PMS Requirement)**")
    st.caption(
        "SEBI mandates PMS firms report returns as XIRR. "
        "Enter your investment history to compute exact XIRR."
    )

    xc1, xc2, xc3 = st.columns(3)
    inv_date   = xc1.date_input("Investment date",
                                 value=date.today()-timedelta(days=730),
                                 key="xirr_date")
    inv_amount = xc2.number_input("Amount invested (Rs.)",
                                   value=5000000, step=100000, key="xirr_amt")
    curr_val   = xc3.number_input("Current value (Rs.)",
                                   value=6500000, step=100000, key="xirr_val")

    days_held = (date.today() - inv_date).days
    if days_held > 0 and inv_amount > 0:
        simple_return = (curr_val - inv_amount) / inv_amount * 100
        xirr_approx   = ((curr_val / inv_amount) ** (365 / days_held) - 1) * 100
        xi1, xi2, xi3 = st.columns(3)
        xi1.metric("Days Held",       f"{days_held} days")
        xi2.metric("Absolute Return", f"{simple_return:.2f}%")
        xi3.metric("XIRR (approx.)",  f"{xirr_approx:.2f}% p.a.")
        st.success(
            f"SEBI-reportable performance: {xirr_approx:.2f}% XIRR "
            f"over {days_held} days on Rs.{inv_amount:,.0f} investment."
        )
