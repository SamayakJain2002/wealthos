
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
from future_returns import render_future_returns
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
STOCK_UNIVERSE = {
    "HDFC Bank":("HDFCBANK.NS","Stock-Bank"),
    "ICICI Bank":("ICICIBANK.NS","Stock-Bank"),
    "State Bank of India":("SBIN.NS","Stock-Bank"),
    "Kotak Mahindra Bank":("KOTAKBANK.NS","Stock-Bank"),
    "Axis Bank":("AXISBANK.NS","Stock-Bank"),
    "IndusInd Bank":("INDUSINDBK.NS","Stock-Bank"),
    "Federal Bank":("FEDERALBNK.NS","Stock-Bank"),
    "Bank of Baroda":("BANKBARODA.NS","Stock-Bank"),
    "Canara Bank":("CANBK.NS","Stock-Bank"),
    "Punjab National Bank":("PNB.NS","Stock-Bank"),
    "Union Bank":("UNIONBANK.NS","Stock-Bank"),
    "IDFC First Bank":("IDFCFIRSTB.NS","Stock-Bank"),
    "AU Small Finance":("AUBANK.NS","Stock-Bank"),
    "Bajaj Finance":("BAJFINANCE.NS","Stock-Finance"),
    "Bajaj Finserv":("BAJAJFINSV.NS","Stock-Finance"),
    "HDFC Life":("HDFCLIFE.NS","Stock-Finance"),
    "SBI Life":("SBILIFE.NS","Stock-Finance"),
    "ICICI Prudential":("ICICIPRULI.NS","Stock-Finance"),
    "Muthoot Finance":("MUTHOOTFIN.NS","Stock-Finance"),
    "Cholamandalam":("CHOLAFIN.NS","Stock-Finance"),
    "Shriram Finance":("SHRIRAMFIN.NS","Stock-Finance"),
    "PFC":("PFC.NS","Stock-Finance"),
    "REC Ltd":("RECLTD.NS","Stock-Finance"),
    "TCS":("TCS.NS","Stock-IT"),
    "Infosys":("INFY.NS","Stock-IT"),
    "HCL Technologies":("HCLTECH.NS","Stock-IT"),
    "Wipro":("WIPRO.NS","Stock-IT"),
    "Tech Mahindra":("TECHM.NS","Stock-IT"),
    "LTIMindtree":("LTIM.NS","Stock-IT"),
    "Mphasis":("MPHASIS.NS","Stock-IT"),
    "Persistent Systems":("PERSISTENT.NS","Stock-IT"),
    "Coforge":("COFORGE.NS","Stock-IT"),
    "Tata Elxsi":("TATAELXSI.NS","Stock-IT"),
    "KPIT Technologies":("KPITTECH.NS","Stock-IT"),
    "Happiest Minds":("HAPPSTMNDS.NS","Stock-IT"),
    "Cyient":("CYIENT.NS","Stock-IT"),
    "LTTS":("LTTS.NS","Stock-IT"),
    "Birlasoft":("BSOFT.NS","Stock-IT"),
    "Hindustan Unilever":("HINDUNILVR.NS","Stock-FMCG"),
    "ITC":("ITC.NS","Stock-FMCG"),
    "Nestle India":("NESTLEIND.NS","Stock-FMCG"),
    "Britannia":("BRITANNIA.NS","Stock-FMCG"),
    "Dabur India":("DABUR.NS","Stock-FMCG"),
    "Marico":("MARICO.NS","Stock-FMCG"),
    "Godrej Consumer":("GODREJCP.NS","Stock-FMCG"),
    "Tata Consumer":("TATACONSUM.NS","Stock-FMCG"),
    "Varun Beverages":("VBL.NS","Stock-FMCG"),
    "Emami":("EMAMILTD.NS","Stock-FMCG"),
    "Colgate Palmolive":("COLPAL.NS","Stock-FMCG"),
    "Maruti Suzuki":("MARUTI.NS","Stock-Auto"),
    "Tata Motors":("TATAMOTORS.NS","Stock-Auto"),
    "Mahindra":("M&M.NS","Stock-Auto"),
    "Hero MotoCorp":("HEROMOTOCO.NS","Stock-Auto"),
    "Bajaj Auto":("BAJAJ-AUTO.NS","Stock-Auto"),
    "Eicher Motors":("EICHERMOT.NS","Stock-Auto"),
    "TVS Motor":("TVSMOTOR.NS","Stock-Auto"),
    "Ashok Leyland":("ASHOKLEY.NS","Stock-Auto"),
    "MRF":("MRF.NS","Stock-Auto"),
    "Apollo Tyres":("APOLLOTYRE.NS","Stock-Auto"),
    "CEAT":("CEATLTD.NS","Stock-Auto"),
    "Exide Industries":("EXIDEIND.NS","Stock-Auto"),
    "Bharat Forge":("BHARATFORG.NS","Stock-Auto"),
    "Sona BLW":("SONACOMS.NS","Stock-Auto"),
    "Uno Minda":("UNOMINDA.NS","Stock-Auto"),
    "Sun Pharmaceutical":("SUNPHARMA.NS","Stock-Pharma"),
    "Dr Reddys":("DRREDDY.NS","Stock-Pharma"),
    "Cipla":("CIPLA.NS","Stock-Pharma"),
    "Divis Laboratories":("DIVISLAB.NS","Stock-Pharma"),
    "Biocon":("BIOCON.NS","Stock-Pharma"),
    "Lupin":("LUPIN.NS","Stock-Pharma"),
    "Aurobindo Pharma":("AUROPHARMA.NS","Stock-Pharma"),
    "Torrent Pharma":("TORNTPHARM.NS","Stock-Pharma"),
    "Alkem Labs":("ALKEM.NS","Stock-Pharma"),
    "Apollo Hospitals":("APOLLOHOSP.NS","Stock-Pharma"),
    "Fortis Healthcare":("FORTIS.NS","Stock-Pharma"),
    "Zydus Lifesciences":("ZYDUSLIFE.NS","Stock-Pharma"),
    "Laurus Labs":("LAURUSLABS.NS","Stock-Pharma"),
    "Max Healthcare":("MAXHEALTH.NS","Stock-Pharma"),
    "Dr Lal Pathlabs":("LALPATHLAB.NS","Stock-Pharma"),
    "Reliance Industries":("RELIANCE.NS","Stock-Energy"),
    "ONGC":("ONGC.NS","Stock-Energy"),
    "Coal India":("COALINDIA.NS","Stock-Energy"),
    "NTPC":("NTPC.NS","Stock-Energy"),
    "Power Grid":("POWERGRID.NS","Stock-Energy"),
    "Adani Enterprises":("ADANIENT.NS","Stock-Energy"),
    "Adani Ports":("ADANIPORTS.NS","Stock-Energy"),
    "Adani Green":("ADANIGREEN.NS","Stock-Energy"),
    "Tata Power":("TATAPOWER.NS","Stock-Energy"),
    "GAIL":("GAIL.NS","Stock-Energy"),
    "IOC":("IOC.NS","Stock-Energy"),
    "BPCL":("BPCL.NS","Stock-Energy"),
    "Hindustan Petroleum":("HINDPETRO.NS","Stock-Energy"),
    "Torrent Power":("TORNTPOWER.NS","Stock-Energy"),
    "JSW Energy":("JSWENERGY.NS","Stock-Energy"),
    "Gujarat Gas":("GUJGASLTD.NS","Stock-Energy"),
    "Oil India":("OIL.NS","Stock-Energy"),
    "Tata Steel":("TATASTEEL.NS","Stock-Metal"),
    "JSW Steel":("JSWSTEEL.NS","Stock-Metal"),
    "Hindalco":("HINDALCO.NS","Stock-Metal"),
    "Vedanta":("VEDL.NS","Stock-Metal"),
    "SAIL":("SAIL.NS","Stock-Metal"),
    "NMDC":("NMDC.NS","Stock-Metal"),
    "Jindal Steel":("JINDALSTEL.NS","Stock-Metal"),
    "APL Apollo":("APLAPOLLO.NS","Stock-Metal"),
    "Hindustan Zinc":("HINDZINC.NS","Stock-Metal"),
    "Larsen & Toubro":("LT.NS","Stock-Infra"),
    "Siemens India":("SIEMENS.NS","Stock-Infra"),
    "ABB India":("ABB.NS","Stock-Infra"),
    "Havells India":("HAVELLS.NS","Stock-Infra"),
    "Voltas":("VOLTAS.NS","Stock-Infra"),
    "Polycab":("POLYCAB.NS","Stock-Infra"),
    "KEI Industries":("KEI.NS","Stock-Infra"),
    "Cummins India":("CUMMINSIND.NS","Stock-Infra"),
    "Bharat Electronics":("BEL.NS","Stock-Infra"),
    "HAL":("HAL.NS","Stock-Infra"),
    "IRCTC":("IRCTC.NS","Stock-Infra"),
    "Dixon Technologies":("DIXON.NS","Stock-Infra"),
    "Crompton":("CROMPTON.NS","Stock-Infra"),
    "Blue Star":("BLUESTARCO.NS","Stock-Infra"),
    "V-Guard":("VGUARD.NS","Stock-Infra"),
    "KEC International":("KEC.NS","Stock-Infra"),
    "Thermax":("THERMAX.NS","Stock-Infra"),
    "Bharti Airtel":("BHARTIARTL.NS","Stock-Telecom"),
    "Indus Towers":("INDUSTOWER.NS","Stock-Telecom"),
    "Zomato":("ZOMATO.NS","Stock-Consumer"),
    "Paytm":("PAYTM.NS","Stock-Consumer"),
    "Nykaa":("NYKAA.NS","Stock-Consumer"),
    "PolicyBazaar":("POLICYBZR.NS","Stock-Consumer"),
    "Delhivery":("DELHIVERY.NS","Stock-Consumer"),
    "Info Edge":("NAUKRI.NS","Stock-Consumer"),
    "Trent":("TRENT.NS","Stock-Consumer"),
    "Indiamart":("INDIAMART.NS","Stock-Consumer"),
    "DLF":("DLF.NS","Stock-Realty"),
    "Godrej Properties":("GODREJPROP.NS","Stock-Realty"),
    "Oberoi Realty":("OBEROIRLTY.NS","Stock-Realty"),
    "Prestige Estates":("PRESTIGE.NS","Stock-Realty"),
    "Sobha":("SOBHA.NS","Stock-Realty"),
    "Brigade Enterprises":("BRIGADE.NS","Stock-Realty"),
    "Asian Paints":("ASIANPAINT.NS","Stock-Chemicals"),
    "Berger Paints":("BERGEPAINT.NS","Stock-Chemicals"),
    "Pidilite":("PIDILITIND.NS","Stock-Chemicals"),
    "SRF Ltd":("SRF.NS","Stock-Chemicals"),
    "Aarti Industries":("AARTIIND.NS","Stock-Chemicals"),
    "PI Industries":("PIIND.NS","Stock-Chemicals"),
    "UPL":("UPL.NS","Stock-Chemicals"),
    "Deepak Nitrite":("DEEPAKNTR.NS","Stock-Chemicals"),
    "Navin Fluorine":("NAVINFLUOR.NS","Stock-Chemicals"),
    "Vinati Organics":("VINATIORGA.NS","Stock-Chemicals"),
    "Coromandel Intl":("COROMANDEL.NS","Stock-Chemicals"),
    "Chambal Fertilizers":("CHAMBLFERT.NS","Stock-Chemicals"),
    "Tata Chemicals":("TATACHEM.NS","Stock-Chemicals"),
    "Avenue Supermarts":("DMART.NS","Stock-Retail"),
    "Titan Company":("TITAN.NS","Stock-Retail"),
    "Jubilant Foodworks":("JUBLFOOD.NS","Stock-Retail"),
    "Page Industries":("PAGEIND.NS","Stock-Retail"),
    "Bata India":("BATAINDIA.NS","Stock-Retail"),
    "Kalyan Jewellers":("KALYANKJIL.NS","Stock-Retail"),
    "Astral":("ASTRAL.NS","Stock-Retail"),
    "Supreme Industries":("SUPREMEIND.NS","Stock-Retail"),
    "PVR Inox":("PVRINOX.NS","Stock-Retail"),
    "Sun TV":("SUNTV.NS","Stock-Media"),
    "Zee Entertainment":("ZEEL.NS","Stock-Media"),
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
    with st.expander("Stocks — Nifty 500 (200+ stocks)"):
        sb_sector = st.selectbox(
            "Filter by sector",
            ["All","Banking & Finance","IT & Technology","FMCG & Consumer",
             "Auto & Ancillary","Pharma & Health","Energy & Oil",
             "Metals & Mining","Infra & Cap Goods","Telecom & New Age",
             "Real Estate","Chemicals & Specialty","Consumer & Retail"],
            key="sb_sector_filter"
        )
        if sb_sector == "All":
            display_stocks = list(STOCK_UNIVERSE.keys())
        else:
            sector_kw = {
                "Banking & Finance":  ["Bank","Finance","Housing","PFC","REC","IDFC","Federal","Baroda","Canara","Punjab","Union","Muthoot","Cholamandalam","Shriram","HDFC Life","SBI Life","ICICI Pru","AU Small","Bandhan"],
                "IT & Technology":    ["TCS","Infosys","HCL","Wipro","Tech Mahindra","LTIMindtree","Mphasis","Persistent","Coforge","Tata Elxsi","KPIT","Happiest","Tanla","Mastek","Zensar","Birlasoft","Cyient","LTTS","Intellect","Newgen","Firstsource"],
                "FMCG & Consumer":    ["Hindustan Unilever","ITC","Nestle","Britannia","Dabur","Marico","Godrej Consumer","Tata Consumer","Varun","Emami","Colgate","Jyothy","Bikaji","Patanjali"],
                "Auto & Ancillary":   ["Maruti","Tata Motors","Mahindra","Hero","Bajaj Auto","Eicher","TVS Motor","Ashok","Bosch","MRF","Apollo Tyres","CEAT","Exide","Motherson","Bharat Forge","Endurance","Sona","Uno Minda","Samvardhana"],
                "Pharma & Health":    ["Sun Pharmaceutical","Dr Reddys","Cipla","Divis","Biocon","Lupin","Aurobindo","Torrent Pharma","Alkem","Abbott","Max Healthcare","Apollo Hospitals","Fortis","Zydus","Gland","Laurus","Ipca","Ajanta","Metropolis","Dr Lal"],
                "Energy & Oil":       ["Reliance","ONGC","Coal India","NTPC","Power Grid","Adani","Tata Power","GAIL","IOC","BPCL","Hindustan Petroleum","Torrent Power","JSW Energy","Petronet","Oil India","Gujarat Gas"],
                "Metals & Mining":    ["Tata Steel","JSW Steel","Hindalco","Vedanta","SAIL","NMDC","Jindal Steel","APL Apollo","Hindustan Zinc","National Aluminium","Ratnamani"],
                "Infra & Cap Goods":  ["Larsen","Siemens","ABB","Havells","Voltas","Polycab","KEI","Cummins","Bharat Electronics","HAL","IRCTC","Dixon","Crompton","Blue Star","V-Guard","KEC","Kalpataru","Thermax","NCC","IRB"],
                "Telecom & New Age":  ["Bharti Airtel","Indus Towers","Zomato","Paytm","Nykaa","PolicyBazaar","Delhivery","Info Edge","Trent","Indiamart"],
                "Real Estate":        ["DLF","Godrej Properties","Oberoi","Prestige","Sobha","Brigade"],
                "Chemicals & Specialty":["Asian Paints","Berger","Pidilite","SRF","Aarti","PI Industries","UPL","Deepak","Navin Fluorine","Vinati","Atul","Tata Chemicals","Coromandel","Chambal"],
                "Consumer & Retail":  ["Avenue Supermarts","Titan","Jubilant","Page Industries","Bata","Kalyan","Astral","Supreme","Whirlpool","PVR","Sun TV","Zee"],
            }
            kws = sector_kw.get(sb_sector, [])
            display_stocks = [
                a for a in STOCK_UNIVERSE.keys()
                if any(k.lower() in a.lower() for k in kws)
            ]
        st.caption(f"{len(display_stocks)} stocks in {sb_sector}")
        for a in display_stocks:
            if st.checkbox(a, value=False, key=f"cb_{a}"):
                selected_assets.append(a)

    st.markdown("#### Risk Profile (Q1-10)")
    QUESTIONS = [
        ("Horizon?",     ["<1yr(1)","1-3yr(2)","3-5yr(3)","5-10yr(4)",">10yr(5)"]),
        ("Emergency?",   ["None(1)","1-3mo(2)","3-6mo(4)",">6mo(5)"]),
        ("Income?",      ["Irregular(1)","Business(2)","Salaried(3)","Govt(4)","Multiple(5)"]),
        ("Obligations?", [">70%(1)","50-70%(2)","30-50%(3)","10-30%(4)","<10%(5)"]),
        ("Drop 25%?",    ["Sell all(1)","Sell most(2)","Hold(3)","Hold+buy(4)","Buy more(5)"]),
        ("Max loss?",    ["None(1)","<5%(2)","5-15%(3)","15-30%(4)",">30%(5)"]),
        ("Emotional?",   ["Severe(1)","High(2)","Moderate(3)","Low(4)","Minimal(5)"]),
        ("Experience?",  ["FDs(1)","MF SIP(2)","MF+eq(3)","Deriv(4)","PMS(5)"]),
        ("Knowledge?",   ["None(1)","Basic(2)","Moderate(3)","Good(4)","Expert(5)"]),
        ("REITs/ETFs?",  ["Never(1)","Heard(2)","1of3(3)","2of3(4)","All3(5)"]),
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
if len(selected_assets) < 2:
    selected_assets = ["Nifty 50","Gold ETF","G-Sec Bond","Bharat Bond 2030","REIT"]

with st.spinner("Loading market data..."):
    result = load_data(tuple(sorted(selected_assets)))

daily_returns, ann_returns, cov, assets, prices = result

if daily_returns is None:
    st.error("Could not load data. Please select more assets.")
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
    "🔭 Forward Returns",
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
(tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,
 tab9,tab10,tab11,tab12,tab13,tab14,tab15,tab16) = tabs

# ── TAB 1 — Portfolio Builder ─────────────────────────────────────────────────
with tab1:
    import pandas as pd
    active_weights, active_metrics = render_portfolio_builder(
        daily_returns, ann_returns, cov, assets, prices, pid,
        ASSET_UNIVERSE, total_investable, monthly_sip,
        annual_topup, goal_amount, goal_years, inflation, name_disp
    )

# Read shared state
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

# ── TAB 2 — Forward Returns ───────────────────────────────────────────────────
with tab2:
    render_future_returns(
        assets, ann_returns, cov, port_weights,
        total_investable, goal_amount, goal_years, pid
    )

# ── TAB 3 — Live Tracker ─────────────────────────────────────────────────────
with tab3:
    render_realtime_tab(assets, port_weights, total_investable)

# ── TAB 4 — Stock Analyser ──────────────────────────────────────────────────
with tab4:
    import yfinance as _yf
    import plotly.graph_objects as _go
    import pandas as _pd
    import numpy as _np

    st.markdown("#### Stock Analyser — Financial Ratios & DCF Valuation")
    st.caption(
        "Search any NSE/BSE stock. Get live financial ratios, "
        "analyst estimates, and an automated DCF valuation."
    )

    # Search box
    col_s1, col_s2 = st.columns([3, 1])
    stock_query = col_s1.text_input(
        "Search stock by name",
        placeholder="e.g. Reliance, TCS, HDFC Bank",
        key="sa_query"
    )
    
    # Build full ticker map from STOCK_UNIVERSE
    name_to_ticker = {n: v[0] for n, v in STOCK_UNIVERSE.items()}
    
    if stock_query and len(stock_query) >= 2:
        matches = {n: t for n, t in name_to_ticker.items()
                   if stock_query.lower() in n.lower()}
        if matches:
            selected_name = col_s2.selectbox(
                "Select", list(matches.keys()), key="sa_select"
            )
            selected_ticker = matches[selected_name]
        else:
            st.info("No match. Enter ticker directly below.")
            selected_name   = None
            selected_ticker = None
    else:
        selected_name   = None
        selected_ticker = None

    # Direct ticker input
    custom_ticker_sa = st.text_input(
        "Or enter NSE ticker directly (e.g. RELIANCE.NS)",
        key="sa_direct_ticker"
    ).strip().upper()
    if custom_ticker_sa:
        selected_ticker = custom_ticker_sa
        selected_name   = custom_ticker_sa

    if selected_ticker:
        with st.spinner(f"Fetching data for {selected_ticker}..."):
            try:
                _t    = _yf.Ticker(selected_ticker)
                _info = _t.info
                _hist = _t.history(period="1y")
            except Exception as e:
                st.error(f"Could not fetch data: {e}")
                _info = {}
                _hist = _pd.DataFrame()

        if _info:
            # ── Company header ────────────────────────────────────────────────
            co_name  = _info.get("longName", selected_name)
            sector   = _info.get("sector", "N/A")
            industry = _info.get("industry", "N/A")
            curr_px  = _info.get("currentPrice") or _info.get("regularMarketPrice", 0)
            mktcap   = _info.get("marketCap", 0)

            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #21262d;
                        border-radius:10px;padding:16px 18px;margin-bottom:16px;">
                <div style="font-size:20px;font-weight:700;color:#f0f6fc;">
                    {co_name}</div>
                <div style="font-size:12px;color:#8b949e;margin-top:4px;">
                    {sector} | {industry} | {selected_ticker}</div>
                <div style="font-size:24px;font-weight:800;
                            color:#3fb950;margin-top:8px;">
                    Rs.{curr_px:,.2f}
                    <span style="font-size:13px;color:#8b949e;">
                        | Mkt Cap: Rs.{mktcap/1e7:,.0f}Cr</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Price chart ───────────────────────────────────────────────────
            if not _hist.empty:
                fig_px = _go.Figure()
                fig_px.add_trace(_go.Scatter(
                    x=_hist.index, y=_hist["Close"],
                    mode="lines", line=dict(color="#3fb950", width=2),
                    fill="tozeroy", fillcolor="rgba(63,185,80,0.08)"
                ))
                fig_px.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#161b22",
                    font_color="white", height=200,
                    margin=dict(t=10,b=30,l=50,r=10),
                    xaxis=dict(showgrid=False, color="#6e7681"),
                    yaxis=dict(showgrid=True, gridcolor="#21262d",
                               color="#6e7681", title="Price (Rs.)")
                )
                st.plotly_chart(fig_px, use_container_width=True)

            # ── Key ratios ────────────────────────────────────────────────────
            st.markdown("#### Key Financial Ratios")
            
            pe      = _info.get("trailingPE", 0)
            fwd_pe  = _info.get("forwardPE", 0)
            pb      = _info.get("priceToBook", 0)
            ps      = _info.get("priceToSalesTrailing12Months", 0)
            ev_eb   = _info.get("enterpriseToEbitda", 0)
            roe     = _info.get("returnOnEquity", 0)
            roa     = _info.get("returnOnAssets", 0)
            npm     = _info.get("profitMargins", 0)
            gpm     = _info.get("grossMargins", 0)
            de      = _info.get("debtToEquity", 0)
            cr      = _info.get("currentRatio", 0)
            div_y   = _info.get("dividendYield", 0)
            rev_gr  = _info.get("revenueGrowth", 0)
            earn_gr = _info.get("earningsGrowth", 0)
            beta    = _info.get("beta", 0)
            eps     = _info.get("trailingEps", 0)
            bvps    = _info.get("bookValue", 0)
            rev     = _info.get("totalRevenue", 0)
            ebitda  = _info.get("ebitda", 0)
            fcf     = _info.get("freeCashflow", 0)

            r1,r2,r3,r4,r5,r6 = st.columns(6)
            r1.metric("P/E (TTM)",    f"{pe:.1f}x"    if pe    else "N/A")
            r2.metric("Fwd P/E",      f"{fwd_pe:.1f}x" if fwd_pe else "N/A")
            r3.metric("P/B",          f"{pb:.2f}x"    if pb    else "N/A")
            r4.metric("EV/EBITDA",    f"{ev_eb:.1f}x" if ev_eb else "N/A")
            r5.metric("P/S",          f"{ps:.2f}x"    if ps    else "N/A")
            r6.metric("Beta",         f"{beta:.2f}"   if beta  else "N/A")

            r7,r8,r9,r10,r11,r12 = st.columns(6)
            r7.metric("ROE",          f"{roe*100:.1f}%"    if roe    else "N/A")
            r8.metric("ROA",          f"{roa*100:.1f}%"    if roa    else "N/A")
            r9.metric("Net Margin",   f"{npm*100:.1f}%"    if npm    else "N/A")
            r10.metric("Gross Margin",f"{gpm*100:.1f}%"    if gpm    else "N/A")
            r11.metric("D/E Ratio",   f"{de:.2f}"          if de     else "N/A")
            r12.metric("Div Yield",   f"{div_y*100:.2f}%"  if div_y  else "N/A")

            r13,r14,r15,r16,r17,r18 = st.columns(6)
            r13.metric("EPS (TTM)",   f"Rs.{eps:.2f}"      if eps    else "N/A")
            r14.metric("Book Value",  f"Rs.{bvps:.2f}"     if bvps   else "N/A")
            r15.metric("Revenue",     f"Rs.{rev/1e7:,.1f}Cr" if rev   else "N/A")
            r16.metric("EBITDA",      f"Rs.{ebitda/1e7:,.1f}Cr" if ebitda else "N/A")
            r17.metric("FCF",         f"Rs.{fcf/1e7:,.1f}Cr" if fcf  else "N/A")
            r18.metric("Rev Growth",  f"{rev_gr*100:.1f}%"  if rev_gr else "N/A")

            # ── Ratio interpretation ──────────────────────────────────────────
            # Full numbers table
            st.markdown("#### Key Financials (Full Numbers)")
            fin_data = {
                "Metric": ["Revenue","EBITDA","Free Cash Flow","Net Income","Total Debt","Cash"],
                "Value (Rs. Cr)": [
                    f"Rs.{rev/1e7:,.2f} Cr"    if rev    else "N/A",
                    f"Rs.{ebitda/1e7:,.2f} Cr" if ebitda else "N/A",
                    f"Rs.{fcf/1e7:,.2f} Cr"    if fcf    else "N/A",
                    f"Rs.{_info.get('netIncomeToCommon',0)/1e7:,.2f} Cr" if _info.get('netIncomeToCommon') else "N/A",
                    f"Rs.{_info.get('totalDebt',0)/1e7:,.2f} Cr"        if _info.get('totalDebt')         else "N/A",
                    f"Rs.{_info.get('totalCash',0)/1e7:,.2f} Cr"        if _info.get('totalCash')         else "N/A",
                ],
                "Value (Rs. Lakh Cr)": [
                    f"Rs.{rev/1e11:,.4f} L.Cr"    if rev    else "N/A",
                    f"Rs.{ebitda/1e11:,.4f} L.Cr" if ebitda else "N/A",
                    f"Rs.{fcf/1e11:,.4f} L.Cr"    if fcf    else "N/A",
                    f"Rs.{_info.get('netIncomeToCommon',0)/1e11:,.4f} L.Cr" if _info.get('netIncomeToCommon') else "N/A",
                    "—","—",
                ],
            }
            import pandas as _pd2
            st.dataframe(_pd2.DataFrame(fin_data), hide_index=True, use_container_width=True)

            st.markdown("#### Ratio Interpretation")
            interp = []
            if pe > 0:
                if pe < 15:   interp.append(("P/E", f"{pe:.1f}x", "Potentially undervalued vs market", "#3fb950"))
                elif pe < 25: interp.append(("P/E", f"{pe:.1f}x", "Fairly valued", "#58a6ff"))
                else:         interp.append(("P/E", f"{pe:.1f}x", "Premium valuation — growth expected", "#ffa657"))
            if roe > 0:
                if roe > 0.20:  interp.append(("ROE", f"{roe*100:.1f}%", "Excellent capital efficiency", "#3fb950"))
                elif roe > 0.12:interp.append(("ROE", f"{roe*100:.1f}%", "Decent returns on equity", "#58a6ff"))
                else:           interp.append(("ROE", f"{roe*100:.1f}%", "Below average capital returns", "#f85149"))
            if de > 0:
                if de < 0.5:  interp.append(("D/E", f"{de:.2f}", "Low leverage — conservative balance sheet", "#3fb950"))
                elif de < 1.5:interp.append(("D/E", f"{de:.2f}", "Moderate leverage", "#58a6ff"))
                else:         interp.append(("D/E", f"{de:.2f}", "High leverage — monitor debt levels", "#f85149"))
            if npm > 0:
                if npm > 0.20: interp.append(("Net Margin", f"{npm*100:.1f}%", "Strong profitability", "#3fb950"))
                elif npm > 0.10:interp.append(("Net Margin",f"{npm*100:.1f}%", "Decent margins", "#58a6ff"))
                else:           interp.append(("Net Margin",f"{npm*100:.1f}%", "Thin margins — watch costs", "#ffa657"))

            if interp:
                ic = st.columns(len(interp))
                for i,(metric,val,msg,color) in enumerate(interp):
                    ic[i].markdown(f"""
                    <div style="background:#161b22;border-left:3px solid {color};
                                border-radius:0 8px 8px 0;padding:10px 12px;">
                        <div style="font-size:11px;color:#6e7681;">{metric}</div>
                        <div style="font-size:16px;font-weight:700;
                                    color:{color};">{val}</div>
                        <div style="font-size:11px;color:#8b949e;">{msg}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── DCF Valuation ─────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### DCF Valuation (Automated)")
            st.caption(
                "DCF uses free cash flow, analyst growth estimates, and WACC "
                "to compute intrinsic value. Numbers sourced live from Yahoo Finance."
            )

            dcf1, dcf2, dcf3 = st.columns(3)
            wacc     = dcf1.slider("WACC (%)", 8, 18, 12, key="sa_wacc") / 100
            gr_yr1_5 = dcf2.slider("Growth Yrs 1-5 (%)", 0, 40, 
                                    int(max(5, (earn_gr or 0.10)*100)),
                                    key="sa_gr1") / 100
            gr_term  = dcf3.slider("Terminal Growth (%)", 2, 6, 4, key="sa_grterm") / 100

            if fcf and fcf > 0 and wacc > gr_term:
                # Project FCF for 5 years
                projected_fcf = []
                cf = fcf
                for yr in range(1, 6):
                    cf = cf * (1 + gr_yr1_5)
                    pv = cf / (1 + wacc)**yr
                    projected_fcf.append({"Year": f"Year {yr}",
                                          "FCF (Rs.Cr)": f"Rs.{cf/1e7:,.0f}Cr",
                                          "PV (Rs.Cr)": f"Rs.{pv/1e7:,.0f}Cr"})

                pv_sum = sum(fcf*(1+gr_yr1_5)**yr / (1+wacc)**yr
                             for yr in range(1, 6))
                terminal_val = (cf*(1+gr_term)) / (wacc-gr_term)
                pv_terminal  = terminal_val / (1+wacc)**5
                shares       = _info.get("sharesOutstanding", 1)
                net_debt     = (_info.get("totalDebt", 0) -
                                _info.get("totalCash", 0))
                equity_val   = pv_sum + pv_terminal - net_debt
                intrinsic_px = equity_val / shares if shares > 0 else 0

                upside = ((intrinsic_px - curr_px) / curr_px * 100
                          if curr_px > 0 else 0)

                d1,d2,d3,d4 = st.columns(4)
                d1.metric("PV of FCF (5yr)", f"Rs.{pv_sum/1e7:,.0f}Cr")
                d2.metric("Terminal Value",   f"Rs.{pv_terminal/1e7:,.0f}Cr")
                d3.metric("Intrinsic Value",  f"Rs.{intrinsic_px:,.2f}",
                          delta=f"{upside:+.1f}% vs CMP")
                d4.metric("Verdict",
                          "Undervalued ✅" if upside > 15
                          else "Fairly Valued ➡️" if upside > -10
                          else "Overvalued ⚠️",
                          delta=f"CMP Rs.{curr_px:,.0f}")

                # Sensitivity table
                st.markdown("**DCF Sensitivity — Intrinsic Value (Rs.)**")
                waccs    = [wacc-0.02, wacc, wacc+0.02]
                growths  = [gr_yr1_5-0.05, gr_yr1_5, gr_yr1_5+0.05]
                sens_data = {}
                for g in growths:
                    row = {}
                    for w in waccs:
                        if w > gr_term and g >= 0:
                            pv_s = sum(fcf*(1+g)**yr/(1+w)**yr for yr in range(1,6))
                            tv_s = (fcf*(1+g)**5*(1+gr_term))/(w-gr_term)
                            pv_tv= tv_s/(1+w)**5
                            iv_s = (pv_s+pv_tv-net_debt)/shares if shares>0 else 0
                            row[f"WACC {w*100:.0f}%"] = f"Rs.{iv_s:,.0f}"
                        else:
                            row[f"WACC {w*100:.0f}%"] = "N/A"
                    sens_data[f"Growth {g*100:.0f}%"] = row
                st.dataframe(_pd.DataFrame(sens_data).T,
                             use_container_width=True)

                st.dataframe(_pd.DataFrame(projected_fcf),
                             hide_index=True, use_container_width=True)
            else:
                # P/E based valuation if no FCF
                if eps > 0 and pe > 0:
                    fair_pe      = min(pe, 25)
                    intrinsic_pe = eps * fair_pe
                    upside_pe    = (intrinsic_pe-curr_px)/curr_px*100 if curr_px else 0
                    st.info(
                        f"FCF not available. Using P/E based valuation: "
                        f"EPS Rs.{eps:.2f} × Fair P/E {fair_pe:.0f}x = "
                        f"**Rs.{intrinsic_pe:,.0f}** intrinsic value "
                        f"({upside_pe:+.1f}% vs CMP Rs.{curr_px:,.0f})"
                    )
                else:
                    st.warning(
                        "Insufficient financial data for DCF. "
                        "This may be a new listing or data unavailable on Yahoo Finance."
                    )

            # ── Add to portfolio ──────────────────────────────────────────────
            st.markdown("---")
            if selected_name and selected_name in STOCK_UNIVERSE:
                already = selected_name in selected_assets
                if not already:
                    if st.button(f"Add {selected_name} to Portfolio",
                                 type="primary", key="sa_add_btn"):
                        selected_assets.append(selected_name)
                        st.success(f"Added {selected_name}! Tick it in sidebar.")
                        st.rerun()
                else:
                    st.success(f"{selected_name} is already in your portfolio.")
        else:
            st.error("Could not fetch company data. Check ticker symbol.")
    else:
        st.markdown("""
        <div style="background:#161b22;border:1px solid #21262d;
                    border-radius:10px;padding:24px;text-align:center;">
            <div style="font-size:32px;margin-bottom:12px;">🔍</div>
            <div style="font-size:16px;font-weight:600;color:#f0f6fc;
                        margin-bottom:8px;">Search any NSE/BSE stock</div>
            <div style="font-size:13px;color:#6e7681;line-height:1.8;">
                Type a company name above to get:<br>
                • Live price & 1-year chart<br>
                • 18 financial ratios (P/E, ROE, D/E, margins)<br>
                • Automated DCF valuation with intrinsic value<br>
                • Sensitivity analysis across WACC & growth scenarios<br>
                • One-click add to portfolio
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 5 — Charts & TA ──────────────────────────────────────────────────────
with tab5:
    render_charts_tab()

# ── TAB 6 — Rebalancing ──────────────────────────────────────────────────────
with tab6:
    st.markdown("#### Rebalancing")
    st.caption("Enter current holdings. Target = your Tab 1 portfolio.")
    inp=st.columns(3); uv={}
    for i,a in enumerate(assets):
        uv[a]=inp[i%3].number_input(a,0,int(1e9),
            int(port_weights[i]*total_investable),
            step=10000,key=f"h_{a}")
    tp=sum(uv.values())
    if tp>0:
        cw={a:v/tp for a,v in uv.items()}
        tw=dict(zip(assets,port_weights))
        st.markdown(f"**Total: Rs.{tp:,.0f}**")
        gr=[]
        for a in assets:
            c=cw[a]*100; t=tw[a]*100; g=c-t
            act="TRIM" if g>3 else "ADD" if g<-3 else "HOLD"
            gr.append({"Asset":a,"Current %":f"{c:.1f}%",
                       "Target %":f"{t:.1f}%","Gap":f"{g:+.1f}%","Action":act,
                       "Amount":f"{'Sell' if act=='TRIM' else 'Buy' if act=='ADD' else 'Hold'} Rs.{abs(g/100)*tp:,.0f}"})
        import pandas as pd
        st.dataframe(pd.DataFrame(gr),hide_index=True,use_container_width=True)
        if any(r["Action"]!="HOLD" for r in gr):
            st.warning("Rebalancing needed.")
        else:
            st.success("Portfolio aligned with target.")

# ── TAB 7 — Tax ──────────────────────────────────────────────────────────────
with tab7:
    st.markdown("#### Tax Optimisation — FY2024-25")
    st.info("Equity LTCG 12.5% above Rs.1.25L | Debt/Gold at slab rate")
    import pandas as pd
    from datetime import date, timedelta
    TAX_RULES={"Equity":{"stcg":0.20,"ltcg":0.125,"ex":125000,"mo":12},
               "Gold ETF":{"stcg":None,"ltcg":None,"ex":0,"mo":12},
               "Debt MF":{"stcg":None,"ltcg":None,"ex":0,"mo":36}}
    TAX_CAT={"Equity-LC":"Equity","Equity-MC":"Equity","Equity-SC":"Equity",
             "Sectoral":"Equity","Intl-Eq":"Equity","Debt-Sov":"Debt MF",
             "Debt-TM":"Debt MF","Gold":"Gold ETF","Silver":"Gold ETF",
             "REIT":"Equity","Stock-Bank":"Equity","Stock-IT":"Equity",
             "Stock-Finance":"Equity","Stock-FMCG":"Equity","Stock-Auto":"Equity",
             "Stock-Pharma":"Equity","Stock-Energy":"Equity","Stock-Infra":"Equity",
             "Stock-Metal":"Equity","Stock-Consumer":"Equity","Stock-Custom":"Equity",
             "Stock-Telecom":"Equity","Stock-Realty":"Equity","Stock-Chemicals":"Equity",
             "Stock-Retail":"Equity","Stock-Media":"Equity"}
    tx1,tx2,tx3=st.columns(3)
    ti=tx1.number_input("Invested (Rs.)",value=int(total_investable),step=100000,key="txi")
    yh=tx2.slider("Years held",1,10,3,key="tyh")
    sl=tx3.selectbox("Tax slab",["5%","10%","20%","30%"],index=3,key="tsl")
    slr=int(sl.replace("%",""))/100
    pd_=date.today()-timedelta(days=365*yh)
    ARET={a:float(ann_returns[a]) for a in assets}
    hc={a:{"u":ti*port_weights[assets.index(a)]/100,"pp":100.0,
           "cp":100*(1+ARET[a])**yh} for a in assets}
    def calc_tax(a,pp,cp,un,sl2,lu=0):
        cat=TAX_CAT.get(ASSET_UNIVERSE.get(a,("","Equity-LC"))[1],"Equity")
        r=TAX_RULES.get(cat,TAX_RULES["Equity"])
        g=(cp-pp)*un
        mh=(date.today().year-pd_.year)*12+(date.today().month-pd_.month)
        is_lt=mh>=r["mo"]
        if cat=="Equity":
            tx=(max(0,g)*r["stcg"] if not is_lt else max(0,g-max(0,r["ex"]-lu))*r["ltcg"])
        else:
            tx=max(0,g)*sl2
        return {"gross":round(g,2),"tax":round(tx,2),"post":round(g-tx,2),
                "type":"LTCG" if is_lt else "STCG","eff":round(tx/g*100 if g>0 else 0,1)}
    def rsc(fr):
        tg=tt=tp_=lu=0.0; rows=[]
        for a,f in fr.items():
            if f==0 or a not in hc: continue
            h=hc[a]; r=calc_tax(a,h["pp"],h["cp"],h["u"]*f,slr,lu)
            if r["type"]=="LTCG": lu=min(125000,lu+r["gross"])
            rows.append({"Asset":a,**r}); tg+=r["gross"]; tt+=r["tax"]; tp_+=r["post"]
        return rows,round(tg),round(tt),round(tp_),round(tt/tg*100 if tg>0 else 0,1)
    eq_a=[a for a in assets if TAX_CAT.get(ASSET_UNIVERSE.get(a,("","Equity-LC"))[1],"Equity")=="Equity"]
    sc_a=rsc({a:1.0 for a in assets})
    sc_b=rsc({a:(0.15 if a in eq_a else 0.0) for a in assets})
    sc_c=rsc({a:1/12 for a in assets})
    tx_df=pd.DataFrame([
        {"Scenario":"Full Exit","Tax":f"Rs.{sc_a[2]:,}","Rate":f"{sc_a[4]}%","Saved":"—"},
        {"Scenario":"Trim 15%","Tax":f"Rs.{sc_b[2]:,}","Rate":f"{sc_b[4]}%","Saved":f"Rs.{sc_a[2]-sc_b[2]:,}"},
        {"Scenario":"Staged/12mo","Tax":f"Rs.{sc_c[2]:,}","Rate":f"{sc_c[4]}%","Saved":f"Rs.{sc_a[2]-sc_c[2]:,}"},
    ])
    st.dataframe(tx_df,hide_index=True,use_container_width=True)
    st.success(f"Staging exit saves Rs.{sc_a[2]-sc_c[2]:,} vs full exit.")

# ── TAB 8 — Glossary ─────────────────────────────────────────────────────────
with tab8:
    glossary_page()

# ── TAB 9 — Benchmarks ───────────────────────────────────────────────────────
with tab9:
    render_benchmark_tab(
        daily_returns, assets, port_weights,
        {"return":m["return"],"vol":m["vol"],
         "sharpe":m["sharpe"],"max_dd":m["max_dd"]},
        PROFILE_NAMES[pid]
    )

# ── TAB 10 — Factor ──────────────────────────────────────────────────────────
with tab10:
    render_factor_tab(daily_returns, assets, port_weights, ann_returns)

# ── TAB 11 — Efficient Frontier ──────────────────────────────────────────────
with tab11:
    import pandas as pd
    st.markdown("#### Efficient Frontier")
    st.caption("Your portfolio (star) vs 4,000 random portfolios.")
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
            mode="markers+text",marker=dict(color="#aaa",size=7,symbol="diamond"),
            text=[a],textposition="top right",textfont=dict(color="#777",size=8),
            name=a,showlegend=False))
    fig_ef.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#161b22",
        font_color="white",xaxis_title="Volatility (%)",yaxis_title="Return (%)",
        height=500,margin=dict(t=20,b=40,l=50,r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_ef,use_container_width=True)

# ── TAB 12 — Scenarios ───────────────────────────────────────────────────────
with tab12:
    render_scenario_tab(assets, port_weights, total_investable, ann_returns)

# ── TAB 13 — Stress Test ─────────────────────────────────────────────────────
with tab13:
    import pandas as pd
    st.markdown("#### Stress Testing")
    STRESS={"COVID (Feb-Mar 2020)":("2020-02-15","2020-03-23"),
            "2022 Rate Hike":("2022-01-01","2022-06-30"),
            "Russia-Ukraine":("2022-02-24","2022-03-15")}
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
            sr.append({"Scenario":sc,"Portfolio":f"{pd_r:.1f}%",
                       "Nifty 50":f"{n50:.1f}%","vs Nifty":f"{pd_r-n50:+.1f}%",
                       "Rs. Impact":f"Rs.{total_investable*pd_r/100:+,.0f}"})
        except Exception:
            sr.append({"Scenario":sc,"Portfolio":"N/A","Nifty 50":"N/A",
                       "vs Nifty":"N/A","Rs. Impact":"N/A"})
    st.dataframe(pd.DataFrame(sr),hide_index=True,use_container_width=True)
    pr_all=daily_returns.values@port_weights
    cum=np.cumprod(1+pr_all); rm=np.maximum.accumulate(cum); dd=(cum-rm)/rm*100
    fig_dd=go.Figure()
    fig_dd.add_trace(go.Scatter(x=daily_returns.index.tolist(),y=dd.tolist(),
        fill="tozeroy",name="Portfolio",line_color="#f85149",
        fillcolor="rgba(248,81,73,0.25)"))
    if "Nifty 50" in assets:
        ni=assets.index("Nifty 50")
        n50c=np.cumprod(1+daily_returns.iloc[:,ni].values)
        n50rm=np.maximum.accumulate(n50c); n50dd=(n50c-n50rm)/n50rm*100
        fig_dd.add_trace(go.Scatter(x=daily_returns.index.tolist(),
            y=n50dd.tolist(),name="Nifty 50",line_color="#58a6ff"))
    fig_dd.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#161b22",
        font_color="white",height=320,margin=dict(t=20,b=40,l=50,r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_dd,use_container_width=True)

# ── TAB 14 — Monte Carlo ─────────────────────────────────────────────────────
with tab14:
    st.markdown("#### Monte Carlo Simulation")
    mc_yr=st.slider("Horizon",1,30,goal_years,key="mc_yr")
    DAYS=mc_yr*252; N=1000
    mu=m["return"]/252; sig=m["vol"]/np.sqrt(252)
    np.random.seed(42)
    paths=np.zeros((N,DAYS+1)); paths[:,0]=total_investable
    for t in range(1,DAYS+1):
        paths[:,t]=paths[:,t-1]*(1+np.random.normal(mu,sig,N))
    fv=paths[:,-1]; xa=np.linspace(0,mc_yr,DAYS+1)
    mc1,mc2,mc3,mc4=st.columns(4)
    mc1.metric(f"Prob Rs.{goal_amount/1e6:.0f}M",f"{(fv>=goal_amount).mean()*100:.1f}%")
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
        font_color="white",height=420,margin=dict(t=20,b=40,l=50,r=20),
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

# ── TAB 15 — Backtester ──────────────────────────────────────────────────────
with tab15:
    render_backtester_tab()

# ── TAB 16 — Walk-Forward ────────────────────────────────────────────────────
with tab16:
    render_walkforward_tab()

st.markdown("---")
st.caption("WealthPy Labs | Built by Samayak Jain | samayakpjain@gmail.com | Educational only | Consult SEBI advisor before investing")
