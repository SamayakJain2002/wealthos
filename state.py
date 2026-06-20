
# state.py — Single source of truth for all tab data
# Every tab reads from and writes to this shared state

import streamlit as st

def init_state():
    """Initialise all session state variables once on app load."""
    defaults = {
        # Client info
        "client_name":       "",
        "client_age":        28,
        "client_city":       "",
        # Financial inputs
        "total_investable":  5000000,
        "monthly_sip":       50000,
        "annual_topup":      500000,
        "inv_goal":          "Wealth creation",
        "goal_amount":       20000000,
        "goal_years":        10,
        "inflation":         0.06,
        # Risk profile
        "risk_scores":       [3,3,3,3,3,3,3,3,3,3],
        "risk_pid":          3,
        "risk_total":        30,
        # Portfolio — set after optimisation
        "port_weights":      None,
        "port_return":       None,
        "port_vol":          None,
        "port_sharpe":       None,
        "port_sortino":      None,
        "port_beta":         None,
        "port_alpha":        None,
        "port_maxdd":        None,
        "port_var95":        None,
        # Selected assets
        "selected_assets":   [],
        # Data
        "daily_returns":     None,
        "ann_returns":       None,
        "cov_matrix":        None,
        "assets":            [],
        "prices":            None,
        "data_date":         "",
        # UI state
        "page":              "landing",   # landing or app
        "active_tab":        0,
        # Price alerts
        "price_alerts":      [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def get(key):
    return st.session_state.get(key)

def set(key, value):
    st.session_state[key] = value

def get_port():
    """Returns current portfolio dict from session state."""
    return {
        "weights": st.session_state.get("port_weights"),
        "return":  st.session_state.get("port_return",  0.15),
        "vol":     st.session_state.get("port_vol",     0.15),
        "sharpe":  st.session_state.get("port_sharpe",  0.5),
        "sortino": st.session_state.get("port_sortino", 0.6),
        "beta":    st.session_state.get("port_beta",    0.8),
        "alpha":   st.session_state.get("port_alpha",   2.0),
        "max_dd":  st.session_state.get("port_maxdd",   -15.0),
        "var95":   st.session_state.get("port_var95",   -1.5),
    }
