
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

SCENARIOS = {
    "RBI Rate Hike +100bps": {
        "description": "RBI hikes repo rate by 100bps. Negative for equity and debt, positive for short-term bonds.",
        "shocks": {"Equity-LC":-8,"Equity-MC":-12,"Equity-SC":-15,"Sectoral":-10,
                   "Debt-Sov":3,"Debt-TM":-5,"Gold":2,"REIT":-10,"Stock-Bank":-12,
                   "Stock-IT":-6,"Stock-Finance":-10,"Stock-FMCG":-4,"Stock-Auto":-8,
                   "Stock-Pharma":-4,"Stock-Energy":-6,"Stock-Infra":-8,"Stock-Metal":-6,
                   "Stock-Consumer":-5,"Intl-Eq":-5,"Silver":1},
    },
    "Crude Oil hits $120": {
        "description": "Oil spike hurts India macro — INR weakens, inflation rises, CA deficit widens.",
        "shocks": {"Equity-LC":-10,"Equity-MC":-14,"Equity-SC":-18,"Sectoral":-12,
                   "Debt-Sov":-2,"Debt-TM":-4,"Gold":8,"REIT":-8,"Stock-Bank":-8,
                   "Stock-IT":5,"Stock-Finance":-8,"Stock-FMCG":-6,"Stock-Auto":-15,
                   "Stock-Pharma":2,"Stock-Energy":20,"Stock-Infra":-10,"Stock-Metal":5,
                   "Stock-Consumer":-8,"Intl-Eq":-5,"Silver":4},
    },
    "INR Depreciates 10%": {
        "description": "Rupee falls 10% vs USD. Benefits IT exporters, hurts importers and debt.",
        "shocks": {"Equity-LC":-5,"Equity-MC":-6,"Equity-SC":-8,"Sectoral":-4,
                   "Debt-Sov":-3,"Debt-TM":-5,"Gold":8,"REIT":-5,"Stock-Bank":-6,
                   "Stock-IT":15,"Stock-Finance":-5,"Stock-FMCG":-8,"Stock-Auto":-10,
                   "Stock-Pharma":8,"Stock-Energy":-12,"Stock-Infra":-6,"Stock-Metal":5,
                   "Stock-Consumer":-6,"Intl-Eq":8,"Silver":6},
    },
    "Bull Market Rally +20%": {
        "description": "Strong FII inflows, earnings beat, risk-on environment.",
        "shocks": {"Equity-LC":20,"Equity-MC":28,"Equity-SC":35,"Sectoral":22,
                   "Debt-Sov":-1,"Debt-TM":2,"Gold":-3,"REIT":15,"Stock-Bank":22,
                   "Stock-IT":18,"Stock-Finance":25,"Stock-FMCG":12,"Stock-Auto":25,
                   "Stock-Pharma":14,"Stock-Energy":20,"Stock-Infra":28,"Stock-Metal":30,
                   "Stock-Consumer":18,"Intl-Eq":15,"Silver":5},
    },
    "Global Recession": {
        "description": "US recession, FII outflows, earnings cuts. Risk-off globally.",
        "shocks": {"Equity-LC":-25,"Equity-MC":-32,"Equity-SC":-40,"Sectoral":-28,
                   "Debt-Sov":5,"Debt-TM":2,"Gold":12,"REIT":-20,"Stock-Bank":-28,
                   "Stock-IT":-20,"Stock-Finance":-30,"Stock-FMCG":-10,"Stock-Auto":-30,
                   "Stock-Pharma":-8,"Stock-Energy":-22,"Stock-Infra":-25,"Stock-Metal":-35,
                   "Stock-Consumer":-15,"Intl-Eq":-25,"Silver":8},
    },
    "India Election Uncertainty": {
        "description": "Pre-election volatility, policy uncertainty, domestic selling.",
        "shocks": {"Equity-LC":-12,"Equity-MC":-16,"Equity-SC":-20,"Sectoral":-14,
                   "Debt-Sov":2,"Debt-TM":1,"Gold":5,"REIT":-10,"Stock-Bank":-12,
                   "Stock-IT":-8,"Stock-Finance":-14,"Stock-FMCG":-6,"Stock-Auto":-12,
                   "Stock-Pharma":-5,"Stock-Energy":-10,"Stock-Infra":-15,"Stock-Metal":-14,
                   "Stock-Consumer":-8,"Intl-Eq":-8,"Silver":3},
    },
}

ASSET_CAT = {
    "Nifty 50":"Equity-LC","Nifty Midcap":"Equity-MC","Nifty Smallcap":"Equity-SC",
    "Nifty IT":"Sectoral","Nifty Pharma":"Sectoral","Nifty Bank":"Sectoral",
    "Nifty Energy":"Sectoral","Nifty Auto":"Sectoral",
    "Nasdaq 100 ETF":"Intl-Eq","S&P 500 ETF":"Intl-Eq",
    "G-Sec Bond":"Debt-Sov","Bharat Bond 2030":"Debt-TM",
    "Gold ETF":"Gold","SGB":"Gold","Silver ETF":"Silver","REIT":"REIT",
    "HDFC Bank":"Stock-Bank","ICICI Bank":"Stock-Bank","Axis Bank":"Stock-Bank",
    "TCS":"Stock-IT","Infosys":"Stock-IT","Wipro":"Stock-IT",
    "Reliance":"Stock-Energy","NTPC":"Stock-Energy",
    "HUL":"Stock-FMCG","ITC":"Stock-FMCG",
    "Sun Pharma":"Stock-Pharma","Dr. Reddys":"Stock-Pharma",
    "Maruti":"Stock-Auto","Tata Motors":"Stock-Auto",
    "L&T":"Stock-Infra","IRCTC":"Stock-Infra",
    "Tata Steel":"Stock-Metal","JSW Steel":"Stock-Metal",
    "Bajaj Finance":"Stock-Finance","Zomato":"Stock-Consumer",
}

def render_scenario_tab(assets, port_weights, total_investable, ann_returns):
    st.markdown("#### Macro Scenario Analysis")
    st.info(
        "Scenario analysis shows how your portfolio behaves under different "
        "macroeconomic conditions. Each scenario applies historically-calibrated "
        "shocks to different asset categories. This is used by PMS firms and "
        "family offices to stress-test client portfolios before major events."
    )

    # ── Predefined scenarios ──────────────────────────────────────────────────
    st.markdown("**Run a Macro Scenario**")
    selected_scenario = st.selectbox(
        "Select scenario", list(SCENARIOS.keys()), key="scenario_select")

    sc = SCENARIOS[selected_scenario]
    st.caption(sc["description"])

    def apply_scenario(shocks):
        total_impact = 0.0
        rows = []
        for i, asset in enumerate(assets):
            w   = port_weights[i]
            cat = ASSET_CAT.get(asset, "Equity-LC")
            shock_pct = shocks.get(cat, shocks.get("Equity-LC", -10))
            impact    = w * shock_pct / 100
            total_impact += impact
            rows.append({
                "Asset":    asset,
                "Weight":   f"{w*100:.1f}%",
                "Shock":    f"{shock_pct:+.1f}%",
                "Impact":   f"{impact*100:+.2f}%",
                "Rs. P&L":  f"Rs.{total_investable*impact:+,.0f}",
            })
        return rows, total_impact * 100

    rows, total_pct = apply_scenario(sc["shocks"])

    # KPIs
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Portfolio Impact",   f"{total_pct:+.2f}%")
    sc2.metric("Rs. Impact",         f"Rs.{total_investable*total_pct/100:+,.0f}")
    sc3.metric("Value After Shock",  f"Rs.{total_investable*(1+total_pct/100):,.0f}")

    # Waterfall chart
    fig_wf = go.Figure()
    sorted_rows = sorted(rows, key=lambda x: float(x["Impact"].replace("%","").replace("+","")))
    assets_wf   = [r["Asset"] for r in sorted_rows]
    impacts_wf  = [float(r["Impact"].replace("%","").replace("+","")) for r in sorted_rows]
    colors_wf   = ["#4CAF50" if v >= 0 else "#FF5722" for v in impacts_wf]

    fig_wf.add_trace(go.Bar(
        x=assets_wf, y=impacts_wf,
        marker_color=colors_wf,
        text=[f"{v:+.2f}%" for v in impacts_wf],
        textposition="outside",
    ))
    fig_wf.update_layout(
        paper_bgcolor="#0e0e1a", plot_bgcolor="#1a1a2e",
        font_color="white",
        title=f"Asset Contribution to Portfolio Impact — {selected_scenario}",
        xaxis_title="Asset", yaxis_title="Portfolio Impact (%)",
        margin=dict(t=50,b=100,l=50,r=20), height=400,
        xaxis_tickangle=-35,
    )
    st.plotly_chart(fig_wf, use_container_width=True)
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    # ── Compare all scenarios ─────────────────────────────────────────────────
    st.markdown("**All Scenarios Comparison**")
    comp_rows = []
    for sc_name, sc_data in SCENARIOS.items():
        _, impact = apply_scenario(sc_data["shocks"])
        comp_rows.append({
            "Scenario":       sc_name,
            "Portfolio Impact":f"{impact:+.2f}%",
            "Rs. Impact":      f"Rs.{total_investable*impact/100:+,.0f}",
            "Value After":     f"Rs.{total_investable*(1+impact/100):,.0f}",
            "Risk Level":      "High" if impact < -15 else "Medium" if impact < -5 else "Low",
        })

    comp_df = pd.DataFrame(comp_rows)
    st.dataframe(comp_df, hide_index=True, use_container_width=True)

    # Scenario comparison bar
    fig_comp = go.Figure()
    sc_names   = [r["Scenario"] for r in comp_rows]
    sc_impacts = [float(r["Portfolio Impact"].replace("%","").replace("+",""))
                  for r in comp_rows]
    fig_comp.add_trace(go.Bar(
        x=sc_names, y=sc_impacts,
        marker_color=["#4CAF50" if v >= 0 else "#FF5722" for v in sc_impacts],
        text=[f"{v:+.1f}%" for v in sc_impacts],
        textposition="outside",
    ))
    fig_comp.add_hline(y=0, line_color="white", line_width=1)
    fig_comp.update_layout(
        paper_bgcolor="#0e0e1a", plot_bgcolor="#1a1a2e",
        font_color="white",
        title="Portfolio Sensitivity Across All Scenarios",
        xaxis_title="Scenario", yaxis_title="Impact (%)",
        margin=dict(t=50,b=120,l=50,r=20), height=420,
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # ── Custom scenario builder ───────────────────────────────────────────────
    st.markdown("**Custom Scenario Builder**")
    st.caption("Build your own macro scenario by setting custom shocks per asset category.")

    cc1, cc2, cc3, cc4 = st.columns(4)
    c_eq  = cc1.slider("Large Cap Equity (%)", -50, 50, -10, key="c_eq")
    c_mc  = cc2.slider("Mid/Small Cap (%)",    -60, 60, -15, key="c_mc")
    c_dbt = cc3.slider("Debt/Bonds (%)",       -20, 20,   2, key="c_dbt")
    c_gld = cc4.slider("Gold (%)",             -20, 30,   5, key="c_gld")
    cc5, cc6, cc7, cc8 = st.columns(4)
    c_it  = cc5.slider("IT Stocks (%)",        -40, 40,  -8, key="c_it")
    c_bk  = cc6.slider("Bank Stocks (%)",      -40, 40, -12, key="c_bk")
    c_pha = cc7.slider("Pharma (%)",           -30, 30,  -5, key="c_pha")
    c_int = cc8.slider("International (%)",    -30, 30,  -8, key="c_int")

    custom_shocks = {
        "Equity-LC":c_eq,"Equity-MC":c_mc,"Equity-SC":c_mc-5,
        "Sectoral":c_eq-2,"Debt-Sov":c_dbt,"Debt-TM":c_dbt-2,
        "Gold":c_gld,"Silver":c_gld-2,"REIT":c_eq-3,
        "Stock-IT":c_it,"Stock-Bank":c_bk,"Stock-Pharma":c_pha,
        "Stock-Finance":c_bk-3,"Stock-FMCG":c_eq-3,"Stock-Auto":c_mc,
        "Stock-Energy":c_eq,"Stock-Infra":c_mc,"Stock-Metal":c_mc+5,
        "Stock-Consumer":c_eq-2,"Intl-Eq":c_int,
    }
    custom_rows, custom_total = apply_scenario(custom_shocks)
    cst1, cst2 = st.columns(2)
    cst1.metric("Custom Scenario Impact", f"{custom_total:+.2f}%")
    cst2.metric("Rs. Impact",             f"Rs.{total_investable*custom_total/100:+,.0f}")
