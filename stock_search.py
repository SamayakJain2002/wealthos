import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

NSE_STOCKS = {
    "HDFC Bank":"HDFCBANK.NS","ICICI Bank":"ICICIBANK.NS",
    "State Bank of India":"SBIN.NS","Kotak Mahindra Bank":"KOTAKBANK.NS",
    "Axis Bank":"AXISBANK.NS","Bajaj Finance":"BAJFINANCE.NS",
    "Bajaj Finserv":"BAJAJFINSV.NS","PFC":"PFC.NS","REC Ltd":"RECLTD.NS",
    "Federal Bank":"FEDERALBNK.NS","Bank of Baroda":"BANKBARODA.NS",
    "Canara Bank":"CANBK.NS","Punjab National Bank":"PNB.NS",
    "TCS":"TCS.NS","Infosys":"INFY.NS","HCL Technologies":"HCLTECH.NS",
    "Wipro":"WIPRO.NS","Tech Mahindra":"TECHM.NS","LTIMindtree":"LTIM.NS",
    "Mphasis":"MPHASIS.NS","Persistent Systems":"PERSISTENT.NS",
    "Coforge":"COFORGE.NS","Tata Elxsi":"TATAELXSI.NS",
    "KPIT Technologies":"KPITTECH.NS","Cyient":"CYIENT.NS","LTTS":"LTTS.NS",
    "Hindustan Unilever":"HINDUNILVR.NS","ITC":"ITC.NS",
    "Nestle India":"NESTLEIND.NS","Britannia":"BRITANNIA.NS",
    "Dabur India":"DABUR.NS","Marico":"MARICO.NS",
    "Tata Consumer":"TATACONSUM.NS","Varun Beverages":"VBL.NS",
    "Maruti Suzuki":"MARUTI.NS","Tata Motors":"TATAMOTORS.NS",
    "Mahindra":"M&M.NS","Hero MotoCorp":"HEROMOTOCO.NS",
    "Bajaj Auto":"BAJAJ-AUTO.NS","Eicher Motors":"EICHERMOT.NS",
    "TVS Motor":"TVSMOTOR.NS","Ashok Leyland":"ASHOKLEY.NS",
    "MRF":"MRF.NS","Apollo Tyres":"APOLLOTYRE.NS",
    "Sun Pharmaceutical":"SUNPHARMA.NS","Dr Reddys":"DRREDDY.NS",
    "Cipla":"CIPLA.NS","Divis Laboratories":"DIVISLAB.NS",
    "Lupin":"LUPIN.NS","Aurobindo Pharma":"AUROPHARMA.NS",
    "Torrent Pharma":"TORNTPHARM.NS","Apollo Hospitals":"APOLLOHOSP.NS",
    "Reliance Industries":"RELIANCE.NS","ONGC":"ONGC.NS",
    "Coal India":"COALINDIA.NS","NTPC":"NTPC.NS","Power Grid":"POWERGRID.NS",
    "Adani Enterprises":"ADANIENT.NS","Adani Ports":"ADANIPORTS.NS",
    "Tata Power":"TATAPOWER.NS","GAIL":"GAIL.NS","IOC":"IOC.NS",
    "BPCL":"BPCL.NS","Torrent Power":"TORNTPOWER.NS",
    "JSW Energy":"JSWENERGY.NS","Gujarat Gas":"GUJGASLTD.NS",
    "Tata Steel":"TATASTEEL.NS","JSW Steel":"JSWSTEEL.NS",
    "Hindalco":"HINDALCO.NS","Vedanta":"VEDL.NS","SAIL":"SAIL.NS",
    "NMDC":"NMDC.NS","Jindal Steel":"JINDALSTEL.NS",
    "Larsen & Toubro":"LT.NS","Siemens India":"SIEMENS.NS",
    "ABB India":"ABB.NS","Havells India":"HAVELLS.NS",
    "Voltas":"VOLTAS.NS","Polycab":"POLYCAB.NS","KEI Industries":"KEI.NS",
    "Bharat Electronics":"BEL.NS","HAL":"HAL.NS","IRCTC":"IRCTC.NS",
    "Dixon Technologies":"DIXON.NS","Crompton":"CROMPTON.NS",
    "Bharti Airtel":"BHARTIARTL.NS","Zomato":"ZOMATO.NS",
    "Nykaa":"NYKAA.NS","Info Edge":"NAUKRI.NS","Trent":"TRENT.NS",
    "DLF":"DLF.NS","Godrej Properties":"GODREJPROP.NS",
    "Oberoi Realty":"OBEROIRLTY.NS","Prestige Estates":"PRESTIGE.NS",
    "Asian Paints":"ASIANPAINT.NS","Pidilite":"PIDILITIND.NS",
    "SRF Ltd":"SRF.NS","PI Industries":"PIIND.NS","UPL":"UPL.NS",
    "Deepak Nitrite":"DEEPAKNTR.NS","Avenue Supermarts":"DMART.NS",
    "Titan Company":"TITAN.NS","Jubilant Foodworks":"JUBLFOOD.NS",
    "Bajaj Auto Ltd":"BAJAJ-AUTO.NS",
}

SECTOR_MAP = {
    "Banking & Finance":["HDFC Bank","ICICI Bank","State Bank of India",
        "Kotak Mahindra Bank","Axis Bank","Bajaj Finance","Bajaj Finserv",
        "PFC","REC Ltd","Federal Bank","Bank of Baroda","Canara Bank",
        "Punjab National Bank"],
    "IT & Technology":["TCS","Infosys","HCL Technologies","Wipro",
        "Tech Mahindra","LTIMindtree","Mphasis","Persistent Systems",
        "Coforge","Tata Elxsi","KPIT Technologies","Cyient","LTTS"],
    "FMCG & Consumer":["Hindustan Unilever","ITC","Nestle India",
        "Britannia","Dabur India","Marico","Tata Consumer","Varun Beverages"],
    "Auto":["Maruti Suzuki","Tata Motors","Mahindra","Hero MotoCorp",
        "Bajaj Auto","Eicher Motors","TVS Motor","Ashok Leyland",
        "MRF","Apollo Tyres"],
    "Pharma":["Sun Pharmaceutical","Dr Reddys","Cipla","Divis Laboratories",
        "Lupin","Aurobindo Pharma","Torrent Pharma","Apollo Hospitals"],
    "Energy":["Reliance Industries","ONGC","Coal India","NTPC","Power Grid",
        "Adani Enterprises","Adani Ports","Tata Power","GAIL","IOC",
        "BPCL","Torrent Power","JSW Energy","Gujarat Gas"],
    "Metals":["Tata Steel","JSW Steel","Hindalco","Vedanta","SAIL",
        "NMDC","Jindal Steel"],
    "Infra":["Larsen & Toubro","Siemens India","ABB India","Havells India",
        "Voltas","Polycab","KEI Industries","Bharat Electronics","HAL",
        "IRCTC","Dixon Technologies","Crompton"],
    "New Age":["Bharti Airtel","Zomato","Nykaa","Info Edge","Trent"],
    "Real Estate":["DLF","Godrej Properties","Oberoi Realty","Prestige Estates"],
    "Chemicals":["Asian Paints","Pidilite","SRF Ltd","PI Industries",
        "UPL","Deepak Nitrite","Avenue Supermarts","Titan Company",
        "Jubilant Foodworks"],
}

@st.cache_data(ttl=86400)
def fetch_stock_data(ticker_symbol):
    try:
        end = date.today().strftime("%Y-%m-%d")
        raw = yf.download(ticker_symbol, start="2020-01-01",
                          end=end, auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        if raw.empty or "Close" not in raw.columns:
            return None
        s = raw["Close"].squeeze()
        return s if len(s) >= 100 else None
    except Exception:
        return None

def render_stock_search(selected_assets, asset_universe):
    st.markdown("#### NSE Stock Search — 80+ Stocks")
    st.caption(
        "Select stocks below. Selected stocks flow into "
        "Portfolio Builder automatically."
    )

    # Sector filter
    sector = st.selectbox(
        "Filter by sector",
        ["All"] + list(SECTOR_MAP.keys()),
        key="ss_sector_select"
    )

    # Get stocks to display
    if sector == "All":
        display = NSE_STOCKS
    else:
        names = SECTOR_MAP[sector]
        display = {n: NSE_STOCKS[n] for n in names if n in NSE_STOCKS}

    st.caption(f"Showing {len(display)} stocks — tick to add to portfolio")

    # Use checkboxes instead of buttons — no duplicate key issues
    cols = st.columns(3)
    for i, (name, ticker) in enumerate(display.items()):
        with cols[i % 3]:
            already = name in selected_assets
            checked = st.checkbox(
                f"{name}",
                value=already,
                key=f"ss_chk_{i}_{sector[:3]}"
            )
            if checked and name not in selected_assets:
                data = fetch_stock_data(ticker)
                if data is not None:
                    asset_universe[name] = (ticker, "Stock-Custom")
                    selected_assets.append(name)
            elif not checked and name in selected_assets:
                selected_assets.remove(name)
                if name in asset_universe:
                    del asset_universe[name]

    # Custom ticker
    st.markdown("---")
    st.markdown("**Add any custom NSE/BSE/US ticker:**")
    c1, c2 = st.columns([2, 1])
    ct = c1.text_input("Ticker (e.g. RELIANCE.NS)",
                        key="ss_custom_ticker").strip().upper()
    cn = c2.text_input("Display name", key="ss_custom_name").strip()

    if st.button("Add Custom Ticker", key="ss_add_custom"):
        if ct:
            with st.spinner(f"Loading {ct}..."):
                data = fetch_stock_data(ct)
            if data is not None:
                dname = cn or ct
                asset_universe[dname] = (ct, "Stock-Custom")
                if dname not in selected_assets:
                    selected_assets.append(dname)
                st.success(f"Added {dname}!")
                st.rerun()
            else:
                st.error(f"Could not load data for {ct}. Check ticker.")

    # Show current selection
    if selected_assets:
        st.markdown("---")
        st.markdown(f"**Currently selected: {len(selected_assets)} assets**")
        sel_cols = st.columns(4)
        for i, a in enumerate(selected_assets):
            ticker = asset_universe.get(a, ("",))[0]
            sel_cols[i % 4].markdown(
                f"<div style='background:#0f3460;border-radius:6px;"
                f"padding:6px;margin-bottom:4px;font-size:11px;"
                f"color:#e0e0ff;'>{a}<br>"
                f"<span style='color:#555;font-size:9px;'>{ticker}"
                f"</span></div>",
                unsafe_allow_html=True
            )

    return selected_assets, asset_universe
