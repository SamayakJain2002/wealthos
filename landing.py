
import streamlit as st
import plotly.graph_objects as go
import numpy as np

def render_landing():

    # ── Top navigation bar ────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding:12px 24px; background:#0d1117;
                border-bottom:1px solid #21262d; margin-bottom:0;">
        <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:22px; font-weight:800; letter-spacing:-0.5px;
                         background:linear-gradient(135deg,#3fb950,#58a6ff);
                         -webkit-background-clip:text;
                         -webkit-text-fill-color:transparent;">
                WealthPy Labs
            </span>
            <span style="font-size:11px; background:#21262d; color:#8b949e;
                         padding:2px 8px; border-radius:20px; border:1px solid #30363d;">
                v2.0 BETA
            </span>
        </div>
        <div style="display:flex; gap:24px; font-size:13px; color:#8b949e;">
            <span>Portfolio Builder</span>
            <span>Analytics</span>
            <span>Tax Engine</span>
            <span>Live Data</span>
            <span style="color:#3fb950;">Docs</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Hero section ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:70px 20px 40px;
                background:linear-gradient(180deg,#0d1117 0%,#161b22 100%);">
        <div style="display:inline-block; background:#21262d; border:1px solid #30363d;
                    border-radius:20px; padding:4px 14px; font-size:11px;
                    color:#58a6ff; margin-bottom:20px; letter-spacing:0.5px;">
            PROFESSIONAL HNI PORTFOLIO ADVISORY PLATFORM
        </div>
        <div style="font-size:54px; font-weight:800; color:#f0f6fc;
                    line-height:1.1; margin-bottom:16px; letter-spacing:-1px;">
            When it comes to your money,<br>
            <span style="background:linear-gradient(135deg,#3fb950,#58a6ff);
                         -webkit-background-clip:text;
                         -webkit-text-fill-color:transparent;">
                stop guessing.
            </span>
        </div>
        <div style="font-size:17px; color:#8b949e; max-width:640px;
                    margin:0 auto 12px; line-height:1.7;">
            The only Indian HNI portfolio platform that optimises allocations using
            Markowitz theory, stress-tests against real crashes, and computes
            your exact FY2024-25 tax liability — all powered by live NSE/BSE data.
        </div>
        <div style="font-size:13px; color:#6e7681; margin-bottom:36px;">
            Used by wealth advisors, PMS firms, and serious investors across India.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA buttons ───────────────────────────────────────────────────────────
    col1,col2,col3 = st.columns([1.5,1,1.5])
    with col2:
        if st.button("Launch Platform →",
                     use_container_width=True,
                     type="primary",
                     key="launch_btn"):
            st.session_state["page"] = "app"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Feature comparison table (like Wealth-Lab) ────────────────────────────
    st.markdown("""
    <div style="max-width:900px; margin:0 auto; padding:0 20px;">
        <div style="text-align:center; font-size:24px; font-weight:700;
                    color:#f0f6fc; margin:30px 0 8px;">
            Why professionals choose WealthPy Labs
        </div>
        <div style="text-align:center; font-size:13px; color:#6e7681;
                    margin-bottom:24px;">
            Compare what matters for serious portfolio management
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_tbl1, col_tbl2 = st.columns([1,1])
    with col_tbl1:
        st.markdown("""
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <thead>
                <tr style="border-bottom:1px solid #21262d;">
                    <th style="text-align:left; padding:10px 12px; color:#8b949e;
                               font-weight:500;">Feature</th>
                    <th style="text-align:center; padding:10px 12px; color:#8b949e;
                               font-weight:500;">Basic Tools</th>
                    <th style="text-align:center; padding:10px 12px; color:#3fb950;
                               font-weight:600;">WealthPy Labs</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid #161b22;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        Portfolio Optimisation</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        Manual only</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ Markowitz + Manual</td>
                </tr>
                <tr style="border-bottom:1px solid #161b22; background:#0d1117;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        Live NSE/BSE Data</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        Delayed or paid</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ Free, live</td>
                </tr>
                <tr style="border-bottom:1px solid #161b22;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        India Tax Engine</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        ✗ Not available</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ FY2024-25 rules</td>
                </tr>
                <tr style="border-bottom:1px solid #161b22; background:#0d1117;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        Monte Carlo Simulation</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        ✗</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ 1,000 paths</td>
                </tr>
                <tr style="border-bottom:1px solid #161b22;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        Factor Exposure Analysis</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        ✗</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ Institutional grade</td>
                </tr>
                <tr style="background:#0d1117;">
                    <td style="padding:10px 12px; color:#c9d1d9;">
                        Stress Testing</td>
                    <td style="text-align:center; padding:10px; color:#f85149;">
                        ✗</td>
                    <td style="text-align:center; padding:10px; color:#3fb950;">
                        ✓ Real crash data</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    with col_tbl2:
        # Mini performance chart
        np.random.seed(42)
        days = 252*4
        ret1 = np.random.normal(0.0006, 0.010, days)
        ret2 = np.random.normal(0.0004, 0.007, days)
        ret3 = np.full(days, 0.000258)
        cum1 = np.cumprod(1+ret1)
        cum2 = np.cumprod(1+ret2)
        cum3 = np.cumprod(1+ret3)

        fig = go.Figure()
        fig.add_trace(go.Scatter(y=cum1*100,mode="lines",name="Aggressive",
            line=dict(color="#3fb950",width=2)))
        fig.add_trace(go.Scatter(y=cum2*100,mode="lines",name="Balanced",
            line=dict(color="#58a6ff",width=2)))
        fig.add_trace(go.Scatter(y=cum3*100,mode="lines",name="FD (6.5%)",
            line=dict(color="#6e7681",width=1,dash="dot")))
        fig.update_layout(
            paper_bgcolor="#0d1117",plot_bgcolor="#0d1117",
            font_color="#8b949e",height=260,
            margin=dict(t=10,b=30,l=40,r=10),
            legend=dict(bgcolor="rgba(0,0,0,0)",font_size=10,
                        orientation="h",yanchor="bottom",y=1.02),
            xaxis=dict(showgrid=False,color="#6e7681",
                       title="Trading Days",tickfont_size=9),
            yaxis=dict(showgrid=True,gridcolor="#21262d",
                       color="#6e7681",title="Growth (Base=100)",
                       tickfont_size=9),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Stats strip ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:0;
                border:1px solid #21262d; border-radius:12px;
                overflow:hidden; margin:30px 20px; background:#0d1117;">
    """, unsafe_allow_html=True)

    stats = [
        ("30+",    "Asset Classes",       "#3fb950"),
        ("200+",   "NSE/BSE Stocks",      "#58a6ff"),
        ("1,000",  "Monte Carlo Paths",   "#d2a8ff"),
        ("10",     "Analysis Modules",    "#ffa657"),
        ("Live",   "NSE/BSE Data Feed",   "#3fb950"),
        ("Free",   "No Subscription",     "#58a6ff"),
    ]
    cols = st.columns(6)
    for col,(val,label,color) in zip(cols,stats):
        col.markdown(f"""
        <div style="text-align:center; padding:20px 8px;
                    border-right:1px solid #21262d;">
            <div style="font-size:28px; font-weight:700;
                        color:{color}; line-height:1.1;">{val}</div>
            <div style="font-size:10px; color:#6e7681;
                        margin-top:4px; text-transform:uppercase;
                        letter-spacing:0.5px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; font-size:22px; font-weight:700;
                color:#f0f6fc; margin:40px 0 8px;">
        Complete Portfolio Management Suite
    </div>
    <div style="text-align:center; font-size:13px; color:#6e7681;
                margin-bottom:24px;">
        Everything a wealth advisor or serious investor needs — in one platform
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("#3fb950","📊","Portfolio Optimisation",
         "Markowitz mean-variance optimisation or manual allocation across 200+ Indian stocks and indices."),
        ("#58a6ff","🔮","Monte Carlo Simulation",
         "1,000 simulated futures. Know the probability of reaching your goal before you invest."),
        ("#d2a8ff","🧮","Factor Analysis",
         "Institutional-grade factor exposure — Value, Momentum, Quality, Low Volatility."),
        ("#ffa657","🌍","Macro Scenarios",
         "Test against RBI rate hikes, crude oil spikes, INR depreciation and global recession."),
        ("#3fb950","📡","Live NSE/BSE Tracker",
         "Real-time prices, intraday charts, and price alerts for every asset in your portfolio."),
        ("#58a6ff","💰","India Tax Engine",
         "FY2024-25 LTCG/STCG calculation, tax harvesting strategy, and SEBI XIRR reporting."),
        ("#d2a8ff","🏆","Peer Benchmarking",
         "Compare vs Nifty 50, Sensex, and top PMS strategies. Rolling Sharpe ratio analysis."),
        ("#ffa657","⚡","Stress Testing",
         "See how your portfolio survives COVID crash, 2022 rate hike, and Russia-Ukraine crisis."),
    ]

    cols = st.columns(4)
    for i,(color,icon,title,desc) in enumerate(features):
        with cols[i%4]:
            st.markdown(f"""
            <div style="background:#161b22; border:1px solid #21262d;
                        border-radius:10px; padding:18px 16px;
                        margin-bottom:12px; min-height:150px;
                        border-top:2px solid {color};">
                <div style="font-size:22px; margin-bottom:8px;">{icon}</div>
                <div style="font-size:13px; font-weight:600; color:#f0f6fc;
                            margin-bottom:6px;">{title}</div>
                <div style="font-size:11px; color:#6e7681; line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="border-top:1px solid #21262d; margin-top:40px;
                padding:20px; text-align:center;">
        <div style="font-size:11px; color:#6e7681; line-height:1.8;">
            <b style="color:#3fb950;">WealthPy Labs</b> — Professional HNI Portfolio Advisory Platform
            &nbsp;|&nbsp; Data sourced live from NSE/BSE via yfinance
            &nbsp;|&nbsp; For educational purposes only
            &nbsp;|&nbsp; Consult a SEBI-registered advisor before investing
            <br>
            Built by
            <a href="https://linkedin.com/in/samayakpjain"
               style="color:#58a6ff;">Samayak Jain</a>
            &nbsp;|&nbsp;
            <a href="https://github.com/SamayakJain2002/wealthos"
               style="color:#58a6ff;">GitHub</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
