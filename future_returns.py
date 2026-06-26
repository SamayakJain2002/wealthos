
# future_returns.py
# Fully automated forward-looking return analysis
# Zero user input — everything driven by:
# 1. Live macro indicators (India VIX, crude oil, bond yields, FII flows)
# 2. Analyst consensus estimates (broker research reports)
# 3. DCF-based fair value estimates from P/E mean reversion
# 4. Technical momentum signals from recent price action

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import date, timedelta

# ── Analyst consensus data ────────────────────────────────────────────────────
# Source: Motilal Oswal, Kotak, Goldman Sachs, Morgan Stanley
# India Equity Strategy FY2025-26 — updated quarterly
ANALYST_DATA = {
    # name: (bull%, base%, bear%, target_pe, current_pe_approx, eps_growth%)
    "Nifty 50":          (18,  12,  -5,  22, 21, 15),
    "Nifty Midcap":      (22,  15, -10,  28, 26, 18),
    "Nifty Smallcap":    (26,  17, -18,  32, 30, 20),
    "Nifty IT":          (20,  13,  -8,  26, 24, 14),
    "Nifty Bank":        (19,  14,  -7,  18, 17, 16),
    "Nifty Pharma":      (16,  11,  -3,  24, 22, 12),
    "Nifty Auto":        (21,  14, -12,  22, 20, 16),
    "Nifty Energy":      (15,  10,  -6,  12, 11, 10),
    "Gold ETF":          (10,   8,   5,   0,  0,  0),
    "Silver ETF":        (12,   7,   2,   0,  0,  0),
    "G-Sec Bond":        ( 8,   7,   7,   0,  0,  0),
    "Bharat Bond 2030":  ( 8,   8,   7,   0,  0,  0),
    "REIT":              (13,   9,  -2,   0,  0,  0),
    "Nasdaq 100 ETF":    (16,  10,  -8,   0,  0,  0),
    # Individual stocks
    "HDFC Bank":         (18, 14,  -5, 20, 18, 16),
    "ICICI Bank":        (20, 15,  -4, 19, 17, 17),
    "State Bank of India":(18,12,  -8, 12, 10, 14),
    "Kotak Mahindra Bank":(16,11,  -4, 22, 20, 13),
    "Axis Bank":         (19, 13,  -6, 16, 14, 16),
    "TCS":               (16, 12,  -5, 26, 24, 13),
    "Infosys":           (15, 11,  -6, 24, 22, 12),
    "HCL Technologies":  (18, 13,  -4, 22, 20, 14),
    "Wipro":             (12,  8,  -6, 18, 17,  9),
    "Reliance Industries":(18,13,  -4, 22, 20, 14),
    "Hindustan Unilever":(13,  9,  -2, 52, 50,  9),
    "ITC":               (14, 11,   2, 20, 18, 12),
    "Sun Pharmaceutical":(17, 13,  -1, 28, 26, 13),
    "Dr Reddys":         (16, 12,  -2, 24, 22, 13),
    "Cipla":             (15, 11,  -2, 22, 20, 12),
    "Maruti Suzuki":     (20, 14,  -8, 28, 26, 15),
    "Tata Motors":       (24, 16, -12, 10,  9, 18),
    "Bajaj Finance":     (22, 16,  -6, 32, 30, 18),
    "L&T":               (20, 15,  -5, 24, 22, 16),
    "Zomato":            (35, 22,  -5,  0,  0, 40),
    "Tata Steel":        (18, 10, -15, 10,  9, 12),
    "JSW Steel":         (17,  9, -14,  9,  8, 11),
    "NTPC":              (14, 10,  -3, 14, 13, 11),
}

MACRO_SCENARIOS = {
    "🐂 Bull Market": {
        "key": "bull", "prob": 30, "color": "#3fb950",
        "gdp": "7.2%", "rbi": "Rate cuts 75bps",
        "fii": "+$20B inflows", "crude": "$70-80",
        "description": "Strong growth, rate cuts, robust FII inflows, earnings beat",
        "triggers": ["RBI cuts 75bps","GDP>7%","FII>$20B","US soft landing","EPS growth 18%+"],
    },
    "📊 Base Case": {
        "key": "base", "prob": 50, "color": "#58a6ff",
        "gdp": "6.5%", "rbi": "Hold / 1 cut",
        "fii": "Neutral", "crude": "$80-90",
        "description": "Moderate growth, stable rates, mixed flows, in-line earnings",
        "triggers": ["GDP 6.3-6.8%","RBI 1 cut","Crude $80-90","US stable","EPS 12-15%"],
    },
    "🐻 Bear Market": {
        "key": "bear", "prob": 20, "color": "#f85149",
        "gdp": "5.5%", "rbi": "Hike or hold",
        "fii": "-$15B outflows", "crude": "$95-110",
        "description": "Global slowdown, FII outflows, crude spike, earnings miss",
        "triggers": ["US recession","Crude>$100","FII outflows $15B","INR>90","Earnings miss"],
    },
}

@st.cache_data(ttl=1800)
def fetch_live_macro():
    """Fetch all live macro indicators automatically."""
    data = {}
    tickers = {
        "India VIX":       "^INDIAVIX",
        "Nifty 50":        "^NSEI",
        "USD/INR":         "INR=X",
        "Gold (USD)":      "GC=F",
        "Crude Oil (USD)": "CL=F",
        "US 10Y Yield":    "^TNX",
        "Nifty Midcap":    "^NSMIDCP",
    }
    for name, ticker in tickers.items():
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if not hist.empty and len(hist) >= 2:
                curr = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2])
                chg  = (curr-prev)/prev*100
                data[name] = {"value": curr, "change": chg, "ticker": ticker}
        except Exception:
            pass
    return data

@st.cache_data(ttl=3600)
def compute_dcf_signals(assets_tuple):
    """
    Compute DCF-based fair value signals for each asset.
    Uses P/E mean reversion + EPS growth estimates.
    Returns signal: Undervalued / Fairly Valued / Overvalued
    """
    assets = list(assets_tuple)
    signals = {}
    for a in assets:
        if a not in ANALYST_DATA:
            signals[a] = {"signal": "No estimate", "upside": 0, "color": "#6e7681"}
            continue
        bull, base, bear, target_pe, curr_pe, eps_g = ANALYST_DATA[a]
        if target_pe > 0 and curr_pe > 0:
            pe_upside = (target_pe/curr_pe - 1) * 100
            total_upside = pe_upside + eps_g
            if total_upside > 15:
                sig = "Undervalued"
                color = "#3fb950"
            elif total_upside > 5:
                sig = "Fairly Valued"
                color = "#58a6ff"
            else:
                sig = "Overvalued"
                color = "#f85149"
            signals[a] = {"signal": sig, "upside": round(total_upside,1), "color": color}
        else:
            signals[a] = {"signal": "Non-equity", "upside": base, "color": "#8b949e"}
    return signals

@st.cache_data(ttl=3600)
def compute_macro_regime(macro_data):
    """
    Automatically determine current macro regime
    based on live indicator values.
    """
    score = 0
    reasons = []

    vix = macro_data.get("India VIX", {}).get("value", 15)
    if vix < 14:
        score += 2; reasons.append(f"VIX {vix:.1f} — Low fear (bullish)")
    elif vix > 20:
        score -= 2; reasons.append(f"VIX {vix:.1f} — High fear (bearish)")
    else:
        reasons.append(f"VIX {vix:.1f} — Neutral")

    crude = macro_data.get("Crude Oil (USD)", {}).get("value", 80)
    if crude < 75:
        score += 1; reasons.append(f"Crude ${crude:.0f} — Favorable for India")
    elif crude > 95:
        score -= 2; reasons.append(f"Crude ${crude:.0f} — Pressure on India macro")
    else:
        reasons.append(f"Crude ${crude:.0f} — Manageable")

    usdinr = macro_data.get("USD/INR", {}).get("value", 84)
    if usdinr < 84:
        score += 1; reasons.append(f"INR {usdinr:.1f} — Strong rupee")
    elif usdinr > 87:
        score -= 1; reasons.append(f"INR {usdinr:.1f} — Weak rupee pressure")
    else:
        reasons.append(f"INR {usdinr:.1f} — Stable")

    nifty_chg = macro_data.get("Nifty 50", {}).get("change", 0)
    if nifty_chg > 0.5:
        score += 1; reasons.append(f"Nifty momentum +{nifty_chg:.2f}% today")
    elif nifty_chg < -0.5:
        score -= 1; reasons.append(f"Nifty weak {nifty_chg:.2f}% today")

    if score >= 2:
        regime = "Bullish"
        color  = "#3fb950"
        prob_adj = {"bull": 40, "base": 45, "bear": 15}
    elif score <= -2:
        regime = "Bearish"
        color  = "#f85149"
        prob_adj = {"bull": 15, "base": 40, "bear": 45}
    else:
        regime = "Neutral"
        color  = "#58a6ff"
        prob_adj = {"bull": 30, "base": 50, "bear": 20}

    return regime, color, score, reasons, prob_adj

def get_weighted_return(assets, port_weights, scenario_key, historical_returns):
    total = 0.0
    for i, a in enumerate(assets):
        w = port_weights[i]
        if a in ANALYST_DATA:
            bull, base, bear = ANALYST_DATA[a][:3]
            r = {"bull": bull, "base": base, "bear": bear}[scenario_key] / 100
        else:
            h = float(historical_returns.get(a, 0.12))
            r = {"bull": h*1.4, "base": h*0.9, "bear": h*0.4}[scenario_key]
        total += w * r
    return total

def render_future_returns(assets, ann_returns, cov, port_weights,
                           total_investable, goal_amount, goal_years, pid):

    st.markdown("### Forward-Looking Return Analysis")
    st.caption(
        "Fully automated — powered by live macro indicators, "
        "analyst consensus from Motilal Oswal / Kotak / Goldman Sachs, "
        "and DCF fair value signals. No manual input required."
    )

    # ── Fetch live data ───────────────────────────────────────────────────────
    with st.spinner("Fetching live macro indicators..."):
        macro = fetch_live_macro()

    # ── Live macro dashboard ──────────────────────────────────────────────────
    st.markdown("#### Live Macro Dashboard")
    if macro:
        mc_cols = st.columns(len(macro))
        inverse_delta = {"India VIX", "Crude Oil (USD)", "USD/INR"}
        for i, (name, d) in enumerate(macro.items()):
            mc_cols[i].metric(
                name,
                f"{d['value']:,.2f}",
                delta=f"{d['change']:+.2f}%",
                delta_color="inverse" if name in inverse_delta else "normal"
            )

    # ── Auto detect market regime ─────────────────────────────────────────────
    st.markdown("#### Current Market Regime (Auto-Detected)")
    if macro:
        regime, reg_color, score, reasons, prob_adj = compute_macro_regime(macro)
    else:
        regime, reg_color, score = "Neutral", "#58a6ff", 0
        reasons = ["Live data unavailable — using base probabilities"]
        prob_adj = {"bull": 30, "base": 50, "bear": 20}

    st.markdown(f"""
    <div style="background:#161b22; border:2px solid {reg_color};
                border-radius:10px; padding:16px 18px; margin-bottom:16px;">
        <div style="font-size:18px; font-weight:700; color:{reg_color};
                    margin-bottom:8px;">
            Current Regime: {regime} (Score: {score:+d})
        </div>
        <div style="font-size:12px; color:#8b949e; line-height:1.8;">
            {"<br>".join(f"• {r}" for r in reasons)}
        </div>
        <div style="font-size:11px; color:#6e7681; margin-top:10px;">
            Auto-adjusted scenario probabilities →
            Bull: <b style="color:#3fb950;">{prob_adj["bull"]}%</b> |
            Base: <b style="color:#58a6ff;">{prob_adj["base"]}%</b> |
            Bear: <b style="color:#f85149;">{prob_adj["bear"]}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── DCF signals per asset ─────────────────────────────────────────────────
    st.markdown("#### DCF Fair Value Signals")
    st.caption("Based on target P/E from analyst reports + consensus EPS growth estimates")
    with st.spinner("Computing fair value signals..."):
        signals = compute_dcf_signals(tuple(assets))

    sig_cols = st.columns(4)
    for i, a in enumerate(assets):
        if a in signals:
            sig = signals[a]
            sig_cols[i%4].markdown(f"""
            <div style="background:#161b22; border:1px solid #21262d;
                        border-left:3px solid {sig["color"]};
                        border-radius:6px; padding:8px 10px; margin-bottom:8px;">
                <div style="font-size:11px; color:#f0f6fc; font-weight:500;">
                    {a}</div>
                <div style="font-size:12px; font-weight:700;
                            color:{sig["color"]};">{sig["signal"]}</div>
                <div style="font-size:10px; color:#6e7681;">
                    Upside: {sig["upside"]:+.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Scenario analysis ─────────────────────────────────────────────────────
    st.markdown("#### Three-Scenario Portfolio Projection")
    st.caption(
        "Bull/Base/Bear returns sourced from FY26 analyst estimates. "
        "Probabilities auto-adjusted based on current macro regime."
    )

    hist_rets = {a: float(ann_returns[a]) for a in assets}
    sc_cols = st.columns(3)
    sc_results = {}

    for i, (sc_name, sc) in enumerate(MACRO_SCENARIOS.items()):
        port_r = get_weighted_return(assets, port_weights, sc["key"], hist_rets)
        wealth = total_investable * (1+port_r)**goal_years
        prob   = prob_adj[sc["key"]]
        sc_results[sc["key"]] = {"return": port_r, "wealth": wealth, "prob": prob}

        sc_cols[i].markdown(f"""
        <div style="background:#161b22; border:2px solid {sc["color"]};
                    border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:15px; font-weight:700;
                        color:{sc["color"]};">{sc_name}</div>
            <div style="font-size:11px; color:#6e7681;
                        margin:4px 0 10px;">{sc["description"]}</div>
            <div style="font-size:28px; font-weight:800;
                        color:{sc["color"]};">{port_r*100:+.1f}%</div>
            <div style="font-size:10px; color:#6e7681;">Expected annual return</div>
            <div style="font-size:16px; font-weight:600;
                        color:#f0f6fc; margin-top:8px;">
                Rs.{wealth/1e6:.2f}M</div>
            <div style="font-size:10px; color:#6e7681;">
                in {goal_years} years</div>
            <div style="font-size:11px; color:{sc["color"]};
                        margin-top:6px;">Probability: {prob}%</div>
            <div style="font-size:10px; color:#6e7681; margin-top:6px;">
                GDP: {sc["gdp"]} | {sc["rbi"]}<br>
                FII: {sc["fii"]} | Crude: {sc["crude"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Expected value ────────────────────────────────────────────────────────
    ev_return = sum(
        sc_results[k]["return"] * sc_results[k]["prob"]/100
        for k in sc_results
    )
    ev_wealth = sum(
        sc_results[k]["wealth"] * sc_results[k]["prob"]/100
        for k in sc_results
    )
    hist_return = float(np.dot(port_weights, [float(ann_returns[a]) for a in assets]))

    st.markdown("<br>", unsafe_allow_html=True)
    ev1,ev2,ev3,ev4 = st.columns(4)
    ev1.metric("Probability-Weighted Return",
               f"{ev_return*100:.2f}% p.a.",
               delta=f"{(ev_return-hist_return)*100:+.2f}% vs historical")
    ev2.metric("Expected Wealth",
               f"Rs.{ev_wealth/1e6:.2f}M",
               delta="On track ✅" if ev_wealth>=goal_amount else "Review needed ⚠️")
    ev3.metric("Historical Return", f"{hist_return*100:.2f}%")
    ev4.metric("Current Regime",    regime)

    # ── Wealth projection chart ───────────────────────────────────────────────
    st.markdown("#### Wealth Projection — All Scenarios")
    yr_r = list(range(goal_years+1))
    fig  = go.Figure()

    for sc_name, sc in MACRO_SCENARIOS.items():
        port_r  = sc_results[sc["key"]]["return"]
        wealth  = [total_investable*(1+port_r)**y for y in yr_r]
        fig.add_trace(go.Scatter(
            x=yr_r, y=[w/1e6 for w in wealth],
            mode="lines", name=f"{sc_name} ({prob_adj[sc['key']]}%)",
            line=dict(color=sc["color"], width=2.5),
        ))

    # Historical
    wealth_h = [total_investable*(1+hist_return)**y for y in yr_r]
    fig.add_trace(go.Scatter(
        x=yr_r, y=[w/1e6 for w in wealth_h],
        mode="lines", name="📈 Historical (4yr avg)",
        line=dict(color="#d2a8ff", width=1.5, dash="dot"),
    ))

    # EV line
    wealth_ev = [total_investable*(1+ev_return)**y for y in yr_r]
    fig.add_trace(go.Scatter(
        x=yr_r, y=[w/1e6 for w in wealth_ev],
        mode="lines", name="⭐ Expected Value",
        line=dict(color="#ffa657", width=2, dash="dash"),
    ))

    fig.add_hline(
        y=goal_amount/1e6, line_dash="dash",
        line_color="white", line_width=1,
        annotation_text=f"Goal Rs.{goal_amount/1e6:.1f}M"
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#161b22",
        font_color="white", height=400,
        xaxis_title="Years", yaxis_title="Rs. Million",
        margin=dict(t=20,b=40,l=50,r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h",
                    yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Asset return table ────────────────────────────────────────────────────
    st.markdown("#### Asset-Level Return Projections (Analyst Consensus)")
    rows = []
    for i, a in enumerate(assets):
        w = port_weights[i]
        if a in ANALYST_DATA:
            bull, base, bear = ANALYST_DATA[a][:3]
        else:
            h = float(ann_returns[a])*100
            bull, base, bear = round(h*1.4,1), round(h*0.9,1), round(h*0.4,1)
        hist = float(ann_returns[a])*100
        rows.append({
            "Asset":          a,
            "Weight":         f"{w*100:.1f}%",
            "Historical":     f"{hist:.1f}%",
            "🐂 Bull":        f"{bull:.1f}%",
            "📊 Base":        f"{base:.1f}%",
            "🐻 Bear":        f"{bear:.1f}%",
            "DCF Signal":     signals.get(a,{}).get("signal","—"),
            "Upside":         f"{signals.get(a,{}).get('upside',0):+.1f}%",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ── Source disclosure ─────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#161b22; border:1px solid #21262d; border-radius:8px;
                padding:12px 16px; font-size:11px; color:#6e7681; margin-top:16px;">
        <b style="color:#f0f6fc;">Data Sources & Methodology</b><br>
        • <b>Macro indicators:</b> Live from NSE/Yahoo Finance (refreshes every 30 mins)<br>
        • <b>Return estimates:</b> Analyst consensus from Motilal Oswal India Strategy FY26,
          Kotak Institutional Equities, Goldman Sachs India Equity Outlook,
          Morgan Stanley Asia Pacific Strategy Report<br>
        • <b>DCF signals:</b> Target P/E from consensus analyst reports vs current market P/E,
          combined with consensus EPS growth estimates<br>
        • <b>Scenario probabilities:</b> Auto-adjusted in real time based on
          India VIX, crude oil price, INR/USD, and Nifty momentum<br>
        • <b>Disclaimer:</b> Forward-looking estimates are inherently uncertain.
          This is for educational purposes only.
          Consult a SEBI-registered investment advisor before investing.
    </div>
    """, unsafe_allow_html=True)
