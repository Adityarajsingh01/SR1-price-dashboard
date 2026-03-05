"""
STIR Dashboard — SR1 (SOFR) · ZQ (EFFR) · Spreads & Flies · Inter-Product
===========================================================================
Run:  streamlit run stir_dashboard.py
Deps: pip install streamlit plotly pandas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar, json

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="STIR Dashboard | SR1 · ZQ",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .main .block-container { padding-top: 0.4rem; max-width: 100%; }
  div[data-testid="metric-container"] {
    background:#1a2332; border:1px solid #2e3a4e;
    border-radius:8px; padding:10px 16px;
  }
  .stTabs [data-baseweb="tab"] { font-size:15px; font-weight:700; padding:8px 20px; }
  .stTabs [aria-selected="true"] { color:#4fc3f7 !important; }
  .sec { font-size:17px; font-weight:700; color:#7eb8f7; margin:10px 0 4px; }
  .tip { background:#162616; border-left:3px solid #4caf50;
         padding:8px 14px; border-radius:4px; font-size:13px; margin:4px 0; color:#c8e6c9; }
  .warn{ background:#2a1a10; border-left:3px solid #ff9800;
         padding:8px 14px; border-radius:4px; font-size:13px; margin:4px 0; color:#ffe0b2; }
  .infobox{ background:#0d1b2a; border-left:3px solid #4fc3f7;
            padding:8px 14px; border-radius:4px; font-size:13px; margin:4px 0; color:#b3d9f7; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

COLORS = [
    "#4fc3f7","#81c784","#ffb74d","#e57373","#ba68c8","#4dd0e1","#aed581",
    "#ff8a65","#f06292","#9575cd","#26c6da","#d4e157","#ffa726","#ef5350",
    "#ab47bc","#26a69a","#8d6e63","#78909c","#ec407a","#42a5f5","#66bb6a",
    "#ffee58","#ff7043","#29b6f6","#80cbc4","#ce93d8","#a5d6a7","#ffcc02",
    "#ff5252","#40c4ff","#69f0ae",
]

DEFAULT_MEETINGS = [
    date(2026,1,28), date(2026,3,18), date(2026,4,29), date(2026,6,17),
    date(2026,7,29), date(2026,9,16), date(2026,10,28), date(2026,12,9),
]

PRESETS = {
    "No Change (0 cuts)":              [ 0,   0,   0,   0,   0,   0,   0,   0],
    "1 Cut -25bp (Sep)":               [ 0,   0,   0,   0,   0, -25,   0,   0],
    "1 Cut -25bp (Dec)":               [ 0,   0,   0,   0,   0,   0,   0, -25],
    "2 Cuts (Jun+Sep)":                [ 0,   0,   0, -25,   0, -25,   0,   0],
    "2 Cuts (Sep+Dec)":                [ 0,   0,   0,   0,   0, -25,   0, -25],
    "3 Cuts (Jun+Sep+Dec)":            [ 0,   0,   0, -25,   0, -25,   0, -25],
    "4 Cuts (Mar+Jun+Sep+Dec)":        [ 0, -25,   0, -25,   0, -25,   0, -25],
    "5 Cuts (Jan+Mar+Jun+Sep+Dec)":    [-25, -25,  0, -25,   0, -25,   0, -25],
    "Hike +25bp (Mar)":                [ 0,  25,   0,   0,   0,   0,   0,   0],
    "2 Hikes (Mar+Jun)":               [ 0,  25,   0,  25,   0,   0,   0,   0],
    "Aggressive cut -50bp (Sep)":      [ 0,   0,   0,   0,   0, -50,   0,   0],
    "Custom":                          [ 0,   0,   0,   0,   0,   0,   0,   0],
}
PRESET_NAMES = list(PRESETS.keys())

# ═══════════════════════════════════════════════════════════════
# PRICING ENGINE
# ═══════════════════════════════════════════════════════════════
def get_last_biz_day(yr, mo):
    last = date(yr, mo, calendar.monthrange(yr, mo)[1])
    while last.weekday() >= 5:
        last -= timedelta(days=1)
    return last

def compute_prices(base_rate, me_adj, qe_adj, ye_adj,
                   meeting_dates, rate_changes_bps, year=2026):
    rate_path = []
    cum = base_rate
    for mtg, chg in zip(meeting_dates, rate_changes_bps):
        cum += chg / 10000.0
        rate_path.append((mtg + timedelta(days=1), cum))

    def rate_for_day(d):
        r = base_rate
        for eff, val in rate_path:
            if d >= eff:
                r = val
        return r

    prices = {}
    for mo_idx in range(1, 13):
        n_days = calendar.monthrange(year, mo_idx)[1]
        last_biz = get_last_biz_day(year, mo_idx)
        me_days = set()
        d = last_biz
        while d.month == mo_idx:
            me_days.add(d); d += timedelta(days=1)

        prev_mo = mo_idx - 1 or 12
        prev_yr = year if mo_idx > 1 else year - 1
        prior_lb = get_last_biz_day(prev_yr, prev_mo)
        d2 = prior_lb + timedelta(days=1)
        carry_in = set()
        while d2.month == mo_idx:
            carry_in.add(d2); d2 += timedelta(days=1)

        is_qe = mo_idx in (3,6,9,12)
        is_ye = mo_idx == 12
        total = 0.0

        for day_num in range(1, n_days + 1):
            d = date(year, mo_idx, day_num)
            if d in carry_in:
                r = rate_for_day(prior_lb) + me_adj
                if prior_lb.month in (3,6,9,12): r += qe_adj
                if prev_mo == 12: r += ye_adj
            else:
                r = rate_for_day(d)
                if d in me_days:
                    r += me_adj
                    if is_qe: r += qe_adj
                    if is_ye: r += ye_adj
            total += r

        avg = total / n_days
        prices[MONTHS[mo_idx-1]] = round(100.0 - avg * 100.0, 6)
    return prices

# ═══════════════════════════════════════════════════════════════
# ANALYTICS ENGINE
# ═══════════════════════════════════════════════════════════════
def compute_analytics(results, cases):
    """Returns calendar spreads (bp), flies (bp), implied rates (%) per case."""
    sp_labels  = [f"{MONTHS[i]}/{MONTHS[i+1]}" for i in range(11)]
    fly_labels = [f"{MONTHS[i-1]}-{MONTHS[i]}-{MONTHS[i+1]}" for i in range(1,11)]

    sp_data, fly_data, rate_data = {}, {}, {}
    for case in cases:
        nm = case["name"]
        p  = [results[nm][m] for m in MONTHS]
        sp_data[nm]  = [round((p[i+1]-p[i])*100, 2) for i in range(11)]
        fly_data[nm] = [round((-p[i-1]+2*p[i]-p[i+1])*100, 2) for i in range(1,11)]
        rate_data[nm]= [round(100-v, 4) for v in p]

    return (
        pd.DataFrame(sp_data,  index=sp_labels).T,
        pd.DataFrame(fly_data, index=fly_labels).T,
        pd.DataFrame(rate_data, index=MONTHS).T,
    )

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════
def _default_cases():
    return [
        {"name":"Base (No Change)", "changes":[0]*8, "color":COLORS[0]},
        {"name":"2 Cuts Jun+Sep",   "changes":[0,0,0,-25,0,-25,0,0], "color":COLORS[1]},
    ]

for key in ["sr1_cases","zq_cases"]:
    if key not in st.session_state:
        st.session_state[key] = _default_cases()
if "meeting_dates" not in st.session_state:
    st.session_state.meeting_dates = DEFAULT_MEETINGS[:]

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Global")
    year = int(st.number_input("Year", value=2026, step=1, min_value=2020, max_value=2035))
    yr2  = str(year)[2:]

    st.markdown("### 📅 FOMC Dates")
    meeting_dates = []
    for i, dfl in enumerate(st.session_state.meeting_dates):
        meeting_dates.append(
            st.date_input(f"Meeting {i+1}", value=dfl, key=f"mtg_{i}", label_visibility="collapsed")
        )
    if st.button("↺ Reset 2026 defaults"):
        st.session_state.meeting_dates = DEFAULT_MEETINGS[:]
        st.rerun()

    st.markdown("---")
    st.markdown("### 🔵 SR1 (SOFR) Params")
    sofr_base = st.number_input("Base SOFR (%)", value=4.25, step=0.25, format="%.2f",
                                 min_value=0.0, max_value=15.0) / 100
    sofr_me   = st.number_input("ME adj (bp)",  value=1.0, step=0.5, format="%.1f", key="s_me") / 10000
    sofr_qe   = st.number_input("QE adj (bp)",  value=0.0, step=0.5, format="%.1f", key="s_qe") / 10000
    sofr_ye   = st.number_input("YE adj (bp)",  value=0.0, step=0.5, format="%.1f", key="s_ye") / 10000

    st.markdown("### 🟠 ZQ (EFFR) Params")
    effr_base = st.number_input("Base EFFR (%)", value=4.33, step=0.25, format="%.2f",
                                 min_value=0.0, max_value=15.0) / 100
    effr_me   = st.number_input("ME adj (bp)",  value=0.0, step=0.5, format="%.1f", key="e_me") / 10000
    effr_qe   = st.number_input("QE adj (bp)",  value=0.0, step=0.5, format="%.1f", key="e_qe") / 10000
    effr_ye   = st.number_input("YE adj (bp)",  value=8.0, step=0.5, format="%.1f", key="e_ye",
                                 help="EFFR jumps ~8bp at year-end (window dressing)") / 10000

    st.markdown("---")
    show_mkr = st.checkbox("Show FOMC meeting markers", value=True)
    show_diff= st.checkbox("Show Δ vs Base", value=True)

mtg_labels = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def contract_label(product, mo):
    return f"{product} {mo}'{yr2}"

def highlight_mm(s):
    out = []
    for v in s:
        if v == s.max():   out.append("background-color:#1a4731;color:#81c784")
        elif v == s.min(): out.append("background-color:#4a1515;color:#e57373")
        else:              out.append("")
    return out

def highlight_diff(s):
    out = []
    for v in s:
        if v > 0:   out.append("background-color:#1a4731;color:#81c784")
        elif v < 0: out.append("background-color:#4a1515;color:#e57373")
        else:       out.append("")
    return out

def highlight_fly(s):
    out = []
    for v in s:
        if v > 0.5:    out.append("background-color:#1a3050;color:#4fc3f7")
        elif v < -0.5: out.append("background-color:#3a2010;color:#ffb74d")
        else:          out.append("")
    return out

def build_chart(results, cases, product, meeting_dates, show_mkr, title_extra=""):
    fig = go.Figure()
    xlabels = [contract_label(product, m) for m in MONTHS]
    for case in cases:
        nm = case["name"]
        y  = [results[nm][m] for m in MONTHS]
        fig.add_trace(go.Scatter(
            x=xlabels, y=y, mode="lines+markers", name=nm,
            line=dict(color=case["color"], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{nm}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>",
        ))
    if show_mkr:
        for d in meeting_dates:
            xl = contract_label(product, MONTHS[d.month-1])
            fig.add_shape(type="line", x0=xl, x1=xl, y0=0, y1=1,
                          xref="x", yref="paper",
                          line=dict(color="rgba(255,210,60,0.5)", width=1.5, dash="dot"))
            fig.add_annotation(x=xl, y=1.05, xref="x", yref="paper",
                               text=d.strftime("%b %d"), showarrow=False,
                               font=dict(size=11, color="#ffdd44"),
                               xanchor="center", yanchor="bottom")
    fig.update_layout(
        title=f"{product} Monthly Prices — {year}{title_extra}",
        xaxis_title="Contract",
        yaxis_title="Price",
        xaxis=dict(tickfont=dict(size=12, color="#c9d1d9"), tickangle=-35,
                   gridcolor="#1e2530", showgrid=True),
        yaxis=dict(tickfont=dict(size=12, color="#c9d1d9"),
                   gridcolor="#1e2530", showgrid=True),
        legend=dict(font=dict(size=12, color="#c9d1d9"),
                    bgcolor="rgba(20,26,36,0.9)", bordercolor="#2e3a4e",
                    borderwidth=1, x=1.01, y=1),
        plot_bgcolor="#13171f", paper_bgcolor="#13171f",
        font=dict(color="#c9d1d9", size=12),
        hovermode="x unified", height=460,
        margin=dict(l=65, r=240, t=80, b=90),
    )
    return fig

def build_spread_chart(df, title, color_fn=None, zero_line=True):
    fig = go.Figure()
    for i, (idx, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Bar(
            name=idx, x=list(row.index), y=list(row.values),
            marker_color=COLORS[i % len(COLORS)],
            hovertemplate=f"<b>{idx}</b><br>%{{x}}: %{{y:+.2f}} bp<extra></extra>",
        ))
    fig.update_layout(
        title=title,
        xaxis=dict(tickfont=dict(size=11, color="#c9d1d9"), gridcolor="#1e2530", tickangle=-30),
        yaxis=dict(title="bp", tickfont=dict(size=11, color="#c9d1d9"),
                   gridcolor="#1e2530", zeroline=zero_line, zerolinecolor="#555", zerolinewidth=1.5),
        barmode="group",
        plot_bgcolor="#13171f", paper_bgcolor="#13171f",
        font=dict(color="#c9d1d9"), height=400,
        legend=dict(font=dict(size=11), bgcolor="rgba(20,26,36,0.9)"),
        margin=dict(l=60, r=20, t=55, b=80),
    )
    return fig

# ═══════════════════════════════════════════════════════════════
# CASE EDITOR (reusable)
# ═══════════════════════════════════════════════════════════════
def case_manager(pk):
    cases = st.session_state[f"{pk}_cases"]
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        if st.button("➕ Add Case", key=f"add_{pk}", use_container_width=True):
            n = len(cases)
            if n < 30:
                cases.append({"name":f"Case {n+1}","changes":[0]*8,"color":COLORS[n%len(COLORS)]})
            st.rerun()
    with c2:
        if st.button("🗑 Clear All", key=f"clr_{pk}", use_container_width=True):
            st.session_state[f"{pk}_cases"] = []
            st.rerun()
    with c3:
        exp = json.dumps([{"name":c["name"],"changes":c["changes"]} for c in cases], indent=2)
        st.download_button("⬇ Export JSON", data=exp, file_name=f"{pk}_cases.json",
                           mime="application/json", use_container_width=True, key=f"exp_{pk}")
    with c4:
        up = st.file_uploader("⬆ Import", type="json", key=f"up_{pk}", label_visibility="collapsed")
        if up:
            imp = json.load(up)
            for i, c in enumerate(imp[:30]): c["color"] = COLORS[i%len(COLORS)]
            st.session_state[f"{pk}_cases"] = imp
            st.rerun()

    to_del = []
    rows = [cases[i:i+3] for i in range(0,len(cases),3)]
    for ri, row in enumerate(rows):
        cols = st.columns(3)
        for ci, case in enumerate(row):
            gi = ri*3 + ci
            with cols[ci]:
                with st.expander(f"**{case['name']}**", expanded=False):
                    a, b = st.columns([3,1])
                    with a:
                        nn = st.text_input("Name", value=case["name"],
                                           key=f"nm_{pk}_{gi}", label_visibility="collapsed")
                        cases[gi]["name"] = nn
                    with b:
                        nc = st.color_picker("", value=case["color"],
                                             key=f"cl_{pk}_{gi}", label_visibility="collapsed")
                        cases[gi]["color"] = nc
                    sel = st.selectbox("Preset", PRESET_NAMES,
                                       index=len(PRESET_NAMES)-1, key=f"ps_{pk}_{gi}")
                    base_chg = PRESETS[sel] if sel != "Custom" else case["changes"]
                    new_ch = []
                    for mi, lbl in enumerate(mtg_labels):
                        v = st.number_input(lbl, value=float(base_chg[mi] if sel!="Custom"
                                            else case["changes"][mi]),
                                            step=25.0, format="%.0f", key=f"ch_{pk}_{gi}_{mi}")
                        new_ch.append(v)
                    cases[gi]["changes"] = new_ch
                    if st.button("🗑 Remove", key=f"del_{pk}_{gi}", use_container_width=True):
                        to_del.append(gi)
    for i in sorted(to_del, reverse=True):
        cases.pop(i)
    if to_del: st.rerun()

# ═══════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════
st.markdown("# 📈 STIR Dashboard — SR1 · ZQ · Spreads · Inter-Product")

TAB_SR1, TAB_ZQ, TAB_SPD, TAB_IPC, TAB_GUIDE = st.tabs([
    "🔵 SR1 (SOFR)", "🟠 ZQ (EFFR)", "📐 Spreads & Flies", "🔀 Inter-Product", "📚 Trading Guide"
])

# ───────────────────────────────────────────────────────────────
# COMPUTE RESULTS
# ───────────────────────────────────────────────────────────────
def compute_all(pk, base_rate, me, qe, ye):
    res = {}
    for c in st.session_state[f"{pk}_cases"]:
        res[c["name"]] = compute_prices(base_rate, me, qe, ye,
                                         meeting_dates, c["changes"], year)
    return res

sr1_res = compute_all("sr1", sofr_base, sofr_me, sofr_qe, sofr_ye)
zq_res  = compute_all("zq",  effr_base, effr_me, effr_qe, effr_ye)

# ═══════════════════════════════════════════════════════════════
# TAB 1: SR1 (SOFR)
# ═══════════════════════════════════════════════════════════════
with TAB_SR1:
    st.markdown(f'<div class="sec">🔵 SR1 (1-Month SOFR Futures) — Base SOFR: {sofr_base*100:.2f}%</div>',
                unsafe_allow_html=True)
    case_manager("sr1")
    st.markdown("---")

    if not sr1_res:
        st.warning("Add at least one case.")
        st.stop()

    cases_sr1 = st.session_state.sr1_cases

    # Metrics
    base_name = cases_sr1[0]["name"] if cases_sr1 else ""
    base_p = sr1_res.get(base_name, {})
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Base SOFR", f"{sofr_base*100:.2f}%")
    m2.metric(f"SR1 Jan'{yr2} (Base)", f"{base_p.get('Jan',0):.4f}")
    m3.metric(f"SR1 Dec'{yr2} (Base)", f"{base_p.get('Dec',0):.4f}")
    m4.metric("Active Cases", len(cases_sr1))
    if len(sr1_res) > 1:
        decs = [sr1_res[c["name"]]["Dec"] for c in cases_sr1]
        m5.metric("Dec Price Range", f"{(max(decs)-min(decs))*100:.2f} bp")
    st.markdown("---")

    t1a, t1b, t1c, t1d = st.tabs(["📈 Price Chart", "📊 Calendar Spreads", "🦋 Butterflies", "🗂 Table"])

    with t1a:
        st.plotly_chart(
            build_chart(sr1_res, cases_sr1, "SR1", meeting_dates, show_mkr,
                        f" (SOFR {sofr_base*100:.2f}%)"),
            use_container_width=True
        )

        if show_diff and len(sr1_res) > 1:
            st.markdown(f"**Δ vs '{base_name}' (bp)**")
            ddf = pd.DataFrame({c["name"]: [sr1_res[c["name"]][m] for m in MONTHS]
                                 for c in cases_sr1}, index=MONTHS).T
            diff = (ddf.subtract(ddf.loc[base_name]) * 100).drop(index=base_name, errors="ignore").round(2)
            diff.columns = [contract_label("SR1", m) for m in MONTHS]
            if not diff.empty:
                st.dataframe(diff.style.apply(highlight_diff, axis=1).format("{:+.2f}"),
                             use_container_width=True)

    with t1b:
        sp_df, fly_df, rate_df = compute_analytics(sr1_res, cases_sr1)
        sp_df.columns = [f"SR1 {c}" for c in sp_df.columns]
        st.plotly_chart(build_spread_chart(sp_df, "SR1 Calendar Spreads (bp) — back minus front"),
                        use_container_width=True)
        st.markdown("**Spread table (bp)** — positive = rates falling, negative = rates rising")
        st.dataframe(sp_df.style.apply(highlight_diff, axis=1).format("{:+.2f}"),
                     use_container_width=True)
        st.markdown("""
        <div class="infobox">
        <b>Reading spreads:</b> SR1 Feb/Mar spread = SR1 Mar price − SR1 Feb price.<br>
        <b>Positive</b> = market pricing a rate cut between those two months (Mar price higher = lower Mar rate).<br>
        <b>Negative</b> = market pricing a rate hike.<br>
        A spread that's <b>too steep vs your view</b> → sell it. <b>Too flat</b> → buy it.
        </div>""", unsafe_allow_html=True)

    with t1c:
        _, fly_df, _ = compute_analytics(sr1_res, cases_sr1)
        fly_df.columns = [f"{c}" for c in fly_df.columns]
        st.plotly_chart(build_spread_chart(fly_df, "SR1 Butterfly Values (bp)"),
                        use_container_width=True)
        st.markdown("**Fly table (bp)** — Fly = −Front + 2×Belly − Back")
        st.dataframe(fly_df.style.apply(highlight_fly, axis=1).format("{:+.2f}"),
                     use_container_width=True)
        st.markdown("""
        <div class="infobox">
        <b>+ve fly:</b> Belly is priced higher than wings → belly cheap (more cuts in belly period).<br>
        <b>−ve fly:</b> Belly priced lower than wings → sell the belly fly.<br>
        Trade: if you expect cuts to be concentrated in a specific meeting window,
        buy the fly centred on that meeting month.
        </div>""", unsafe_allow_html=True)

    with t1d:
        price_tbl = pd.DataFrame({c["name"]: [sr1_res[c["name"]][m] for m in MONTHS]
                                   for c in cases_sr1}, index=MONTHS).T
        price_tbl.columns = [contract_label("SR1", m) for m in MONTHS]
        price_tbl.index.name = "Case"
        st.markdown("**SR1 Prices**")
        st.dataframe(price_tbl.style.apply(highlight_mm).format("{:.4f}"),
                     use_container_width=True, height=min(100+35*len(price_tbl), 700))
        csv = price_tbl.to_csv()
        st.download_button("⬇ Download CSV", csv, f"sr1_prices_{year}.csv", "text/csv")

        _, _, rate_df = compute_analytics(sr1_res, cases_sr1)
        rate_df.columns = [contract_label("SR1", m) for m in MONTHS]
        rate_df.index.name = "Case"
        st.markdown("**Implied SOFR rates (%)**")
        st.dataframe(rate_df.style.apply(lambda s: [
            "background-color:#4a1515;color:#e57373" if v==s.max() else
            "background-color:#1a4731;color:#81c784" if v==s.min() else ""
            for v in s], axis=1).format("{:.4f}"), use_container_width=True,
            height=min(100+35*len(rate_df), 600))

# ═══════════════════════════════════════════════════════════════
# TAB 2: ZQ (EFFR)
# ═══════════════════════════════════════════════════════════════
with TAB_ZQ:
    st.markdown(f'<div class="sec">🟠 ZQ (30-Day Fed Funds Futures) — Base EFFR: {effr_base*100:.2f}%</div>',
                unsafe_allow_html=True)
    case_manager("zq")
    st.markdown("---")

    if not zq_res:
        st.warning("Add at least one case.")
        st.stop()

    cases_zq = st.session_state.zq_cases
    base_zq = cases_zq[0]["name"] if cases_zq else ""
    base_zq_p = zq_res.get(base_zq, {})

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Base EFFR", f"{effr_base*100:.2f}%")
    m2.metric(f"ZQ Jan'{yr2} (Base)", f"{base_zq_p.get('Jan',0):.4f}")
    m3.metric(f"ZQ Dec'{yr2} (Base)", f"{base_zq_p.get('Dec',0):.4f}")
    m4.metric("Active Cases", len(cases_zq))
    if len(zq_res) > 1:
        decs = [zq_res[c["name"]]["Dec"] for c in cases_zq]
        m5.metric("Dec Price Range", f"{(max(decs)-min(decs))*100:.2f} bp")
    st.markdown("---")

    t2a, t2b, t2c, t2d = st.tabs(["📈 Price Chart", "📊 Calendar Spreads", "🦋 Butterflies", "🗂 Table"])

    with t2a:
        st.plotly_chart(
            build_chart(zq_res, cases_zq, "ZQ", meeting_dates, show_mkr,
                        f" (EFFR {effr_base*100:.2f}%)"),
            use_container_width=True
        )

    with t2b:
        sp_df, _, _ = compute_analytics(zq_res, cases_zq)
        sp_df.columns = [f"ZQ {c}" for c in sp_df.columns]
        st.plotly_chart(build_spread_chart(sp_df, "ZQ Calendar Spreads (bp)"),
                        use_container_width=True)
        st.dataframe(sp_df.style.apply(highlight_diff, axis=1).format("{:+.2f}"),
                     use_container_width=True)

    with t2c:
        _, fly_df, _ = compute_analytics(zq_res, cases_zq)
        st.plotly_chart(build_spread_chart(fly_df, "ZQ Butterfly Values (bp)"),
                        use_container_width=True)
        st.dataframe(fly_df.style.apply(highlight_fly, axis=1).format("{:+.2f}"),
                     use_container_width=True)

    with t2d:
        price_tbl = pd.DataFrame({c["name"]: [zq_res[c["name"]][m] for m in MONTHS]
                                   for c in cases_zq}, index=MONTHS).T
        price_tbl.columns = [contract_label("ZQ", m) for m in MONTHS]
        price_tbl.index.name = "Case"
        st.dataframe(price_tbl.style.apply(highlight_mm).format("{:.4f}"),
                     use_container_width=True, height=min(100+35*len(price_tbl), 700))
        st.download_button("⬇ Download CSV", price_tbl.to_csv(),
                           f"zq_prices_{year}.csv", "text/csv")

# ═══════════════════════════════════════════════════════════════
# TAB 3: SPREADS & FLIES
# ═══════════════════════════════════════════════════════════════
with TAB_SPD:
    st.markdown('<div class="sec">📐 Spread & Fly Builder</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="infobox">
    Build any 2-leg spread or 3-leg butterfly across SR1 or ZQ contracts.
    Results are shown across all your scenario cases simultaneously.
    </div>""", unsafe_allow_html=True)

    sp_col1, sp_col2 = st.columns([1,2])

    with sp_col1:
        st.markdown("**Configure Legs**")
        product_sel = st.selectbox("Product", ["SR1","ZQ"], key="sp_prod")
        leg_type = st.radio("Structure", ["2-Leg Spread","3-Leg Butterfly (1×2×1)","Custom Weightings"],
                            horizontal=False)

        all_contracts = [contract_label(product_sel, m) for m in MONTHS]

        if leg_type == "2-Leg Spread":
            l1_mo = st.selectbox("Buy leg (Leg 1)", MONTHS, index=0, key="sp_l1")
            l2_mo = st.selectbox("Sell leg (Leg 2)", MONTHS, index=1, key="sp_l2")
            legs = [(l1_mo, +1), (l2_mo, -1)]
            label = f"{product_sel} {l1_mo}−{l2_mo}'{yr2} Spread"

        elif leg_type == "3-Leg Butterfly (1×2×1)":
            front_mo = st.selectbox("Front leg",  MONTHS, index=0, key="sp_front")
            belly_mo = st.selectbox("Belly leg",  MONTHS, index=1, key="sp_belly")
            back_mo  = st.selectbox("Back leg",   MONTHS, index=2, key="sp_back")
            legs = [(front_mo, -1), (belly_mo, +2), (back_mo, -1)]
            label = f"{product_sel} {front_mo}/{belly_mo}/{back_mo}'{yr2} Fly"

        else:  # Custom
            st.markdown("Enter weight for each month (0 = not included)")
            legs = []
            wcols = st.columns(3)
            for mi, mo in enumerate(MONTHS):
                with wcols[mi % 3]:
                    w = st.number_input(f"{product_sel} {mo}", value=0, step=1,
                                        key=f"cw_{mi}", format="%d")
                    if w != 0:
                        legs.append((mo, w))
            label = f"{product_sel} Custom'{yr2}"

    with sp_col2:
        st.markdown(f"**{label}**")
        res_sel = sr1_res if product_sel == "SR1" else zq_res
        cases_sel = st.session_state.sr1_cases if product_sel == "SR1" else st.session_state.zq_cases

        if not res_sel or not legs:
            st.info("Configure legs and add cases to see results.")
        else:
            spread_vals = {}
            for case in cases_sel:
                nm = case["name"]
                p  = res_sel[nm]
                val = sum(p[mo] * w for mo, w in legs) * 100  # convert to bp
                spread_vals[nm] = round(val, 3)

            # Bar chart
            fig_sp = go.Figure()
            sorted_cases = sorted(spread_vals.items(), key=lambda x: x[1])
            names_s = [x[0] for x in sorted_cases]
            vals_s  = [x[1] for x in sorted_cases]
            colors_s= [COLORS[cases_sel.index(next(c for c in cases_sel if c["name"]==n)) % len(COLORS)]
                       for n in names_s]
            fig_sp.add_trace(go.Bar(
                x=names_s, y=vals_s, marker_color=colors_s,
                hovertemplate="<b>%{x}</b><br>%{y:+.3f} bp<extra></extra>",
            ))
            fig_sp.update_layout(
                title=label,
                xaxis=dict(tickfont=dict(size=11, color="#c9d1d9"), tickangle=-35),
                yaxis=dict(title="bp", zeroline=True, zerolinecolor="#666",
                           gridcolor="#1e2530", tickfont=dict(size=11, color="#c9d1d9")),
                plot_bgcolor="#13171f", paper_bgcolor="#13171f",
                font=dict(color="#c9d1d9"), height=380,
                margin=dict(l=60, r=20, t=50, b=100),
            )
            st.plotly_chart(fig_sp, use_container_width=True)

            # Summary table
            sv_df = pd.DataFrame.from_dict(spread_vals, orient="index", columns=[f"{label} (bp)"])
            sv_df.index.name = "Case"
            sv_df["vs Base"] = (sv_df[f"{label} (bp)"] - sv_df[f"{label} (bp)"].iloc[0]).round(3)
            st.dataframe(
                sv_df.style.apply(highlight_diff).format("{:+.3f}"),
                use_container_width=True
            )

    st.markdown("---")
    st.markdown('<div class="sec">📊 Full Calendar Spread Matrix</div>', unsafe_allow_html=True)
    mat_prod = st.selectbox("Product for matrix", ["SR1","ZQ"], key="mat_prod")
    mat_res   = sr1_res if mat_prod=="SR1" else zq_res
    mat_cases = st.session_state.sr1_cases if mat_prod=="SR1" else st.session_state.zq_cases

    if mat_res and mat_cases:
        sp_df, fly_df, _ = compute_analytics(mat_res, mat_cases)
        sp_df.columns  = [f"{mat_prod} {c}" for c in sp_df.columns]
        fly_df.columns = [f"{c}" for c in fly_df.columns]

        st.markdown("**Calendar Spreads (bp)** — consecutive month pairs")
        st.dataframe(sp_df.style.apply(highlight_diff, axis=1).format("{:+.2f}"),
                     use_container_width=True)
        st.markdown("**Butterfly Values (bp)** — −Front + 2×Belly − Back")
        st.dataframe(fly_df.style.apply(highlight_fly, axis=1).format("{:+.2f}"),
                     use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 4: INTER-PRODUCT (SR1 vs ZQ)
# ═══════════════════════════════════════════════════════════════
with TAB_IPC:
    st.markdown('<div class="sec">🔀 Inter-Product: SR1 vs ZQ (SOFR–FF Basis)</div>',
                unsafe_allow_html=True)
    st.markdown("""
    <div class="infobox">
    <b>SR1 − ZQ basis</b> = SOFR futures price − Fed Funds futures price for the same delivery month.<br>
    Positive basis = SOFR priced higher than EFFR (normal, SOFR typically slightly above EFFR).<br>
    Negative basis = unusual, stress signal. Basis tends to widen at quarter/year-end.
    </div>""", unsafe_allow_html=True)

    ip_col1, ip_col2 = st.columns([1,3])
    with ip_col1:
        st.markdown("**Select cases to compare**")
        sr1_case_names = [c["name"] for c in st.session_state.sr1_cases]
        zq_case_names  = [c["name"] for c in st.session_state.zq_cases]

        sel_sr1 = st.selectbox("SR1 Case", sr1_case_names, index=0, key="ip_sr1") if sr1_case_names else None
        sel_zq  = st.selectbox("ZQ Case",  zq_case_names,  index=0, key="ip_zq")  if zq_case_names  else None
        show_both_lines = st.checkbox("Overlay SR1 and ZQ prices", value=True)

    with ip_col2:
        if sel_sr1 and sel_zq and sel_sr1 in sr1_res and sel_zq in zq_res:
            sr1_p = [sr1_res[sel_sr1][m] for m in MONTHS]
            zq_p  = [zq_res[sel_zq][m]  for m in MONTHS]
            basis = [round((s-z)*100, 3) for s,z in zip(sr1_p, zq_p)]  # in bp
            xlabels = MONTHS

            fig_ip = go.Figure()
            if show_both_lines:
                fig_ip.add_trace(go.Scatter(
                    x=[contract_label("SR1", m) for m in MONTHS], y=sr1_p,
                    name=f"SR1: {sel_sr1}", line=dict(color="#4fc3f7", width=2.5),
                    marker=dict(size=6), yaxis="y1",
                    hovertemplate="SR1 %{x}: %{y:.4f}<extra></extra>",
                ))
                fig_ip.add_trace(go.Scatter(
                    x=[contract_label("ZQ", m) for m in MONTHS], y=zq_p,
                    name=f"ZQ: {sel_zq}", line=dict(color="#ffb74d", width=2.5, dash="dash"),
                    marker=dict(size=6), yaxis="y1",
                    hovertemplate="ZQ %{x}: %{y:.4f}<extra></extra>",
                ))
            fig_ip.add_trace(go.Bar(
                x=MONTHS, y=basis,
                name="Basis (SR1−ZQ, bp)",
                marker_color=["#81c784" if v>=0 else "#e57373" for v in basis],
                yaxis="y2",
                hovertemplate="%{x} Basis: %{y:+.2f} bp<extra></extra>",
            ))
            fig_ip.update_layout(
                title=f"SR1 vs ZQ — {sel_sr1} / {sel_zq}",
                xaxis=dict(tickfont=dict(size=11, color="#c9d1d9"), tickangle=-30),
                yaxis=dict(title="Price", gridcolor="#1e2530", tickfont=dict(size=11, color="#c9d1d9")),
                yaxis2=dict(title="Basis (bp)", overlaying="y", side="right",
                            zeroline=True, zerolinecolor="#666", showgrid=False,
                            tickfont=dict(size=11, color="#aaa")),
                legend=dict(font=dict(size=11), bgcolor="rgba(20,26,36,0.9)"),
                plot_bgcolor="#13171f", paper_bgcolor="#13171f",
                font=dict(color="#c9d1d9"), height=430, barmode="overlay",
                margin=dict(l=65, r=80, t=60, b=80),
            )
            st.plotly_chart(fig_ip, use_container_width=True)

            # Basis table
            basis_df = pd.DataFrame({
                "Month": [contract_label("SR1",m) for m in MONTHS],
                f"SR1 ({sel_sr1})": [f"{v:.4f}" for v in sr1_p],
                f"ZQ  ({sel_zq})":  [f"{v:.4f}" for v in zq_p],
                "Basis (bp)":       [f"{v:+.2f}" for v in basis],
            }).set_index("Month")
            st.dataframe(basis_df, use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="sec">All-Case Basis Comparison</div>', unsafe_allow_html=True)
    basis_mo = st.selectbox("Select month", MONTHS, index=8, key="basis_mo")  # default Sep
    if st.session_state.sr1_cases and st.session_state.zq_cases:
        rows = []
        for sr1_c in st.session_state.sr1_cases:
            for zq_c in st.session_state.zq_cases:
                s_nm = sr1_c["name"]; z_nm = zq_c["name"]
                if s_nm in sr1_res and z_nm in zq_res:
                    b = round((sr1_res[s_nm][basis_mo] - zq_res[z_nm][basis_mo])*100, 3)
                    rows.append({"SR1 Case": s_nm, "ZQ Case": z_nm,
                                 f"Basis {basis_mo} (bp)": b})
        if rows:
            bdf = pd.DataFrame(rows)
            st.dataframe(bdf.style.apply(
                lambda s: [("background-color:#1a4731;color:#81c784" if v>0
                            else "background-color:#4a1515;color:#e57373") for v in s]
                if s.name == f"Basis {basis_mo} (bp)" else [""]*len(s), axis=0
            ).format({f"Basis {basis_mo} (bp)": "{:+.3f}"}), use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 5: TRADING GUIDE
# ═══════════════════════════════════════════════════════════════
with TAB_GUIDE:
    st.markdown('<div class="sec">📚 STIR Trading Guide — SR1, ZQ & Spreads</div>',
                unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    with g1:
        st.markdown("### 🔵 What is SR1?")
        st.markdown("""
        **SR1** is the CME 1-Month SOFR futures contract.
        - Price = **100 − average daily SOFR** for the delivery month
        - Settlement is based on the daily compounded SOFR rate published by the NY Fed
        - Each contract covers one calendar month (Jan, Feb, … Dec)
        - **1 bp move = $41.67** per contract (based on $5M notional × 30/360)
        - SR1 reflects **exact Fed meeting outcomes** because SOFR tracks the Fed's target directly

        **Key SR1 price relationships:**
        - SR1 Jan trades flat if no cut is expected before Jan 28 meeting
        - SR1 Mar prices in the Mar 18 meeting outcome
        - Months *after* the last meeting of the year are "terminal rate" contracts
        """)

        st.markdown("### 🟠 What is ZQ?")
        st.markdown("""
        **ZQ** is the CBOT 30-Day Fed Funds futures contract.
        - Price = **100 − average daily EFFR** (Effective Fed Funds Rate)
        - EFFR is published daily by the NY Fed; it trades within the FOMC target range
        - Typically **5–8bp below** the upper bound of the FF target range
        - **1 bp move = $41.67** per contract
        - ZQ is the *older* and more liquid product; SR1 has gained ground since SOFR transition

        **SOFR vs EFFR:**
        - Pre-2022: LIBOR → SOFR basis was important
        - Post-2022: SOFR ≈ EFFR ≈ FF target upper bound −5bp to −8bp
        - At QE/YE: EFFR can move more than SOFR (window dressing effects)
        """)

    with g2:
        st.markdown("### 📐 Calendar Spreads")
        st.markdown("""
        **Definition:** Spread = Price(back month) − Price(front month)

        A SR1 **Jun/Jul spread** = SR1 Jul price − SR1 Jun price

        | Spread value | Interpretation |
        |---|---|
        | **+25 bp** | Market expects one 25bp cut between Jun and Jul meetings |
        | **0 bp** | No cut expected; rates flat between the two months |
        | **−25 bp** | Market prices a hike between the two months |
        | **+12.5 bp** | 50% probability of a 25bp cut |

        **How to trade:**
        - **Buy the spread** (buy back, sell front) → you profit if cuts get priced in
        - **Sell the spread** → you profit if cuts get priced out / hikes priced in
        - Spreads around *active meeting months* are the most volatile and interesting
        """)

        st.markdown("### 🦋 Butterflies")
        st.markdown("""
        **Definition:** Fly = −Front + 2×Belly − Back (in price terms, expressed in bp)

        A SR1 **May/Jun/Jul fly** = −SR1_May + 2×SR1_Jun − SR1_Jul

        | Fly value | Interpretation |
        |---|---|
        | **+ve** | Belly is *cheap* — more cuts priced between belly meetings |
        | **−ve** | Belly is *rich* — fewer cuts in belly vs wings |
        | **Near zero** | Curve is linear; cuts spread evenly |

        **How to trade:**
        - **Buy the fly** → profit if belly richens (even more cuts priced there)
        - **Sell the fly** → profit if belly cheapens vs wings
        - Flies are low-carry trades but high-information — great for expressing *when* not just *how many* cuts
        """)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🔀 Inter-Product (SR1 vs ZQ)")
        st.markdown("""
        **Basis = SR1 price − ZQ price** for the same month

        - Normally **+2 to +8bp** (SOFR slightly above EFFR on average)
        - **Widens at quarter-end / year-end** → buy basis (buy SR1, sell ZQ) going into QE
        - **Narrows / inverts** in stress → sell basis
        - Inter-product spreads are heavily affected by Fed balance sheet policy (RRP, reserve scarcity)

        **Typical inter-product trade:**
        > If you think year-end pressure will push EFFR lower relative to SOFR:
        > Buy ZQ Dec, Sell SR1 Dec (sell the basis)
        """)

    with c2:
        st.markdown("### 🛠 Using This Tool for Real Trading")
        st.markdown("""
        **Scenario analysis workflow:**
        1. Set your **base case** (market-implied path from broker screens / futures prices)
        2. Add **bull/bear scenarios** reflecting your macro view
        3. Compare **December prices** across scenarios = your P&L distribution
        4. Use **spreads tab** to find which months have the most disagreement between scenarios
        5. That disagreement point is your highest-conviction trade

        **Step-by-step example:**
        > Market prices 2 cuts in 2026 (Jun + Sep). You think there will be 4 cuts.
        > 1. Set Base = "2 Cuts Jun+Sep", add "4 Cuts Mar+Jun+Sep+Dec"
        > 2. Look at SR1 calendar spreads — biggest difference is in Mar/Apr spread
        > 3. That spread is your expression: **buy SR1 Apr, sell SR1 Mar** (buy the Mar meeting cut)
        > 4. Size per bp of conviction using the Analytics tab

        **Risk management:**
        - SR1/ZQ spreads have very tight bid/offer (0.25–0.5bp for liquids)
        - Flies are wider but have lower delta risk
        - Always check carry: a steep spread has positive carry if held, flat spread has zero carry
        """)

    st.markdown("---")
    st.markdown("""
    <div class="tip">
    <b>💡 Pro tip:</b> The most efficient way to express a view on a specific FOMC meeting
    is via the <b>two contracts that straddle it</b>. For example, to trade the Sep 16 meeting,
    use SR1 Sep (which includes Sep 16) vs SR1 Aug (which doesn't).
    The Sep/Oct spread captures the Oct 28 meeting, not Sep. Map meetings to contract months carefully.
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="warn">
    <b>⚠️ Meeting-to-contract mapping for 2026:</b><br>
    Jan 28 → prices into SR1 Jan (Jan 28 effective date falls in Jan) → but effective date is Jan 29, so SR1 Feb is first full contract after Jan meeting<br>
    Mar 18 → SR1 Apr is first post-meeting contract | Jun 17 → SR1 Jul | Jul 29 → SR1 Aug | Sep 16 → SR1 Oct | Oct 28 → SR1 Nov | Dec 9 → SR1 Jan'27<br>
    <b>Rule:</b> the rate change takes effect the day AFTER the meeting. The first contract fully priced at the new rate = the contract for the month containing the effective date.
    </div>""", unsafe_allow_html=True)

st.markdown("---")
st.caption(
    f"STIR Dashboard — SR1 (SOFR {sofr_base*100:.2f}%) · ZQ (EFFR {effr_base*100:.2f}%) · "
    f"ME {sofr_me*10000:.1f}bp · YE(ZQ) {effr_ye*10000:.1f}bp · {year}"
)
