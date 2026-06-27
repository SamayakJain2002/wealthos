
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta

# ── Nifty 200 ticker map ──────────────────────────────────────────────────────
TICKERS = {
    # Indices
    "Nifty 50":"^NSEI","Nifty Midcap":"^NSMIDCP","Nifty Smallcap":"^CNXSC",
    "Nifty IT":"^CNXIT","Nifty Bank":"^NSEBANK","Nifty Pharma":"^CNXPHARMA",
    "Nifty Auto":"^CNXAUTO","Nifty Energy":"^CNXENERGY",
    # ETFs
    "Gold ETF":"GOLDBEES.NS","Silver ETF":"SILVERETF.NS",
    "Bharat Bond 2030":"CPSEETF.NS","G-Sec Bond":"LIQUIDBEES.NS",
    "REIT":"EMBASSY.NS","Nasdaq 100 ETF":"MOTI0100.NS",
    # Banking
    "HDFC Bank":"HDFCBANK.NS","ICICI Bank":"ICICIBANK.NS",
    "State Bank of India":"SBIN.NS","Kotak Mahindra Bank":"KOTAKBANK.NS",
    "Axis Bank":"AXISBANK.NS","IndusInd Bank":"INDUSINDBK.NS",
    "Federal Bank":"FEDERALBNK.NS","Bank of Baroda":"BANKBARODA.NS",
    "Canara Bank":"CANBK.NS","Punjab National Bank":"PNB.NS",
    "IDFC First Bank":"IDFCFIRSTB.NS",
    # Finance
    "Bajaj Finance":"BAJFINANCE.NS","Bajaj Finserv":"BAJAJFINSV.NS",
    "HDFC Life":"HDFCLIFE.NS","SBI Life":"SBILIFE.NS",
    "Muthoot Finance":"MUTHOOTFIN.NS","Cholamandalam":"CHOLAFIN.NS",
    "PFC":"PFC.NS","REC Ltd":"RECLTD.NS",
    # IT
    "TCS":"TCS.NS","Infosys":"INFY.NS","HCL Technologies":"HCLTECH.NS",
    "Wipro":"WIPRO.NS","Tech Mahindra":"TECHM.NS","LTIMindtree":"LTIM.NS",
    "Mphasis":"MPHASIS.NS","Persistent Systems":"PERSISTENT.NS",
    "Coforge":"COFORGE.NS","Tata Elxsi":"TATAELXSI.NS",
    "KPIT Technologies":"KPITTECH.NS","Cyient":"CYIENT.NS","LTTS":"LTTS.NS",
    # FMCG
    "Hindustan Unilever":"HINDUNILVR.NS","ITC":"ITC.NS",
    "Nestle India":"NESTLEIND.NS","Britannia":"BRITANNIA.NS",
    "Dabur India":"DABUR.NS","Marico":"MARICO.NS",
    "Godrej Consumer":"GODREJCP.NS","Tata Consumer":"TATACONSUM.NS",
    "Varun Beverages":"VBL.NS","Emami":"EMAMILTD.NS",
    # Auto
    "Maruti Suzuki":"MARUTI.NS","Tata Motors":"TATAMOTORS.NS",
    "Mahindra":"M&M.NS","Hero MotoCorp":"HEROMOTOCO.NS",
    "Bajaj Auto":"BAJAJ-AUTO.NS","Eicher Motors":"EICHERMOT.NS",
    "TVS Motor":"TVSMOTOR.NS","Ashok Leyland":"ASHOKLEY.NS",
    "MRF":"MRF.NS","Apollo Tyres":"APOLLOTYRE.NS",
    # Pharma
    "Sun Pharmaceutical":"SUNPHARMA.NS","Dr Reddys":"DRREDDY.NS",
    "Cipla":"CIPLA.NS","Divis Laboratories":"DIVISLAB.NS",
    "Lupin":"LUPIN.NS","Aurobindo Pharma":"AUROPHARMA.NS",
    "Torrent Pharma":"TORNTPHARM.NS","Apollo Hospitals":"APOLLOHOSP.NS",
    "Fortis Healthcare":"FORTIS.NS","Zydus Lifesciences":"ZYDUSLIFE.NS",
    "Max Healthcare":"MAXHEALTH.NS",
    # Energy
    "Reliance Industries":"RELIANCE.NS","ONGC":"ONGC.NS",
    "Coal India":"COALINDIA.NS","NTPC":"NTPC.NS","Power Grid":"POWERGRID.NS",
    "Adani Enterprises":"ADANIENT.NS","Adani Ports":"ADANIPORTS.NS",
    "Tata Power":"TATAPOWER.NS","GAIL":"GAIL.NS","IOC":"IOC.NS",
    "BPCL":"BPCL.NS","Torrent Power":"TORNTPOWER.NS","JSW Energy":"JSWENERGY.NS",
    # Metals
    "Tata Steel":"TATASTEEL.NS","JSW Steel":"JSWSTEEL.NS",
    "Hindalco":"HINDALCO.NS","Vedanta":"VEDL.NS","SAIL":"SAIL.NS",
    "NMDC":"NMDC.NS","Jindal Steel":"JINDALSTEL.NS",
    # Infra
    "Larsen & Toubro":"LT.NS","Siemens India":"SIEMENS.NS",
    "ABB India":"ABB.NS","Havells India":"HAVELLS.NS","Voltas":"VOLTAS.NS",
    "Polycab":"POLYCAB.NS","Bharat Electronics":"BEL.NS","HAL":"HAL.NS",
    "IRCTC":"IRCTC.NS","Dixon Technologies":"DIXON.NS",
    # Consumer & New Age
    "Bharti Airtel":"BHARTIARTL.NS","Zomato":"ZOMATO.NS","Nykaa":"NYKAA.NS",
    "Info Edge":"NAUKRI.NS","Trent":"TRENT.NS",
    "DLF":"DLF.NS","Godrej Properties":"GODREJPROP.NS",
    "Asian Paints":"ASIANPAINT.NS","Pidilite":"PIDILITIND.NS",
    "Avenue Supermarts":"DMART.NS","Titan Company":"TITAN.NS",
    "Jubilant Foodworks":"JUBLFOOD.NS","Kalyan Jewellers":"KALYANKJIL.NS",
}

@st.cache_data(ttl=300)  # refresh every 5 minutes
def get_live_prices(tickers_dict):
    symbols = list(tickers_dict.values())
    try:
        raw = yf.download(symbols, period="2d", interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw[["Close"]]
        close.columns = [col if col in tickers_dict.values() else col 
                         for col in close.columns]
        # Rename back to asset names
        rev = {v: k for k, v in tickers_dict.items()}
        close = close.rename(columns=rev)
        return close
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=60)  # refresh every 1 minute
def get_intraday(ticker_symbol):
    try:
        df = yf.download(ticker_symbol, period="1d", interval="5m",
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()

def render_realtime_tab(assets, port_weights, total_investable):
    st.markdown("#### Live Portfolio Tracker")
    
    col_refresh, col_time = st.columns([1, 3])
    if col_refresh.button("Refresh Prices"):
        st.cache_data.clear()
        st.rerun()
    col_time.caption("Prices refresh automatically every 5 minutes. Click Refresh for instant update.")

    # Get live prices
    with st.spinner("Fetching live prices..."):
        prices_df = get_live_prices(TICKERS)

    if prices_df.empty:
        st.error("Could not fetch live prices. Check internet connection.")
        return

    # ── Live price table ──────────────────────────────────────────────────────
    st.markdown("**Live Prices & Daily Change**")
    
    price_rows = []
    for asset in assets:
        if asset not in prices_df.columns:
            continue
        col_data = prices_df[asset].dropna()
        if len(col_data) < 2:
            continue
        
        prev_close = float(col_data.iloc[-2])
        curr_price = float(col_data.iloc[-1])
        chg        = curr_price - prev_close
        chg_pct    = (chg / prev_close) * 100
        
        # Portfolio weight and value
        idx    = assets.index(asset) if asset in assets else -1
        weight = port_weights[idx] if idx >= 0 else 0
        value  = weight * total_investable

        price_rows.append({
            "Asset":        asset,
            "Price":        f"Rs.{curr_price:,.2f}",
            "Change":       f"{chg:+.2f}",
            "Change %":     f"{chg_pct:+.2f}%",
            "Portfolio Wt": f"{weight*100:.1f}%",
            "Value":        f"Rs.{value:,.0f}",
            "Day P&L":      f"Rs.{value*chg_pct/100:+,.0f}",
            "Signal":       "🟢" if chg_pct > 1 else "🔴" if chg_pct < -1 else "🟡",
        })

    if price_rows:
        price_df = pd.DataFrame(price_rows)
        st.dataframe(price_df, hide_index=True, use_container_width=True)

        # ── Portfolio P&L summary ─────────────────────────────────────────────
        total_day_pl = sum(
            float(r["Day P&L"].replace("Rs.","").replace(",","").replace("+",""))
            for r in price_rows
        )
        total_val = sum(
            float(r["Value"].replace("Rs.","").replace(",",""))
            for r in price_rows
        )

        pl1, pl2, pl3, pl4 = st.columns(4)
        pl1.metric("Total Portfolio Value", f"Rs.{total_val:,.0f}")
        pl2.metric("Today P&L",             f"Rs.{total_day_pl:+,.0f}",
                   delta=f"{total_day_pl/total_val*100:+.2f}%" if total_val > 0 else None)
        
        gainers  = [r for r in price_rows if "+" in r["Change"]]
        losers   = [r for r in price_rows if r["Change"].startswith("-")]
        pl3.metric("Gainers today", len(gainers))
        pl4.metric("Losers today",  len(losers))

    # ── Intraday chart ────────────────────────────────────────────────────────
    st.markdown("**Intraday Chart**")
    chart_asset = st.selectbox(
        "Select asset for intraday view",
        [a for a in assets if a in TICKERS],
        key="intraday_select"
    )

    if chart_asset and chart_asset in TICKERS:
        with st.spinner(f"Loading intraday data for {chart_asset}..."):
            intra_df = get_intraday(TICKERS[chart_asset])

        if not intra_df.empty and "Close" in intra_df.columns:
            fig = go.Figure()
            open_price = float(intra_df["Close"].iloc[0])
            colors = ["#4CAF50" if float(p) >= open_price else "#FF5722"
                      for p in intra_df["Close"]]

            fig.add_trace(go.Scatter(
                x=intra_df.index,
                y=intra_df["Close"],
                mode="lines",
                line=dict(color="#4CAF50", width=2),
                fill="tozeroy",
                fillcolor="rgba(76,175,80,0.1)",
                name=chart_asset,
            ))
            fig.add_hline(
                y=open_price,
                line_dash="dash",
                line_color="white",
                line_width=1,
                annotation_text=f"Open: Rs.{open_price:.2f}",
            )
            fig.update_layout(
                paper_bgcolor="#0e0e1a",
                plot_bgcolor="#1a1a2e",
                font_color="white",
                xaxis_title="Time",
                yaxis_title="Price (Rs.)",
                title=f"{chart_asset} — Intraday (5-min)",
                margin=dict(t=50, b=40, l=50, r=20),
                height=380,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Intraday data not available. Market may be closed.")

    # ── Price alerts ──────────────────────────────────────────────────────────
    st.markdown("**Set Price Alerts**")
    st.caption("These alerts show on this page whenever you refresh. For push notifications, we add that in Phase 4.")

    alert_col1, alert_col2, alert_col3 = st.columns(3)
    alert_asset = alert_col1.selectbox("Asset", list(TICKERS.keys()), key="alert_asset")
    alert_type  = alert_col2.selectbox("Alert when price", ["goes above", "goes below"], key="alert_type")
    alert_price = alert_col3.number_input("Target price (Rs.)", min_value=0.0, value=100.0, key="alert_price")

    if "price_alerts" not in st.session_state:
        st.session_state.price_alerts = []

    if st.button("Add Alert"):
        st.session_state.price_alerts.append({
            "asset": alert_asset,
            "type":  alert_type,
            "price": alert_price,
        })
        st.success(f"Alert set: {alert_asset} {alert_type} Rs.{alert_price:,.0f}")

    # Check alerts
    if st.session_state.price_alerts and not prices_df.empty:
        triggered = []
        for alert in st.session_state.price_alerts:
            a = alert["asset"]
            if a in prices_df.columns:
                curr = float(prices_df[a].dropna().iloc[-1])
                if alert["type"] == "goes above" and curr > alert["price"]:
                    triggered.append(f"ALERT: {a} is Rs.{curr:,.2f} — above your target of Rs.{alert['price']:,.0f}")
                elif alert["type"] == "goes below" and curr < alert["price"]:
                    triggered.append(f"ALERT: {a} is Rs.{curr:,.2f} — below your target of Rs.{alert['price']:,.0f}")
        
        if triggered:
            for msg in triggered:
                st.error(msg)

        st.markdown("**Active Alerts**")
        if st.session_state.price_alerts:
            al_df = pd.DataFrame(st.session_state.price_alerts)
            st.dataframe(al_df, hide_index=True, use_container_width=True)
            if st.button("Clear All Alerts"):
                st.session_state.price_alerts = []
                st.rerun()
