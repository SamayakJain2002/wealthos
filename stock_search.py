
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

NSE_STOCKS = {
    # ── Large Cap — Banking & Finance ─────────────────────────────────────────
    "HDFC Bank":           "HDFCBANK.NS",
    "ICICI Bank":          "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Axis Bank":           "AXISBANK.NS",
    "IndusInd Bank":       "INDUSINDBK.NS",
    "Bajaj Finance":       "BAJFINANCE.NS",
    "Bajaj Finserv":       "BAJAJFINSV.NS",
    "HDFC Life":           "HDFCLIFE.NS",
    "SBI Life":            "SBILIFE.NS",
    "ICICI Prudential":    "ICICIPRULI.NS",
    "Muthoot Finance":     "MUTHOOTFIN.NS",
    "Cholamandalam":       "CHOLAFIN.NS",
    "Shriram Finance":     "SHRIRAMFIN.NS",
    "PFC":                 "PFC.NS",
    "REC Ltd":             "RECLTD.NS",
    "LIC Housing Finance": "LICHSGFIN.NS",
    "Piramal Enterprises": "PEL.NS",
    "Manappuram Finance":  "MANAPPURAM.NS",
    "IDFC First Bank":     "IDFCFIRSTB.NS",
    "Federal Bank":        "FEDERALBNK.NS",
    "Bank of Baroda":      "BANKBARODA.NS",
    "Canara Bank":         "CANBK.NS",
    "Punjab National Bank":"PNB.NS",
    "Union Bank":          "UNIONBANK.NS",
    "Indian Bank":         "INDIANB.NS",
    "Central Bank":        "CENTRALBK.NS",
    "UCO Bank":            "UCOBANK.NS",
    # ── IT ────────────────────────────────────────────────────────────────────
    "TCS":                 "TCS.NS",
    "Infosys":             "INFY.NS",
    "HCL Technologies":    "HCLTECH.NS",
    "Wipro":               "WIPRO.NS",
    "Tech Mahindra":       "TECHM.NS",
    "LTIMindtree":         "LTIM.NS",
    "Mphasis":             "MPHASIS.NS",
    "Persistent Systems":  "PERSISTENT.NS",
    "Coforge":             "COFORGE.NS",
    "Tata Elxsi":          "TATAELXSI.NS",
    "KPIT Technologies":   "KPITTECH.NS",
    "Happiest Minds":      "HAPPSTMNDS.NS",
    "Tanla Platforms":     "TANLA.NS",
    "Mastek":              "MASTEK.NS",
    "Zensar Technologies": "ZENSARTECH.NS",
    "Birlasoft":           "BSOFT.NS",
    "Sonata Software":     "SONATSOFTW.NS",
    "Cyient":              "CYIENT.NS",
    "LTTS":                "LTTS.NS",
    "Intellect Design":    "INTELLECT.NS",
    "Newgen Software":     "NEWGEN.NS",
    "Hexaware":            "HEXAWARE.NS",
    "Firstsource":         "FSL.NS",
    "NIIT Technologies":   "NIIT.NS",
    # ── FMCG & Consumer ───────────────────────────────────────────────────────
    "Hindustan Unilever":  "HINDUNILVR.NS",
    "ITC":                 "ITC.NS",
    "Nestle India":        "NESTLEIND.NS",
    "Britannia":           "BRITANNIA.NS",
    "Dabur India":         "DABUR.NS",
    "Marico":              "MARICO.NS",
    "Godrej Consumer":     "GODREJCP.NS",
    "Tata Consumer":       "TATACONSUM.NS",
    "Varun Beverages":     "VBL.NS",
    "United Spirits":      "MCDOWELL-N.NS",
    "United Breweries":    "UBL.NS",
    "Emami":               "EMAMILTD.NS",
    "Jyothy Labs":         "JYOTHYLAB.NS",
    "Mrs Bectors Food":    "BECTORFOOD.NS",
    "Bikaji Foods":        "BIKAJI.NS",
    "Prataap Snacks":      "DIAMONDYD.NS",
    "Patanjali Foods":     "PATANJALI.NS",
    "Agro Tech Foods":     "ATFL.NS",
    # ── Auto & Auto Ancillary ─────────────────────────────────────────────────
    "Maruti Suzuki":       "MARUTI.NS",
    "Tata Motors":         "TATAMOTORS.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Hero MotoCorp":       "HEROMOTOCO.NS",
    "Bajaj Auto":          "BAJAJ-AUTO.NS",
    "Eicher Motors":       "EICHERMOT.NS",
    "TVS Motor":           "TVSMOTOR.NS",
    "Ashok Leyland":       "ASHOKLEY.NS",
    "Bosch":               "BOSCHLTD.NS",
    "MRF":                 "MRF.NS",
    "Apollo Tyres":        "APOLLOTYRE.NS",
    "CEAT":                "CEATLTD.NS",
    "Exide Industries":    "EXIDEIND.NS",
    "Amara Raja":          "AMARAJABAT.NS",
    "Motherson Sumi":      "MOTHERSUMI.NS",
    "Minda Industries":    "MINDAIND.NS",
    "Bharat Forge":        "BHARATFORG.NS",
    "Endurance Tech":      "ENDURANCE.NS",
    "Samvardhana Motherson":"MOTHERSON.NS",
    "Sona BLW":            "SONACOMS.NS",
    "Uno Minda":           "UNOMINDA.NS",
    "Suprajit Engineering":"SUPRAJIT.NS",
    "Lumax Industries":    "LUMAXIND.NS",
    # ── Pharma & Healthcare ───────────────────────────────────────────────────
    "Sun Pharmaceutical":  "SUNPHARMA.NS",
    "Dr Reddys":           "DRREDDY.NS",
    "Cipla":               "CIPLA.NS",
    "Divis Laboratories":  "DIVISLAB.NS",
    "Biocon":              "BIOCON.NS",
    "Lupin":               "LUPIN.NS",
    "Aurobindo Pharma":    "AUROPHARMA.NS",
    "Torrent Pharma":      "TORNTPHARM.NS",
    "Alkem Labs":          "ALKEM.NS",
    "Abbott India":        "ABBOTINDIA.NS",
    "Max Healthcare":      "MAXHEALTH.NS",
    "Apollo Hospitals":    "APOLLOHOSP.NS",
    "Fortis Healthcare":   "FORTIS.NS",
    "Zydus Lifesciences":  "ZYDUSLIFE.NS",
    "Gland Pharma":        "GLAND.NS",
    "Laurus Labs":         "LAURUSLABS.NS",
    "Ipca Labs":           "IPCALAB.NS",
    "Natco Pharma":        "NATCOPHARM.NS",
    "Ajanta Pharma":       "AJANTPHARM.NS",
    "JB Chemicals":        "JBCHEPHARM.NS",
    "Sanofi India":        "SANOFI.NS",
    "Pfizer India":        "PFIZER.NS",
    "GlaxoSmith Pharma":   "GLAXO.NS",
    "Suven Pharma":        "SUVENPHAR.NS",
    "Metropolis Health":   "METROPOLIS.NS",
    "Dr Lal Pathlabs":     "LALPATHLAB.NS",
    "Krishna Institute":   "KIMS.NS",
    # ── Energy & Oil ─────────────────────────────────────────────────────────
    "Reliance Industries": "RELIANCE.NS",
    "ONGC":                "ONGC.NS",
    "Coal India":          "COALINDIA.NS",
    "NTPC":                "NTPC.NS",
    "Power Grid":          "POWERGRID.NS",
    "Adani Enterprises":   "ADANIENT.NS",
    "Adani Ports":         "ADANIPORTS.NS",
    "Adani Green":         "ADANIGREEN.NS",
    "Adani Power":         "ADANIPOWER.NS",
    "Tata Power":          "TATAPOWER.NS",
    "BHEL":                "BHEL.NS",
    "GAIL":                "GAIL.NS",
    "IOC":                 "IOC.NS",
    "BPCL":                "BPCL.NS",
    "Hindustan Petroleum": "HINDPETRO.NS",
    "Torrent Power":       "TORNTPOWER.NS",
    "JSW Energy":          "JSWENERGY.NS",
    "Cesc":                "CESC.NS",
    "Gujarat Gas":         "GUJGASLTD.NS",
    "Petronet LNG":        "PETRONET.NS",
    "GSPL":                "GSPL.NS",
    "Oil India":           "OIL.NS",
    "MRPL":                "MRPL.NS",
    # ── Metals & Mining ───────────────────────────────────────────────────────
    "Tata Steel":          "TATASTEEL.NS",
    "JSW Steel":           "JSWSTEEL.NS",
    "Hindalco":            "HINDALCO.NS",
    "Vedanta":             "VEDL.NS",
    "SAIL":                "SAIL.NS",
    "NMDC":                "NMDC.NS",
    "Jindal Steel":        "JINDALSTEL.NS",
    "APL Apollo Tubes":    "APLAPOLLO.NS",
    "Ratnamani Metals":    "RATNAMANI.NS",
    "Welspun Corp":        "WELCORP.NS",
    "National Aluminium":  "NATIONALUM.NS",
    "MOIL":                "MOIL.NS",
    "Hindustan Zinc":      "HINDZINC.NS",
    "Lloyds Metals":       "LLOYDSME.NS",
    # ── Infra & Capital Goods ────────────────────────────────────────────────
    "Larsen & Toubro":     "LT.NS",
    "Siemens India":       "SIEMENS.NS",
    "ABB India":           "ABB.NS",
    "Havells India":       "HAVELLS.NS",
    "Voltas":              "VOLTAS.NS",
    "Polycab":             "POLYCAB.NS",
    "KEI Industries":      "KEI.NS",
    "Cummins India":       "CUMMINSIND.NS",
    "Bharat Electronics":  "BEL.NS",
    "HAL":                 "HAL.NS",
    "IRCTC":               "IRCTC.NS",
    "Dixon Technologies":  "DIXON.NS",
    "Crompton":            "CROMPTON.NS",
    "Blue Star":           "BLUESTARCO.NS",
    "V-Guard":             "VGUARD.NS",
    "Finolex Cables":      "FNXCAB.NS",
    "Schaeffler India":    "SCHAEFFLER.NS",
    "SKF India":           "SKFINDIA.NS",
    "Timken India":        "TIMKEN.NS",
    "Grindwell Norton":    "GRINDWELL.NS",
    "KEC International":   "KEC.NS",
    "Kalpataru Power":     "KPIL.NS",
    "Thermax":             "THERMAX.NS",
    "Bharat Heavy":        "BHEL.NS",
    "NCC Ltd":             "NCC.NS",
    "PNC Infratech":       "PNCINFRA.NS",
    "IRB Infrastructure":  "IRB.NS",
    "G R Infraprojects":   "GRINFRA.NS",
    # ── Telecom & New Age ────────────────────────────────────────────────────
    "Bharti Airtel":       "BHARTIARTL.NS",
    "Indus Towers":        "INDUSTOWER.NS",
    "Zomato":              "ZOMATO.NS",
    "Paytm":               "PAYTM.NS",
    "Nykaa":               "NYKAA.NS",
    "PolicyBazaar":        "POLICYBZR.NS",
    "Delhivery":           "DELHIVERY.NS",
    "Info Edge":           "NAUKRI.NS",
    "Just Dial":           "JUSTDIAL.NS",
    "Trent":               "TRENT.NS",
    "Indiamart":           "INDIAMART.NS",
    "MapMyIndia":          "MAPMYINDIA.NS",
    "PB Fintech":          "POLICYBZR.NS",
    # ── Real Estate ───────────────────────────────────────────────────────────
    "DLF":                 "DLF.NS",
    "Godrej Properties":   "GODREJPROP.NS",
    "Oberoi Realty":       "OBEROIRLTY.NS",
    "Prestige Estates":    "PRESTIGE.NS",
    "Sobha":               "SOBHA.NS",
    "Brigade Enterprises": "BRIGADE.NS",
    "Mahindra Lifespace":  "MAHLIFE.NS",
    "Kolte Patil":         "KOLTEPATIL.NS",
    "Embassy REIT":        "EMBASSY.NS",
    "Mindspace REIT":      "MINDSPACE.NS",
    # ── Specialty & Consumer ─────────────────────────────────────────────────
    "Asian Paints":        "ASIANPAINT.NS",
    "Berger Paints":       "BERGEPAINT.NS",
    "Pidilite":            "PIDILITIND.NS",
    "SRF Ltd":             "SRF.NS",
    "Aarti Industries":    "AARTIIND.NS",
    "PI Industries":       "PIIND.NS",
    "UPL":                 "UPL.NS",
    "Deepak Nitrite":      "DEEPAKNTR.NS",
    "Navin Fluorine":      "NAVINFLUOR.NS",
    "Astral":              "ASTRAL.NS",
    "Supreme Industries":  "SUPREMEIND.NS",
    "Avenue Supermarts":   "DMART.NS",
    "Titan Company":       "TITAN.NS",
    "Jubilant Foodworks":  "JUBLFOOD.NS",
    "Page Industries":     "PAGEIND.NS",
    "Relaxo Footwears":    "RELAXO.NS",
    "Bata India":          "BATAINDIA.NS",
    "Kalyan Jewellers":    "KALYANKJIL.NS",
    "PC Jeweller":         "PCJEWELLER.NS",
    "Amber Enterprises":   "AMBER.NS",
    "Whirlpool India":     "WHIRLPOOL.NS",
    "Polycab India":       "POLYCAB.NS",
    "Orient Electric":     "ORIENTELEC.NS",
    "Havells India":       "HAVELLS.NS",
    "Crompton Greaves":    "CROMPTON.NS",
    "Finolex Industries":  "FINPIPE.NS",
    "Cera Sanitaryware":   "CERA.NS",
    "Kajaria Ceramics":    "KAJARIACER.NS",
    "Somany Ceramics":     "SOMANYCERA.NS",
    "Wonderla Holidays":   "WONDERLA.NS",
    "PVR Inox":            "PVRINOX.NS",
    "Zee Entertainment":   "ZEEL.NS",
    "Sun TV":              "SUNTV.NS",
    # ── Chemicals & Agri ─────────────────────────────────────────────────────
    "Coromandel Intl":     "COROMANDEL.NS",
    "Chambal Fertilizers": "CHAMBLFERT.NS",
    "GNFC":                "GNFC.NS",
    "Gujarat Fluorochem":  "FLUOROCHEM.NS",
    "Bayer Cropscience":   "BAYERCROP.NS",
    "Dhanuka Agritech":    "DHANUKA.NS",
    "Rallis India":        "RALLIS.NS",
    "Excel Industries":    "EXCELINDUS.NS",
    "Vinati Organics":     "VINATIORGA.NS",
    "Atul Ltd":            "ATUL.NS",
    "Tata Chemicals":      "TATACHEM.NS",
    "Ghcl":                "GHCL.NS",
}

SECTOR_MAP = {
    "Banking & Finance": ["Bank","Finance","Housing","Insurance","Muthoot",
                          "Cholamandalam","Shriram","PFC","REC","IDFC",
                          "Federal","Baroda","Canara","Punjab","Union","Indian"],
    "IT & Technology":   ["TCS","Infosys","HCL","Wipro","Tech Mahindra","LTI",
                          "Mphasis","Persistent","Coforge","Tata Elxsi","KPIT",
                          "Happiest","Tanla","Mastek","Zensar","Birlasoft",
                          "Sonata","Cyient","LTTS","Intellect","Newgen",
                          "Hexaware","Firstsource","NIIT"],
    "FMCG & Consumer":   ["Hindustan","ITC","Nestle","Britannia","Dabur",
                          "Marico","Godrej","Tata Consumer","Varun","United",
                          "Emami","Jyothy","Bectors","Bikaji","Patanjali"],
    "Auto & Ancillary":  ["Maruti","Tata Motors","Mahindra","Hero","Bajaj Auto",
                          "Eicher","TVS","Ashok","Bosch","MRF","Apollo Tyres",
                          "CEAT","Exide","Amara","Motherson","Minda","Bharat Forge",
                          "Endurance","Sona","Uno","Suprajit","Lumax"],
    "Pharma & Health":   ["Sun","Reddys","Cipla","Divis","Biocon","Lupin",
                          "Aurobindo","Torrent","Alkem","Abbott","Max Healthcare",
                          "Apollo Hospitals","Fortis","Zydus","Gland","Laurus",
                          "Ipca","Natco","Ajanta","JB Chem","Sanofi","Pfizer",
                          "GlaxoSmith","Metropolis","Dr Lal","Krishna"],
    "Energy & Oil":      ["Reliance","ONGC","Coal India","NTPC","Power Grid",
                          "Adani","Tata Power","BHEL","GAIL","IOC","BPCL",
                          "Hindustan Petroleum","Torrent Power","JSW Energy",
                          "Cesc","Gujarat Gas","Petronet","Oil India"],
    "Metals & Mining":   ["Tata Steel","JSW Steel","Hindalco","Vedanta","SAIL",
                          "NMDC","Jindal","APL Apollo","Ratnamani","Welspun",
                          "National Aluminium","MOIL","Hindustan Zinc","Lloyds"],
    "Infra & Cap Goods": ["Larsen","Siemens","ABB","Havells","Voltas","Polycab",
                          "KEI","Cummins","Bharat Electronics","HAL","IRCTC",
                          "Dixon","Crompton","Blue Star","V-Guard","KEC",
                          "Kalpataru","Thermax","NCC","PNC","IRB","G R Infra"],
    "Telecom & New Age": ["Bharti","Indus","Zomato","Paytm","Nykaa","Policy",
                          "Delhivery","Info Edge","Just Dial","Trent","Indiamart",
                          "MapMyIndia"],
    "Real Estate":       ["DLF","Godrej Properties","Oberoi","Prestige","Sobha",
                          "Brigade","Mahindra Life","Kolte","Embassy","Mindspace"],
    "Chemicals & Agri":  ["Asian Paints","Berger","Pidilite","SRF","Aarti",
                          "PI Industries","UPL","Deepak","Navin","Astral",
                          "Supreme","Coromandel","Chambal","GNFC","Gujarat Fluoro",
                          "Bayer","Dhanuka","Rallis","Vinati","Atul","Tata Chem"],
    "Consumer & Retail": ["Avenue","Titan","Jubilant","Page","Relaxo","Bata",
                          "Kalyan","Amber","Whirlpool","Orient","Cera","Kajaria",
                          "Somany","PVR","Zee","Sun TV"],
}

@st.cache_data(ttl=300)
def verify_ticker(ticker_symbol):
    try:
        t    = yf.Ticker(ticker_symbol)
        info = t.info
        return {
            "valid":   True,
            "name":    info.get("longName") or info.get("shortName", ticker_symbol),
            "price":   info.get("regularMarketPrice") or info.get("currentPrice", 0),
            "sector":  info.get("sector", "Unknown"),
        }
    except Exception:
        return {"valid": False}

@st.cache_data(ttl=86400)
def fetch_stock_data(ticker_symbol):
    try:
        end = date.today().strftime("%Y-%m-%d")
        raw = yf.download(ticker_symbol, start="2020-01-01", end=end,
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        if raw.empty or "Close" not in raw.columns:
            return None
        s = raw["Close"].squeeze()
        return s if len(s) >= 100 else None
    except Exception:
        return None

def render_stock_search(selected_assets, asset_universe):
    st.markdown("#### NSE Stock Search — 300+ Nifty 500 Stocks")
    st.caption(
        "Search by name or browse by sector. "
        "Added stocks appear in the sidebar for portfolio selection."
    )

    search_tab, browse_tab, custom_tab = st.tabs([
        "🔍 Search by name",
        "📋 Browse by sector",
        "✏️ Custom ticker",
    ])

    # ── Search tab ────────────────────────────────────────────────────────────
    with search_tab:
        query = st.text_input(
            "Type company name",
            placeholder="e.g. Reliance, Tata, HDFC...",
            key="ss_query"
        )
        if query and len(query) >= 2:
            matches = {n: t for n,t in NSE_STOCKS.items()
                       if query.lower() in n.lower()}
            if matches:
                st.caption(f"{len(matches)} results")
                cols = st.columns(3)
                for i,(name,ticker) in enumerate(list(matches.items())[:15]):
                    with cols[i%3]:
                        already = name in selected_assets
                        st.markdown(f"""
                        <div style="background:#161b22;border:1px solid #21262d;
                                    border-radius:8px;padding:10px 12px;margin-bottom:8px;">
                            <div style="font-size:12px;font-weight:600;color:#f0f6fc;">
                                {"✅ " if already else ""}{name}</div>
                            <div style="font-size:10px;color:#6e7681;">{ticker}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if not already:
                            if st.button(f"Add", key=f"add_{ticker}",
                                         use_container_width=True):
                                data = fetch_stock_data(ticker)
                                if data is not None:
                                    asset_universe[name] = (ticker,"Stock-Custom")
                                    selected_assets.append(name)
                                    st.success(f"Added {name}!")
                                    st.rerun()
                                else:
                                    st.error(f"No data for {name}")
                        else:
                            if st.button("Remove", key=f"rem_{ticker}",
                                         use_container_width=True):
                                selected_assets.remove(name)
                                st.rerun()
            else:
                st.info("No matches. Try custom ticker tab.")

    # ── Browse tab ────────────────────────────────────────────────────────────
    with browse_tab:
        sector = st.selectbox("Select sector",
                               ["All"] + list(SECTOR_MAP.keys()),
                               key="ss_sector")
        if sector == "All":
            display = NSE_STOCKS
        else:
            kws = SECTOR_MAP[sector]
            display = {n:t for n,t in NSE_STOCKS.items()
                       if any(k.lower() in n.lower() for k in kws)}

        st.caption(f"{len(display)} stocks in {sector}")
        cols = st.columns(4)
        for i,(name,ticker) in enumerate(display.items()):
            with cols[i%4]:
                already = name in selected_assets
                st.markdown(f"""
                <div style="background:#161b22;border:1px solid #21262d;
                            border-radius:6px;padding:8px 10px;margin-bottom:6px;">
                    <div style="font-size:11px;font-weight:500;color:#f0f6fc;">
                        {"✅ " if already else ""}{name}</div>
                    <div style="font-size:9px;color:#6e7681;">{ticker}</div>
                </div>
                """, unsafe_allow_html=True)
                if not already:
                    if st.button("Add", key=f"br_{ticker}",
                                 use_container_width=True):
                        data = fetch_stock_data(ticker)
                        if data is not None:
                            asset_universe[name] = (ticker,"Stock-Custom")
                            selected_assets.append(name)
                            st.success(f"Added {name}")
                            st.rerun()
                        else:
                            st.error("No data")
                else:
                    if st.button("✓ Added", key=f"br_{ticker}",
                                 use_container_width=True, disabled=True):
                        pass

    # ── Custom ticker tab ──────────────────────────────────────────────────────
    with custom_tab:
        st.markdown("""
        - **NSE stocks:** add `.NS` (e.g. `RELIANCE.NS`)
        - **BSE stocks:** add `.BO` (e.g. `500325.BO`)
        - **US stocks:** as-is (e.g. `AAPL`, `MSFT`)
        """)
        c1,c2 = st.columns([2,1])
        ct = c1.text_input("Ticker symbol",
                            placeholder="RELIANCE.NS",
                            key="ss_ct").strip().upper()
        cn = c2.text_input("Display name",
                            placeholder="Reliance",
                            key="ss_cn").strip()

        if st.button("Search & Add", type="primary", key="ss_add"):
            if ct:
                with st.spinner(f"Searching {ct}..."):
                    info = verify_ticker(ct)
                if info["valid"]:
                    dname = cn or info["name"]
                    st.success(
                        f"Found: **{info['name']}** | "
                        f"Price: Rs.{info['price']:,.2f} | "
                        f"Sector: {info['sector']}"
                    )
                    data = fetch_stock_data(ct)
                    if data is not None and dname not in selected_assets:
                        asset_universe[dname] = (ct,"Stock-Custom")
                        selected_assets.append(dname)
                        st.success(f"Added {dname}!")
                        st.rerun()
                    elif dname in selected_assets:
                        st.info("Already in selection.")
                    else:
                        st.error("Could not load historical data.")
                else:
                    st.error(f"Ticker {ct} not found.")

    # ── Current selection ──────────────────────────────────────────────────────
    if selected_assets:
        st.markdown("---")
        st.markdown(f"**Selected: {len(selected_assets)} assets**")
        cols = st.columns(5)
        for i,a in enumerate(selected_assets):
            with cols[i%5]:
                ticker = asset_universe.get(a,("N/A",""))[0]
                st.markdown(f"""
                <div style="background:#0f3460;border:1px solid #1a4a8a;
                            border-radius:6px;padding:6px 8px;margin-bottom:6px;
                            font-size:11px;color:#e0e0ff;">
                    {a}<br>
                    <span style="color:#555;font-size:9px;">{ticker}</span>
                </div>
                """, unsafe_allow_html=True)

    return selected_assets, asset_universe
