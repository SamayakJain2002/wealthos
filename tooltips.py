
import streamlit as st

# Dictionary of all financial terms used in WealthOS
TERMS = {
    "Sharpe Ratio": {
        "simple": "A measure of how much return you earn for each unit of risk taken.",
        "detail": (
            "Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Volatility. "
            "A Sharpe of 1.0 means you earn 1% extra return for every 1% of risk. "
            "Above 0.5 is considered good. Above 1.0 is excellent. "
            "A higher Sharpe means better risk-adjusted performance."
        ),
        "example": "If your portfolio returns 15% and has 10% volatility, "
                   "with a 6.5% risk-free rate, Sharpe = (15-6.5)/10 = 0.85",
    },
    "Sortino Ratio": {
        "simple": "Like Sharpe Ratio, but only counts downward risk — not upside surprises.",
        "detail": (
            "Sortino only penalises bad volatility (losses), not good volatility (gains). "
            "This makes it a fairer measure for investors who don't mind their portfolio "
            "going up sharply but want to minimise downside. "
            "A higher Sortino = better protection against losses."
        ),
        "example": "If your portfolio occasionally jumps 5% in a day, "
                   "Sharpe would penalise that. Sortino would not.",
    },
    "Beta": {
        "simple": "How much your portfolio moves when the Nifty 50 moves.",
        "detail": (
            "Beta of 1.0 means your portfolio moves exactly with Nifty 50. "
            "Beta of 0.7 means if Nifty falls 10%, your portfolio falls ~7%. "
            "Beta below 1.0 = less volatile than the market. "
            "Beta above 1.0 = more volatile than the market. "
            "Conservative portfolios typically have Beta 0.3-0.6."
        ),
        "example": "Debt funds have Beta near 0. Smallcap funds have Beta above 1.2.",
    },
    "Alpha": {
        "simple": "The extra return your portfolio earns beyond what the market explains.",
        "detail": (
            "Alpha measures skill or edge. If the market (Nifty 50) went up 12% "
            "and your portfolio went up 15%, your Alpha is roughly +3%. "
            "Positive Alpha means your asset selection or allocation added value. "
            "Most mutual funds have near-zero or negative Alpha after fees."
        ),
        "example": "A PMS with consistent Alpha of 4-5% p.a. is considered excellent.",
    },
    "Max Drawdown": {
        "simple": "The biggest loss from peak to bottom your portfolio has ever experienced.",
        "detail": (
            "If your portfolio grew to Rs.12L then fell to Rs.9L before recovering, "
            "the Max Drawdown is -25%. "
            "This tells you the worst loss you would have felt if you invested at the peak. "
            "Conservative investors should look for portfolios with Max Drawdown below -15%."
        ),
        "example": "Nifty 50 had a Max Drawdown of -38% during COVID crash (Feb-Mar 2020).",
    },
    "VaR (Value at Risk)": {
        "simple": "The maximum loss you can expect on a typical bad day.",
        "detail": (
            "VaR at 95% confidence means: on 95 out of 100 trading days, "
            "your portfolio will NOT lose more than this amount. "
            "On the remaining 5 days (the worst days), losses could be higher. "
            "VaR of -1.5% on a Rs.50L portfolio means you could lose Rs.75,000 on a bad day."
        ),
        "example": "VaR is used by banks and fund managers to set risk limits.",
    },
    "CVaR / Expected Shortfall": {
        "simple": "The average loss on your worst days — a more complete picture than VaR.",
        "detail": (
            "While VaR tells you the threshold, CVaR tells you the average loss "
            "when you breach that threshold. "
            "If VaR is -1.5%, CVaR might be -2.2%, meaning on the worst 5% of days "
            "you lose an average of 2.2%. CVaR is used by institutional risk managers."
        ),
        "example": "SEBI uses Expected Shortfall in its risk management framework for PMS.",
    },
    "Efficient Frontier": {
        "simple": "The set of best possible portfolios — highest return for each level of risk.",
        "detail": (
            "Developed by Harry Markowitz (Nobel Prize 1990). "
            "Every dot on the frontier is a portfolio that cannot be improved — "
            "you cannot get more return without taking more risk, "
            "and you cannot reduce risk without giving up return. "
            "Portfolios below the frontier are suboptimal."
        ),
        "example": "Moving from a pure equity portfolio to a diversified one "
                   "typically moves you toward the efficient frontier.",
    },
    "XIRR": {
        "simple": "The true annualised return on your investment, accounting for when money went in and came out.",
        "detail": (
            "Unlike simple returns, XIRR handles irregular cash flows — "
            "SIPs, lump sums, partial withdrawals at different times. "
            "SEBI mandates that PMS firms report client returns as XIRR. "
            "It gives the most accurate picture of your actual investment performance."
        ),
        "example": "If you invested Rs.1L in Jan and Rs.2L in June, "
                   "and your portfolio is worth Rs.3.5L in December, "
                   "XIRR gives the exact annualised return considering both investments.",
    },
    "Markowitz Optimisation": {
        "simple": "A mathematical method to find the best mix of assets for your risk level.",
        "detail": (
            "Created by Harry Markowitz in 1952. "
            "It finds the portfolio weights that give the maximum return "
            "for a given level of risk, using historical returns and how assets "
            "move relative to each other (correlation). "
            "WealthOS runs this optimisation for 5 different risk profiles."
        ),
        "example": "Adding Gold to an equity portfolio often improves the Sharpe Ratio "
                   "because Gold tends to go up when equities fall.",
    },
    "Monte Carlo Simulation": {
        "simple": "Running thousands of possible futures to see the range of outcomes.",
        "detail": (
            "WealthOS simulates 1,000 possible future market paths using "
            "historical return and volatility data. "
            "Each path is one possible version of the future. "
            "The result shows you a realistic range — best case, worst case, and most likely. "
            "Used by pension funds, insurance companies, and wealth managers worldwide."
        ),
        "example": "If 820 out of 1,000 simulations reach your Rs.2Cr goal, "
                   "the probability of achieving your goal is 82%.",
    },
    "Factor Investing": {
        "simple": "Investing based on proven characteristics that historically deliver better returns.",
        "detail": (
            "Academic research has identified 5 main factors that explain stock returns: "
            "Value (cheap stocks), Momentum (stocks going up), Quality (profitable companies), "
            "Low Volatility (stable stocks), and Size (smaller companies). "
            "Factor ETFs and index funds systematically target these characteristics."
        ),
        "example": "Nifty Quality 30 index selects 30 stocks with the highest quality scores "
                   "— these have historically outperformed Nifty 50 over long periods.",
    },
    "LTCG": {
        "simple": "Long Term Capital Gains — profit on investments held for more than 12 months.",
        "detail": (
            "In India (FY2024-25): Equity LTCG above Rs.1.25 lakh per year "
            "is taxed at 12.5% flat. "
            "The first Rs.1.25L of equity LTCG every financial year is completely tax-free. "
            "This exemption resets every April 1 — harvest it before March 31 each year."
        ),
        "example": "If you have Rs.2L equity gains, Rs.1.25L is tax-free "
                   "and only Rs.75,000 is taxed at 12.5% = Rs.9,375 tax.",
    },
    "STCG": {
        "simple": "Short Term Capital Gains — profit on investments sold within 12 months.",
        "detail": (
            "In India (FY2024-25): Equity STCG is taxed at 20% flat "
            "regardless of your income slab. "
            "This is higher than the 12.5% LTCG rate, so holding equity "
            "for at least 12 months before selling saves tax."
        ),
        "example": "Buying Nifty ETF in January and selling in October = STCG at 20%. "
                   "Selling in the following February = LTCG at 12.5%.",
    },
    "SGB (Sovereign Gold Bond)": {
        "simple": "Government-issued gold bonds that pay 2.5% interest and are tax-free at maturity.",
        "detail": (
            "SGBs are issued by RBI on behalf of the Government of India. "
            "They track gold prices and pay 2.5% annual interest on top. "
            "If held for the full 8-year maturity period, capital gains are completely tax-free. "
            "This makes them the most tax-efficient way to hold gold in India."
        ),
        "example": "Rs.1L invested in SGB tracking gold at Rs.6,000/gram. "
                   "At maturity if gold is Rs.9,000, the Rs.50,000 gain is tax-free.",
    },
    "REIT": {
        "simple": "A listed fund that owns real estate and distributes rental income to investors.",
        "detail": (
            "Real Estate Investment Trusts allow retail investors to invest in "
            "commercial real estate (offices, malls, warehouses) with as little as Rs.10,000-15,000. "
            "They are required to distribute 90% of income as dividends. "
            "Listed on NSE/BSE — you can buy and sell like a stock."
        ),
        "example": "Embassy Office Parks REIT owns office spaces leased to companies "
                   "like Google and IBM in Bengaluru and Mumbai.",
    },
}

def info_tooltip(term):
    """
    Shows an expander with simple + detailed explanation of a financial term.
    Use next to any technical term in the app.
    Usage: info_tooltip("Sharpe Ratio")
    """
    if term not in TERMS:
        return
    data = TERMS[term]
    with st.expander(f"ℹ️ What is {term}?"):
        st.markdown(f"**In simple words:** {data['simple']}")
        st.markdown(f"**How it works:** {data['detail']}")
        if "example" in data:
            st.markdown(f"**Example:** {data['example']}")

def metric_with_info(col, label, value, term=None, delta=None):
    """
    Displays a metric with an optional info tooltip below it.
    Usage: metric_with_info(st.columns(3)[0], "Sharpe Ratio", "0.85", "Sharpe Ratio")
    """
    col.metric(label, value, delta=delta)
    if term and term in TERMS:
        with col:
            info_tooltip(term)

def glossary_page():
    """Full glossary of all terms — can be added as a tab."""
    st.markdown("#### Financial Terms Glossary")
    st.caption("Click any term to see a plain-English explanation.")
    for term, data in TERMS.items():
        with st.expander(f"📖 {term}"):
            st.markdown(f"**In simple words:** {data['simple']}")
            st.markdown(f"**How it works:** {data['detail']}")
            if "example" in data:
                st.info(f"**Example:** {data['example']}")
