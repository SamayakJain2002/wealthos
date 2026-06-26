import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from scipy.optimize import minimize
from scipy import stats
from datetime import date, timedelta

RISK_FREE = 0.065
PROFILE_NAMES  = {1:"Conservative",2:"Mod. Conservative",
                  3:"Balanced",4:"Mod. Aggressive",5:"Aggressive"}
PROFILE_COLORS = {1:"#2196F3",2:"#4CAF50",3:"#FF9800",4:"#FF5722",5:"#9C27B0"}

def compute_portfolio_metrics(weights, daily_returns, ann_returns, cov, assets):
    w = np.array(weights)
    ret = float(np.dot(w, ann_returns.values))
    vol = float(np.sqrt(w @ cov @ w))
    sharpe = (ret - RISK_FREE) / vol if vol > 0 else 0

    pr = daily_returns.values @ w
    dn = pr[pr < RISK_FREE/252]
    ds = np.std(dn)*np.sqrt(252) if len(dn) > 0 else 1
    sortino = (ret - RISK_FREE) / ds if ds > 0 else 0

    beta = 1.0
    alpha = 0.0
    if "Nifty 50" in assets:
        idx = assets.index("Nifty 50")
        nr  = daily_returns.iloc[:,idx].values
        ml  = min(len(pr), len(nr))
        try:
            slope,_,_,_,_ = stats.linregress(nr[:ml], pr[:ml])
            beta  = round(slope, 3)
            nr_ann = float(ann_returns.iloc[idx])
            alpha = round((ret-(RISK_FREE+beta*(nr_ann-RISK_FREE)))*100, 2)
        except Exception:
            pass

    cum = np.cumprod(1+pr)
    rm  = np.maximum.accumulate(cum)
    max_dd = round(((cum-rm)/rm).min()*100, 2)
    var95  = round(np.percentile(pr, 5)*100, 2)

    return {
        "weights": w,
        "return":  round(ret, 4),
        "vol":     round(vol, 4),
        "sharpe":  round(sharpe, 4),
        "sortino": round(sortino, 4),
        "beta":    beta,
        "alpha":   alpha,
        "max_dd":  max_dd,
        "var95":   var95,
    }

def get_optimizer_bounds(pid, asset_list, asset_universe):
    is_stock = lambda a: asset_universe.get(a, ("",""))[1].startswith("Stock-")
    is_debt  = lambda a: asset_universe.get(a, ("",""))[1] in ("Debt-Sov","Debt-TM","Liquid")
    is_gold  = lambda a: asset_universe.get(a, ("",""))[1] in ("Gold","Silver","Gold-SGB")
    is_alt   = lambda a: asset_universe.get(a, ("",""))[1] in ("REIT","InvIT")

    eq_bud  = {1:0.10,2:0.28,3:0.52,4:0.68,5:0.82}[pid]
    stk_bud = {1:0.02,2:0.05,3:0.10,4:0.15,5:0.22}[pid]
    db_bud  = {1:0.72,2:0.52,3:0.32,4:0.18,5:0.08}[pid]

    n_eq  = max(sum(1 for a in asset_list
                    if not is_stock(a) and not is_debt(a)
                    and not is_gold(a) and not is_alt(a)), 1)
    n_stk = max(sum(1 for a in asset_list if is_stock(a)), 1)
    n_db  = max(sum(1 for a in asset_list if is_debt(a)), 1)
    n_gl  = max(sum(1 for a in asset_list if is_gold(a)), 1)

    bounds = []
    for a in asset_list:
        if is_stock(a):
            bounds.append((0.0, min(stk_bud/n_stk*3, 0.15)))
        elif is_debt(a):
            bounds.append((0.01, min(db_bud/n_db*2, 0.65)))
        elif is_gold(a):
            bounds.append((0.01, min(0.15/n_gl*2, 0.20)))
        elif is_alt(a):
            bounds.append((0.0, 0.12))
        else:
            bounds.append((0.0, min(eq_bud/n_eq*2.5, 0.50)))
    return bounds

def render_portfolio_builder(daily_returns, ann_returns, cov,
                              assets, prices, pid, asset_universe,
                              total_investable, monthly_sip,
                              annual_topup, goal_amount, goal_years,
                              inflation, name_disp):

    n = len(assets)

    def neg_sharpe(w):
        r = float(np.dot(w, ann_returns.values))
        v = float(np.sqrt(w @ cov @ w))
        return -(r-RISK_FREE)/v if v > 0 else 0

    st.markdown("### Portfolio Builder")
    st.caption(
        "This tab is the control center. "
        "Everything you set here flows automatically into all other tabs."
    )

    mode = st.radio(
        "How do you want to build your portfolio?",
        ["🤖 Let the optimizer decide (recommended)",
         "✍️ I will set my own allocation"],
        horizontal=True,
        key="pb_mode_selector"
    )

    # ── OPTIMIZER MODE ────────────────────────────────────────────────────────
    if "optimizer" in mode:
        st.info(
            f"Based on your **{PROFILE_NAMES[pid]}** risk profile, "
            f"the optimizer will find the best allocation across your "
            f"selected {n} assets to maximise risk-adjusted return."
        )

        w0   = np.array([1/n]*n)
        cons = {"type":"eq","fun":lambda w: np.sum(w)-1}
        try:
            res = minimize(neg_sharpe, w0, method="SLSQP",
                           bounds=get_optimizer_bounds(pid, assets, asset_universe),
                           constraints=cons,
                           options={"maxiter":1000,"ftol":1e-9})
            weights = res.x
        except Exception:
            weights = w0.copy()

        weights = np.clip(weights, 0, None)
        if weights.sum() > 0:
            weights = weights / weights.sum()

        metrics = compute_portfolio_metrics(
            weights, daily_returns, ann_returns, cov, assets)

        st.session_state["active_weights"] = weights.tolist()
        st.session_state["active_metrics"] = metrics
        st.session_state["active_assets"]  = assets

        col_pie, col_tbl = st.columns([1,1])

        with col_pie:
            nz = [(weights[i], a) for i,a in enumerate(assets) if weights[i]>0.003]
            fig = go.Figure(go.Pie(
                labels=[x[1] for x in nz],
                values=[x[0] for x in nz],
                hole=0.45, textfont_size=10,
                marker=dict(line=dict(color="#0a0a14",width=1.5))
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white", height=300,
                margin=dict(t=10,b=10,l=10,r=10),
                legend=dict(bgcolor="rgba(0,0,0,0)",font_size=10),
                title=dict(
                    text=f"Optimal — {PROFILE_NAMES[pid]}",
                    font_color=PROFILE_COLORS[pid])
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_tbl:
            rows = []
            for i, a in enumerate(assets):
                w = weights[i]
                if w > 0.003:
                    cat = ""
                    au_val = asset_universe.get(a)
                    if au_val and len(au_val) > 1:
                        cat = str(au_val[1])
                    rows.append({
                        "Asset":   a,
                        "Weight":  f"{w*100:.1f}%",
                        "Amount":  f"Rs.{w*total_investable:,.0f}",
                        "Exp.Ret": f"{ann_returns[a]*100:.1f}%",
                        "Cat":     cat,
                    })
            if rows:
                st.dataframe(pd.DataFrame(rows),
                             hide_index=True, use_container_width=True)

    # ── MANUAL MODE ───────────────────────────────────────────────────────────
    else:
        st.info(
            "Set your own allocation below. "
            "Weights must add up to 100%."
        )
        st.markdown("**Set allocation for each asset (%)**")

        default_w = {a: round(100/n, 1) for a in assets}
        manual_weights = {}
        cols = st.columns(3)

        for i, a in enumerate(assets):
            with cols[i % 3]:
                w = st.number_input(
                    f"{a} (%)",
                    min_value=0.0, max_value=100.0,
                    value=default_w[a], step=0.5,
                    key=f"manual_w_{a}", format="%.1f"
                )
                manual_weights[a] = w

        total_w = sum(manual_weights.values())
        st.progress(min(total_w/100, 1.0))

        if abs(total_w - 100) < 0.1:
            st.success(f"Total: {total_w:.1f}% — Perfect!")
        elif total_w > 100:
            st.error(f"Total: {total_w:.1f}% — Reduce by {total_w-100:.1f}%")
        else:
            st.warning(f"Total: {total_w:.1f}% — {100-total_w:.1f}% unallocated")

        if total_w > 0:
            weights = np.array([manual_weights[a]/100 for a in assets])
            weights = weights / weights.sum()
        else:
            weights = np.array([1/n]*n)

        metrics = compute_portfolio_metrics(
            weights, daily_returns, ann_returns, cov, assets)

        st.session_state["active_weights"] = weights.tolist()
        st.session_state["active_metrics"] = metrics
        st.session_state["active_assets"]  = assets

        nz = [(weights[i], a) for i,a in enumerate(assets) if weights[i]>0.005]
        if nz:
            fig = go.Figure(go.Pie(
                labels=[x[1] for x in nz],
                values=[x[0] for x in nz],
                hole=0.45, textfont_size=10,
                marker=dict(line=dict(color="#0a0a14",width=1.5))
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="white", height=280,
                margin=dict(t=10,b=10,l=10,r=10),
                legend=dict(bgcolor="rgba(0,0,0,0)",font_size=10),
                title=dict(text="Your Custom Allocation",font_color="#FF9800")
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Portfolio metrics ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Your Portfolio Risk Metrics")
    st.caption("These metrics update live based on your allocation above.")

    m = metrics
    mc1,mc2,mc3,mc4,mc5,mc6,mc7 = st.columns(7)
    mc1.metric("Annual Return",  f"{m['return']*100:.2f}%")
    mc2.metric("Volatility",     f"{m['vol']*100:.2f}%")
    mc3.metric("Sharpe Ratio",   f"{m['sharpe']:.3f}")
    mc4.metric("Sortino Ratio",  f"{m['sortino']:.3f}")
    mc5.metric("Beta",           f"{m['beta']:.3f}")
    mc6.metric("Max Drawdown",   f"{m['max_dd']:.1f}%")
    mc7.metric("VaR 95%",        f"{m['var95']:.2f}%")

    # ── Wealth projection ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Wealth Projection")

    ann_r  = m["return"]
    mo_r   = ann_r/12
    mo_tot = goal_years*12
    lf     = total_investable*(1+ann_r)**goal_years
    sf     = (monthly_sip*(((1+mo_r)**mo_tot-1)/mo_r)
              if mo_r > 0 and monthly_sip > 0 else 0)
    tf     = (sum(annual_topup*(1+ann_r)**(goal_years-y)
                  for y in range(1, goal_years+1))
              if annual_topup > 0 else 0)
    total_f = lf+sf+tf
    total_i = total_investable+monthly_sip*mo_tot+annual_topup*goal_years

    wc1,wc2,wc3,wc4 = st.columns(4)
    wc1.metric("Lump Sum Grows To", f"Rs.{lf/1e6:.2f}M")
    wc2.metric("SIP Corpus",        f"Rs.{sf/1e6:.2f}M")
    wc3.metric("Top-up Corpus",     f"Rs.{tf/1e6:.2f}M")
    wc4.metric("Total Wealth",      f"Rs.{total_f/1e6:.2f}M",
               delta=f"+Rs.{(total_f-total_i)/1e6:.2f}M")

    if total_f >= goal_amount:
        st.success(
            f"On track to reach your goal of Rs.{goal_amount/1e6:.1f}M "
            f"in {goal_years} years!")
    else:
        st.warning(
            f"Shortfall of Rs.{(goal_amount-total_f)/1e6:.2f}M vs goal. "
            f"Consider increasing SIP or adjusting allocation.")

    yr_r = list(range(goal_years+1))
    lv   = [total_investable*(1+ann_r)**y for y in yr_r]
    sv   = [(monthly_sip*(((1+mo_r)**(y*12)-1)/mo_r)
             if mo_r>0 and y>0 else 0) for y in yr_r]
    tv2  = [(sum(annual_topup*(1+ann_r)**(y-yr)
                 for yr in range(1,y+1)) if y>0 else 0) for y in yr_r]

    fig_w = go.Figure()
    fig_w.add_trace(go.Scatter(
        x=yr_r, y=[v/1e6 for v in lv],
        fill="tozeroy", name="Lump Sum",
        line_color="#FF5722", fillcolor="rgba(255,87,34,0.2)"))
    fig_w.add_trace(go.Scatter(
        x=yr_r, y=[(l+s)/1e6 for l,s in zip(lv,sv)],
        fill="tonexty", name="+ SIP",
        line_color="#4CAF50", fillcolor="rgba(76,175,80,0.2)"))
    fig_w.add_trace(go.Scatter(
        x=yr_r, y=[(l+s+t)/1e6 for l,s,t in zip(lv,sv,tv2)],
        fill="tonexty", name="+ Top-up",
        line_color="#2196F3", fillcolor="rgba(33,150,243,0.2)"))
    fig_w.add_hline(
        y=goal_amount/1e6, line_dash="dash",
        line_color="white", line_width=1.2,
        annotation_text=f"Goal Rs.{goal_amount/1e6:.1f}M")
    fig_w.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#1a1a2e",
        font_color="white",
        xaxis_title="Year", yaxis_title="Rs. Million",
        height=320, margin=dict(t=20,b=40,l=50,r=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h"))
    st.plotly_chart(fig_w, use_container_width=True)

    # ── Asset statistics ──────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Asset Statistics")

    one_yr = pd.Timestamp(date.today()-timedelta(days=365))
    stat_rows = []
    for i, a in enumerate(assets):
        try:
            r1y = (prices[a].iloc[-1]/prices[a].asof(one_yr)-1)*100
        except Exception:
            r1y = 0.0
        v = np.sqrt(cov[i,i])
        stat_rows.append({
            "Asset":      a,
            "Allocation": f"{weights[i]*100:.1f}%",
            "Amount":     f"Rs.{weights[i]*total_investable:,.0f}",
            "Ann.Return": f"{ann_returns[a]*100:.1f}%",
            "Volatility": f"{v*100:.1f}%",
            "Sharpe":     f"{(ann_returns[a]-RISK_FREE)/v:.2f}" if v>0 else "N/A",
            "1Y Return":  f"{r1y:.1f}%",
            "Signal":     ("🟢 Buy" if r1y>10 else
                           "🟡 Hold" if r1y>0 else "🔴 Caution"),
        })

    st.dataframe(pd.DataFrame(stat_rows),
                 hide_index=True, use_container_width=True)

    return weights, metrics
