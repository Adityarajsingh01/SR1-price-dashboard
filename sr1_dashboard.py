"""
STIR TERMINAL — SR1 (SOFR) · ZQ (EFFR) · Spreads & Flies · Inter-Product
Bloomberg-style dark terminal for US STIR scenario analysis
Run:  streamlit run stir_dashboard.py
Deps: pip install streamlit plotly pandas openpyxl xlsxwriter
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar, json, io

# ══════════════════════════════════════════════════════
# PAGE CONFIG & BLOOMBERG CSS
# ══════════════════════════════════════════════════════
st.set_page_config(
    page_title="STIR TERMINAL | SR1 · ZQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BB = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] {
    background-color: #0a0a0f !important;
    color: #e8c84a !important;
    font-family: 'Roboto Mono', 'Courier New', monospace !important;
}
.main .block-container { padding-top: 0.3rem; max-width: 100%; }
[data-testid="stSidebar"] { background-color: #050508 !important; border-right: 1px solid #2a2a1a !important; }
[data-testid="stSidebar"] * { color: #c8a820 !important; }
[data-testid="stSidebar"] input { background:#111108 !important; color:#f0d050 !important; border:1px solid #3a3a1a !important; }
div[data-testid="metric-container"] { background:#0d0d0a !important; border:1px solid #3a3a10 !important; border-top:2px solid #e8c84a !important; border-radius:2px !important; padding:8px 14px !important; }
div[data-testid="metric-container"] label { color:#888850 !important; font-size:10px !important; letter-spacing:1px; text-transform:uppercase; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color:#f0d050 !important; font-size:22px !important; font-weight:700; }
.stTabs [data-baseweb="tab-list"] { background:#050508 !important; border-bottom:1px solid #3a3a10 !important; gap:0 !important; }
.stTabs [data-baseweb="tab"] { background:#050508 !important; color:#666640 !important; font-size:12px !important; font-weight:700 !important; font-family:'Roboto Mono',monospace !important; padding:8px 20px !important; border-radius:0 !important; border-right:1px solid #1a1a10 !important; letter-spacing:0.5px; }
.stTabs [aria-selected="true"] { background:#1a1a08 !important; color:#f0d050 !important; border-top:2px solid #f0d050 !important; }
.stButton > button { background:#111108 !important; color:#e8c84a !important; border:1px solid #3a3a10 !important; border-radius:2px !important; font-family:'Roboto Mono',monospace !important; font-size:11px !important; font-weight:700 !important; letter-spacing:0.5px !important; padding:6px 12px !important; }
.stButton > button:hover { background:#1e1e0a !important; border-color:#e8c84a !important; }
.stDownloadButton > button { background:#0a1a08 !important; color:#4af04a !important; border:1px solid #1a4a1a !important; border-radius:2px !important; font-family:'Roboto Mono',monospace !important; font-size:11px !important; font-weight:700 !important; }
.stSelectbox > div > div { background:#111108 !important; color:#e8c84a !important; border:1px solid #3a3a10 !important; }
.stNumberInput input { background:#111108 !important; color:#f0d050 !important; border:1px solid #3a3a10 !important; }
.stTextInput input { background:#111108 !important; color:#f0d050 !important; border:1px solid #3a3a10 !important; }
.stRadio label, .stCheckbox label { color:#c8a820 !important; font-size:12px !important; }
details { background:#0d0d0a !important; border:1px solid #2a2a10 !important; border-radius:2px !important; }
details summary { color:#c8a820 !important; font-size:12px !important; font-weight:700 !important; padding:6px 10px !important; }
hr { border-color:#2a2a10 !important; }
.tip  { background:#061206; border-left:3px solid #22cc22; padding:8px 14px; border-radius:2px; font-size:12px; margin:4px 0; color:#88ee88; font-family:monospace; }
.warn { background:#120a06; border-left:3px solid #cc8822; padding:8px 14px; border-radius:2px; font-size:12px; margin:4px 0; color:#eebb88; font-family:monospace; }
.ibox { background:#060c12; border-left:3px solid #4488cc; padding:8px 14px; border-radius:2px; font-size:12px; margin:4px 0; color:#88bbee; font-family:monospace; }
.bb-hdr { font-size:13px; font-weight:700; color:#f0d050; letter-spacing:1.5px; text-transform:uppercase; border-bottom:1px solid #3a3a10; padding-bottom:4px; margin:8px 0 6px 0; font-family:'Roboto Mono',monospace; }
</style>
"""
st.markdown(BB, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
COLORS = [
    "#f0d050","#4af04a","#4ac8f0","#f04a4a","#c84af0","#f0884a","#4af088","#884af0",
    "#f0c84a","#4a88f0","#f04a88","#88f04a","#4af0c8","#f08888","#88c8f0","#c8f04a",
    "#f04ac8","#4a4af0","#f0f04a","#4af0f0","#aaaaaa","#ff8844","#44ff88","#8844ff",
    "#ff4488","#44ffff","#ffff44","#ff4444","#44ff44","#4444ff",
]
DEFAULT_MEETINGS = [
    date(2026,1,28), date(2026,3,18), date(2026,4,29), date(2026,6,17),
    date(2026,7,29), date(2026,9,16), date(2026,10,28), date(2026,12,9),
]
PRESETS = {
    "No Change":                        [ 0,   0,   0,   0,   0,   0,   0,   0],
    "1 Cut -25 (Mar)":                  [ 0, -25,   0,   0,   0,   0,   0,   0],
    "1 Cut -25 (Jun)":                  [ 0,   0,   0, -25,   0,   0,   0,   0],
    "1 Cut -25 (Sep)":                  [ 0,   0,   0,   0,   0, -25,   0,   0],
    "1 Cut -25 (Dec)":                  [ 0,   0,   0,   0,   0,   0,   0, -25],
    "2 Cuts (Jun+Sep)":                 [ 0,   0,   0, -25,   0, -25,   0,   0],
    "2 Cuts (Sep+Dec)":                 [ 0,   0,   0,   0,   0, -25,   0, -25],
    "3 Cuts (Jun+Sep+Dec)":             [ 0,   0,   0, -25,   0, -25,   0, -25],
    "4 Cuts (Mar+Jun+Sep+Dec)":         [ 0, -25,   0, -25,   0, -25,   0, -25],
    "5 Cuts (Jan+Mar+Jun+Sep+Dec)":     [-25, -25,   0, -25,   0, -25,   0, -25],
    "Hike +25 (Mar)":                   [ 0,  25,   0,   0,   0,   0,   0,   0],
    "2 Hikes (Mar+Jun)":                [ 0,  25,   0,  25,   0,   0,   0,   0],
    "Aggressive -50 (Sep)":             [ 0,   0,   0,   0,   0, -50,   0,   0],
    "Custom":                           [ 0,   0,   0,   0,   0,   0,   0,   0],
}
PRESET_NAMES = list(PRESETS.keys())

BB_LAYOUT = dict(
    plot_bgcolor="#050508", paper_bgcolor="#050508",
    font=dict(color="#c8a820", size=11, family="Roboto Mono, Courier New, monospace"),
    xaxis=dict(gridcolor="#1a1a10", showgrid=True, zeroline=False,
               tickfont=dict(size=11, color="#c8a820"), tickangle=-35,
               linecolor="#3a3a10", showline=True),
    yaxis=dict(gridcolor="#1a1a10", showgrid=True, zeroline=False,
               tickfont=dict(size=11, color="#c8a820"),
               linecolor="#3a3a10", showline=True),
    legend=dict(bgcolor="rgba(5,5,8,0.95)", bordercolor="#3a3a10", borderwidth=1,
                font=dict(size=11, color="#c8a820"), x=1.01, y=1),
    hoverlabel=dict(bgcolor="#111108", bordercolor="#e8c84a",
                    font=dict(size=11, color="#f0d050")),
    hovermode="x unified",
    margin=dict(l=65, r=230, t=55, b=80),
)

# ══════════════════════════════════════════════════════
# PRICING ENGINE
# ══════════════════════════════════════════════════════
def get_last_biz_day(yr, mo):
    last = date(yr, mo, calendar.monthrange(yr, mo)[1])
    while last.weekday() >= 5:
        last -= timedelta(days=1)
    return last

def compute_prices(base_rate, me_adj, qe_adj, ye_adj, meeting_dates, rate_changes_bps, year=2026):
    rate_path = []
    cum = base_rate
    for mtg, chg in zip(meeting_dates, rate_changes_bps):
        cum += chg / 10000.0
        rate_path.append((mtg + timedelta(days=1), cum))
    def rate_for_day(d):
        r = base_rate
        for eff, val in rate_path:
            if d >= eff: r = val
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

# ══════════════════════════════════════════════════════
# ANALYTICS
# SPREAD: FRONT − BACK (standard STIR convention)
# Jun/Jul = SR1_Jun − SR1_Jul
# Negative = cuts priced (back > front)
# ══════════════════════════════════════════════════════
def compute_analytics(results, cases):
    sp_labels  = [f"{MONTHS[i]}/{MONTHS[i+1]}" for i in range(11)]
    fly_labels = [f"{MONTHS[i-1]}/{MONTHS[i]}/{MONTHS[i+1]}" for i in range(1,11)]
    sp_data, fly_data, rate_data = {}, {}, {}
    for case in cases:
        nm = case["name"]
        if nm not in results: continue
        p = [results[nm][m] for m in MONTHS]
        sp_data[nm]   = [round((p[i] - p[i+1]) * 100, 3) for i in range(11)]
        fly_data[nm]  = [round((-p[i-1] + 2*p[i] - p[i+1]) * 100, 3) for i in range(1,11)]
        rate_data[nm] = [round(100 - v, 4) for v in p]
    return (
        pd.DataFrame(sp_data,  index=sp_labels).T,
        pd.DataFrame(fly_data, index=fly_labels).T,
        pd.DataFrame(rate_data, index=MONTHS).T,
    )

# ══════════════════════════════════════════════════════
# EXCEL EXPORT
# ══════════════════════════════════════════════════════
def build_excel(sr1_res, zq_res, sr1_cases, zq_cases, year, yr2, meeting_dates):
    buf = io.BytesIO()
    mtg_lbl = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        def write_product(results, cases, product):
            if not results or not cases: return
            px, sp, fly, rt = [], [], [], []
            for c in cases:
                nm = c["name"]
                if nm not in results: continue
                p = results[nm]
                pl = [p[m] for m in MONTHS]
                px.append( {**{"Case":nm}, **{f"{product} {m}'{yr2}": p[m] for m in MONTHS}} )
                sp.append( {**{"Case":nm}, **{f"{MONTHS[i]}/{MONTHS[i+1]}": round((pl[i]-pl[i+1])*100,3) for i in range(11)}} )
                fly.append({**{"Case":nm}, **{f"{MONTHS[i-1]}/{MONTHS[i]}/{MONTHS[i+1]}": round((-pl[i-1]+2*pl[i]-pl[i+1])*100,3) for i in range(1,11)}})
                rt.append( {**{"Case":nm}, **{f"{product} {m}'{yr2}": round(100-p[m],4) for m in MONTHS}} )
            pd.DataFrame(px).set_index("Case").to_excel(writer, sheet_name=f"{product} Prices")
            pd.DataFrame(sp).set_index("Case").to_excel(writer, sheet_name=f"{product} Spreads (bp)")
            pd.DataFrame(fly).set_index("Case").to_excel(writer, sheet_name=f"{product} Flies (bp)")
            pd.DataFrame(rt).set_index("Case").to_excel(writer, sheet_name=f"{product} Impl Rates")

        write_product(sr1_res, sr1_cases, "SR1")
        write_product(zq_res,  zq_cases,  "ZQ")

        if sr1_res and zq_res:
            rows = []
            for sc in sr1_cases:
                for zc in zq_cases:
                    if sc["name"] in sr1_res and zc["name"] in zq_res:
                        row = {"SR1 Case": sc["name"], "ZQ Case": zc["name"]}
                        for m in MONTHS:
                            row[f"Basis {m} (bp)"] = round((sr1_res[sc["name"]][m]-zq_res[zc["name"]][m])*100,3)
                        rows.append(row)
            if rows: pd.DataFrame(rows).to_excel(writer, sheet_name="SR1-ZQ Basis (bp)", index=False)

        cfg = []
        for c in sr1_cases:
            row = {"Product":"SR1","Case":c["name"]}
            for i,l in enumerate(mtg_lbl): row[l] = c["changes"][i]
            cfg.append(row)
        for c in zq_cases:
            row = {"Product":"ZQ","Case":c["name"]}
            for i,l in enumerate(mtg_lbl): row[l] = c["changes"][i]
            cfg.append(row)
        pd.DataFrame(cfg).to_excel(writer, sheet_name="Case Config", index=False)

    buf.seek(0)
    return buf.getvalue()

# ══════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════
def _defaults():
    return [
        {"name":"Base (No Change)", "changes":[0]*8, "color":COLORS[0]},
        {"name":"2 Cuts Jun+Sep",   "changes":[0,0,0,-25,0,-25,0,0], "color":COLORS[1]},
    ]
for k in ["sr1_cases","zq_cases"]:
    if k not in st.session_state: st.session_state[k] = _defaults()
if "meeting_dates" not in st.session_state: st.session_state.meeting_dates = DEFAULT_MEETINGS[:]

# ══════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ◈ STIR TERMINAL")
    year = int(st.number_input("YEAR", value=2026, step=1, min_value=2020, max_value=2035))
    yr2  = str(year)[2:]
    st.markdown("**FOMC MEETING DATES**")
    meeting_dates = []
    for i, dfl in enumerate(st.session_state.meeting_dates):
        meeting_dates.append(st.date_input(f"MTG {i+1}", value=dfl, key=f"mtg_{i}"))
    if st.button("↺ RESET 2026"): st.session_state.meeting_dates = DEFAULT_MEETINGS[:]; st.rerun()
    st.markdown("---")
    st.markdown("**● SR1 (SOFR)**")
    sofr_base = st.number_input("Base SOFR %", value=4.25, step=0.25, format="%.2f", min_value=0.0, max_value=15.0, key="sb") / 100
    sofr_me   = st.number_input("ME adj bp",   value=1.0,  step=0.5,  format="%.1f", key="sm") / 10000
    sofr_qe   = st.number_input("QE adj bp",   value=0.0,  step=0.5,  format="%.1f", key="sq") / 10000
    sofr_ye   = st.number_input("YE adj bp",   value=0.0,  step=0.5,  format="%.1f", key="sy") / 10000
    st.markdown("**● ZQ (EFFR)**")
    effr_base = st.number_input("Base EFFR %", value=4.33, step=0.25, format="%.2f", min_value=0.0, max_value=15.0, key="eb") / 100
    effr_me   = st.number_input("ME adj bp",   value=0.0,  step=0.5,  format="%.1f", key="em") / 10000
    effr_qe   = st.number_input("QE adj bp",   value=0.0,  step=0.5,  format="%.1f", key="eq") / 10000
    effr_ye   = st.number_input("YE adj bp",   value=8.0,  step=0.5,  format="%.1f", key="ey") / 10000
    st.markdown("---")
    show_mkr  = st.checkbox("FOMC MARKERS",   value=True)
    show_diff = st.checkbox("SHOW Δ VS BASE", value=True)

mtg_labels = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]

# ══════════════════════════════════════════════════════
# STYLING HELPERS
# ══════════════════════════════════════════════════════
def hl_price(s):
    return ["background:#0a2a0a;color:#4af04a;font-weight:bold" if v==s.max()
            else "background:#2a0a0a;color:#f04a4a;font-weight:bold" if v==s.min()
            else "color:#c8a820" for v in s]

def hl_spread(s):
    return ["background:#2a0a0a;color:#f04a4a;font-weight:bold" if v < -0.5
            else "background:#0a2a0a;color:#4af04a;font-weight:bold" if v > 0.5
            else "color:#888860" for v in s]

def hl_fly(s):
    return ["background:#0a1a2a;color:#4ac8f0;font-weight:bold" if v > 0.5
            else "background:#1a1a0a;color:#f0c84a;font-weight:bold" if v < -0.5
            else "color:#888860" for v in s]

def hl_rate(s):
    return ["background:#2a0a0a;color:#f04a4a;font-weight:bold" if v==s.max()
            else "background:#0a2a0a;color:#4af04a;font-weight:bold" if v==s.min()
            else "color:#c8a820" for v in s]

# ══════════════════════════════════════════════════════
# CHART HELPERS
# ══════════════════════════════════════════════════════
def clbl(product, mo): return f"{product} {mo}'{yr2}"

def build_price_chart(results, cases, product, meeting_dates, show_mkr, sub=""):
    fig = go.Figure()
    xlabels = [clbl(product, m) for m in MONTHS]
    for case in cases:
        nm = case["name"]
        if nm not in results: continue
        fig.add_trace(go.Scatter(
            x=xlabels, y=[results[nm][m] for m in MONTHS],
            mode="lines+markers", name=nm,
            line=dict(color=case["color"], width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{nm}</b><br>%{{x}}: %{{y:.4f}}<extra></extra>",
        ))
    if show_mkr:
        for d in meeting_dates:
            xl = clbl(product, MONTHS[d.month-1])
            fig.add_shape(type="line", x0=xl, x1=xl, y0=0, y1=1,
                          xref="x", yref="paper",
                          line=dict(color="rgba(240,208,80,0.4)", width=1, dash="dot"))
            fig.add_annotation(x=xl, y=1.04, xref="x", yref="paper",
                               text=d.strftime("%b %d"), showarrow=False,
                               font=dict(size=10, color="#f0d050"), xanchor="center", yanchor="bottom")
    layout = {**BB_LAYOUT, "title": f"{product} PRICE CURVE — {year}{sub}",
              "xaxis_title": "CONTRACT", "yaxis_title": "PRICE", "height": 400}
    fig.update_layout(**layout)
    return fig

def build_bar_chart(df, title, unit="bp"):
    fig = go.Figure()
    for i, (idx, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Bar(
            name=idx, x=list(row.index), y=list(row.values),
            marker_color=COLORS[i % len(COLORS)],
            hovertemplate=f"<b>{idx}</b><br>%{{x}}: %{{y:+.3f}} {unit}<extra></extra>",
        ))
    layout = {**BB_LAYOUT, "title": title, "yaxis_title": unit, "barmode": "group",
              "height": 360, "margin": dict(l=60, r=20, t=50, b=80)}
    fig.update_layout(**layout)
    fig.update_yaxes(zeroline=True, zerolinecolor="#555530", zerolinewidth=1.5)
    return fig

# ══════════════════════════════════════════════════════
# CASE EDITOR
# ══════════════════════════════════════════════════════
def case_manager(pk):
    cases = st.session_state[f"{pk}_cases"]
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        if st.button("+ ADD CASE", key=f"add_{pk}", use_container_width=True):
            n = len(cases)
            if n < 30: cases.append({"name":f"Case {n+1}","changes":[0]*8,"color":COLORS[n%len(COLORS)]})
            st.rerun()
    with c2:
        if st.button("X CLEAR ALL", key=f"clr_{pk}", use_container_width=True):
            st.session_state[f"{pk}_cases"] = []; st.rerun()
    with c3:
        exp = json.dumps([{"name":c["name"],"changes":c["changes"]} for c in cases], indent=2)
        st.download_button("DL JSON", data=exp, file_name=f"{pk}_cases.json",
                           mime="application/json", use_container_width=True, key=f"exp_{pk}")
    with c4:
        up = st.file_uploader("IMPORT JSON", type="json", key=f"up_{pk}", label_visibility="collapsed")
        if up:
            imp = json.load(up)
            for i, c in enumerate(imp[:30]): c["color"] = COLORS[i%len(COLORS)]
            st.session_state[f"{pk}_cases"] = imp; st.rerun()
    to_del = []
    for ri, row_g in enumerate([cases[i:i+3] for i in range(0,len(cases),3)]):
        cols = st.columns(3)
        for ci, case in enumerate(row_g):
            gi = ri*3+ci
            with cols[ci]:
                with st.expander(f"▶ {case['name']}", expanded=False):
                    a, b = st.columns([3,1])
                    with a:
                        nn = st.text_input("NAME", value=case["name"], key=f"nm_{pk}_{gi}", label_visibility="collapsed")
                        cases[gi]["name"] = nn
                    with b:
                        nc = st.color_picker("", value=case["color"], key=f"cl_{pk}_{gi}", label_visibility="collapsed")
                        cases[gi]["color"] = nc
                    sel = st.selectbox("PRESET", PRESET_NAMES, index=len(PRESET_NAMES)-1, key=f"ps_{pk}_{gi}")
                    base_chg = PRESETS[sel] if sel != "Custom" else case["changes"]
                    new_ch = []
                    for mi, lbl in enumerate(mtg_labels):
                        v = st.number_input(lbl, value=float(base_chg[mi] if sel!="Custom" else case["changes"][mi]),
                                            step=25.0, format="%.0f", key=f"ch_{pk}_{gi}_{mi}")
                        new_ch.append(v)
                    cases[gi]["changes"] = new_ch
                    if st.button("X REMOVE", key=f"del_{pk}_{gi}", use_container_width=True): to_del.append(gi)
    for i in sorted(to_del, reverse=True): cases.pop(i)
    if to_del: st.rerun()

# ══════════════════════════════════════════════════════
# COMPUTE
# ══════════════════════════════════════════════════════
def compute_all(pk, base_rate, me, qe, ye):
    res = {}
    for c in st.session_state[f"{pk}_cases"]:
        res[c["name"]] = compute_prices(base_rate, me, qe, ye, meeting_dates, c["changes"], year)
    return res

sr1_res = compute_all("sr1", sofr_base, sofr_me, sofr_qe, sofr_ye)
zq_res  = compute_all("zq",  effr_base, effr_me, effr_qe, effr_ye)

# ══════════════════════════════════════════════════════
# HEADER + GLOBAL EXPORT
# ══════════════════════════════════════════════════════
h1, h2, h3 = st.columns([4,2,1])
with h1:
    st.markdown(f"<span style='font-size:20px;font-weight:700;color:#f0d050;font-family:Roboto Mono,monospace;'>◈ STIR TERMINAL &nbsp;|&nbsp; SR1·ZQ·SPREADS·FLIES &nbsp;|&nbsp; {year}</span>", unsafe_allow_html=True)
with h2:
    st.markdown(f"<span style='color:#888860;font-size:11px;font-family:Roboto Mono,monospace;'>SOFR {sofr_base*100:.2f}% &nbsp;|&nbsp; EFFR {effr_base*100:.2f}%</span>", unsafe_allow_html=True)
with h3:
    if sr1_res or zq_res:
        xl = build_excel(sr1_res, zq_res, st.session_state.sr1_cases, st.session_state.zq_cases, year, yr2, meeting_dates)
        st.download_button("⬇ EXPORT ALL → XLSX", data=xl, file_name=f"STIR_{year}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# SHARED RENDERER
# ══════════════════════════════════════════════════════
def render_product(pk, product, base_rate, results):
    cases = st.session_state[f"{pk}_cases"]
    st.markdown(f"<div class='bb-hdr'>◈ {product} — BASE: {base_rate*100:.2f}% | {len(cases)} CASES</div>", unsafe_allow_html=True)
    case_manager(pk)
    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
    if not results:
        st.warning("ADD AT LEAST ONE CASE.")
        return
    base_name = cases[0]["name"] if cases else ""
    base_p = results.get(base_name, {})
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("BASE RATE",           f"{base_rate*100:.2f}%")
    m2.metric(f"{product} JAN '{yr2}", f"{base_p.get('Jan',0):.4f}")
    m3.metric(f"{product} DEC '{yr2}", f"{base_p.get('Dec',0):.4f}")
    m4.metric("ACTIVE CASES",         str(len(cases)))
    if len(results) > 1:
        decs = [results[c["name"]]["Dec"] for c in cases if c["name"] in results]
        m5.metric("DEC RANGE (bp)", f"{(max(decs)-min(decs))*100:.2f}")
    st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

    t_chart, t_sp, t_fly, t_tbl = st.tabs(["PRICE CHART","CALENDAR SPREADS","BUTTERFLIES","FULL TABLE"])
    sp_df, fly_df, rate_df = compute_analytics(results, cases)

    # ── Price Table helper ──
    def make_price_table():
        pt = pd.DataFrame(
            {c["name"]: [results[c["name"]][m] for m in MONTHS]
             for c in cases if c["name"] in results}, index=MONTHS
        ).T
        pt.columns = [clbl(product, m) for m in MONTHS]
        pt.index.name = "CASE"
        return pt

    with t_chart:
        st.plotly_chart(build_price_chart(results, cases, product, meeting_dates, show_mkr,
                        f" | SOFR {sofr_base*100:.2f}%" if pk=="sr1" else f" | EFFR {effr_base*100:.2f}%"),
                        use_container_width=True)
        st.markdown("<div class='bb-hdr'>CONTRACT PRICES — ALL CASES</div>", unsafe_allow_html=True)
        pt = make_price_table()
        st.dataframe(pt.style.apply(hl_price, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(80+35*len(pt), 500))
        if show_diff and len(results) > 1 and base_name in pt.index:
            st.markdown(f"<div class='bb-hdr'>Δ VS '{base_name}' (bp)</div>", unsafe_allow_html=True)
            diff = (pt.subtract(pt.loc[base_name]) * 100).drop(index=base_name, errors="ignore").round(2)
            if not diff.empty:
                st.dataframe(diff.style.apply(hl_spread, axis=1).format("{:+.2f}"),
                             use_container_width=True, height=min(80+35*len(diff), 400))

    with t_sp:
        sp_disp = sp_df.copy()
        sp_disp.columns = [f"{product} {c}" for c in sp_disp.columns]
        st.plotly_chart(build_bar_chart(sp_disp, f"{product} CALENDAR SPREADS (FRONT − BACK, bp)"),
                        use_container_width=True)
        st.markdown("<div class='bb-hdr'>SPREAD TABLE (bp) — FRONT MINUS BACK</div>", unsafe_allow_html=True)
        st.markdown("""<div class='ibox'>
        CONVENTION: Front − Back &nbsp;|&nbsp;
        <span style='color:#f04a4a'>NEGATIVE = STEEPENING = CUTS PRICED</span> &nbsp;|&nbsp;
        <span style='color:#4af04a'>POSITIVE = FLAT / HIKES PRICED</span><br>
        Jun/Jul = SR1_Jun − SR1_Jul. If −25bp: one full 25bp cut priced between those months.
        Prob(cut) = |spread| / 25bp
        </div>""", unsafe_allow_html=True)
        st.dataframe(sp_disp.style.apply(hl_spread, axis=1).format("{:+.3f}"),
                     use_container_width=True)

    with t_fly:
        st.plotly_chart(build_bar_chart(fly_df, f"{product} BUTTERFLIES (−F + 2×B − K, bp)"),
                        use_container_width=True)
        st.markdown("<div class='bb-hdr'>FLY TABLE (bp)</div>", unsafe_allow_html=True)
        st.markdown("""<div class='ibox'>
        FLY = −Front + 2×Belly − Back &nbsp;|&nbsp;
        <span style='color:#4ac8f0'>POSITIVE: belly rich vs wings → SELL THE FLY</span> &nbsp;|&nbsp;
        <span style='color:#f0c84a'>NEGATIVE: belly cheap vs wings → BUY THE FLY</span><br>
        Best expression: fly centred on the meeting month where your view differs most from market.
        </div>""", unsafe_allow_html=True)
        st.dataframe(fly_df.style.apply(hl_fly, axis=1).format("{:+.3f}"),
                     use_container_width=True)

    with t_tbl:
        pt2 = make_price_table()
        st.markdown("<div class='bb-hdr'>PRICES</div>", unsafe_allow_html=True)
        st.dataframe(pt2.style.apply(hl_price, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(80+35*len(pt2), 600))
        rd = rate_df.copy(); rd.columns = [clbl(product, m) for m in MONTHS]; rd.index.name = "CASE"
        st.markdown("<div class='bb-hdr'>IMPLIED RATES (%)</div>", unsafe_allow_html=True)
        st.dataframe(rd.style.apply(hl_rate, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(80+35*len(rd), 500))
        st.download_button(f"⬇ {product} PRICES CSV", pt2.to_csv(), f"{pk}_{year}.csv", "text/csv")

# ══════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════
TAB_SR1, TAB_ZQ, TAB_SPD, TAB_IPC, TAB_GUIDE = st.tabs([
    "● SR1  SOFR", "● ZQ  EFFR", "▲ SPREADS & FLIES", "⇄ INTER-PRODUCT", "◉ TRADING GUIDE"
])

with TAB_SR1: render_product("sr1", "SR1", sofr_base, sr1_res)
with TAB_ZQ:  render_product("zq",  "ZQ",  effr_base, zq_res)

# ══════════════════════════════════════════════════════
# SPREADS & FLIES BUILDER
# ══════════════════════════════════════════════════════
with TAB_SPD:
    st.markdown("<div class='bb-hdr'>◈ SPREAD & FLY BUILDER</div>", unsafe_allow_html=True)
    col_cfg, col_res = st.columns([1,2])
    with col_cfg:
        prod_sel  = st.selectbox("PRODUCT", ["SR1","ZQ"], key="sp_prod")
        leg_type  = st.radio("STRUCTURE", ["2-LEG SPREAD","3-LEG BUTTERFLY","CUSTOM WEIGHTS"])
        res_sel   = sr1_res if prod_sel=="SR1" else zq_res
        cases_sel = st.session_state.sr1_cases if prod_sel=="SR1" else st.session_state.zq_cases
        if leg_type == "2-LEG SPREAD":
            l1 = st.selectbox("BUY LEG",  MONTHS, index=0, key="l1")
            l2 = st.selectbox("SELL LEG", MONTHS, index=1, key="l2")
            legs = [(l1,+1),(l2,-1)]; label = f"{prod_sel} {l1}-{l2}'{yr2} SPREAD"
        elif leg_type == "3-LEG BUTTERFLY":
            fr = st.selectbox("FRONT", MONTHS, index=0, key="fr")
            be = st.selectbox("BELLY", MONTHS, index=1, key="be")
            bk = st.selectbox("BACK",  MONTHS, index=2, key="bk")
            legs = [(fr,-1),(be,+2),(bk,-1)]; label = f"{prod_sel} {fr}/{be}/{bk}'{yr2} FLY"
        else:
            legs = []
            for mi, mo in enumerate(MONTHS):
                w = st.number_input(f"{prod_sel} {mo}", value=0, step=1, key=f"cw_{mi}", format="%d")
                if w != 0: legs.append((mo, w))
            label = f"{prod_sel} CUSTOM'{yr2}"
    with col_res:
        if res_sel and legs and cases_sel:
            sv = {c["name"]: round(sum(res_sel[c["name"]][mo]*w for mo,w in legs if c["name"] in res_sel)*100,3)
                  for c in cases_sel if c["name"] in res_sel}
            fig_sp = go.Figure(go.Bar(x=list(sv.keys()), y=list(sv.values()),
                                      marker_color=[COLORS[i%len(COLORS)] for i in range(len(sv))],
                                      hovertemplate="<b>%{x}</b><br>%{y:+.3f} bp<extra></extra>"))
            layout = {**BB_LAYOUT, "title": label, "yaxis_title": "bp",
                      "height": 320, "margin": dict(l=60,r=20,t=50,b=100)}
            fig_sp.update_layout(**layout)
            fig_sp.update_yaxes(zeroline=True, zerolinecolor="#555530")
            fig_sp.update_xaxes(tickangle=-35)
            st.plotly_chart(fig_sp, use_container_width=True)
            sv_df = pd.DataFrame.from_dict(sv, orient="index", columns=[f"{label} (bp)"])
            sv_df.index.name = "CASE"
            base_v = sv_df.iloc[0,0] if not sv_df.empty else 0
            sv_df["Δ vs Base (bp)"] = (sv_df.iloc[:,0] - base_v).round(3)
            st.dataframe(sv_df.style.apply(hl_spread).format("{:+.3f}"), use_container_width=True)

    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-hdr'>FULL MATRIX</div>", unsafe_allow_html=True)
    mat_prod  = st.selectbox("PRODUCT FOR MATRIX", ["SR1","ZQ"], key="mat_p")
    mat_res   = sr1_res if mat_prod=="SR1" else zq_res
    mat_cases = st.session_state.sr1_cases if mat_prod=="SR1" else st.session_state.zq_cases
    if mat_res and mat_cases:
        sp2, fly2, _ = compute_analytics(mat_res, mat_cases)
        sp2.columns = [f"{mat_prod} {c}" for c in sp2.columns]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='bb-hdr'>SPREADS (bp)</div>", unsafe_allow_html=True)
            st.dataframe(sp2.style.apply(hl_spread, axis=1).format("{:+.3f}"), use_container_width=True)
        with c2:
            st.markdown("<div class='bb-hdr'>FLIES (bp)</div>", unsafe_allow_html=True)
            st.dataframe(fly2.style.apply(hl_fly, axis=1).format("{:+.3f}"), use_container_width=True)

# ══════════════════════════════════════════════════════
# INTER-PRODUCT
# ══════════════════════════════════════════════════════
with TAB_IPC:
    st.markdown("<div class='bb-hdr'>◈ INTER-PRODUCT: SR1 vs ZQ BASIS (SOFR − EFFR)</div>", unsafe_allow_html=True)
    st.markdown("""<div class='ibox'>BASIS = SR1 PRICE − ZQ PRICE (same month) | NORMAL: +2 to +8bp |
    WIDENS at QE/YE → BUY BASIS (buy SR1, sell ZQ) | INVERTS in stress → SELL BASIS</div>""", unsafe_allow_html=True)
    c1, c2 = st.columns([1,3])
    with c1:
        sr1_n = [c["name"] for c in st.session_state.sr1_cases]
        zq_n  = [c["name"] for c in st.session_state.zq_cases]
        sel_s = st.selectbox("SR1 CASE", sr1_n, index=0, key="ip_s") if sr1_n else None
        sel_z = st.selectbox("ZQ CASE",  zq_n,  index=0, key="ip_z") if zq_n  else None
        overlay = st.checkbox("OVERLAY CURVES", value=True)
    with c2:
        if sel_s and sel_z and sel_s in sr1_res and sel_z in zq_res:
            sp = [sr1_res[sel_s][m] for m in MONTHS]
            zp = [zq_res[sel_z][m]  for m in MONTHS]
            basis = [round((s-z)*100,3) for s,z in zip(sp,zp)]
            fig_ip = go.Figure()
            if overlay:
                fig_ip.add_trace(go.Scatter(x=[clbl("SR1",m) for m in MONTHS], y=sp, name=f"SR1: {sel_s}",
                    line=dict(color="#f0d050",width=2), marker=dict(size=5), yaxis="y1",
                    hovertemplate="SR1 %{x}: %{y:.4f}<extra></extra>"))
                fig_ip.add_trace(go.Scatter(x=[clbl("ZQ",m) for m in MONTHS], y=zp, name=f"ZQ:  {sel_z}",
                    line=dict(color="#4af04a",width=2,dash="dash"), marker=dict(size=5), yaxis="y1",
                    hovertemplate="ZQ %{x}: %{y:.4f}<extra></extra>"))
            fig_ip.add_trace(go.Bar(x=MONTHS, y=basis, name="Basis (bp)",
                marker_color=["#4af04a" if v>=0 else "#f04a4a" for v in basis],
                yaxis="y2", opacity=0.8, hovertemplate="%{x} BASIS: %{y:+.2f} bp<extra></extra>"))
            layout = {**BB_LAYOUT, "title": f"SR1 vs ZQ | {sel_s} / {sel_z}", "height": 400,
                      "barmode": "overlay",
                      "yaxis2": dict(title="Basis(bp)", overlaying="y", side="right",
                                     zeroline=True, zerolinecolor="#555530", showgrid=False,
                                     tickfont=dict(size=10, color="#888860"))}
            fig_ip.update_layout(**layout)
            st.plotly_chart(fig_ip, use_container_width=True)
            bdf = pd.DataFrame({"CONTRACT":[clbl("SR1",m) for m in MONTHS],
                                f"SR1":[f"{v:.4f}" for v in sp],
                                f"ZQ": [f"{v:.4f}" for v in zp],
                                "BASIS(bp)":[f"{v:+.2f}" for v in basis]}).set_index("CONTRACT")
            st.dataframe(bdf, use_container_width=True)

    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='bb-hdr'>ALL-CASE BASIS TABLE</div>", unsafe_allow_html=True)
    bmo = st.selectbox("MONTH", MONTHS, index=8, key="bm")
    rows_b = [{"SR1 CASE":sc["name"],"ZQ CASE":zc["name"],
               f"BASIS {bmo} (bp)":round((sr1_res[sc["name"]][bmo]-zq_res[zc["name"]][bmo])*100,3)}
              for sc in st.session_state.sr1_cases for zc in st.session_state.zq_cases
              if sc["name"] in sr1_res and zc["name"] in zq_res]
    if rows_b:
        bdf2 = pd.DataFrame(rows_b); col = f"BASIS {bmo} (bp)"
        st.dataframe(bdf2.style.apply(
            lambda s: ["background:#0a2a0a;color:#4af04a" if v>0 else "background:#2a0a0a;color:#f04a4a" for v in s]
            if s.name==col else [""]*len(s), axis=0).format({col:"{:+.3f}"}), use_container_width=True)

# ══════════════════════════════════════════════════════
# TRADING GUIDE
# ══════════════════════════════════════════════════════
with TAB_GUIDE:
    st.markdown("<div class='bb-hdr'>◈ STIR TRADING GUIDE & PRO DASHBOARD SUGGESTIONS</div>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("""
### ● SR1 — 1-Month SOFR Futures
`Price = 100 − avg daily SOFR for delivery month`
- **DV01 = $41.67/bp** per contract ($5M notional × 30/360 / 12)
- Tracks Fed target almost exactly (SOFR ≈ FF upper bound −1 to −2bp)
- Each contract = one calendar month Jan–Dec
- First contract fully at new rate = month containing the **effective date** (day after meeting)

### ● ZQ — 30-Day Fed Funds Futures
`Price = 100 − avg daily EFFR for delivery month`
- **DV01 = $41.67/bp** (same as SR1)
- EFFR historically **5–8bp below** FF upper bound → lower than SOFR
- More sensitive to **year-end** window dressing (ZQ Dec richens)
- Older/more liquid; widely used by macro funds and for hedging FF risk
        """)

    with g2:
        st.markdown("""
### ▲ Calendar Spreads (FRONT − BACK)
`Jun/Jul spread = SR1_Jun − SR1_Jul`

| Value | Meaning |
|---|---|
| **−25 bp** | One 25bp cut fully priced Jun→Jul |
| **−12.5 bp** | 50% prob of a 25bp cut |
| **0 bp** | No cut priced (flat curve) |
| **+25 bp** | Hike priced |

**Prob(cut between two meetings) = |spread| / 25bp**

### 🦋 Butterflies
`Fly = −Front + 2×Belly − Back`

| Value | Trade |
|---|---|
| **Positive** | Belly rich vs wings → **SELL the fly** |
| **Negative** | Belly cheap vs wings → **BUY the fly** |

Express *when* cuts happen (not just how many) using flies.
        """)

    st.markdown("---")
    st.markdown("""
### 🔴 PRO TRADER RECOMMENDATIONS FOR THIS DASHBOARD

**① ADD CUT PROBABILITY TABLE** (highest priority)
Convert every spread to implied probability: `Prob = |spread_bp| / 25`.
This is what every STIR trader looks at first — it's more intuitive than raw prices.

**② ADD P&L SCENARIO MATRIX**
Given a position you enter (e.g. *long 100 SR1 Sep, short 100 SR1 Aug*), auto-calculate
P&L in bp and USD across all your cases. This makes the tool directly usable for risk management.

**③ ADD MARKET PRICE INPUT**
Enter current CME screen prices for each contract. The dashboard then shows
`Your Scenario − Market Price` = your edge / dislocation per month.
This is the core signal for finding trades.

**④ CARRY TABLE**
For each spread, show daily carry in bp/day. A long Sep/Oct spread earns carry
if Sep > Oct (inverted curve). Critical for sizing and hold-time decisions.

**⑤ MEETING IMPACT BREAKDOWN**
Show what fraction (in bp) of each contract's price comes from each meeting.
e.g. SR1 Sep: "3.2bp from Jul 29 meeting (partial month), 21.8bp from Sep 16 meeting".

**⑥ QUICK TRADE TICKET**
After building your scenario, generate:
*"VIEW: 3 cuts (Jun+Sep+Dec) vs MARKET: 2 cuts → TRADE: BUY SR1 Dec, SELL SR1 Nov @ -25bp.
Target: -50bp. Stop: -12.5bp. DV01: $41.67/bp/lot"*
    """)

    st.markdown("""<div class='warn'>
MEETING → CONTRACT MAP 2026 (EFFECTIVE DATE = DAY AFTER MEETING)<br>
Jan 28 → eff Jan 29 (partial Jan, full Feb+) | Mar 18 → eff Mar 19 (partial Mar, full Apr+)<br>
Apr 29 → eff Apr 30 (partial Apr, full May+) | Jun 17 → eff Jun 18 (partial Jun, full Jul+)<br>
Jul 29 → eff Jul 30 (partial Jul, full Aug+) | Sep 16 → eff Sep 17 (partial Sep, full Oct+)<br>
Oct 28 → eff Oct 29 (partial Oct, full Nov+) | Dec 9  → eff Dec 10 (partial Dec, full Jan27+)<br>
RULE: contract spanning the meeting date prices a PARTIAL cut weighted by days-after/days-in-month
</div>""", unsafe_allow_html=True)

st.markdown(
    f"<div style='font-size:10px;color:#444430;font-family:Roboto Mono,monospace;margin-top:6px;'>"
    f"STIR TERMINAL v2.1 | SR1 SOFR {sofr_base*100:.2f}% | ZQ EFFR {effr_base*100:.2f}% | "
    f"ME {sofr_me*10000:.1f}bp | YE(ZQ) {effr_ye*10000:.1f}bp | {year} | SPREADS: FRONT-BACK CONVENTION"
    f"</div>", unsafe_allow_html=True)
