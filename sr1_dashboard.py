"""
SR1 SOFR Futures Pricing Dashboard
===================================
Run with:  streamlit run sr1_dashboard.py
Install:   pip install streamlit plotly pandas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import calendar
import json

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="SR1 SOFR Pricing Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; }
    .stDataFrame { font-size: 13px; }
    div[data-testid="metric-container"] {
        background: #1e2530;
        border: 1px solid #2e3a4e;
        border-radius: 8px;
        padding: 12px 18px;
    }
    .case-header { font-size: 15px; font-weight: 700; color: #e0e6f0; }
    .section-title { font-size: 18px; font-weight: 700; color: #7eb8f7; margin: 6px 0 2px 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PRICING ENGINE
# ──────────────────────────────────────────────

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def get_last_biz_day(yr, mo):
    """Return the last business day (Mon–Fri) of a given month."""
    last = date(yr, mo, calendar.monthrange(yr, mo)[1])
    while last.weekday() >= 5:   # 5=Sat, 6=Sun
        last -= timedelta(days=1)
    return last

def compute_prices(sofr_base: float, me_adj: float, qe_adj: float, ye_adj: float,
                   meeting_dates: list, rate_changes_bps: list, year: int = 2026):
    """
    Compute monthly SR1 prices for one scenario.

    Parameters
    ----------
    sofr_base       : float  – e.g. 0.05 for 5%
    me_adj          : float  – month-end bump, e.g. 0.0001
    qe_adj          : float  – quarter-end additional bump, e.g. 0.0002
    ye_adj          : float  – year-end additional bump
    meeting_dates   : list[date]  – Fed FOMC dates
    rate_changes_bps: list[float] – bp change at each meeting (e.g. -25)
    year            : int

    Returns
    -------
    dict: {month_name: price, ...}  for Jan–Dec
    """
    # Build cumulative rate path keyed by effective date (day after meeting)
    rate_path = []   # list of (effective_date, cumulative_rate_decimal)
    cum = sofr_base
    for mtg, chg_bps in zip(meeting_dates, rate_changes_bps):
        cum += chg_bps / 10000.0
        eff = mtg + timedelta(days=1)   # rate effective next calendar day
        rate_path.append((eff, cum))

    def rate_for_day(d: date) -> float:
        """Base rate for a calendar day (before special adjustments)."""
        r = sofr_base
        for eff, val in rate_path:
            if d >= eff:
                r = val
        return r

    prices = {}
    for mo_idx in range(1, 13):
        n_days = calendar.monthrange(year, mo_idx)[1]
        last_biz = get_last_biz_day(year, mo_idx)

        # Days that carry the month-end rate bump (last biz day + following weekends)
        me_days = set()
        d = last_biz
        while d.month == mo_idx:
            me_days.add(d)
            d += timedelta(days=1)
        # Also include weekend days in next month that carry (SOFR published Fri applies Sat+Sun)
        # Those are accounted for in NEXT month's calculation (they appear as day 1/2 of next mo)

        # Also account for carry-in from prior month-end (Sun/Sat that fall in this month)
        prev_mo = mo_idx - 1
        prev_yr = year
        if prev_mo == 0:
            prev_mo = 12
            prev_yr = year - 1
        prior_last_biz = get_last_biz_day(prev_yr, prev_mo)
        d2 = prior_last_biz + timedelta(days=1)
        carry_in_days = set()
        while d2.month == mo_idx:
            carry_in_days.add(d2)
            d2 += timedelta(days=1)

        # Is this a quarter-end month?
        is_qe = mo_idx in (3, 6, 9, 12)
        # Is this year-end month?
        is_ye = mo_idx == 12

        total = 0.0
        for day_num in range(1, n_days + 1):
            d = date(year, mo_idx, day_num)
            r = rate_for_day(d)

            # Month-end adjustment for last biz day(s) of THIS month
            if d in me_days:
                r += me_adj
                if is_qe:
                    r += qe_adj
                if is_ye:
                    r += ye_adj

            # Carry-in from prior month-end (weekend days at start of this month)
            if d in carry_in_days:
                prior_r = rate_for_day(prior_last_biz)
                r = prior_r + me_adj
                if get_last_biz_day(prev_yr, prev_mo).month in (3, 6, 9, 12):
                    r += qe_adj
                if prev_mo == 12:
                    r += ye_adj

            total += r

        avg = total / n_days
        prices[MONTHS[mo_idx - 1]] = round(100.0 - avg * 100.0, 6)

    return prices


# ──────────────────────────────────────────────
# DEFAULT MEETING DATES
# ──────────────────────────────────────────────
DEFAULT_MEETINGS = [
    date(2026, 1, 28),
    date(2026, 3, 18),
    date(2026, 4, 29),
    date(2026, 6, 17),
    date(2026, 7, 29),
    date(2026, 9, 16),
    date(2026, 10, 28),
    date(2026, 12,  9),
]

# ──────────────────────────────────────────────
# PRESET SCENARIOS
# ──────────────────────────────────────────────
PRESETS = {
    "Base — No Change (0 cuts)":       [0,    0,    0,    0,    0,    0,    0,    0],
    "1 Cut -25bp (Sep)":               [0,    0,    0,    0,    0,  -25,    0,    0],
    "2 Cuts -25bp (Jun, Sep)":         [0,    0,    0,  -25,    0,  -25,    0,    0],
    "2 Cuts -25bp (Sep, Dec)":         [0,    0,    0,    0,    0,  -25,    0,  -25],
    "3 Cuts -25bp (Jun, Sep, Dec)":    [0,    0,    0,  -25,    0,  -25,    0,  -25],
    "4 Cuts -25bp (Mar, Jun, Sep, Dec)":[0,  -25,    0,  -25,    0,  -25,    0,  -25],
    "1 Hike +25bp (Mar)":              [0,   25,    0,    0,    0,    0,    0,    0],
    "Aggressive easing -50bp (Jun)":   [0,    0,    0,  -50,    0,    0,    0,    0],
    "Custom":                          [0,    0,    0,    0,    0,    0,    0,    0],
}

PRESET_NAMES = list(PRESETS.keys())

# ──────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────
if "cases" not in st.session_state:
    st.session_state.cases = [
        {"name": "Base (No Change)", "changes": [0]*8, "color": "#4fc3f7"},
        {"name": "2 Cuts Jun+Sep",   "changes": [0,0,0,-25,0,-25,0,0], "color": "#81c784"},
    ]
if "meeting_dates" not in st.session_state:
    st.session_state.meeting_dates = DEFAULT_MEETINGS[:]

COLORS = [
    "#4fc3f7","#81c784","#ffb74d","#e57373","#ba68c8",
    "#4dd0e1","#aed581","#ff8a65","#f06292","#9575cd",
    "#26c6da","#d4e157","#ffa726","#ef5350","#ab47bc",
    "#26a69a","#8d6e63","#78909c","#ec407a","#42a5f5",
    "#66bb6a","#ffee58","#ff7043","#29b6f6","#26c6da",
    "#d4e157","#ffa726","#ef5350","#ab47bc","#26a69a",
]

# ──────────────────────────────────────────────
# SIDEBAR — GLOBAL PARAMETERS
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Global Parameters")

    sofr_base_pct = st.number_input(
        "Base SOFR (%)", min_value=0.0, max_value=15.0,
        value=5.0, step=0.25, format="%.2f"
    )
    sofr_base = sofr_base_pct / 100.0

    col1, col2 = st.columns(2)
    with col1:
        me_adj_bp = st.number_input("ME adj (bp)", value=1.0, step=0.5, format="%.1f")
        qe_adj_bp = st.number_input("QE adj (bp)", value=0.0, step=0.5, format="%.1f")
    with col2:
        ye_adj_bp = st.number_input("YE adj (bp)", value=0.0, step=0.5, format="%.1f")
        year = st.number_input("Year", value=2026, step=1, min_value=2020, max_value=2035)

    me_adj = me_adj_bp / 10000.0
    qe_adj = qe_adj_bp / 10000.0
    ye_adj = ye_adj_bp / 10000.0

    st.markdown("---")
    st.markdown("### 📅 FOMC Meeting Dates")
    meeting_dates = []
    for i, default_d in enumerate(st.session_state.meeting_dates):
        d = st.date_input(f"Meeting {i+1}", value=default_d, key=f"mtg_{i}",
                          label_visibility="collapsed")
        meeting_dates.append(d)

    if st.button("↺ Reset to 2026 Defaults"):
        st.session_state.meeting_dates = DEFAULT_MEETINGS[:]
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎨 Chart Options")
    show_markers = st.checkbox("Show Fed meeting markers", value=True)
    show_diff    = st.checkbox("Show Δ vs Base Case", value=True)
    base_case_idx = st.selectbox(
        "Base case for Δ comparison",
        options=range(len(st.session_state.cases)),
        format_func=lambda i: st.session_state.cases[i]["name"],
        index=0
    )

# ──────────────────────────────────────────────
# CASE MANAGEMENT
# ──────────────────────────────────────────────
st.markdown('<div class="section-title">📋 Scenario Cases</div>', unsafe_allow_html=True)

col_add, col_clear, col_import, col_export = st.columns([1,1,1,1])
with col_add:
    if st.button("➕ Add Case", use_container_width=True):
        n = len(st.session_state.cases)
        if n < 30:
            st.session_state.cases.append({
                "name": f"Case {n+1}",
                "changes": [0]*8,
                "color": COLORS[n % len(COLORS)]
            })
        st.rerun()

with col_clear:
    if st.button("🗑 Clear All Cases", use_container_width=True):
        st.session_state.cases = []
        st.rerun()

with col_export:
    export_data = json.dumps([
        {"name": c["name"], "changes": c["changes"]}
        for c in st.session_state.cases
    ], indent=2)
    st.download_button("⬇ Export Cases (JSON)", data=export_data,
                       file_name="sr1_cases.json", mime="application/json",
                       use_container_width=True)

with col_import:
    uploaded = st.file_uploader("⬆ Import Cases (JSON)", type="json", label_visibility="collapsed")
    if uploaded:
        imported = json.load(uploaded)
        for i, c in enumerate(imported[:30]):
            c["color"] = COLORS[i % len(COLORS)]
        st.session_state.cases = imported
        st.rerun()

st.markdown("---")

# ──────────────────────────────────────────────
# CASE EDITORS (collapsed into expanders)
# ──────────────────────────────────────────────
mtg_labels = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]
cases_to_delete = []

num_cols = 3
case_rows = [
    st.session_state.cases[i:i+num_cols]
    for i in range(0, len(st.session_state.cases), num_cols)
]
for row_idx, row in enumerate(case_rows):
    cols = st.columns(num_cols)
    for col_idx, case in enumerate(row):
        global_idx = row_idx * num_cols + col_idx
        with cols[col_idx]:
            with st.expander(f"**{case['name']}**", expanded=False):
                # Name + color
                c1, c2 = st.columns([3,1])
                with c1:
                    new_name = st.text_input("Name", value=case["name"],
                                             key=f"name_{global_idx}", label_visibility="collapsed")
                    st.session_state.cases[global_idx]["name"] = new_name
                with c2:
                    new_color = st.color_picker("Color", value=case["color"],
                                                key=f"color_{global_idx}", label_visibility="collapsed")
                    st.session_state.cases[global_idx]["color"] = new_color

                # Preset selector
                preset_key = f"preset_{global_idx}"
                sel = st.selectbox("Load Preset", options=PRESET_NAMES,
                                   index=len(PRESET_NAMES)-1, key=preset_key)
                if sel != "Custom":
                    preset_changes = PRESETS[sel]
                else:
                    preset_changes = case["changes"]

                # Per-meeting rate changes
                st.markdown("**Rate changes (bp) at each meeting:**")
                new_changes = []
                for m_i, label in enumerate(mtg_labels):
                    val = st.number_input(
                        label, value=float(preset_changes[m_i] if sel != "Custom" else case["changes"][m_i]),
                        step=25.0, format="%.0f", key=f"chg_{global_idx}_{m_i}"
                    )
                    new_changes.append(val)
                st.session_state.cases[global_idx]["changes"] = new_changes

                if st.button("🗑 Remove", key=f"del_{global_idx}", use_container_width=True):
                    cases_to_delete.append(global_idx)

# Remove deleted cases
for idx in sorted(cases_to_delete, reverse=True):
    st.session_state.cases.pop(idx)
if cases_to_delete:
    st.rerun()

# ──────────────────────────────────────────────
# COMPUTE ALL CASES
# ──────────────────────────────────────────────
results = {}   # case_name -> dict {month: price}
for case in st.session_state.cases:
    prices = compute_prices(
        sofr_base, me_adj, qe_adj, ye_adj,
        meeting_dates, case["changes"], year=int(year)
    )
    results[case["name"]] = prices

if not results:
    st.warning("Add at least one case to see results.")
    st.stop()

# ──────────────────────────────────────────────
# METRICS ROW
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-title">📊 Dashboard</div>', unsafe_allow_html=True)

base_case_name = st.session_state.cases[base_case_idx]["name"]
base_prices = results[base_case_name]

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Base SOFR", f"{sofr_base_pct:.2f}%")
with m2:
    jan_p = base_prices["Jan"]
    st.metric("Jan Price (Base)", f"{jan_p:.4f}")
with m3:
    dec_p = base_prices["Dec"]
    st.metric("Dec Price (Base)", f"{dec_p:.4f}")
with m4:
    st.metric("Active Cases", len(st.session_state.cases))
with m5:
    rng = max(p["Dec"] for p in results.values()) - min(p["Dec"] for p in results.values())
    st.metric("Dec Price Range", f"{rng:.4f}")

st.markdown("---")

# ──────────────────────────────────────────────
# BUILD DATAFRAME
# ──────────────────────────────────────────────
price_df = pd.DataFrame({
    case["name"]: results[case["name"]]
    for case in st.session_state.cases
}, index=MONTHS).T

diff_df = price_df.subtract(price_df.loc[base_case_name])
diff_df.columns = [f"Δ {m}" for m in MONTHS]

# ──────────────────────────────────────────────
# CHARTS
# ──────────────────────────────────────────────
tab_chart, tab_diff, tab_table = st.tabs(["📈 Price Chart", "📉 Δ vs Base", "🗂 Comparison Table"])

# Meeting month markers (for vertical lines)
mtg_months = set()
for d in meeting_dates:
    mtg_months.add(MONTHS[d.month - 1])

with tab_chart:
    fig = go.Figure()

    for case in st.session_state.cases:
        name = case["name"]
        prices_list = [results[name][m] for m in MONTHS]
        fig.add_trace(go.Scatter(
            x=MONTHS, y=prices_list,
            mode="lines+markers",
            name=name,
            line=dict(color=case["color"], width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>"
        ))

    # Fed meeting vertical markers (add_shape + add_annotation for broad Plotly compatibility)
    if show_markers:
        for d in meeting_dates:
            mo = MONTHS[d.month - 1]
            fig.add_shape(
                type="line",
                x0=mo, x1=mo, y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(color="rgba(255,200,60,0.6)", width=1.5, dash="dot"),
            )
            fig.add_annotation(
                x=mo, y=1.02,
                xref="x", yref="paper",
                text=d.strftime("%b %d"),
                showarrow=False,
                font=dict(size=9, color="rgba(255,200,60,0.9)"),
                xanchor="center",
            )

    fig.update_layout(
        title=f"SR1 Monthly Prices — {int(year)} (Base SOFR {sofr_base_pct:.2f}%)",
        xaxis_title="Month",
        yaxis_title="Price (100 − avg rate × 100)",
        legend=dict(orientation="v", x=1.01, y=1),
        plot_bgcolor="#13171f",
        paper_bgcolor="#13171f",
        font_color="#c9d1d9",
        hovermode="x unified",
        height=520,
        margin=dict(l=50, r=200, t=60, b=40),
    )
    fig.update_xaxes(gridcolor="#1e2530", showgrid=True)
    fig.update_yaxes(gridcolor="#1e2530", showgrid=True)
    st.plotly_chart(fig, use_container_width=True)

with tab_diff:
    if not show_diff:
        st.info("Enable 'Show Δ vs Base Case' in the sidebar to see this view.")
    else:
        fig2 = go.Figure()
        for case in st.session_state.cases:
            name = case["name"]
            if name == base_case_name:
                continue
            diffs = [diff_df.loc[name, f"Δ {m}"] for m in MONTHS]
            fig2.add_trace(go.Bar(
                name=name,
                x=MONTHS,
                y=diffs,
                marker_color=case["color"],
                hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:+.4f}}<extra></extra>"
            ))
        fig2.update_layout(
            title=f"Price Difference vs '{base_case_name}'",
            xaxis_title="Month",
            yaxis_title="Δ Price",
            barmode="group",
            plot_bgcolor="#13171f",
            paper_bgcolor="#13171f",
            font_color="#c9d1d9",
            height=480,
            legend=dict(orientation="v", x=1.01, y=1),
            margin=dict(l=50, r=200, t=60, b=40),
        )
        fig2.update_xaxes(gridcolor="#1e2530")
        fig2.update_yaxes(gridcolor="#1e2530", zeroline=True, zerolinecolor="#444")
        st.plotly_chart(fig2, use_container_width=True)

with tab_table:
    st.markdown(f"#### Prices by Case and Month")

    # Full price table
    display_df = price_df.copy()
    display_df.index.name = "Case"
    display_df = display_df.round(4)

    # Style: highlight min/max per month
    def color_cells(val):
        return "color: #c9d1d9"

    st.dataframe(
        display_df.style
        .background_gradient(cmap="RdYlGn", axis=0)
        .format("{:.4f}"),
        use_container_width=True, height=min(60 + 35*len(display_df), 700)
    )

    if show_diff:
        st.markdown(f"#### Δ vs '{base_case_name}'")
        diff_display = diff_df.copy()
        diff_display.columns = MONTHS
        diff_display = diff_display.round(4)
        diff_display = diff_display.drop(index=base_case_name, errors="ignore")

        st.dataframe(
            diff_display.style
            .background_gradient(cmap="RdYlGn", axis=0)
            .format("{:+.4f}"),
            use_container_width=True, height=min(60 + 35*len(diff_display), 600)
        )

    # Download
    csv = display_df.to_csv()
    st.download_button("⬇ Download Price Table (CSV)", data=csv,
                       file_name=f"sr1_prices_{int(year)}.csv", mime="text/csv")

# ──────────────────────────────────────────────
# RATE PATH DETAIL
# ──────────────────────────────────────────────
st.markdown("---")
with st.expander("🔍 Rate Path Detail per Case", expanded=False):
    path_rows = []
    for case in st.session_state.cases:
        cum = sofr_base_pct
        row = {"Case": case["name"]}
        for i, (d, chg) in enumerate(zip(meeting_dates, case["changes"])):
            cum += chg / 100.0
            row[f"After {d.strftime('%b %d')} ({chg:+.0f}bp)"] = f"{cum:.3f}%"
        path_rows.append(row)
    path_df = pd.DataFrame(path_rows).set_index("Case")
    st.dataframe(path_df, use_container_width=True)

st.caption(
    f"SR1 Dashboard • Base SOFR {sofr_base_pct:.2f}% • ME adj {me_adj_bp:.1f}bp "
    f"• QE adj {qe_adj_bp:.1f}bp • YE adj {ye_adj_bp:.1f}bp • Year {int(year)}"
)
