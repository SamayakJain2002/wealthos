
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import minimize
from scipy import stats
from datetime import date, timedelta
import warnings
warnings.filterwarnings("ignore")

import state
from landing import render_landing
from portfolio_builder import render_portfolio_builder
from realtime import render_realtime_tab
from factor import render_factor_tab
from scenario import render_scenario_tab
from benchmark import render_benchmark_tab
from tooltips import info_tooltip, glossary_page
from stock_search import render_stock_search
from charts import render_charts_tab
from backtester import render_backtester_tab
from walkforward import render_walkforward_tab

st.set_page_config(
    page_title="WealthPy Labs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background-color: #0d1117; }
section[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #21262d !important;
}
section[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
div[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 8px; padding: 10px 14px;
}
div[data-testid="metric-container"] label {
    color: #6e7681 !important; font-size: 10px !important;
    text-transform: uppercase; letter-spacing: 0.5px;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #f0f6fc !important; font-size: 18px !important; font-weight: 700 !important;
}
button[data-baseweb="tab"] {
    font-size: 11px !important; padding: 6px 10px !important;
    color: #6e7681 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #3fb950 !important;
    border-bottom: 2px solid #3fb950 !important;
}
button[kind="primary"] {
    background: #238636 !important;
    border: 1px solid #2ea043 !important;
    font-weight: 600 !important; color: #fff !important;
}
button[kind="secondary"] {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #21262d !important;
    border-radius: 6px;
}
.stAlert { border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── Init state ────────────────────────────────────────────────────────────────
state.init_state()

# ── Landing page ──────────────────────────────────────────────────────────────
if st.session_state.get("page","landing") == "landing":
    render_landing()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# ASSET UNIVERSE
# ═══════════════════════════════════════════════════════════════════════════════
INDEX_UNIVERSE = {
    "Nifty 50":         ("^NSEI",         "Equity-LC"),
    "Nifty Midcap":     ("^NSMIDCP",      "Equity-MC"),
    "Nifty Smallcap":   ("^CNXSC",        "Equity-SC"),
    "Nifty IT":         ("^CNXIT",        "Sectoral"),
    "Nifty Pharma":     ("^CNXPHARMA",    "Sectoral"),
    "Nifty Bank":       ("^NSEBANK",      "Sectoral"),
    "Nifty Energy":     ("^CNXENERGY",    "Sectoral"),
    "Nifty Auto":       ("^CNXAUTO",      "Sectoral"),
    "Nasdaq 100 ETF":   ("MOTI0100.NS",   "Intl-Eq"),
    "G-Sec Bond":       ("LIQUIDBEES.NS", "Debt-Sov"),
    "Bharat Bond 2030": ("CPSEETF.NS",    "Debt-TM"),
    "Gold ETF":         ("GOLDBEES.NS",   "Gold"),
    "Silver ETF":       ("SILVERETF.NS",  "Silver"),
    "REIT":             ("EMBASSY.NS",    "REIT"),
}
# Import full Nifty 500 stock list from stock_search
from stock_search import NSE_STOCKS as _NSE_STOCKS
STOCK_UNIVERSE = {
    name: (ticker, "Stock-Custom")
    for name, ticker in _NSE_STOCKS.items()
}
ASSET_UNIVERSE = {**INDEX_UNIVERSE, **STOCK_UNIVERSE}

# Add any custom stocks from stock search
if "custom_asset_universe" in st.session_state:
    ASSET_UNIVERSE.update(st.session_state["custom_asset_universe"])

TAX_CAT = {
    "Equity-LC":"Equity","Equity-MC":"Equity","Equity-SC":"Equity",
    "Sectoral":"Equity","Intl-Eq":"Equity","Debt-Sov":"Debt MF",
    "Debt-TM":"Debt MF","Gold":"Gold ETF","Silver":"Gold ETF",
    "REIT":"Equity","Stock-Bank":"Equity","Stock-IT":"Equity",
    "Stock-Finance":"Equity","Stock-FMCG":"Equity","Stock-Auto":"Equity",
    "Stock-Pharma":"Equity","Stock-Energy":"Equity","Stock-Infra":"Equity",
    "Stock-Metal":"Equity","Stock-Consumer":"Equity","Stock-Custom":"Equity",
}

PROFILE_NAMES  = {1:"Conservative",2:"Mod. Conservative",
                  3:"Balanced",4:"Mod. Aggressive",5:"Aggressive"}
PROFILE_COLORS = {1:"#58a6ff",2:"#3fb950",3:"#FF9800",4:"#FF5722",5:"#9C27B0"}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADER
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400, show_spinner=False)
def load_data(selected_tuple):
    import yfinance as yf
    selected   = list(selected_tuple)
    ticker_map = {ASSET_UNIVERSE[a][0]: a for a in selected
                  if a in ASSET_UNIVERSE}
    tickers    = list(ticker_map.keys())
    END        = date.today().strftime("%Y-%m-%d")
    START      = "2020-01-01"

    raw = yf.download(tickers, start=START, end=END,
                      auto_adjust=True, progress=False, threads=True)
    if raw.empty:
        return None,None,None,[],pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]
    else:
        close = raw

    close = close.rename(columns=ticker_map)
    valid = [c for c in close.columns
             if c in selected and close[c].notna().sum()>100]
    if len(valid) < 2:
        return None,None,None,[],pd.DataFrame()

    prices        = close[valid].ffill().bfill()
    daily_returns = prices.pct_change().dropna()

    for col in daily_returns.columns:
        cat = ASSET_UNIVERSE.get(col,("",""))[1]
        if cat in ("Gold","Silver") and daily_returns[col].std()>0.05:
            daily_returns[col] = daily_returns[col]/100

    TDAYS       = 252
    ann_returns = daily_returns.mean()*TDAYS
    cov         = daily_returns.cov().values*TDAYS
    assets      = list(ann_returns.index)
    return daily_returns, ann_returns, cov, assets, prices

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    if st.button("← Home", key="back_home"):
        st.session_state["page"] = "landing"
        st.rerun()
    st.markdown("---")

    st.markdown("""
    <div style="text-align:center;padding:6px 0 12px;">
        <span style="font-size:20px;font-weight:800;
                     background:linear-gradient(135deg,#3fb950,#58a6ff);
                     -webkit-background-clip:text;
                     -webkit-text-fill-color:transparent;">WealthPy Labs</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Client")
    client_name = st.text_input("Name", placeholder="Your name", key="sb_name")
    c1,c2 = st.columns(2)
    age  = c1.number_input("Age", 18, 80, 28, key="sb_age")
    city = c2.text_input("City", placeholder="Mumbai", key="sb_city")

    st.markdown("#### Financials")
    total_investable = st.number_input("Investable (Rs.)",
        100000,500000000,5000000,100000,key="sb_inv")
    monthly_sip = st.number_input("Monthly SIP (Rs.)",
        0,10000000,50000,5000,key="sb_sip")
    annual_topup = st.number_input("Annual Top-up (Rs.)",
        0,50000000,500000,50000,key="sb_topup")
    inv_goal = st.selectbox("Goal",[
        "Retirement corpus","Child education","Home purchase",
        "Wealth creation","Regular income","Tax saving","Wedding fund"],
        key="sb_goal")
    goal_amount = st.number_input("Target (Rs.)",
        1000000,500000000,20000000,1000000,key="sb_gamt")
    goal_years = st.slider("Years to Goal",1,30,10,key="sb_gyrs")
    inflation  = st.slider("Inflation (%)",3,10,6,key="sb_infl")/100

    st.markdown("#### Select Assets")
    selected_assets = []
    with st.expander("Indices & ETFs", expanded=True):
        defaults = ["Nifty 50","Nifty Midcap","G-Sec Bond",
                    "Bharat Bond 2030","Gold ETF","REIT"]
        for a in INDEX_UNIVERSE:
            if st.checkbox(a, value=(a in defaults), key=f"cb_{a}"):
                selected_assets.append(a)
    with st.expander("Stocks — Nifty 500 (300+ stocks)"):
        SECTORS_SB = {
            "All": [],
            "Banking & Finance": ["Bank","Finance","Housing","PFC","REC","IDFC","Federal","Baroda","Canara","Punjab","Union"],
            "IT & Technology":   ["TCS","Infosys","HCL","Wipro","Tech Mahindra","LTI","Mphasis","Persistent","Coforge","Tata Elxsi","KPIT","Tanla","Mastek","Zensar","Birlasoft","Cyient","LTTS"],
            "FMCG & Consumer":   ["Hindustan","ITC","Nestle","Britannia","Dabur","Marico","Godrej","Tata Consumer","Varun","United","Emami"],
            "Auto & Ancillary":  ["Maruti","Tata Motors","Mahindra","Hero","Bajaj Auto","Eicher","TVS","Ashok","Bosch","MRF","Apollo Tyres","Exide","Motherson","Minda","Bharat Forge"],
            "Pharma & Health":   ["Sun","Reddys","Cipla","Divis","Biocon","Lupin","Aurobindo","Torrent","Alkem","Abbott","Apollo Hospitals","Fortis","Zydus","Laurus","Metropolis"],
            "Energy & Oil":      ["Reliance","ONGC","Coal","NTPC","Power Grid","Adani","Tata Power","BHEL","GAIL","IOC","BPCL","Petroleum","Torrent Power"],
            "Metals & Mining":   ["Tata Steel","JSW Steel","Hindalco","Vedanta","SAIL","NMDC","Jindal","APL Apollo","Hindzinc"],
            "Infra & Cap Goods": ["Larsen","Siemens","ABB","Havells","Voltas","Polycab","KEI","Cummins","Bharat Electronics","HAL","IRCTC","Dixon","Crompton"],
            "Pharma & Chemicals":["Asian Paints","Berger","Pidilite","SRF","Aarti","PI Industries","UPL","Deepak","Navin","Astral","Coromandel","Chambal"],
            "New Age & Telecom": ["Zomato","Paytm","Nykaa","Delhivery","Info Edge","Indiamart","Bharti","Indus"],
            "Real Estate":       ["DLF","Godrej Properties","Oberoi","Prestige","Sobha","Brigade"],
        }
        sector_filter = st.selectbox(
            "Filter by sector", list(SECTORS_SB.keys()),
            key="sb_sector_filter"
        )
        if sector_filter == "All":
            display_stocks = list(STOCK_UNIVERSE.keys())
        else:
            kws = SECTORS_SB[sector_filter]
            display_stocks = [
                n for n in STOCK_UNIVERSE
                if any(k.lower() in n.lower() for k in kws)
            ]
        st.caption(f"{len(display_stocks)} stocks in {sector_filter}")
        for a in display_stocks:
            if st.checkbox(a, value=False, key=f"cb_{a}"):
                selected_assets.append(a)
    # Add custom stocks from search
    if "custom_assets" in st.session_state:
        for a in st.session_state["custom_assets"]:
            if a not in selected_assets:
                selected_assets.append(a)
                st.sidebar.caption(f"+ {a} (custom)")

    # Always ensure minimum default assets are included
    default_always = ["Nifty 50", "Nifty Midcap", "Gold ETF",
                      "G-Sec Bond", "Bharat Bond 2030", "REIT"]
    for a in default_always:
        if a not in selected_assets:
            selected_assets.append(a)

    st.markdown("#### Risk Profile (Q1-10)")
    QUESTIONS = [
        ("Horizon?",
         ["<1yr(1)","1-3yr(2)","3-5yr(3)","5-10yr(4)",">10yr(5)"]),
        ("Emergency fund?",
         ["None(1)","1-3mo(2)","3-6mo(4)",">6mo(5)"]),
        ("Income?",
         ["Irregular(1)","Business(2)","Salaried(3)","Govt(4)","Multiple(5)"]),
        ("Obligations?",
         [">70%(1)","50-70%(2)","30-50%(3)","10-30%(4)","<10%(5)"]),
        ("Drop 25%?",
         ["Sell all(1)","Sell most(2)","Hold(3)","Hold+buy(4)","Buy more(5)"]),
        ("Max loss?",
         ["None(1)","<5%(2)","5-15%(3)","15-30%(4)",">30%(5)"]),
        ("Emotional?",
         ["Severe(1)","High(2)","Moderate(3)","Low(4)","Minimal(5)"]),
        ("Experience?",
         ["FDs(1)","MF SIP(2)","MF+eq(3)","Deriv(4)","PMS(5)"]),
        ("Knowledge?",
         ["None(1)","Basic(2)","Moderate(3)","Good(4)","Expert(5)"]),
        ("REITs/ETFs?",
         ["Never(1)","Heard(2)","1of3(3)","2of3(4)","All3(5)"]),
    ]
    scores = []
    for i,(q,opts) in enumerate(QUESTIONS,1):
        ans = st.selectbox(f"Q{i}. {q}", opts, key=f"rq{i}")
        scores.append(int(ans.split("(")[1].replace(")","").strip()))

    total_score = sum(scores)
    pct = total_score/50
    if   pct<=0.25: pid=1
    elif pct<=0.42: pid=2
    elif pct<=0.60: pid=3
    elif pct<=0.78: pid=4
    else:           pid=5

    st.markdown(f"**Score: {total_score}/50**")
    st.markdown(
        f'<div style="display:inline-block;padding:4px 12px;'
        f'border-radius:16px;font-size:12px;font-weight:600;'
        f'background:{PROFILE_COLORS[pid]}22;'
        f'color:{PROFILE_COLORS[pid]};'
        f'border:1px solid {PROFILE_COLORS[pid]};">'
        f'{PROFILE_NAMES[pid]}</div>',
        unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("Loading market data..."):
    result = load_data(tuple(sorted(selected_assets)))

daily_returns, ann_returns, cov, assets, prices = result

if daily_returns is None:
    # Force load with default assets regardless of sidebar selection
    fallback = ["Nifty 50","Nifty Midcap","Gold ETF",
                "G-Sec Bond","Bharat Bond 2030","REIT"]
    result = load_data(tuple(sorted(fallback)))
    daily_returns, ann_returns, cov, assets, prices = result
    if daily_returns is None:
        st.error("Could not load data. Check internet connection.")
        st.stop()

n         = len(assets)
RISK_FREE = 0.065
DATA_DATE = prices.index[-1].strftime("%d %b %Y")
name_disp = client_name.strip() if client_name.strip() else "there"

# ═══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:10px 0 8px;border-bottom:1px solid #21262d;margin-bottom:14px;">
    <span style="font-size:20px;font-weight:800;
                 background:linear-gradient(135deg,#3fb950,#58a6ff);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        WealthPy Labs
    </span>
    <span style="font-size:12px;color:#555;">
        Hi <b style="color:#3fb950;">{name_disp}</b> |
        Age {age} | {city} |
        <b style="color:{PROFILE_COLORS[pid]};">{PROFILE_NAMES[pid]}</b> |
        Live: <b style="color:#3fb950;">{DATA_DATE}</b> |
        {n} assets loaded
    </span>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 Portfolio Builder",
    "📡 Live Tracker",
    "🔍 Stock Search",
    "📉 Charts & TA",
    "📂 Rebalancing",
    "💰 Tax",
    "📖 Glossary",
    "🏆 Benchmarks",
    "🧮 Factor",
    "📈 Efficient Frontier",
    "🌍 Scenarios",
    "⚡ Stress Test",
    "🔮 Monte Carlo",
    "⚙️ Backtester",
    "🔄 Walk-Forward",
])
(tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10,tab11,tab12,tab13,tab14,tab15) = tabs
# ── TAB 1 — Portfolio Builder ────────────────────────────────────────────────
with tab1:
    import pandas as pd
    active_weights, active_metrics = render_portfolio_builder(
        daily_returns, ann_returns, cov, assets, prices, pid,
        ASSET_UNIVERSE, total_investable, monthly_sip,
        annual_topup, goal_amount, goal_years, inflation, name_disp
    )

# Read shared portfolio from session state — used by ALL tabs
w_raw = st.session_state.get("active_weights", [1/n]*n)
port_weights = np.array(w_raw)
if len(port_weights) != n:
    port_weights = np.array([1/n]*n)
port_weights = port_weights / port_weights.sum()
m = st.session_state.get("active_metrics", {
    "return":0.12,"vol":0.15,"sharpe":0.5,
    "sortino":0.6,"beta":0.8,"alpha":2.0,
    "max_dd":-15.0,"var95":-1.5
})
port = {**m, "weights": port_weights, "name": PROFILE_NAMES[pid]}

# ── TAB 2 — Live Tracker ─────────────────────────────────────────────────────
with tab2:
    render_realtime_tab(assets, port_weights, total_investable)

# ── TAB 3 — Stock Search ─────────────────────────────────────────────────────
with tab3:
    st.markdown("#### NSE / BSE Stock Search")
    st.caption("Search and add any stock. Tick it in the sidebar to include in portfolio.")
    custom_assets = st.session_state.get("custom_assets", [])
    custom_au     = st.session_state.get("custom_asset_universe", {})
    updated_assets, updated_au = render_stock_search(custom_assets, custom_au)
    st.session_state["custom_assets"]         = updated_assets
    st.session_state["custom_asset_universe"] = updated_au
    if updated_assets:
        st.info(f"Added: {', '.join(updated_assets)}. Tick them in sidebar to include in portfolio.")

# ── TAB 4 — Charts & TA ──────────────────────────────────────────────────────
with tab4:
    render_charts_tab()

# ── TAB 5 — Rebalancing ──────────────────────────────────────────────────────
with tab5:
    st.markdown("#### Rebalancing")
    st.caption("Enter current holdings. Target = your Tab 1 portfolio.")
    inp = st.columns(3); uv = {}
    for i, a in enumerate(assets):
        uv[a] = inp[i%3].number_input(
            a, 0, int(1e9),
            int(port_weights[i]*total_investable),
            step=10000, key=f"h_{a}")
    tp = sum(uv.values())
    if tp > 0:
        cw = {a: v/tp for a,v in uv.items()}
        tw = dict(zip(assets, port_weights))
        st.markdown(f"**Total: Rs.{tp:,.0f}**")
        gr = []
        for a in assets:
            c = cw[a]*100; t = tw[a]*100; g = c-t
            act = "TRIM" if g>3 else "ADD" if g<-3 else "HOLD"
            gr.append({
                "Asset": a, "Current %": f"{c:.1f}%",
                "Target %": f"{t:.1f}%", "Gap": f"{g:+.1f}%",
                "Action": act,
                "Amount": f"{'Sell' if act=='TRIM' else 'Buy' if act=='ADD' else 'Hold'} Rs.{abs(g/100)*tp:,.0f}"
            })
        st.dataframe(pd.DataFrame(gr), hide_index=True, use_container_width=True)
        if any(r["Action"] != "HOLD" for r in gr):
            st.warning("Rebalancing recommended.")
        else:
            st.success("Portfolio aligned with target.")
        fig_rb = go.Figure()
        fig_rb.add_trace(go.Bar(x=assets, y=[cw[a]*100 for a in assets],
            name="Current",
            marker_color=["#f85149" if cw[a]>tw[a]+0.03
                          else "#3fb950" if cw[a]<tw[a]-0.03
                          else "#555" for a in assets], opacity=0.85))
        fig_rb.add_trace(go.Bar(x=assets, y=[tw[a]*100 for a in assets],
            name="Target (Tab 1)", marker_color="#58a6ff", opacity=0.65))
        fig_rb.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#161b22",
            font_color="white", barmode="group", xaxis_tickangle=-30,
            yaxis_title="Weight (%)", height=350,
            margin=dict(t=10,b=80,l=50,r=20),
            legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_rb, use_container_width=True)

# ── TAB 6 — Tax ──────────────────────────────────────────────────────────────
with tab6:
    st.markdown("#### Tax Optimisation — FY2024-25")
    st.caption("Tax calculated on YOUR Tab 1 portfolio.")
    st.info("Equity LTCG 12.5% above Rs.1.25L | Debt/Gold at slab rate | SGB tax-free at 8yr")
    TAX_RULES = {
        "Equity":   {"stcg":0.20,"ltcg":0.125,"ex":125000,"mo":12},
        "Gold ETF": {"stcg":None,"ltcg":None,  "ex":0,     "mo":12},
        "Debt MF":  {"stcg":None,"ltcg":None,  "ex":0,     "mo":36},
    }
    def calc_tax(a, pd_, pp, cp, un, sl, lu=0):
        cat = TAX_CAT.get(ASSET_UNIVERSE.get(a,("","Equity-LC"))[1], "Equity")
        r   = TAX_RULES.get(cat, TAX_RULES["Equity"])
        g   = (cp-pp)*un
        mh  = (date.today().year-pd_.year)*12+(date.today().month-pd_.month)
        is_lt = mh >= r["mo"]
        if cat == "Equity":
            tx = (max(0,g)*r["stcg"] if not is_lt
                  else max(0,g-max(0,r["ex"]-lu))*r["ltcg"])
        else:
            tx = max(0,g)*sl
        return {"gross":round(g,2),"tax":round(tx,2),"post":round(g-tx,2),
                "type":"LTCG" if is_lt else "STCG",
                "eff":round(tx/g*100 if g>0 else 0,1)}
    tx1,tx2,tx3 = st.columns(3)
    ti  = tx1.number_input("Invested (Rs.)", value=int(total_investable), step=100000, key="txi")
    yh  = tx2.slider("Years held", 1, 10, 3, key="tyh")
    sl  = tx3.selectbox("Tax slab", ["5%","10%","20%","30%"], index=3, key="tsl")
    slr = int(sl.replace("%",""))/100
    pd_ = date.today()-timedelta(days=365*yh)
    ARET = {a: float(ann_returns[a]) for a in assets}
    hc = {a: {"u": ti*port_weights[assets.index(a)]/100,
               "pp": 100.0, "cp": 100*(1+ARET[a])**yh}
          for a in assets}
    def rsc(fr):
        tg=tt=tp_=lu=0.0; rows=[]
        for a,f in fr.items():
            if f==0 or a not in hc: continue
            h = hc[a]
            r = calc_tax(a,pd_,h["pp"],h["cp"],h["u"]*f,slr,lu)
            if r["type"]=="LTCG": lu = min(125000,lu+r["gross"])
            rows.append({"Asset":a,**r})
            tg+=r["gross"]; tt+=r["tax"]; tp_+=r["post"]
        return rows,round(tg),round(tt),round(tp_),round(tt/tg*100 if tg>0 else 0,1)
    eq_a = [a for a in assets
            if TAX_CAT.get(ASSET_UNIVERSE.get(a,("","Equity-LC"))[1],"Equity")=="Equity"]
    sc_a = rsc({a:1.0  for a in assets})
    sc_b = rsc({a:(0.15 if a in eq_a else 0.0) for a in assets})
    sc_c = rsc({a:1/12 for a in assets})
    tx_df = pd.DataFrame([
        {"Scenario":"Full Exit",   "Tax":f"Rs.{sc_a[2]:,}","Rate":f"{sc_a[4]}%","Saved":"—"},
        {"Scenario":"Trim 15%",    "Tax":f"Rs.{sc_b[2]:,}","Rate":f"{sc_b[4]}%",
         "Saved":f"Rs.{sc_a[2]-sc_b[2]:,}"},
        {"Scenario":"Staged/12mo","Tax":f"Rs.{sc_c[2]:,}","Rate":f"{sc_c[4]}%",
         "Saved":f"Rs.{sc_a[2]-sc_c[2]:,}"},
    ])
    st.dataframe(tx_df, hide_index=True, use_container_width=True)
    st.success(f"Staging exit saves Rs.{sc_a[2]-sc_c[2]:,} in tax vs full exit today.")
    rdf = pd.DataFrame(sc_a[0])[["Asset","gross","tax","post","type","eff"]]
    rdf.columns = ["Asset","Gross","Tax","Post-Tax","Type","Eff.%"]
    for c in ["Gross","Tax","Post-Tax"]:
        rdf[c] = rdf[c].apply(lambda x: f"Rs.{x:,.0f}")
    st.dataframe(rdf, hide_index=True, use_container_width=True)

# ── TAB 7 — Glossary ─────────────────────────────────────────────────────────
with tab7:
    glossary_page()

# ── TAB 8 — Benchmarks ───────────────────────────────────────────────────────
with tab8:
    render_benchmark_tab(
        daily_returns, assets, port_weights,
        {"return":m["return"],"vol":m["vol"],
         "sharpe":m["sharpe"],"max_dd":m["max_dd"]},
        PROFILE_NAMES[pid]
    )

# ── TAB 9 — Factor ───────────────────────────────────────────────────────────
with tab9:
    render_factor_tab(daily_returns, assets, port_weights, ann_returns)

# ── TAB 10 — Efficient Frontier ──────────────────────────────────────────────
with tab10:
    st.markdown("#### Efficient Frontier")
    st.caption("Your portfolio (star) vs 4,000 random portfolios. Update Tab 1 to move your position.")
    N_SIM=4000; np.random.seed(42)
    def p_ret(w): return float(np.dot(w,ann_returns.values))
    def p_vol(w): return float(np.sqrt(w@cov@w))
    sim_r=np.array([p_ret(np.random.dirichlet(np.ones(n))) for _ in range(N_SIM)])
    sim_v=np.array([p_vol(np.random.dirichlet(np.ones(n))) for _ in range(N_SIM)])
    sim_s=(sim_r-RISK_FREE)/sim_v
    fig_ef=go.Figure()
    fig_ef.add_trace(go.Scatter(x=sim_v*100,y=sim_r*100,mode="markers",
        marker=dict(color=sim_s,colorscale="Viridis",size=4,opacity=0.3,
                    colorbar=dict(title="Sharpe",thickness=12)),name="Portfolios"))
    fig_ef.add_trace(go.Scatter(
        x=[m["vol"]*100],y=[m["return"]*100],mode="markers+text",
        marker=dict(color="#3fb950",size=22,symbol="star",
                    line=dict(color="white",width=2)),
        text=["YOUR PORTFOLIO"],textposition="top right",
        textfont=dict(color="#3fb950",size=11),name="Your Portfolio"))
    for i,a in enumerate(assets):
        fig_ef.add_trace(go.Scatter(
            x=[np.sqrt(cov[i,i])*100],y=[ann_returns[a]*100],
            mode="markers+text",
            marker=dict(color="#aaa",size=7,symbol="diamond"),
            text=[a],textposition="top right",
            textfont=dict(color="#777",size=8),
            name=a,showlegend=False))
    fig_ef.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#161b22",
        font_color="white",xaxis_title="Volatility (%)",
        yaxis_title="Return (%)",height=500,
        margin=dict(t=20,b=40,l=50,r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_ef,use_container_width=True)

# ── TAB 11 — Scenarios ───────────────────────────────────────────────────────
with tab11:
    render_scenario_tab(assets, port_weights, total_investable, ann_returns)

# ── TAB 12 — Stress Test ─────────────────────────────────────────────────────
with tab12:
    st.markdown("#### Stress Testing")
    st.caption("Tests YOUR Tab 1 portfolio against historical crashes.")
    STRESS={"COVID (Feb-Mar 2020)":("2020-02-15","2020-03-23"),
            "2022 Rate Hike":("2022-01-01","2022-06-30"),
            "Russia-Ukraine 2022":("2022-02-24","2022-03-15")}
    sr=[]
    for sc,(s,e) in STRESS.items():
        try:
            mask=(daily_returns.index>=pd.Timestamp(s))&(daily_returns.index<=pd.Timestamp(e))
            sc_r=daily_returns[mask]
            if len(sc_r)<3: raise ValueError
            pd_r=(np.prod(1+sc_r.values@port_weights)-1)*100
            n50=0.0
            if "Nifty 50" in assets:
                ni=assets.index("Nifty 50")
                n50=(np.prod(1+sc_r.iloc[:,ni].values)-1)*100
            sr.append({"Scenario":sc,"Your Portfolio":f"{pd_r:.1f}%",
                       "Nifty 50":f"{n50:.1f}%","Outperformance":f"{pd_r-n50:+.1f}%",
                       "Rs. Impact":f"Rs.{total_investable*pd_r/100:+,.0f}"})
        except Exception:
            sr.append({"Scenario":sc,"Your Portfolio":"N/A","Nifty 50":"N/A",
                       "Outperformance":"N/A","Rs. Impact":"N/A"})
    st.dataframe(pd.DataFrame(sr),hide_index=True,use_container_width=True)
    pr_all=daily_returns.values@port_weights
    cum=np.cumprod(1+pr_all); rm=np.maximum.accumulate(cum); dd=(cum-rm)/rm*100
    fig_dd=go.Figure()
    fig_dd.add_trace(go.Scatter(x=daily_returns.index.tolist(),y=dd.tolist(),
        fill="tozeroy",name="Your Portfolio",line_color="#f85149",
        fillcolor="rgba(248,81,73,0.25)"))
    if "Nifty 50" in assets:
        ni=assets.index("Nifty 50")
        n50c=np.cumprod(1+daily_returns.iloc[:,ni].values)
        n50rm=np.maximum.accumulate(n50c); n50dd=(n50c-n50rm)/n50rm*100
        fig_dd.add_trace(go.Scatter(x=daily_returns.index.tolist(),
            y=n50dd.tolist(),name="Nifty 50",line_color="#58a6ff"))
    fig_dd.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#161b22",
                          font_color="white",height=320,
                          margin=dict(t=20,b=40,l=50,r=20),
                          legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_dd,use_container_width=True)

# ── TAB 13 — Monte Carlo ─────────────────────────────────────────────────────
with tab13:
    st.markdown("#### Monte Carlo Simulation")
    st.caption("Uses your Tab 1 portfolio.")
    mc_yr=st.slider("Horizon",1,30,goal_years,key="mc_yr")
    DAYS=mc_yr*252; N=1000
    mu=m["return"]/252; sig=m["vol"]/np.sqrt(252)
    np.random.seed(42)
    paths=np.zeros((N,DAYS+1)); paths[:,0]=total_investable
    for t in range(1,DAYS+1):
        paths[:,t]=paths[:,t-1]*(1+np.random.normal(mu,sig,N))
    fv=paths[:,-1]; xa=np.linspace(0,mc_yr,DAYS+1)
    mc1,mc2,mc3,mc4=st.columns(4)
    mc1.metric(f"Prob reach Rs.{goal_amount/1e6:.0f}M",f"{(fv>=goal_amount).mean()*100:.1f}%")
    mc2.metric("Prob 2x",f"{(fv>=total_investable*2).mean()*100:.1f}%")
    mc3.metric("Prob loss",f"{(fv<total_investable).mean()*100:.1f}%")
    mc4.metric("Median",f"Rs.{np.median(fv)/1e6:.2f}M")
    fig_mc=go.Figure()
    for i in range(min(150,N)):
        fig_mc.add_trace(go.Scatter(x=xa,y=paths[i]/1e6,mode="lines",
            line=dict(width=0.5,color="#3fb950" if paths[i,-1]>=goal_amount else "#f85149"),
            opacity=0.1,showlegend=False,hoverinfo="skip"))
    p10=np.percentile(paths,10,axis=0); p90=np.percentile(paths,90,axis=0)
    pmd=np.percentile(paths,50,axis=0)
    fig_mc.add_trace(go.Scatter(x=xa,y=p90/1e6,fill=None,mode="lines",
        line_color="rgba(255,152,0,0)",showlegend=False))
    fig_mc.add_trace(go.Scatter(x=xa,y=p10/1e6,fill="tonexty",mode="lines",
        line_color="rgba(255,152,0,0)",fillcolor="rgba(255,152,0,0.12)",name="80% range"))
    fig_mc.add_trace(go.Scatter(x=xa,y=pmd/1e6,mode="lines",
        line=dict(color="#3fb950",width=2.5),name="Median"))
    fig_mc.add_hline(y=goal_amount/1e6,line_dash="dash",line_color="white",
                     annotation_text=f"Goal Rs.{goal_amount/1e6:.1f}M")
    fig_mc.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#161b22",
                          font_color="white",height=420,
                          margin=dict(t=20,b=40,l=50,r=20),
                          legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_mc,use_container_width=True)
    lump_g=total_investable*(1+m["return"])**goal_years
    rem=max(0,goal_amount-lump_g); mo_r2=m["return"]/12; mo2=goal_years*12
    req=(rem*mo_r2/((1+mo_r2)**mo2-1) if mo_r2>0 and rem>0 and mo2>0 else 0)
    gs1,gs2,gs3=st.columns(3)
    gs1.metric("Lump sum at goal",f"Rs.{lump_g/1e6:.2f}M")
    gs2.metric("Gap via SIP",f"Rs.{rem/1e6:.2f}M")
    gs3.metric("Required SIP",f"Rs.{req:,.0f}/month")
    if monthly_sip>0:
        if monthly_sip>=req: st.success(f"Your SIP of Rs.{monthly_sip:,.0f} is sufficient!")
        else: st.warning(f"Increase SIP by Rs.{req-monthly_sip:,.0f} to reach goal.")

# ── TAB 14 — Backtester ──────────────────────────────────────────────────────
with tab14:
    render_backtester_tab()

# ── TAB 15 — Walk-Forward ────────────────────────────────────────────────────
with tab15:
    render_walkforward_tab()


st.markdown("---")
st.caption("WealthPy Labs | Built by Samayak Jain | samayakpjain@gmail.com | Educational only | Consult SEBI advisor before investing")
