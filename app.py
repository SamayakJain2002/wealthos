# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy import stats
from datetime import date, timedelta
import plotly.graph_objects as go
import warnings
from realtime import render_realtime_tab
from factor import render_factor_tab
from benchmark import render_benchmark_tab
from scenario import render_scenario_tab
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="WealthOS - HNI Advisory",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.section-header {
    font-size: 16px; font-weight: 600; color: #e0e0ff;
    border-bottom: 1px solid #2a2a4a;
    padding-bottom: 5px; margin: 14px 0 8px;
}
.insight-box {
    background: #0d1f0d; border-left: 3px solid #4CAF50;
    padding: 8px 12px; border-radius: 0 6px 6px 0;
    margin: 6px 0; font-size: 12px; color: #b0c4b0;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ASSET UNIVERSE
# ═══════════════════════════════════════════════════════════════════════════════
INDEX_UNIVERSE = {
    "Nifty 50":           ("^NSEI",          "Equity-LC"),
    "Nifty Midcap":       ("^NSMIDCP",       "Equity-MC"),
    "Nifty Smallcap":     ("^CNXSC",         "Equity-SC"),
    "Nifty IT":           ("^CNXIT",         "Sectoral"),
    "Nifty Pharma":       ("^CNXPHARMA",     "Sectoral"),
    "Nifty Bank":         ("^NSEBANK",       "Sectoral"),
    "Nifty Energy":       ("^CNXENERGY",     "Sectoral"),
    "Nifty Auto":         ("^CNXAUTO",       "Sectoral"),
    "Nasdaq 100 ETF":     ("MOTI0100.NS",    "Intl-Eq"),
    "G-Sec Bond":         ("LIQUIDBEES.NS",  "Debt-Sov"),
    "Bharat Bond 2030":   ("CPSEETF.NS",     "Debt-TM"),
    "Gold ETF":           ("GOLDBEES.NS",    "Gold"),
    "REIT":               ("EMBASSY.NS",     "REIT"),
    "Silver ETF":         ("SILVERETF.NS",   "Silver"),
}

STOCK_UNIVERSE = {
    "HDFC Bank":    ("HDFCBANK.NS",   "Stock-Bank"),
    "ICICI Bank":   ("ICICIBANK.NS",  "Stock-Bank"),
    "TCS":          ("TCS.NS",        "Stock-IT"),
    "Infosys":      ("INFY.NS",       "Stock-IT"),
    "Reliance":     ("RELIANCE.NS",   "Stock-Energy"),
    "HUL":          ("HINDUNILVR.NS", "Stock-FMCG"),
    "ITC":          ("ITC.NS",        "Stock-FMCG"),
    "Sun Pharma":   ("SUNPHARMA.NS",  "Stock-Pharma"),
    "Maruti":       ("MARUTI.NS",     "Stock-Auto"),
    "L&T":          ("LT.NS",         "Stock-Infra"),
    "Tata Steel":   ("TATASTEEL.NS",  "Stock-Metal"),
    "Bajaj Finance":("BAJFINANCE.NS", "Stock-Finance"),
    "Axis Bank":    ("AXISBANK.NS",   "Stock-Bank"),
    "Wipro":        ("WIPRO.NS",      "Stock-IT"),
    "NTPC":         ("NTPC.NS",       "Stock-Energy"),
    "Tata Motors":  ("TATAMOTORS.NS", "Stock-Auto"),
    "Zomato":       ("ZOMATO.NS",     "Stock-Consumer"),
    "IRCTC":        ("IRCTC.NS",      "Stock-Infra"),
    "Dr. Reddys":   ("DRREDDY.NS",    "Stock-Pharma"),
    "JSW Steel":    ("JSWSTEEL.NS",   "Stock-Metal"),
}

ASSET_UNIVERSE = {**INDEX_UNIVERSE, **STOCK_UNIVERSE}

TAX_CAT = {
    "Equity-LC":"Equity","Equity-MC":"Equity","Equity-SC":"Equity",
    "Sectoral":"Equity","Intl-Eq":"Equity",
    "Debt-Sov":"Debt MF","Debt-TM":"Debt MF",
    "Gold":"Gold ETF","Silver":"Gold ETF","REIT":"Equity",
    "Stock-Bank":"Equity","Stock-IT":"Equity","Stock-Finance":"Equity",
    "Stock-FMCG":"Equity","Stock-Auto":"Equity","Stock-Pharma":"Equity",
    "Stock-Energy":"Equity","Stock-Infra":"Equity","Stock-Metal":"Equity",
    "Stock-Consumer":"Equity",
}

PROFILE_NAMES  = {1:"Conservative",2:"Mod. Conservative",
                  3:"Balanced",4:"Mod. Aggressive",5:"Aggressive"}
PROFILE_COLORS = {1:"#2196F3",2:"#4CAF50",3:"#FF9800",4:"#FF5722",5:"#9C27B0"}

# ═══════════════════════════════════════════════════════════════════════════════
# FAST DATA LOADER — downloads all tickers in ONE batch call
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400, show_spinner=False)
def load_data_fast(selected_tuple):
    import yfinance as yf
    selected = list(selected_tuple)
    ticker_map = {ASSET_UNIVERSE[a][0]: a for a in selected}
    tickers    = list(ticker_map.keys())

    END   = date.today().strftime("%Y-%m-%d")
    START = "2020-01-01"   # 4 years — faster than 5, still statistically valid

    # Download ALL tickers in a single batch call — 10x faster than loop
    raw = yf.download(tickers, start=START, end=END,
                      auto_adjust=True, progress=False, threads=True)

    if raw.empty:
        return None, None, None, [], pd.DataFrame(), selected

    # Extract Close prices
    if isinstance(raw.columns, pd.MultiIndex):
        try:
            close = raw["Close"]
        except KeyError:
            return None, None, None, [], pd.DataFrame(), selected
    else:
        close = raw[["Close"]] if "Close" in raw.columns else raw

    # Rename columns from ticker to asset name
    close = close.rename(columns=ticker_map)
    # Keep only selected assets that loaded
    valid_cols = [c for c in close.columns if c in selected and close[c].notna().sum() > 100]
    close = close[valid_cols].ffill().bfill().dropna(how="all")

    if len(valid_cols) < 2:
        return None, None, None, [], pd.DataFrame(), selected

    prices        = close
    daily_returns = prices.pct_change().dropna()

    # Fix gold scaling
    for col in daily_returns.columns:
        cat = ASSET_UNIVERSE.get(col, ("",""))[1]
        if cat in ("Gold","Silver") and daily_returns[col].std() > 0.05:
            daily_returns[col] = daily_returns[col] / 100

    TDAYS       = 252
    ann_returns = daily_returns.mean() * TDAYS
    cov         = daily_returns.cov().values * TDAYS
    assets      = list(ann_returns.index)
    failed      = [a for a in selected if a not in assets]
    return daily_returns, ann_returns, cov, assets, prices, failed

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
st.sidebar.title("WealthOS")

st.sidebar.markdown("### Client")
client_name = st.sidebar.text_input("Name", placeholder="Samayak Jain")
client_age  = st.sidebar.number_input("Age", 18, 80, 28)
client_city = st.sidebar.text_input("City", placeholder="Mumbai")

st.sidebar.markdown("### Financials")
total_investable = st.sidebar.number_input(
    "Investable Amount (Rs.)", 100000, 500000000, 5000000, 100000)
monthly_sip  = st.sidebar.number_input("Monthly SIP (Rs.)", 0, 10000000, 50000, 5000)
annual_topup = st.sidebar.number_input("Annual Top-up (Rs.)", 0, 50000000, 500000, 50000)
inv_goal     = st.sidebar.selectbox("Goal", [
    "Retirement corpus","Child education","Home purchase",
    "Wealth creation","Regular income","Tax saving","Wedding fund"])
goal_amount  = st.sidebar.number_input("Target (Rs.)", 1000000, 500000000, 20000000, 1000000)
goal_years   = st.sidebar.slider("Years to Goal", 1, 30, 10)
inflation    = st.sidebar.slider("Inflation (%)", 3, 10, 6) / 100

st.sidebar.markdown("### Assets")
st.sidebar.caption("Select assets to include in optimisation")

selected_assets = []

with st.sidebar.expander("Indices", expanded=True):
    defaults = ["Nifty 50","Nifty Midcap","G-Sec Bond","Bharat Bond 2030","Gold ETF","REIT"]
    for a in INDEX_UNIVERSE:
        if st.checkbox(a, value=(a in defaults), key=f"cb_{a}"):
            selected_assets.append(a)

with st.sidebar.expander("Stocks (Nifty 200)"):
    for a in STOCK_UNIVERSE:
        if st.checkbox(a, value=False, key=f"cb_{a}"):
            selected_assets.append(a)

if len(selected_assets) < 2:
    selected_assets = ["Nifty 50","Gold ETF","G-Sec Bond","Bharat Bond 2030","REIT"]

st.sidebar.markdown("### Risk Profile")
QUESTIONS = [
    ("Investment horizon?",
     ["< 1 year (1)","1-3 years (2)","3-5 years (3)","5-10 years (4)","> 10 years (5)"]),
    ("Emergency fund?",
     ["None (1)","1-3 months (2)","3-6 months (4)","> 6 months (5)"]),
    ("Income source?",
     ["Irregular (1)","Business (2)","Salaried (3)","Govt (4)","Multiple (5)"]),
    ("Fixed obligations?",
     ["> 70% (1)","50-70% (2)","30-50% (3)","10-30% (4)","< 10% (5)"]),
    ("Portfolio drops 25%?",
     ["Sell all (1)","Sell most (2)","Hold (3)","Hold+buy (4)","Buy more (5)"]),
    ("Max annual loss?",
     ["None (1)","< 5% (2)","5-15% (3)","15-30% (4)","> 30% (5)"]),
    ("Emotional impact?",
     ["Severe (1)","High (2)","Moderate (3)","Low (4)","Minimal (5)"]),
    ("Experience?",
     ["FDs (1)","MF SIP (2)","MF+equity (3)","Derivatives (4)","PMS/AIF (5)"]),
    ("Market knowledge?",
     ["None (1)","Basic (2)","Moderate (3)","Good (4)","Expert (5)"]),
    ("REITs/SGBs/ETFs?",
     ["Never (1)","Heard (2)","1 of them (3)","2 of them (4)","All 3 (5)"]),
]
scores = []
for i,(q,opts) in enumerate(QUESTIONS,1):
    ans = st.sidebar.selectbox(f"Q{i}. {q}", opts, key=f"rq{i}")
    scores.append(int(ans.split("(")[1].replace(")","").strip()))

total_score = sum(scores)
pct = total_score/50
if   pct<=0.25: pid=1
elif pct<=0.42: pid=2
elif pct<=0.60: pid=3
elif pct<=0.78: pid=4
else:           pid=5

st.sidebar.markdown(f"**Score: {total_score}/50 — {PROFILE_NAMES[pid]}**")

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("Loading market data..."):
    daily_returns, ann_returns, cov, assets, prices, failed = load_data_fast(
        tuple(sorted(selected_assets)))

if daily_returns is None or len(assets) < 2:
    st.error("Not enough data loaded. Please select more assets.")
    st.stop()

n         = len(assets)
RISK_FREE = 0.065
DATA_DATE = prices.index[-1].strftime("%d %b %Y")

# ═══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def port_ret(w):   return float(np.dot(w, ann_returns.values))
def port_vol(w):   return float(np.sqrt(w @ cov @ w))
def neg_sharpe(w): return -(port_ret(w)-RISK_FREE)/port_vol(w)

def port_beta(w):
    if "Nifty 50" not in assets: return 1.0
    idx = assets.index("Nifty 50")
    pr  = daily_returns.values @ w
    nr  = daily_returns.iloc[:,idx].values
    ml  = min(len(pr),len(nr))
    s,_,_,_,_ = stats.linregress(nr[:ml],pr[:ml])
    return round(s,3)

def port_alpha(w):
    if "Nifty 50" not in assets: return 0.0
    idx = assets.index("Nifty 50")
    b   = port_beta(w)
    return round((port_ret(w)-(RISK_FREE+b*(float(ann_returns.iloc[idx])-RISK_FREE)))*100,2)

def port_sortino(w):
    pr = daily_returns.values @ w
    dn = pr[pr < RISK_FREE/252]
    if len(dn)==0: return 9.99
    ds = np.std(dn)*np.sqrt(252)
    return round((port_ret(w)-RISK_FREE)/ds,3) if ds>0 else 9.99

def port_maxdd(w):
    cum = np.cumprod(1+daily_returns.values@w)
    rm  = np.maximum.accumulate(cum)
    return round(((cum-rm)/rm).min()*100,2)

def port_var(w):
    return round(np.percentile(daily_returns.values@w,5)*100,2)

def get_bounds(pid_l, asset_list):
    is_stock = lambda a: ASSET_UNIVERSE.get(a,("",""))[1].startswith("Stock-")
    is_debt  = lambda a: ASSET_UNIVERSE.get(a,("",""))[1] in ("Debt-Sov","Debt-TM","Liquid")
    is_gold  = lambda a: ASSET_UNIVERSE.get(a,("",""))[1] in ("Gold","Silver")
    is_alt   = lambda a: ASSET_UNIVERSE.get(a,("",""))[1] in ("REIT","InvIT")

    eq_bud  = {1:0.10,2:0.28,3:0.52,4:0.68,5:0.82}[pid_l]
    stk_bud = {1:0.02,2:0.05,3:0.10,4:0.15,5:0.20}[pid_l]
    db_bud  = {1:0.72,2:0.52,3:0.32,4:0.18,5:0.08}[pid_l]

    n_eq  = max(sum(1 for a in asset_list if not is_stock(a) and not is_debt(a) and not is_gold(a) and not is_alt(a)),1)
    n_stk = max(sum(1 for a in asset_list if is_stock(a)),1)
    n_db  = max(sum(1 for a in asset_list if is_debt(a)),1)
    n_gl  = max(sum(1 for a in asset_list if is_gold(a)),1)

    bounds=[]
    for a in asset_list:
        if is_stock(a):
            bounds.append((0.0, min(stk_bud/n_stk*3, 0.12)))
        elif is_debt(a):
            bounds.append((0.01, min(db_bud/n_db*2, 0.60)))
        elif is_gold(a):
            bounds.append((0.01, min(0.12/n_gl*2, 0.18)))
        elif is_alt(a):
            bounds.append((0.0, 0.10))
        else:
            bounds.append((0.0, min(eq_bud/n_eq*2.5, 0.45)))
    return bounds

@st.cache_data(show_spinner=False)
def get_portfolios(assets_key, pid_l):
    ports={}; w0=np.array([1/n]*n)
    cons={"type":"eq","fun":lambda w: np.sum(w)-1}
    for p in range(1,6):
        try:
            res=minimize(neg_sharpe,w0,method="SLSQP",
                         bounds=get_bounds(p,assets),constraints=cons,
                         options={"maxiter":500,"ftol":1e-7})
            w=res.x
        except Exception:
            w=w0.copy()
        r=port_ret(w); v=port_vol(w)
        ports[p]={"weights":w,"name":PROFILE_NAMES[p],
                  "return":r,"vol":v,"sharpe":(r-RISK_FREE)/v,
                  "sortino":port_sortino(w),"beta":port_beta(w),
                  "alpha":port_alpha(w),"max_dd":port_maxdd(w),
                  "var95":port_var(w)}
    return ports

model_portfolios = get_portfolios(tuple(assets), pid)
port = model_portfolios[pid]

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
name_disp = client_name.strip() if client_name.strip() else "there"
st.title(f"Hi, {name_disp}! — WealthOS")
st.caption(
    f"{client_city+' | ' if client_city.strip() else ''}Age {client_age} | "
    f"{inv_goal} in {goal_years}yr | Live: {DATA_DATE} | "
    f"{n} assets{' | Failed: '+', '.join(failed) if failed else ''}"
)

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric("Profile",    PROFILE_NAMES[pid])
c2.metric("Return",     f"{port['return']*100:.1f}%")
c3.metric("Volatility", f"{port['vol']*100:.1f}%")
c4.metric("Sharpe",     f"{port['sharpe']:.2f}")
c5.metric("Sortino",    f"{port['sortino']:.2f}")
c6.metric("Max DD",     f"{port['max_dd']:.1f}%")
c7.metric("Alpha",      f"{port['alpha']:.2f}%")
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9,tab10 = st.tabs([
    "📊 Allocation",
    "📈 Frontier & Comparison",
    "🔮 Monte Carlo",
    "⚡ Stress Test",
    "📂 Rebalancing",
    "💰 Tax + Recommendations",
    "📡 Live Tracker",
    "🧮 Factor Exposure",
    "🌍 Scenario Analysis",
    "🏆 Peer Benchmarking",
])

# ── TAB 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    col_a,col_b = st.columns([1,1])
    with col_a:
        st.markdown("**Allocation Table**")
        rows=[]
        for i,a in enumerate(assets):
            w=port["weights"][i]
            if w>0.003:
                rows.append({"Asset":a,
                             "Weight":f"{w*100:.1f}%",
                             "Amount":f"Rs.{w*total_investable:,.0f}",
                             "Ann.Ret":f"{ann_returns[a]*100:.1f}%",
                             "Category":ASSET_UNIVERSE.get(a,("","Unknown"))[1]})
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)

    with col_b:
        nz=[(port["weights"][i],a) for i,a in enumerate(assets) if port["weights"][i]>0.005]
        ws=[x[0] for x in nz]; lbls=[x[1] for x in nz]
        fig_p,ax_p=plt.subplots(figsize=(5,4),facecolor="#0e0e1a")
        ax_p.pie(ws,labels=lbls,autopct="%1.0f%%",
                 textprops={"color":"white","fontsize":7},
                 wedgeprops={"linewidth":0.5,"edgecolor":"#0e0e1a"})
        ax_p.set_facecolor("#0e0e1a")
        ax_p.set_title(PROFILE_NAMES[pid],color="white",fontsize=10)
        st.pyplot(fig_p); plt.close()

    st.markdown("**Asset Statistics**")
    stat_rows=[]
    one_yr=pd.Timestamp(date.today()-timedelta(days=365))
    for i,a in enumerate(assets):
        try:
            r1y=(prices[a].iloc[-1]/prices[a].asof(one_yr)-1)*100
        except Exception:
            r1y=0.0
        v=np.sqrt(cov[i,i])
        stat_rows.append({"Asset":a,
                          "Ann.Return":f"{ann_returns[a]*100:.1f}%",
                          "Volatility":f"{v*100:.1f}%",
                          "Sharpe":f"{(ann_returns[a]-RISK_FREE)/v:.2f}",
                          "1Y Return":f"{r1y:.1f}%",
                          "Signal":("Buy" if r1y>10 else "Hold" if r1y>0 else "Caution")})
    st.dataframe(pd.DataFrame(stat_rows),hide_index=True,use_container_width=True)

    st.markdown("**Wealth Accumulation**")
    ann_r=port["return"]; mo_r=ann_r/12; mo_tot=goal_years*12
    lf=total_investable*(1+ann_r)**goal_years
    sf=(monthly_sip*(((1+mo_r)**mo_tot-1)/mo_r) if mo_r>0 and monthly_sip>0 else 0)
    tf=(sum(annual_topup*(1+ann_r)**(goal_years-y) for y in range(1,goal_years+1))
        if annual_topup>0 else 0)
    total_f=lf+sf+tf
    total_i=total_investable+monthly_sip*mo_tot+annual_topup*goal_years

    wc1,wc2,wc3,wc4 = st.columns(4)
    wc1.metric("Lump Sum",  f"Rs.{lf/1e6:.2f}M")
    wc2.metric("SIP Corpus",f"Rs.{sf/1e6:.2f}M")
    wc3.metric("Top-up",    f"Rs.{tf/1e6:.2f}M")
    wc4.metric("Total Wealth",f"Rs.{total_f/1e6:.2f}M",
               delta=f"+Rs.{(total_f-total_i)/1e6:.2f}M gain")

    yr_r=list(range(goal_years+1))
    lv=[total_investable*(1+ann_r)**y for y in yr_r]
    sv=[(monthly_sip*(((1+mo_r)**(y*12)-1)/mo_r) if mo_r>0 and y>0 else 0) for y in yr_r]
    tv2=[(sum(annual_topup*(1+ann_r)**(y-yr) for yr in range(1,y+1)) if y>0 else 0) for y in yr_r]
    fig_w,ax_w=plt.subplots(figsize=(8,3),facecolor="#0e0e1a")
    ax_w.set_facecolor("#0e0e1a")
    ax_w.stackplot(yr_r,[v/1e6 for v in lv],[v/1e6 for v in sv],[v/1e6 for v in tv2],
                   labels=["Lump Sum","SIP","Top-up"],
                   colors=["#FF5722","#4CAF50","#2196F3"],alpha=0.8)
    ax_w.axhline(goal_amount/1e6,color="white",lw=1.2,linestyle="--",label="Goal")
    ax_w.set_xlabel("Year",color="white",fontsize=8)
    ax_w.set_ylabel("Rs. Million",color="white",fontsize=8)
    ax_w.tick_params(colors="white",labelsize=7)
    ax_w.legend(facecolor="#1a1a2e",labelcolor="white",fontsize=7)
    ax_w.grid(True,alpha=0.1,color="white")
    st.pyplot(fig_w); plt.close()

# ── TAB 2 ─────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("**Efficient Frontier**")
    st.caption("Each dot = one portfolio. Upper-left = best risk-adjusted return. White ring = your profile.")

    N_SIM=4000; np.random.seed(42)
    sim_r=np.zeros(N_SIM); sim_v=np.zeros(N_SIM)
    for i in range(N_SIM):
        w=np.random.dirichlet(np.ones(n))
        sim_r[i]=port_ret(w); sim_v[i]=port_vol(w)
    sim_s=(sim_r-RISK_FREE)/sim_v

    fig_ef,ax_ef=plt.subplots(figsize=(9,5.5),facecolor="#0e0e1a")
    ax_ef.set_facecolor("#0e0e1a")
    sc=ax_ef.scatter(sim_v*100,sim_r*100,c=sim_s,cmap="viridis",alpha=0.2,s=5)
    plt.colorbar(sc,ax=ax_ef,label="Sharpe",shrink=0.8)

    for p_id,p in model_portfolios.items():
        ax_ef.scatter(p["vol"]*100,p["return"]*100,
                      color=PROFILE_COLORS[p_id],
                      s=220 if p_id==pid else 70,zorder=5,
                      edgecolors="white" if p_id==pid else "none",linewidths=1.5)
        if p_id==pid:
            ax_ef.annotate(f" {p['name']}",
                           xy=(p["vol"]*100,p["return"]*100),
                           color=PROFILE_COLORS[p_id],fontsize=8,fontweight="bold")

    for i,a in enumerate(assets):
        ax_ef.scatter(np.sqrt(cov[i,i])*100,ann_returns[a]*100,
                      color="#aaa",s=25,marker="D",zorder=4,alpha=0.6)
        ax_ef.annotate(a,(np.sqrt(cov[i,i])*100,ann_returns[a]*100),
                       fontsize=5.5,color="#999",xytext=(2,1),textcoords="offset points")

    ax_ef.set_xlabel("Volatility (%)",color="white",fontsize=9)
    ax_ef.set_ylabel("Return (%)",    color="white",fontsize=9)
    ax_ef.tick_params(colors="white",labelsize=8)
    ax_ef.set_title(f"Efficient Frontier | {n} assets | {DATA_DATE}",
                    color="white",fontsize=10)
    ax_ef.grid(True,alpha=0.1,color="white")
    st.pyplot(fig_ef); plt.close()

    st.markdown("**All Profiles**")
    comp=[{"Profile":p["name"],
           "Return":f"{p['return']*100:.1f}%","Vol":f"{p['vol']*100:.1f}%",
           "Sharpe":f"{p['sharpe']:.3f}","Sortino":f"{p['sortino']:.3f}",
           "Beta":f"{p['beta']:.3f}","Alpha%":f"{p['alpha']:.2f}",
           "MaxDD":f"{p['max_dd']:.1f}%","VaR95":f"{p['var95']:.2f}%"}
          for p in model_portfolios.values()]
    st.dataframe(pd.DataFrame(comp),hide_index=True,use_container_width=True)

# ── TAB 3 ─────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("**Monte Carlo Simulation — 1,000 paths**")
    st.caption("Green = reaches goal | Red = falls short | Orange band = 80% of outcomes")

    mc_yr=st.slider("Horizon (years)",1,30,goal_years,key="mc_yr")
    DAYS=mc_yr*252; N=1000
    mu=port["return"]/252; sig=port["vol"]/np.sqrt(252)
    np.random.seed(42)
    paths=np.zeros((N,DAYS+1)); paths[:,0]=total_investable
    for t in range(1,DAYS+1):
        paths[:,t]=paths[:,t-1]*(1+np.random.normal(mu,sig,N))

    fv=paths[:,-1]
    mc1,mc2,mc3,mc4=st.columns(4)
    mc1.metric(f"Prob reach Rs.{goal_amount/1e6:.0f}M",
               f"{(fv>=goal_amount).mean()*100:.1f}%")
    mc2.metric("Prob 2x money",   f"{(fv>=total_investable*2).mean()*100:.1f}%")
    mc3.metric("Prob capital loss",f"{(fv<total_investable).mean()*100:.1f}%")
    mc4.metric("Median outcome",   f"Rs.{np.median(fv)/1e6:.2f}M")

    xa=np.linspace(0,mc_yr,DAYS+1)
    fig_mc,ax_mc=plt.subplots(figsize=(9,4.5),facecolor="#0e0e1a")
    ax_mc.set_facecolor("#0e0e1a")
    for i in range(min(150,N)):
        ax_mc.plot(xa,paths[i]/1e6,alpha=0.05,lw=0.5,
                   color="#4CAF50" if paths[i,-1]>=goal_amount else "#FF5722")
    p10=np.percentile(paths,10,axis=0); p90=np.percentile(paths,90,axis=0)
    pmd=np.percentile(paths,50,axis=0)
    ax_mc.fill_between(xa,p10/1e6,p90/1e6,alpha=0.15,color="#FF9800")
    ax_mc.plot(xa,pmd/1e6,color="#4CAF50",lw=2,label="Median")
    ax_mc.axhline(goal_amount/1e6,color="white",lw=1.2,linestyle="--",
                  label=f"Goal Rs.{goal_amount/1e6:.1f}M")
    ax_mc.set_xlabel("Years",color="white",fontsize=8)
    ax_mc.set_ylabel("Rs. Million",color="white",fontsize=8)
    ax_mc.tick_params(colors="white",labelsize=7)
    ax_mc.legend(facecolor="#1a1a2e",labelcolor="white",fontsize=8)
    ax_mc.grid(True,alpha=0.1,color="white")
    st.pyplot(fig_mc); plt.close()

    # Required SIP
    lump_g=total_investable*(1+port["return"])**goal_years
    rem=max(0,goal_amount-lump_g); mo_r2=port["return"]/12; mo2=goal_years*12
    req=(rem*mo_r2/((1+mo_r2)**mo2-1) if mo_r2>0 and rem>0 and mo2>0 else 0)
    gs1,gs2,gs3=st.columns(3)
    gs1.metric("Lump sum at goal",    f"Rs.{lump_g/1e6:.2f}M")
    gs2.metric("Gap to fill via SIP", f"Rs.{rem/1e6:.2f}M")
    gs3.metric("Required SIP",        f"Rs.{req:,.0f}/month")
    if monthly_sip>0:
        if monthly_sip>=req:
            st.success(f"Your SIP of Rs.{monthly_sip:,.0f} is sufficient!")
        else:
            st.warning(f"Increase SIP by Rs.{req-monthly_sip:,.0f} to reach goal.")

# ── TAB 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("**Historical Stress Tests**")
    STRESS={
        "COVID (Feb-Mar 2020)":("2020-02-15","2020-03-23"),
        "2022 Rate Hike":      ("2022-01-01","2022-06-30"),
        "Russia-Ukraine 2022": ("2022-02-24","2022-03-15"),
        "IL&FS Crisis 2018":   ("2018-09-01","2018-10-31"),
    }
    sr=[]
    for sc,(s,e) in STRESS.items():
        try:
            mask=(daily_returns.index>=pd.Timestamp(s))&(daily_returns.index<=pd.Timestamp(e))
            sc_r=daily_returns[mask]
            if len(sc_r)<3: raise ValueError
            pd_r=(np.prod(1+sc_r.values@port["weights"])-1)*100
            n50=0.0
            if "Nifty 50" in assets:
                ni=assets.index("Nifty 50")
                n50=(np.prod(1+sc_r.iloc[:,ni].values)-1)*100
            sr.append({"Scenario":sc,"Portfolio":f"{pd_r:.1f}%",
                       "Nifty 50":f"{n50:.1f}%","Outperformance":f"{pd_r-n50:+.1f}%",
                       "Rs. Impact":f"Rs.{total_investable*pd_r/100:,.0f}"})
        except Exception:
            sr.append({"Scenario":sc,"Portfolio":"N/A","Nifty 50":"N/A",
                       "Outperformance":"N/A","Rs. Impact":"N/A"})
    st.dataframe(pd.DataFrame(sr),hide_index=True,use_container_width=True)

    # Drawdown
    pr_all=daily_returns.values@port["weights"]
    cum=np.cumprod(1+pr_all); rm=np.maximum.accumulate(cum)
    dd=(cum-rm)/rm*100
    fig_dd,ax_dd=plt.subplots(figsize=(9,3),facecolor="#0e0e1a")
    ax_dd.set_facecolor("#0e0e1a")
    ax_dd.fill_between(daily_returns.index,dd,0,alpha=0.7,color="#FF5722",label="Portfolio")
    if "Nifty 50" in assets:
        ni=assets.index("Nifty 50"); n50c=np.cumprod(1+daily_returns.iloc[:,ni].values)
        n50rm=np.maximum.accumulate(n50c); n50dd=(n50c-n50rm)/n50rm*100
        ax_dd.plot(daily_returns.index,n50dd,color="#2196F3",lw=1,alpha=0.8,label="Nifty 50")
    ax_dd.set_xlabel("Date",color="white",fontsize=8)
    ax_dd.set_ylabel("Drawdown (%)",color="white",fontsize=8)
    ax_dd.tick_params(colors="white",labelsize=7)
    ax_dd.legend(facecolor="#1a1a2e",labelcolor="white",fontsize=8)
    ax_dd.grid(True,alpha=0.1,color="white")
    st.pyplot(fig_dd); plt.close()

    # Custom shock
    st.markdown("**Custom Shock Simulator**")
    sh1,sh2,sh3,sh4=st.columns(4)
    eq_sh =sh1.number_input("Equity shock (%)",-80,50,-20,key="sh_eq")
    dbt_sh=sh2.number_input("Debt shock (%)",  -20,10, 2, key="sh_db")
    gld_sh=sh3.number_input("Gold shock (%)",  -30,50, 5, key="sh_gl")
    alt_sh=sh4.number_input("REIT shock (%)",  -50,20,-15,key="sh_al")

    def get_shock(a):
        cat=ASSET_UNIVERSE.get(a,("",""))[1]
        if cat in ("Debt-Sov","Debt-TM","Liquid"): return dbt_sh/100
        if cat in ("Gold","Silver"): return gld_sh/100
        if cat in ("REIT","InvIT"):  return alt_sh/100
        return eq_sh/100

    shock_pct=sum(port["weights"][i]*get_shock(a) for i,a in enumerate(assets))*100
    sa1,sa2,sa3=st.columns(3)
    sa1.metric("Portfolio Impact",  f"{shock_pct:.1f}%")
    sa2.metric("Value After Shock", f"Rs.{total_investable*(1+shock_pct/100):,.0f}")
    sa3.metric("Rs. Change",        f"Rs.{total_investable*shock_pct/100:,.0f}")

# ── TAB 5 ─────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("**Current Holdings vs Target**")
    inp=st.columns(3); uv={}
    for i,a in enumerate(assets):
        uv[a]=inp[i%3].number_input(a,0,int(1e9),int(port["weights"][i]*total_investable),
                                     step=10000,key=f"h_{a}")
    tp=sum(uv.values())
    if tp>0:
        cw={a:v/tp for a,v in uv.items()}; tw=dict(zip(assets,port["weights"]))
        st.markdown(f"**Total: Rs.{tp:,.0f}**")
        gr=[]
        for a in assets:
            c=cw[a]*100; t=tw[a]*100; g=c-t
            act="TRIM" if g>3 else "ADD" if g<-3 else "HOLD"
            gr.append({"Asset":a,"Current":f"{c:.1f}%","Target":f"{t:.1f}%",
                       "Gap":f"{g:+.1f}%","Action":act,
                       "Amount":f"{'Sell' if act=='TRIM' else 'Buy' if act=='ADD' else 'Hold'} Rs.{abs(g/100)*tp:,.0f}"})
        st.dataframe(pd.DataFrame(gr),hide_index=True,use_container_width=True)
        needs=any(r["Action"]!="HOLD" for r in gr)
        st.warning("Rebalancing needed.") if needs else st.success("Portfolio balanced.")

        fig_rb,ax_rb=plt.subplots(figsize=(9,3),facecolor="#0e0e1a")
        ax_rb.set_facecolor("#0e0e1a"); x=np.arange(len(assets)); bw=0.35
        ax_rb.bar(x-bw/2,[cw[a]*100 for a in assets],bw,
                  color=["#FF5722" if cw[a]>tw[a]+0.03 else "#4CAF50" if cw[a]<tw[a]-0.03
                          else "#888" for a in assets],alpha=0.85,label="Current")
        ax_rb.bar(x+bw/2,[tw[a]*100 for a in assets],bw,color="#2196F3",alpha=0.65,label="Target")
        ax_rb.set_xticks(x)
        ax_rb.set_xticklabels(assets,rotation=30,ha="right",fontsize=7,color="white")
        ax_rb.tick_params(colors="white")
        ax_rb.set_ylabel("Weight (%)",color="white",fontsize=8)
        ax_rb.legend(facecolor="#1a1a2e",labelcolor="white",fontsize=8)
        ax_rb.grid(True,alpha=0.1,color="white",axis="y")
        st.pyplot(fig_rb); plt.close()

# ── TAB 6 — Tax + Recommendations ────────────────────────────────────────────
with tab6:
    col_tx,col_rec=st.columns([1,1])

    with col_tx:
        st.markdown("**Tax Optimisation**")
        st.caption("FY2024-25: Equity LTCG 12.5% (>Rs.1.25L). Debt/Gold at slab rate.")
        TAX_RULES={"Equity":{"stcg":0.20,"ltcg":0.125,"ex":125000,"mo":12},
                   "Gold ETF":{"stcg":None,"ltcg":None,"ex":0,"mo":12},
                   "Debt MF":{"stcg":None,"ltcg":None,"ex":0,"mo":36},
                   "SGB":{"stcg":None,"ltcg":0.0,"ex":float("inf"),"mo":96}}

        def calc_tax(a,pd_,pp,cp,un,sl,lu=0):
            cat=TAX_CAT.get(ASSET_UNIVERSE.get(a,("",""))[1],"Equity")
            r=TAX_RULES[cat]; g=(cp-pp)*un; mh=(date.today().year-pd_.year)*12+(date.today().month-pd_.month)
            is_lt=mh>=r["mo"]
            if cat=="Equity":
                tx=(max(0,g)*r["stcg"] if not is_lt else max(0,g-max(0,r["ex"]-lu))*r["ltcg"])
            elif cat in ("Gold ETF","Debt MF"):
                tx=max(0,g)*sl
            else:
                tx=0 if mh>=96 else max(0,g)*sl
            return {"gross":round(g,2),"tax":round(tx,2),"post":round(g-tx,2),
                    "type":"LTCG" if is_lt else "STCG",
                    "eff":round(tx/g*100 if g>0 else 0,1)}

        tx1,tx2,tx3=st.columns(3)
        ti=tx1.number_input("Invested",value=int(total_investable),step=100000,key="txi")
        yh=tx2.slider("Years held",1,10,3,key="tyh")
        sl=tx3.selectbox("Tax slab",["5%","10%","20%","30%"],index=3,key="tsl")
        slr=int(sl.replace("%",""))/100; pd_=date.today()-timedelta(days=365*yh)
        ARET={a:float(ann_returns[a]) for a in assets}
        hc={a:{"u":ti*port["weights"][assets.index(a)]/100,
               "pp":100.0,"cp":100*(1+ARET[a])**yh} for a in assets}

        def rsc(fr):
            tg=tt=tp=lu=0.0; rows=[]
            for a,f in fr.items():
                if f==0 or a not in hc: continue
                h=hc[a]; r=calc_tax(a,pd_,h["pp"],h["cp"],h["u"]*f,slr,lu)
                if r["type"]=="LTCG": lu=min(125000,lu+r["gross"])
                rows.append({"Asset":a,**r}); tg+=r["gross"]; tt+=r["tax"]; tp+=r["post"]
            return rows,round(tg),round(tt),round(tp),round(tt/tg*100 if tg>0 else 0,1)

        eq_a=[a for a in assets if TAX_CAT.get(ASSET_UNIVERSE.get(a,("",""))[1],"Equity")=="Equity"]
        sc_a=rsc({a:1.0  for a in assets})
        sc_b=rsc({a:(0.15 if a in eq_a else 0.0) for a in assets})
        sc_c=rsc({a:1/12 for a in assets})

        tx_df=pd.DataFrame([
            {"Scenario":"Full Exit","Tax":f"Rs.{sc_a[2]:,}","Eff.Rate":f"{sc_a[4]}%","Saved":"—"},
            {"Scenario":"Trim 15%","Tax":f"Rs.{sc_b[2]:,}","Eff.Rate":f"{sc_b[4]}%","Saved":f"Rs.{sc_a[2]-sc_b[2]:,}"},
            {"Scenario":"Staged/12","Tax":f"Rs.{sc_c[2]:,}","Eff.Rate":f"{sc_c[4]}%","Saved":f"Rs.{sc_a[2]-sc_c[2]:,}"},
        ])
        st.dataframe(tx_df,hide_index=True,use_container_width=True)
        st.success(f"Staging saves Rs.{sc_a[2]-sc_c[2]:,} vs full exit.")

    with col_rec:
        st.markdown("**Recommendations**")
        recs={
            1:f"Conservative: 65% G-Sec/Bond + 15% Nifty 50 + 12% Gold + 8% REIT. Review every 6 months.",
            2:f"Mod. Conservative: 50% debt + 30% large-cap + 12% gold + 8% REIT. Add equity 5%/year.",
            3:f"Balanced: 50% equity (Nifty 50+Midcap+factor) + 30% debt + 12% gold + 8% REIT. SIP Rs.{max(monthly_sip,25000):,.0f}/mo.",
            4:f"Mod. Aggressive: 65% equity + 5% intl ETF + 15% debt + 10% gold + 5% REIT. Annual rebalance.",
            5:f"Aggressive: 80% equity (momentum/alpha/midcap/smallcap) + 10% gold + 5% intl + 5% REIT. 10yr horizon.",
        }
        st.info(f"Hi {name_disp}! {recs[pid]}")

        st.markdown("**Age-Based Rule**")
        rule_eq=max(10,min(90,100-client_age)); rule_db=max(10,client_age-10)
        ra1,ra2,ra3=st.columns(3)
        tot_r=rule_eq+rule_db+22
        ra1.metric("Equity",f"{round(rule_eq/tot_r*100)}%")
        ra2.metric("Debt",  f"{round(rule_db/tot_r*100)}%")
        ra3.metric("Gold+Alt",f"{round(22/tot_r*100)}%")

        st.markdown("**Action Checklist**")
        cl=[(True,"Invest per allocation above"),
            (monthly_sip>0,f"SIP Rs.{monthly_sip:,.0f}/month active"),
            (True,"Max 80C via ELSS (Rs.1.5L)"),
            (True,"NPS for Rs.50,000 extra deduction"),
            (pid>=3,"Harvest LTCG Rs.1.25L before March 31"),
            (True,"6-month emergency fund first"),
            (True,"Rebalance annually"),
            (pid>=3,"Add Nasdaq/S&P 500 ETF for USD hedge")]
        for rel,action in cl:
            st.markdown(f"{'✅' if rel else '⬜'} {action}")


with tab7:
    render_realtime_tab(assets, port["weights"], total_investable)


with tab8:
    render_factor_tab(daily_returns, assets, port["weights"], ann_returns)

with tab9:
    render_scenario_tab(assets, port["weights"], total_investable, ann_returns)


with tab10:
    render_benchmark_tab(
        daily_returns, assets, port["weights"],
        {"return": port["return"], "vol": port["vol"],
         "sharpe": port["sharpe"], "max_dd": port["max_dd"]},
        PROFILE_NAMES[pid]
    )

st.markdown("---")
st.caption(f"WealthOS | Live data | {DATA_DATE} | {n} assets | Educational only.")
