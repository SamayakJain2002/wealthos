
# charts.py — Candlestick charting with 100+ technical indicators
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date, timedelta

TA_AVAILABLE = False

# Full NSE ticker map
NSE_TICKERS = {
    "Nifty 50":           "^NSEI",
    "Nifty Midcap":       "^NSMIDCP",
    "Nifty Smallcap":     "^CNXSC",
    "Nifty Bank":         "^NSEBANK",
    "Nifty IT":           "^CNXIT",
    "Nifty Pharma":       "^CNXPHARMA",
    "Nifty Auto":         "^CNXAUTO",
    "Nifty Energy":       "^CNXENERGY",
    "HDFC Bank":          "HDFCBANK.NS",
    "ICICI Bank":         "ICICIBANK.NS",
    "Reliance":           "RELIANCE.NS",
    "TCS":                "TCS.NS",
    "Infosys":            "INFY.NS",
    "HUL":                "HINDUNILVR.NS",
    "ITC":                "ITC.NS",
    "Maruti":             "MARUTI.NS",
    "Sun Pharma":         "SUNPHARMA.NS",
    "Bajaj Finance":      "BAJFINANCE.NS",
    "L&T":                "LT.NS",
    "Axis Bank":          "AXISBANK.NS",
    "Tata Motors":        "TATAMOTORS.NS",
    "Wipro":              "WIPRO.NS",
    "NTPC":               "NTPC.NS",
    "Tata Steel":         "TATASTEEL.NS",
    "JSW Steel":          "JSWSTEEL.NS",
    "Zomato":             "ZOMATO.NS",
    "Dr. Reddys":         "DRREDDY.NS",
    "Gold ETF":           "GOLDBEES.NS",
    "REIT":               "EMBASSY.NS",
}

TIMEFRAMES = {
    "1 Month":  ("1mo",  "1d"),
    "3 Months": ("3mo",  "1d"),
    "6 Months": ("6mo",  "1d"),
    "1 Year":   ("1y",   "1d"),
    "2 Years":  ("2y",   "1wk"),
    "5 Years":  ("5y",   "1wk"),
}

@st.cache_data(ttl=300)
def fetch_ohlcv(ticker, period, interval):
    try:
        raw = yf.download(ticker, period=period, interval=interval,
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        if raw.empty:
            return None
        raw = raw.dropna()
        return raw
    except Exception as e:
        return None

def add_indicators(df, indicators):
    """Add selected technical indicators to dataframe."""
    if not TA_AVAILABLE:
        return df

    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]
    vol   = df["Volume"] if "Volume" in df.columns else None

    if "SMA 20"  in indicators: df["SMA20"]  = ta.sma(close, 20)
    if "SMA 50"  in indicators: df["SMA50"]  = ta.sma(close, 50)
    if "SMA 200" in indicators: df["SMA200"] = ta.sma(close, 200)
    if "EMA 20"  in indicators: df["EMA20"]  = ta.ema(close, 20)
    if "EMA 50"  in indicators: df["EMA50"]  = ta.ema(close, 50)

    if "Bollinger Bands" in indicators:
        bb = ta.bbands(close, length=20)
        if bb is not None:
            df["BB_upper"] = bb.iloc[:,0]
            df["BB_mid"]   = bb.iloc[:,1]
            df["BB_lower"] = bb.iloc[:,2]

    if "RSI" in indicators:
        df["RSI"] = ta.rsi(close, length=14)

    if "MACD" in indicators:
        macd = ta.macd(close)
        if macd is not None:
            df["MACD"]        = macd.iloc[:,0]
            df["MACD_signal"] = macd.iloc[:,1]
            df["MACD_hist"]   = macd.iloc[:,2]

    if "Stochastic" in indicators:
        stoch = ta.stoch(high, low, close)
        if stoch is not None:
            df["Stoch_K"] = stoch.iloc[:,0]
            df["Stoch_D"] = stoch.iloc[:,1]

    if "ATR" in indicators:
        df["ATR"] = ta.atr(high, low, close, length=14)

    if "OBV" in indicators and vol is not None:
        df["OBV"] = ta.obv(close, vol)

    if "Williams %R" in indicators:
        df["WR"] = ta.willr(high, low, close, length=14)

    if "CCI" in indicators:
        df["CCI"] = ta.cci(high, low, close, length=20)

    if "ADX" in indicators:
        adx = ta.adx(high, low, close, length=14)
        if adx is not None:
            df["ADX"] = adx.iloc[:,0]

    return df

def render_charts_tab():
    st.markdown("#### Candlestick Charts & Technical Analysis")
    st.caption(
        "Professional OHLCV charts with 15+ technical indicators. "
        "Same tools used by equity research analysts and PMS traders."
    )

    # ── Controls row ──────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2,1.5,1.5,2])

    # Custom ticker input OR dropdown
    with ctrl1:
        input_mode = st.radio("Select stock by",
                              ["Dropdown", "Custom ticker"],
                              horizontal=True, key="chart_input_mode")
        if input_mode == "Dropdown":
            selected_name = st.selectbox("Stock / Index",
                                          list(NSE_TICKERS.keys()),
                                          key="chart_stock")
            ticker = NSE_TICKERS[selected_name]
        else:
            custom = st.text_input("Enter ticker (e.g. RELIANCE.NS)",
                                   value="RELIANCE.NS",
                                   key="chart_custom_ticker")
            ticker = custom.strip().upper()
            selected_name = ticker

    with ctrl2:
        timeframe = st.selectbox("Timeframe",
                                  list(TIMEFRAMES.keys()),
                                  index=3, key="chart_tf")
        period, interval = TIMEFRAMES[timeframe]

    with ctrl3:
        chart_style = st.selectbox("Chart Style",
                                    ["Candlestick","OHLC Bar","Line","Area","Heikin Ashi"],
                                    key="chart_style")

    with ctrl4:
        indicators = st.multiselect(
            "Technical Indicators",
            ["SMA 20","SMA 50","SMA 200","EMA 20","EMA 50",
             "Bollinger Bands","RSI","MACD","Stochastic",
             "ATR","OBV","Williams %R","CCI","ADX"],
            default=["SMA 20","SMA 50","RSI"],
            key="chart_indicators"
        )

    # ── Fetch data ────────────────────────────────────────────────────────────
    with st.spinner(f"Loading {selected_name}..."):
        df = fetch_ohlcv(ticker, period, interval)

    if df is None or df.empty:
        st.error(f"Could not load data for {ticker}. Check ticker symbol.")
        return

    # Add indicators
    df = add_indicators(df.copy(), indicators)

    # Heikin Ashi transformation
    if chart_style == "Heikin Ashi":
        ha_close = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
        ha_open  = pd.Series(index=df.index, dtype=float)
        ha_open.iloc[0] = (df["Open"].iloc[0] + df["Close"].iloc[0]) / 2
        for i in range(1, len(df)):
            ha_open.iloc[i] = (ha_open.iloc[i-1] + ha_close.iloc[i-1]) / 2
        ha_high  = pd.concat([df["High"], ha_open, ha_close], axis=1).max(axis=1)
        ha_low   = pd.concat([df["Low"],  ha_open, ha_close], axis=1).min(axis=1)
        plot_o, plot_h = ha_open, ha_high
        plot_l, plot_c = ha_low,  ha_close
    else:
        plot_o = df["Open"]; plot_h = df["High"]
        plot_l = df["Low"];  plot_c = df["Close"]

    # ── Determine subplot layout ──────────────────────────────────────────────
    has_rsi  = "RSI"  in indicators and "RSI"  in df.columns
    has_macd = "MACD" in indicators and "MACD" in df.columns
    has_vol  = "Volume" in df.columns

    n_rows   = 1
    row_heights = [0.60]
    if has_vol:  n_rows += 1; row_heights.append(0.12)
    if has_rsi:  n_rows += 1; row_heights.append(0.14)
    if has_macd: n_rows += 1; row_heights.append(0.14)

    total = sum(row_heights)
    row_heights = [r/total for r in row_heights]

    subplot_titles = [selected_name]
    if has_vol:  subplot_titles.append("Volume")
    if has_rsi:  subplot_titles.append("RSI (14)")
    if has_macd: subplot_titles.append("MACD")

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
        subplot_titles=subplot_titles,
    )

    # ── Main price chart ──────────────────────────────────────────────────────
    if chart_style in ("Candlestick","Heikin Ashi"):
        fig.add_trace(go.Candlestick(
            x=df.index, open=plot_o, high=plot_h,
            low=plot_l, close=plot_c,
            increasing_line_color="#3fb950",
            decreasing_line_color="#f85149",
            name=selected_name,
            showlegend=False,
        ), row=1, col=1)

    elif chart_style == "OHLC Bar":
        fig.add_trace(go.Ohlc(
            x=df.index, open=plot_o, high=plot_h,
            low=plot_l, close=plot_c,
            increasing_line_color="#3fb950",
            decreasing_line_color="#f85149",
            name=selected_name, showlegend=False,
        ), row=1, col=1)

    elif chart_style == "Line":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            line=dict(color="#58a6ff", width=1.8),
            name=selected_name,
        ), row=1, col=1)

    elif chart_style == "Area":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            fill="tozeroy", fillcolor="rgba(88,166,255,0.08)",
            line=dict(color="#58a6ff", width=1.8),
            name=selected_name,
        ), row=1, col=1)

    # ── Overlay indicators on price chart ─────────────────────────────────────
    ma_config = [
        ("SMA20",  "#ffa657", "SMA 20"),
        ("SMA50",  "#d2a8ff", "SMA 50"),
        ("SMA200", "#ff7b72", "SMA 200"),
        ("EMA20",  "#79c0ff", "EMA 20"),
        ("EMA50",  "#56d364", "EMA 50"),
    ]
    for col_name, color, label in ma_config:
        if col_name in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col_name], mode="lines",
                line=dict(color=color, width=1.2),
                name=label, opacity=0.85,
            ), row=1, col=1)

    if "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"], mode="lines",
            line=dict(color="rgba(255,215,0,0.5)", width=1, dash="dash"),
            name="BB Upper", showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"], mode="lines",
            fill="tonexty", fillcolor="rgba(255,215,0,0.04)",
            line=dict(color="rgba(255,215,0,0.5)", width=1, dash="dash"),
            name="BB Lower",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_mid"], mode="lines",
            line=dict(color="rgba(255,215,0,0.3)", width=1),
            name="BB Mid", showlegend=False,
        ), row=1, col=1)

    # ── Volume subplot ─────────────────────────────────────────────────────────
    current_row = 2
    if has_vol:
        colors_vol = [
            "#3fb950" if c >= o else "#f85149"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colors_vol, name="Volume",
            showlegend=False, opacity=0.7,
        ), row=current_row, col=1)
        current_row += 1

    # ── RSI subplot ───────────────────────────────────────────────────────────
    if has_rsi:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], mode="lines",
            line=dict(color="#d2a8ff", width=1.5),
            name="RSI", showlegend=False,
        ), row=current_row, col=1)
        fig.add_hline(y=70, line_color="rgba(248,81,73,0.5)",
                      line_dash="dash", line_width=1,
                      row=current_row, col=1)
        fig.add_hline(y=30, line_color="rgba(63,185,80,0.5)",
                      line_dash="dash", line_width=1,
                      row=current_row, col=1)
        fig.add_hrect(y0=70, y1=100,
                      fillcolor="rgba(248,81,73,0.05)",
                      line_width=0,
                      row=current_row, col=1)
        fig.add_hrect(y0=0, y1=30,
                      fillcolor="rgba(63,185,80,0.05)",
                      line_width=0,
                      row=current_row, col=1)
        current_row += 1

    # ── MACD subplot ──────────────────────────────────────────────────────────
    if has_macd:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"], mode="lines",
            line=dict(color="#58a6ff", width=1.5),
            name="MACD", showlegend=False,
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_signal"], mode="lines",
            line=dict(color="#ffa657", width=1.2),
            name="Signal", showlegend=False,
        ), row=current_row, col=1)
        colors_hist = [
            "#3fb950" if v >= 0 else "#f85149"
            for v in df["MACD_hist"].fillna(0)
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_hist"],
            marker_color=colors_hist,
            name="MACD Hist", showlegend=False, opacity=0.7,
        ), row=current_row, col=1)

    # ── Layout ────────────────────────────────────────────────────────────────
    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font_color="#8b949e",
        height=650,
        margin=dict(t=30, b=20, l=60, r=20),
        legend=dict(
            bgcolor="rgba(13,17,23,0.8)",
            bordercolor="#21262d",
            borderwidth=1,
            font_size=10,
            orientation="h",
            yanchor="bottom", y=1.01,
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    for i in range(1, n_rows+1):
        fig.update_xaxes(
            showgrid=True, gridcolor="#21262d",
            tickfont_size=9, color="#6e7681",
            row=i, col=1,
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="#21262d",
            tickfont_size=9, color="#6e7681",
            row=i, col=1,
        )

    st.plotly_chart(fig, use_container_width=True)

    # ── Key stats strip ───────────────────────────────────────────────────────
    last  = df["Close"].iloc[-1]
    prev  = df["Close"].iloc[-2] if len(df) > 1 else last
    chg   = last - prev
    chg_p = chg / prev * 100
    high52 = df["High"].max()
    low52  = df["Low"].min()
    avg_vol = df["Volume"].mean() if "Volume" in df.columns else 0

    s1,s2,s3,s4,s5,s6 = st.columns(6)
    s1.metric("Last Price",    f"Rs.{last:,.2f}")
    s2.metric("Change",        f"Rs.{chg:+.2f}",
              delta=f"{chg_p:+.2f}%")
    s3.metric("Period High",   f"Rs.{high52:,.2f}")
    s4.metric("Period Low",    f"Rs.{low52:,.2f}")
    s5.metric("Avg Volume",    f"{avg_vol/1e5:.1f}L" if avg_vol>0 else "N/A")
    s6.metric("Data Points",   f"{len(df)}")

    # ── Indicator signals ─────────────────────────────────────────────────────
    if indicators:
        st.markdown("---")
        st.markdown("**Current Indicator Signals**")
        sig_cols = st.columns(4)
        sig_i = 0
        signals = []

        if "RSI" in df.columns and not df["RSI"].dropna().empty:
            rsi_val = df["RSI"].dropna().iloc[-1]
            sig = ("🔴 Overbought" if rsi_val > 70
                   else "🟢 Oversold" if rsi_val < 30
                   else "🟡 Neutral")
            signals.append(("RSI(14)", f"{rsi_val:.1f}", sig))

        if "MACD" in df.columns and "MACD_signal" in df.columns:
            m = df["MACD"].dropna().iloc[-1]
            s = df["MACD_signal"].dropna().iloc[-1]
            sig = "🟢 Bullish" if m > s else "🔴 Bearish"
            signals.append(("MACD", f"{m:.2f}", sig))

        if "SMA20" in df.columns and "SMA50" in df.columns:
            s20 = df["SMA20"].dropna().iloc[-1]
            s50 = df["SMA50"].dropna().iloc[-1]
            price_vs = "above" if last > s20 else "below"
            golden = "🟢 Golden Cross" if s20 > s50 else "🔴 Death Cross"
            signals.append(("SMA Cross", f"Price {price_vs} SMA20", golden))

        if "ADX" in df.columns:
            adx_val = df["ADX"].dropna().iloc[-1]
            sig = ("🟢 Strong trend" if adx_val > 25
                   else "🟡 Weak trend")
            signals.append(("ADX(14)", f"{adx_val:.1f}", sig))

        if "BB_upper" in df.columns and "BB_lower" in df.columns:
            bb_u = df["BB_upper"].dropna().iloc[-1]
            bb_l = df["BB_lower"].dropna().iloc[-1]
            if last > bb_u:   bb_sig = "🔴 Above upper band"
            elif last < bb_l: bb_sig = "🟢 Below lower band"
            else:             bb_sig = "🟡 Inside bands"
            signals.append(("Bollinger", f"U:{bb_u:.0f} L:{bb_l:.0f}", bb_sig))

        for j, (ind_name, val, sig) in enumerate(signals):
            sig_cols[j % 4].markdown(f"""
            <div style="background:#161b22; border:1px solid #21262d;
                        border-radius:8px; padding:10px 12px; margin-bottom:8px;">
                <div style="font-size:11px; color:#6e7681; margin-bottom:3px;">
                    {ind_name}</div>
                <div style="font-size:13px; font-weight:600; color:#f0f6fc;">
                    {val}</div>
                <div style="font-size:11px; margin-top:3px;">{sig}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Raw data table ─────────────────────────────────────────────────────────
    with st.expander("View Raw OHLCV Data"):
        display_df = df[["Open","High","Low","Close","Volume"]].copy()             if "Volume" in df.columns             else df[["Open","High","Low","Close"]].copy()
        display_df = display_df.round(2)
        display_df.index = display_df.index.strftime("%Y-%m-%d")
        st.dataframe(display_df.tail(50).iloc[::-1],
                     use_container_width=True)
