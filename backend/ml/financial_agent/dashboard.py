
"""
Stockly – Financial Agent Dashboard
Module 3: Financial Analysis & ML Model Comparison
Presentation-ready local dashboard built with Streamlit + Plotly.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ── Plotly imported lazily so we can show a nicer error if missing ──────────
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ModuleNotFoundError:
    PLOTLY_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stockly – Financial Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLING
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Background & Base ───────────────────────────────── */
.stApp {
    background-color: #0A1628;
    color: #E2E8F0;
}
section[data-testid="stSidebar"] {
    background-color: #0D1E35;
    border-right: 1px solid #1E3A5F;
}
/* ── Top header bar ─────────────────────────────────── */
.main-header {
    background: linear-gradient(135deg, #0D1E35 0%, #132742 100%);
    border: 1px solid #1E3A5F;
    border-radius: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
}
.main-header h1 {
    color: #4A9EFF;
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94A3B8;
    margin: 6px 0 0 0;
    font-size: 0.95rem;
}
/* ── KPI Cards ──────────────────────────────────────── */
.kpi-card {
    background: linear-gradient(135deg, #0D1E35, #132742);
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
    height: 100%;
}
.kpi-label {
    color: #64748B;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.kpi-value {
    color: #F1F5F9;
    font-size: 1.5rem;
    font-weight: 800;
    margin-bottom: 4px;
}
.kpi-sub {
    color: #94A3B8;
    font-size: 11px;
}
.kpi-positive { color: #A3E635; }
.kpi-negative { color: #F87171; }
.kpi-neutral  { color: #4A9EFF; }
/* ── Section headings ───────────────────────────────── */
.section-title {
    color: #4A9EFF;
    font-size: 1.1rem;
    font-weight: 700;
    padding-bottom: 6px;
    border-bottom: 2px solid #1E3A5F;
    margin-bottom: 16px;
}
/* ── Warning / info banners ─────────────────────────── */
.warn-banner {
    background: rgba(248, 113, 113, 0.08);
    border: 1px solid rgba(248, 113, 113, 0.35);
    border-radius: 8px;
    padding: 12px 16px;
    color: #FCA5A5;
    font-size: 0.88rem;
    margin-bottom: 12px;
}
.info-banner {
    background: rgba(74, 158, 255, 0.08);
    border: 1px solid rgba(74, 158, 255, 0.3);
    border-radius: 8px;
    padding: 12px 16px;
    color: #93C5FD;
    font-size: 0.88rem;
    margin-bottom: 12px;
}
.highlight-banner {
    background: rgba(163, 230, 53, 0.08);
    border: 1px solid rgba(163, 230, 53, 0.3);
    border-radius: 8px;
    padding: 12px 16px;
    color: #BEF264;
    font-size: 0.88rem;
    margin-bottom: 12px;
}
/* ── Dataframe styling ──────────────────────────────── */
.stDataFrame { border-radius: 8px; overflow: hidden; }
/* ── Metric override ────────────────────────────────── */
[data-testid="metric-container"] {
    background: #0D1E35;
    border: 1px solid #1E3A5F;
    border-radius: 10px;
    padding: 14px 18px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]   # repo root
DATA_DIR = PROJECT_ROOT / "backend" / "ml" / "financial_agent" / "data" / "processed"
MODEL_PATH = PROJECT_ROOT / "backend" / "ml" / "financial_agent" / "models" / "best_financial_model.pkl"

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_TEMPLATE = "plotly_dark"
COLORS = {
    "blue":  "#4A9EFF",
    "lime":  "#A3E635",
    "teal":  "#2DD4BF",
    "red":   "#F87171",
    "gold":  "#FBBF24",
    "slate": "#94A3B8",
    "navy":  "#0D1E35",
    "grid":  "#1E3A5F",
}


def inr_cr(value):
    """Format a raw INR value into ₹ Crores string."""
    if pd.isna(value):
        return "—"
    return f"₹{value / 1e7:,.2f} Cr"


def pct(value, dec=2):
    """Format as percentage string."""
    if pd.isna(value):
        return "—"
    return f"{value:.{dec}f}%"


def fmt(value, dec=2, prefix="", suffix=""):
    if pd.isna(value):
        return "—"
    return f"{prefix}{value:,.{dec}f}{suffix}"


@st.cache_data(show_spinner=False)
def load_csv(filename: str) -> pd.DataFrame | None:
    path = DATA_DIR / filename
    if not path.exists():
        return None
    return pd.read_csv(path)


def plotly_bar(df, x, y, title="", color=None, ylabel="", fmt_hover=None):
    if not PLOTLY_AVAILABLE:
        st.bar_chart(df.set_index(x)[y])
        return
    color = color or COLORS["blue"]
    fig = px.bar(df, x=x, y=y, title=title, template=PLOTLY_TEMPLATE,
                 color_discrete_sequence=[color])
    fig.update_layout(
        paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font_color="#CBD5E1", title_font_color="#4A9EFF",
        yaxis_title=ylabel, xaxis_title="",
        yaxis=dict(gridcolor=COLORS["grid"]),
        margin=dict(t=50, l=10, r=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def plotly_line(df, x, y_cols, title="", colors=None, ylabel=""):
    if not PLOTLY_AVAILABLE:
        st.line_chart(df.set_index(x)[y_cols])
        return
    colors = colors or list(COLORS.values())
    fig = go.Figure()
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], name=col,
            mode="lines+markers",
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=6),
        ))
    fig.update_layout(
        title=title, paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
        font_color="#CBD5E1", title_font_color="#4A9EFF",
        yaxis_title=ylabel, xaxis_title="",
        yaxis=dict(gridcolor=COLORS["grid"]),
        legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
        margin=dict(t=50, l=10, r=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def kpi_card(label, value, sub="", color_class="kpi-neutral"):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color_class}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 20px 0;">
        <div style="font-size:2rem;">📊</div>
        <div style="color:#4A9EFF; font-weight:800; font-size:1.1rem;">STOCKLY</div>
        <div style="color:#64748B; font-size:0.75rem; letter-spacing:1px;">FINANCIAL AGENT · MODULE 3</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        [
            "🏠  Overview",
            "📈  Historical Performance",
            "💰  Profitability",
            "🏦  Financial Stability",
            "📊  Valuation",
            "🤖  Machine Learning",
            "🔍  Data Quality",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("""
    <div style="color:#475569; font-size:0.75rem; padding:8px 0;">
        <strong style="color:#94A3B8;">Company:</strong> Reliance Industries<br>
        <strong style="color:#94A3B8;">Ticker:</strong> RELIANCE.NS<br>
        <strong style="color:#94A3B8;">Exchange:</strong> NSE India<br>
        <strong style="color:#94A3B8;">Data:</strong> Yahoo Finance (yfinance)
    </div>
    """, unsafe_allow_html=True)

page_key = page.split("  ", 1)[-1]

# ─────────────────────────────────────────────────────────────────────────────
# LOAD ALL DATA
# ─────────────────────────────────────────────────────────────────────────────
rev_df   = load_csv("reliance_revenue_earnings_analysis.csv")
prof_df  = load_csv("reliance_profitability_analysis.csv")
debt_df  = load_csv("reliance_debt_stability_analysis.csv")
ratio_df = load_csv("reliance_financial_ratios_analysis.csv")
mkt_df   = load_csv("reliance_market_price_history.csv")
ml_df    = load_csv("model_comparison.csv")

# ─────────────────────────────────────────────────────────────────────────────
# SHARED HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>📊 Stockly – Financial Agent</h1>
    <p>Module 3 · Reliance Industries (RELIANCE.NS) · AI-Powered Market Analysis &amp; Research</p>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 – OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
if page_key == "Overview":
    st.markdown('<div class="section-title">KEY PERFORMANCE INDICATORS</div>', unsafe_allow_html=True)

    # Collect values safely
    latest_rev = latest_ni = rev_growth = npm = roe = price = pe = pb = None
    latest_fy = price_date = "—"

    if rev_df is not None:
        valid = rev_df.dropna(subset=["Revenue"])
        if not valid.empty:
            row = valid.iloc[-1]
            latest_rev = row["Revenue"]
            latest_ni  = row.get("Net_Income")
            rev_growth = row.get("Revenue_Growth_%")
            latest_fy  = str(row["Financial_Year"])[:10]

    if prof_df is not None:
        valid_p = prof_df.dropna(subset=["Net_Profit_Margin_%"])
        if not valid_p.empty:
            npm = valid_p.iloc[-1]["Net_Profit_Margin_%"]

    if ratio_df is not None:
        valid_r = ratio_df.dropna(subset=["ROE_%"])
        if not valid_r.empty:
            roe = valid_r.iloc[-1]["ROE_%"]
        price_row = ratio_df.dropna(subset=["Latest_Stock_Price"])
        if not price_row.empty:
            price      = price_row.iloc[-1]["Latest_Stock_Price"]
            pe         = price_row.iloc[-1].get("PE_Ratio")
            pb         = price_row.iloc[-1].get("PB_Ratio")
            price_date = str(price_row.iloc[-1].get("Stock_Price_Date", ""))[:10]

    # KPI grid – 4 cards per row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Latest Revenue", inr_cr(latest_rev), f"FY {latest_fy}", "kpi-neutral")
    with col2:
        kpi_card("Latest Net Income", inr_cr(latest_ni), f"FY {latest_fy}", "kpi-positive")
    with col3:
        rev_clr = "kpi-positive" if (rev_growth or 0) >= 0 else "kpi-negative"
        kpi_card("Revenue Growth", pct(rev_growth), "Year-on-year", rev_clr)
    with col4:
        kpi_card("Net Profit Margin", pct(npm), "Latest available FY", "kpi-neutral")

    st.markdown("<div style='margin:14px 0'></div>", unsafe_allow_html=True)
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        kpi_card("Return on Equity", pct(roe), "Latest available FY", "kpi-positive" if (roe or 0) > 0 else "kpi-neutral")
    with col6:
        kpi_card("Stock Price", f"₹{price:,.2f}" if price else "—", f"As of {price_date}", "kpi-neutral")
    with col7:
        kpi_card("P/E Ratio", fmt(pe, 2, suffix="x"), "Price / EPS", "kpi-neutral")
    with col8:
        kpi_card("P/B Ratio", fmt(pb, 2, suffix="x"), "Price / Book Value", "kpi-neutral")

    st.markdown("---")
    st.markdown('<div class="section-title">REVENUE & NET INCOME SNAPSHOT</div>', unsafe_allow_html=True)

    if rev_df is not None:
        snap = rev_df.dropna(subset=["Revenue"]).copy()
        snap["Revenue_Cr"]  = snap["Revenue"]  / 1e7
        snap["NetIncome_Cr"] = snap["Net_Income"] / 1e7
        if PLOTLY_AVAILABLE:
            fig = make_subplots(rows=1, cols=2, subplot_titles=("Revenue (₹ Cr)", "Net Income (₹ Cr)"))
            fig.add_trace(go.Bar(x=snap["Financial_Year"], y=snap["Revenue_Cr"],
                                 name="Revenue", marker_color=COLORS["blue"]), row=1, col=1)
            fig.add_trace(go.Bar(x=snap["Financial_Year"], y=snap["NetIncome_Cr"],
                                 name="Net Income", marker_color=COLORS["lime"]), row=1, col=2)
            fig.update_layout(
                paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                font_color="#CBD5E1", showlegend=False,
                yaxis=dict(gridcolor=COLORS["grid"]),
                yaxis2=dict(gridcolor=COLORS["grid"]),
                margin=dict(t=40, l=10, r=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown('<div class="warn-banner">⚠ Revenue/earnings data file not found.</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-banner">ℹ All financial values are sourced from Yahoo Finance via the <code>yfinance</code> Python library. Data reflects Reliance Industries\' consolidated annual results.</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 – HISTORICAL PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Historical Performance":
    st.markdown('<div class="section-title">REVENUE & EARNINGS HISTORY</div>', unsafe_allow_html=True)

    if rev_df is None:
        st.error("⚠ reliance_revenue_earnings_analysis.csv not found.")
    else:
        df = rev_df.dropna(subset=["Revenue"]).copy()
        df["Revenue_Cr"]   = df["Revenue"]   / 1e7
        df["NetIncome_Cr"] = df["Net_Income"] / 1e7

        c1, c2 = st.columns(2)
        with c1:
            plotly_bar(df, "Financial_Year", "Revenue_Cr",
                       title="Annual Revenue (₹ Cr)", color=COLORS["blue"], ylabel="₹ Crores")
        with c2:
            plotly_bar(df, "Financial_Year", "NetIncome_Cr",
                       title="Annual Net Income (₹ Cr)", color=COLORS["lime"], ylabel="₹ Crores")

        st.markdown('<div class="section-title" style="margin-top:16px">GROWTH TRENDS</div>', unsafe_allow_html=True)
        growth_df = rev_df.dropna(subset=["Revenue_Growth_%"]).copy()
        if not growth_df.empty:
            c3, c4 = st.columns(2)
            with c3:
                plotly_bar(growth_df, "Financial_Year", "Revenue_Growth_%",
                           title="Revenue Growth (% YoY)", color=COLORS["teal"], ylabel="%")
            with c4:
                plotly_bar(growth_df, "Financial_Year", "Earnings_Growth_%",
                           title="Earnings Growth (% YoY)", color=COLORS["gold"], ylabel="%")
        else:
            st.info("Growth data requires at least two financial years.")

    # EPS TREND
    if ratio_df is not None:
        eps_df = ratio_df.dropna(subset=["EPS"]).copy()
        if not eps_df.empty:
            st.markdown('<div class="section-title" style="margin-top:16px">EPS TREND (₹ per share)</div>', unsafe_allow_html=True)
            plotly_bar(eps_df, "Financial_Year", "EPS",
                       title="Earnings Per Share (EPS) – ₹", color=COLORS["blue"], ylabel="₹")

    # STOCK PRICE HISTORY
    st.markdown('<div class="section-title" style="margin-top:16px">5-YEAR STOCK PRICE HISTORY</div>', unsafe_allow_html=True)
    if mkt_df is None:
        st.error("⚠ reliance_market_price_history.csv not found.")
    else:
        mkt = mkt_df.copy()
        mkt["Date"] = pd.to_datetime(mkt["Date"])
        if PLOTLY_AVAILABLE:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=mkt["Date"], y=mkt["Close"],
                mode="lines", name="Close Price",
                line=dict(color=COLORS["blue"], width=1.5),
                fill="tozeroy", fillcolor="rgba(74,158,255,0.07)",
            ))
            fig.update_layout(
                title="RELIANCE.NS – Closing Price (Last 5 Years)",
                paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                font_color="#CBD5E1", title_font_color="#4A9EFF",
                yaxis=dict(gridcolor=COLORS["grid"], title="Price (₹)"),
                xaxis=dict(gridcolor=COLORS["grid"]),
                margin=dict(t=50, l=10, r=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
            # Latest
            latest_close = mkt["Close"].iloc[-1]
            latest_date  = mkt["Date"].iloc[-1].strftime("%Y-%m-%d")
            st.markdown(f'<div class="highlight-banner">📌 Latest available closing price: <strong>₹{latest_close:,.2f}</strong> as of <strong>{latest_date}</strong></div>', unsafe_allow_html=True)
        else:
            st.line_chart(mkt.set_index("Date")["Close"])


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 – PROFITABILITY
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Profitability":
    st.markdown('<div class="section-title">PROFITABILITY MARGINS</div>', unsafe_allow_html=True)

    if prof_df is None:
        st.error("⚠ reliance_profitability_analysis.csv not found.")
    else:
        df = prof_df.dropna(subset=["Net_Profit_Margin_%"]).copy()

        c1, c2 = st.columns(2)
        with c1:
            plotly_line(df, "Financial_Year",
                        ["Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%", "EBITDA_Margin_%"],
                        title="Profitability Margins Over Time",
                        colors=[COLORS["blue"], COLORS["teal"], COLORS["lime"], COLORS["gold"]],
                        ylabel="%")
        with c2:
            if PLOTLY_AVAILABLE:
                margin_cols = ["Gross_Profit_Margin_%", "Operating_Margin_%", "Net_Profit_Margin_%", "EBITDA_Margin_%"]
                latest = prof_df.dropna(subset=["Net_Profit_Margin_%"]).iloc[-1]
                vals   = [latest.get(c, np.nan) for c in margin_cols]
                labels = ["Gross Margin", "Operating Margin", "Net Profit Margin", "EBITDA Margin"]
                fig = go.Figure(go.Bar(
                    x=[v for v in vals if not pd.isna(v)],
                    y=[l for l, v in zip(labels, vals) if not pd.isna(v)],
                    orientation="h",
                    marker_color=[COLORS["blue"], COLORS["teal"], COLORS["lime"], COLORS["gold"]],
                ))
                fig.update_layout(
                    title=f"Latest FY ({str(latest['Financial_Year'])[:10]}) Margins",
                    paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                    font_color="#CBD5E1", title_font_color="#4A9EFF",
                    xaxis=dict(gridcolor=COLORS["grid"], title="%"),
                    margin=dict(t=50, l=10, r=10, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)

        # ── PROFITABILITY CLASSIFICATION ──────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="section-title">PROFITABILITY CLASSIFICATION</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="info-banner">
        ℹ The thresholds below are <strong>our own rule-based classification</strong> created for this analysis.
        They are <u>not</u> official accounting or financial standards. You can adjust them using the sliders.
        </div>
        """, unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            hp_thresh  = st.slider("Highly Profitable threshold (Net Profit Margin ≥)", 5.0, 30.0, 15.0, 0.5, format="%.1f%%")
        with col_s2:
            mp_thresh  = st.slider("Moderately Profitable threshold (≥)", 1.0, 15.0, 5.0, 0.5, format="%.1f%%")

        def classify_profitability(npm_val):
            if pd.isna(npm_val):
                return "Insufficient Data", COLORS["slate"]
            elif npm_val >= hp_thresh:
                return "Highly Profitable", COLORS["lime"]
            elif npm_val >= mp_thresh:
                return "Moderately Profitable", COLORS["blue"]
            elif npm_val >= 0:
                return "Low Profitability", COLORS["gold"]
            else:
                return "Not Profitable", COLORS["red"]

        class_rows = []
        for _, row in prof_df.iterrows():
            npm_val = row.get("Net_Profit_Margin_%")
            label, color = classify_profitability(npm_val)
            class_rows.append({
                "Financial Year": str(row["Financial_Year"])[:10],
                "Net Profit Margin": pct(npm_val),
                "Classification": label,
            })

        class_df = pd.DataFrame(class_rows)
        st.dataframe(class_df, use_container_width=True, hide_index=True)

        # Visualise classifications
        if PLOTLY_AVAILABLE:
            viz = prof_df.dropna(subset=["Net_Profit_Margin_%"]).copy()
            viz["Classification"], viz["Colour"] = zip(*viz["Net_Profit_Margin_%"].apply(classify_profitability))
            fig = px.bar(viz, x="Financial_Year", y="Net_Profit_Margin_%",
                         color="Classification",
                         color_discrete_map={
                             "Highly Profitable": COLORS["lime"],
                             "Moderately Profitable": COLORS["blue"],
                             "Low Profitability": COLORS["gold"],
                             "Not Profitable": COLORS["red"],
                             "Insufficient Data": COLORS["slate"],
                         },
                         title="Net Profit Margin with Classification",
                         template=PLOTLY_TEMPLATE)
            fig.update_layout(
                paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                font_color="#CBD5E1", title_font_color="#4A9EFF",
                yaxis=dict(gridcolor=COLORS["grid"], title="%"),
                legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
                margin=dict(t=50, l=10, r=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4 – FINANCIAL STABILITY
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Financial Stability":
    st.markdown('<div class="section-title">DEBT & FINANCIAL STABILITY RATIOS</div>', unsafe_allow_html=True)

    if debt_df is None:
        st.error("⚠ reliance_debt_stability_analysis.csv not found.")
    else:
        df = debt_df.copy()

        # KPI row – latest year
        latest = df.iloc[-1]
        st.markdown(f"**Latest Financial Year: {str(latest['Financial_Year'])[:10]}**")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Debt-to-Equity", fmt(latest.get("Debt_to_Equity_Ratio"), 4, suffix="x"), "Total Debt / Equity", "kpi-neutral")
        with c2:
            kpi_card("Debt-to-Assets", fmt(latest.get("Debt_to_Assets_Ratio"), 4, suffix="x"), "Total Debt / Assets", "kpi-neutral")
        with c3:
            cr = latest.get("Current_Ratio")
            cr_color = "kpi-positive" if (cr or 0) >= 1 else "kpi-negative"
            kpi_card("Current Ratio", fmt(cr, 4, suffix="x"), "Current Assets / Liabilities", cr_color)
        with c4:
            kpi_card("Cash-to-Debt", fmt(latest.get("Cash_to_Debt_Ratio"), 4, suffix="x"), "Cash / Total Debt", "kpi-positive")
        with c5:
            kpi_card("Net Debt-to-Assets", fmt(latest.get("Net_Debt_to_Assets_Ratio"), 4, suffix="x"), "Net Debt / Assets", "kpi-neutral")

        st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)

        # Charts
        ratio_cols = [
            ("Debt_to_Equity_Ratio",   "Debt-to-Equity",   COLORS["blue"]),
            ("Debt_to_Assets_Ratio",   "Debt-to-Assets",   COLORS["teal"]),
            ("Current_Ratio",          "Current Ratio",     COLORS["lime"]),
            ("Cash_to_Debt_Ratio",     "Cash-to-Debt",      COLORS["gold"]),
            ("Net_Debt_to_Assets_Ratio","Net Debt-to-Assets",COLORS["red"]),
        ]

        c1, c2 = st.columns(2)
        with c1:
            if PLOTLY_AVAILABLE:
                fig = go.Figure()
                for col, label, color in ratio_cols:
                    fig.add_trace(go.Scatter(
                        x=df["Financial_Year"], y=df[col],
                        name=label, mode="lines+markers",
                        line=dict(color=color, width=2),
                        marker=dict(size=7),
                    ))
                fig.update_layout(
                    title="All Stability Ratios Over Time",
                    paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                    font_color="#CBD5E1", title_font_color="#4A9EFF",
                    yaxis=dict(gridcolor=COLORS["grid"], title="Ratio"),
                    legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
                    margin=dict(t=50, l=10, r=10, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if PLOTLY_AVAILABLE:
                # Balance sheet overview bar
                snap = df[["Financial_Year", "Total_Debt", "Stockholders_Equity", "Total_Assets"]].copy()
                snap["Total_Debt_Cr"]   = snap["Total_Debt"] / 1e7
                snap["Equity_Cr"]       = snap["Stockholders_Equity"] / 1e7
                snap["Total_Assets_Cr"] = snap["Total_Assets"] / 1e7
                fig2 = go.Figure()
                for col, label, color in [
                    ("Total_Assets_Cr", "Total Assets", COLORS["blue"]),
                    ("Equity_Cr",       "Equity",       COLORS["lime"]),
                    ("Total_Debt_Cr",   "Total Debt",   COLORS["red"]),
                ]:
                    fig2.add_trace(go.Bar(x=snap["Financial_Year"], y=snap[col], name=label,
                                          marker_color=color))
                fig2.update_layout(
                    barmode="group", title="Balance Sheet Overview (₹ Cr)",
                    paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                    font_color="#CBD5E1", title_font_color="#4A9EFF",
                    yaxis=dict(gridcolor=COLORS["grid"], title="₹ Crores"),
                    legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
                    margin=dict(t=50, l=10, r=10, b=10),
                )
                st.plotly_chart(fig2, use_container_width=True)

        # Detailed table
        st.markdown('<div class="section-title">DETAILED RATIOS TABLE</div>', unsafe_allow_html=True)
        tbl = df.copy()
        for col in ["Total_Debt", "Net_Debt", "Total_Assets", "Stockholders_Equity",
                    "Current_Assets", "Current_Liabilities", "Cash_And_Cash_Equivalents"]:
            tbl[col] = tbl[col].apply(inr_cr)
        for col in ["Debt_to_Equity_Ratio", "Debt_to_Assets_Ratio", "Current_Ratio",
                    "Cash_to_Debt_Ratio", "Net_Debt_to_Assets_Ratio"]:
            tbl[col] = tbl[col].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "—")
        st.dataframe(tbl, use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5 – VALUATION
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Valuation":
    st.markdown('<div class="section-title">VALUATION RATIOS & SHAREHOLDER VALUE</div>', unsafe_allow_html=True)

    if ratio_df is None:
        st.error("⚠ reliance_financial_ratios_analysis.csv not found.")
    else:
        df = ratio_df.copy()
        # Latest row with stock price
        price_row = df.dropna(subset=["Latest_Stock_Price"])
        pe = pb = price = price_date = None
        latest_fy = "—"
        if not price_row.empty:
            lr = price_row.iloc[-1]
            pe = lr.get("PE_Ratio"); pb = lr.get("PB_Ratio")
            price = lr.get("Latest_Stock_Price")
            price_date = str(lr.get("Stock_Price_Date", ""))[:10]
            latest_fy = str(lr["Financial_Year"])[:10]

        c1, c2, c3, c4, c5 = st.columns(5)
        valid_roe = df.dropna(subset=["ROE_%"])
        with c1:
            roe_v = valid_roe.iloc[-1]["ROE_%"] if not valid_roe.empty else None
            kpi_card("ROE", pct(roe_v), "Net Income / Equity", "kpi-positive" if (roe_v or 0) > 0 else "kpi-neutral")
        valid_eps = df.dropna(subset=["EPS"])
        with c2:
            eps_v = valid_eps.iloc[-1]["EPS"] if not valid_eps.empty else None
            kpi_card("EPS", fmt(eps_v, 2, prefix="₹"), "Per share", "kpi-neutral")
        valid_bv = df.dropna(subset=["Book_Value_Per_Share"])
        with c3:
            bv_v = valid_bv.iloc[-1]["Book_Value_Per_Share"] if not valid_bv.empty else None
            kpi_card("Book Value/Share", fmt(bv_v, 2, prefix="₹"), "Equity / Shares", "kpi-neutral")
        with c4:
            kpi_card("P/E Ratio", fmt(pe, 2, suffix="x"), f"FY {latest_fy}", "kpi-neutral")
        with c5:
            kpi_card("P/B Ratio", fmt(pb, 2, suffix="x"), f"FY {latest_fy}", "kpi-neutral")

        if price:
            st.markdown(f'<div class="highlight-banner">📌 Valuation computed using stock price <strong>₹{price:,.2f}</strong> as of <strong>{price_date}</strong>, against financial year <strong>{latest_fy}</strong> results.</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin:16px 0'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            df_roe = df.dropna(subset=["ROE_%"])
            plotly_bar(df_roe, "Financial_Year", "ROE_%",
                       title="Return on Equity (%)", color=COLORS["lime"], ylabel="%")
        with c2:
            df_eps = df.dropna(subset=["EPS"])
            plotly_line(df_eps, "Financial_Year", ["EPS", "Book_Value_Per_Share"],
                        title="EPS & Book Value Per Share (₹)",
                        colors=[COLORS["blue"], COLORS["gold"]], ylabel="₹")

        # Full table
        st.markdown('<div class="section-title">FULL VALUATION DATA</div>', unsafe_allow_html=True)
        tbl = df.copy()
        tbl["Net_Income"]          = tbl["Net_Income"].apply(inr_cr)
        tbl["Stockholders_Equity"] = tbl["Stockholders_Equity"].apply(inr_cr)
        tbl["Ordinary_Shares_Number"] = tbl["Ordinary_Shares_Number"].apply(
            lambda x: f"{x/1e7:,.2f} Cr" if pd.notna(x) else "—"
        )
        tbl["ROE_%"]    = tbl["ROE_%"].apply(pct)
        tbl["EPS"]      = tbl["EPS"].apply(lambda x: fmt(x, 2, prefix="₹"))
        tbl["Book_Value_Per_Share"] = tbl["Book_Value_Per_Share"].apply(lambda x: fmt(x, 2, prefix="₹"))
        tbl["Latest_Stock_Price"] = tbl["Latest_Stock_Price"].apply(lambda x: fmt(x, 2, prefix="₹"))
        tbl["PE_Ratio"] = tbl["PE_Ratio"].apply(lambda x: fmt(x, 2, suffix="x"))
        tbl["PB_Ratio"] = tbl["PB_Ratio"].apply(lambda x: fmt(x, 2, suffix="x"))
        st.dataframe(tbl, use_container_width=True, hide_index=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 6 – MACHINE LEARNING
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Machine Learning":
    st.markdown('<div class="section-title">ML MODEL COMPARISON</div>', unsafe_allow_html=True)

    # Prominent warning
    st.markdown("""
    <div class="warn-banner">
    ⚠️ <strong>EXPERIMENTAL MODEL – NOT INVESTMENT ADVICE</strong><br>
    The current best model (SVM) achieves approximately <strong>52% accuracy</strong>, which is barely above random chance (50%).
    This model is experimental and intended for academic/demonstration purposes only.
    <strong>Do not use these predictions to make investment decisions.</strong>
    </div>
    """, unsafe_allow_html=True)

    # Model file status
    model_exists = MODEL_PATH.exists()
    model_status = f"✅ Found: {MODEL_PATH.name}" if model_exists else f"⚠ Not found at: {MODEL_PATH}"
    st.markdown(f'<div class="{"highlight-banner" if model_exists else "warn-banner"}">📦 Saved Model: {model_status}</div>', unsafe_allow_html=True)

    if ml_df is None:
        st.error("⚠ model_comparison.csv not found.")
    else:
        df = ml_df.copy()

        # Highlight SVM (best selected model)
        st.markdown('<div class="section-title">MODEL PERFORMANCE METRICS</div>', unsafe_allow_html=True)

        c1, c2 = st.columns([2, 1])
        with c1:
            if PLOTLY_AVAILABLE:
                metric_cols = [c for c in ["Accuracy", "Precision", "Recall", "F1_Score", "Balanced_Accuracy"] if c in df.columns]
                fig = go.Figure()
                bar_colors = {
                    "Logistic Regression": COLORS["blue"],
                    "Random Forest":       COLORS["teal"],
                    "Gradient Boosting":   COLORS["gold"],
                    "SVM":                 COLORS["lime"],
                }
                for _, row in df.iterrows():
                    model_name = row["Model"]
                    fig.add_trace(go.Bar(
                        name=model_name,
                        x=metric_cols,
                        y=[row.get(m, 0) for m in metric_cols],
                        marker_color=bar_colors.get(model_name, COLORS["slate"]),
                    ))
                # 50% chance line
                fig.add_hline(y=0.5, line_dash="dot", line_color="#F87171",
                              annotation_text="50% (random chance)",
                              annotation_position="top right",
                              annotation_font_color="#F87171")
                fig.update_layout(
                    barmode="group",
                    title="Model Comparison – Accuracy, Precision, Recall, F1",
                    paper_bgcolor="#0A1628", plot_bgcolor="#0A1628",
                    font_color="#CBD5E1", title_font_color="#4A9EFF",
                    yaxis=dict(gridcolor=COLORS["grid"], title="Score", range=[0, 1]),
                    legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
                    margin=dict(t=50, l=10, r=10, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.markdown("**Raw Scores:**")
            display_ml = df.copy()
            for col in ["Accuracy", "Precision", "Recall", "F1_Score", "Balanced_Accuracy"]:
                if col in display_ml.columns:
                    display_ml[col] = display_ml[col].apply(lambda x: f"{x:.4f}")
            # highlight SVM row
            st.dataframe(
                display_ml,
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("""
            <div class="highlight-banner" style="margin-top:12px">
            🏆 <strong>Selected Model: SVM</strong><br>
            Chosen as best based on balanced accuracy and overall performance across metrics.
            </div>
            """, unsafe_allow_html=True)

        # Radar / spider chart
        if PLOTLY_AVAILABLE:
            st.markdown('<div class="section-title" style="margin-top:16px">RADAR COMPARISON</div>', unsafe_allow_html=True)
            radar_metrics = [c for c in ["Accuracy", "Precision", "Recall", "F1_Score"] if c in df.columns]
            fig_r = go.Figure()
            bar_colors_list = [COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["lime"]]
            for i, (_, row) in enumerate(df.iterrows()):
                vals = [row.get(m, 0) for m in radar_metrics]
                vals_closed = vals + [vals[0]]
                metrics_closed = radar_metrics + [radar_metrics[0]]
                fig_r.add_trace(go.Scatterpolar(
                    r=vals_closed, theta=metrics_closed,
                    name=row["Model"],
                    fill="toself", opacity=0.5,
                    line=dict(color=bar_colors_list[i % 4]),
                ))
            fig_r.update_layout(
                polar=dict(
                    bgcolor="#0D1E35",
                    radialaxis=dict(visible=True, range=[0, 1], gridcolor=COLORS["grid"], color="#94A3B8"),
                    angularaxis=dict(gridcolor=COLORS["grid"], color="#94A3B8"),
                ),
                paper_bgcolor="#0A1628",
                font_color="#CBD5E1",
                legend=dict(bgcolor="#0D1E35", bordercolor=COLORS["grid"]),
                margin=dict(t=20, l=10, r=10, b=10),
            )
            st.plotly_chart(fig_r, use_container_width=True)

        # Prediction target explanation
        st.markdown("""
        <div class="info-banner">
        ℹ <strong>Prediction Target:</strong> The ML model predicts whether Reliance's profitability will
        <em>Improve</em> or <em>Decline</em> based on engineered financial features (revenue trends,
        margin changes, debt ratios). The dataset is small (derived from annual financial statements),
        which limits model accuracy. This is an educational demonstration only.
        </div>
        """, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 7 – DATA QUALITY
# ═════════════════════════════════════════════════════════════════════════════
elif page_key == "Data Quality":
    st.markdown('<div class="section-title">DATA QUALITY REPORT</div>', unsafe_allow_html=True)

    files_to_check = {
        "Revenue & Earnings":    ("reliance_revenue_earnings_analysis.csv", rev_df),
        "Profitability":         ("reliance_profitability_analysis.csv",    prof_df),
        "Debt & Stability":      ("reliance_debt_stability_analysis.csv",   debt_df),
        "Financial Ratios":      ("reliance_financial_ratios_analysis.csv", ratio_df),
        "Market Price History":  ("reliance_market_price_history.csv",      mkt_df),
        "ML Model Comparison":   ("model_comparison.csv",                   ml_df),
    }

    # File availability
    st.markdown("#### File Availability")
    for label, (fname, df_loaded) in files_to_check.items():
        full_path = DATA_DIR / fname
        if df_loaded is not None:
            rows = len(df_loaded)
            st.success(f"✅ **{label}** – {fname} ({rows} rows)")
        else:
            st.error(f"❌ **{label}** – {fname} — FILE NOT FOUND")

    model_exists = MODEL_PATH.exists()
    if model_exists:
        st.success(f"✅ **Trained ML Model** – {MODEL_PATH.name}")
    else:
        st.error(f"❌ **Trained ML Model** – best_financial_model.pkl — NOT FOUND at {MODEL_PATH}")

    # Missing value analysis
    st.markdown("---")
    st.markdown("#### Missing Values Per File")

    for label, (fname, df_loaded) in files_to_check.items():
        if df_loaded is None:
            continue
        missing = df_loaded.isnull().sum()
        missing = missing[missing > 0]
        if missing.empty:
            st.markdown(f"**{label}** – No missing values ✅")
        else:
            with st.expander(f"⚠ **{label}** – {len(missing)} column(s) with missing values"):
                miss_df = missing.reset_index()
                miss_df.columns = ["Column", "Missing Count"]
                miss_df["Missing %"] = (miss_df["Missing Count"] / len(df_loaded) * 100).apply(lambda x: f"{x:.1f}%")
                st.dataframe(miss_df, use_container_width=True, hide_index=True)

    # Financial years coverage
    st.markdown("---")
    st.markdown("#### Financial Year Coverage")

    fy_data = {}
    for label, col_name, df_loaded in [
        ("Revenue & Earnings", "Financial_Year", rev_df),
        ("Profitability",      "Financial_Year", prof_df),
        ("Debt & Stability",   "Financial_Year", debt_df),
        ("Financial Ratios",   "Financial_Year", ratio_df),
    ]:
        if df_loaded is not None and "Financial_Year" in df_loaded.columns:
            fy_data[label] = df_loaded["Financial_Year"].apply(lambda x: str(x)[:7]).tolist()

    if fy_data:
        all_fy = sorted(set(fy for fylist in fy_data.values() for fy in fylist))
        coverage_rows = []
        for fy in all_fy:
            row = {"Financial Period": fy}
            for label, fylist in fy_data.items():
                row[label] = "✅" if fy in fylist else "❌"
            coverage_rows.append(row)
        st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

    # Warnings
    st.markdown("---")
    st.markdown("#### Data Availability Warnings")

    warnings = []
    if rev_df is not None:
        nan_rows = rev_df[rev_df["Revenue"].isna()]
        if not nan_rows.empty:
            for _, r in nan_rows.iterrows():
                warnings.append(f"Revenue & Earnings: FY {str(r['Financial_Year'])[:10]} has no revenue data.")

    if prof_df is not None:
        for _, r in prof_df.iterrows():
            if pd.isna(r.get("Net_Profit_Margin_%")):
                warnings.append(f"Profitability: FY {str(r['Financial_Year'])[:10]} has no net profit margin data.")

    if ratio_df is not None:
        no_price = ratio_df[ratio_df["Latest_Stock_Price"].isna()]
        if not no_price.empty:
            warnings.append(f"Valuation: P/E and P/B are only available for the latest financial year (stock price matched to most recent annual results).")

    if warnings:
        for w in warnings:
            st.markdown(f'<div class="warn-banner">⚠ {w}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="highlight-banner">✅ No critical data quality warnings detected.</div>', unsafe_allow_html=True)

    st.markdown('<div class="info-banner">ℹ Missing financial values are displayed as <strong>—</strong> throughout the dashboard. No missing values have been substituted with zero.</div>', unsafe_allow_html=True)
