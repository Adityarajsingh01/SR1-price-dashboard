"""
STIR TERMINAL v3 — SR1 (SOFR) · ZQ (EFFR) · Spreads · Flies · Inter-Product
Bloomberg Professional terminal replica for US STIR scenario analysis
CME-accurate butterfly convention: BUY FLY = +Front - 2×Belly + Back
Run:  streamlit run stir_dashboard.py
Deps: pip install streamlit plotly pandas openpyxl xlsxwriter
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import calendar, json, io

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="STIR TERMINAL",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# BLOOMBERG CSS — TRUE TERMINAL REPLICA
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500;700&display=swap');

/* ── Root ── */
*, html, body { box-sizing: border-box; }
html, body, [class*="css"], .main {
    background-color: #000000 !important;
    color: #ff8c00 !important;
    font-family: 'Roboto Mono', 'Courier New', monospace !important;
    font-size: 12px !important;
}
.main .block-container { padding: 0.2rem 0.6rem 1rem 0.6rem; max-width: 100%; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #000000 !important;
    border-right: 1px solid #333300 !important;
    min-width: 200px !important;
}
[data-testid="stSidebar"] * { color: #ff8c00 !important; font-size: 11px !important; font-family: 'Roboto Mono', monospace !important; }
[data-testid="stSidebar"] input {
    background: #0a0a00 !important; color: #ffff00 !important;
    border: 1px solid #444400 !important; font-family: 'Roboto Mono', monospace !important;
    font-size: 11px !important;
}
[data-testid="stSidebar"] label { color: #888800 !important; font-size: 10px !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stSidebar"] .stMarkdown p { color: #ff8c00 !important; font-size: 10px !important; }

/* ── Metrics ── */
div[data-testid="metric-container"] {
    background: #000000 !important;
    border: 1px solid #333300 !important;
    border-top: 2px solid #ff8c00 !important;
    border-radius: 0 !important;
    padding: 6px 12px !important;
    margin: 1px !important;
}
div[data-testid="metric-container"] label {
    color: #666600 !important; font-size: 9px !important;
    letter-spacing: 1.5px; text-transform: uppercase; font-family: 'Roboto Mono', monospace !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #ffff00 !important; font-size: 20px !important; font-weight: 700;
    font-family: 'Roboto Mono', monospace !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 11px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #000000 !important;
    border-bottom: 2px solid #ff8c00 !important;
    gap: 0 !important; padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: #000000 !important;
    color: #555500 !important;
    font-size: 11px !important; font-weight: 700 !important;
    font-family: 'Roboto Mono', monospace !important;
    padding: 6px 16px !important; border-radius: 0 !important;
    border-right: 1px solid #222200 !important;
    border-top: 2px solid transparent !important;
    letter-spacing: 0.8px; text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    background: #0a0800 !important;
    color: #ffff00 !important;
    border-top: 2px solid #ffff00 !important;
    border-bottom: 2px solid #0a0800 !important;
}
.stTabs [aria-selected="false"]:hover { color: #ff8c00 !important; }

/* ── Buttons ── */
.stButton > button {
    background: #000000 !important; color: #ff8c00 !important;
    border: 1px solid #444400 !important; border-radius: 0 !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 10px !important;
    font-weight: 700 !important; letter-spacing: 0.8px !important;
    padding: 5px 10px !important; text-transform: uppercase;
}
.stButton > button:hover { background: #1a1400 !important; color: #ffff00 !important; border-color: #ffff00 !important; }

/* ── Download buttons ── */
.stDownloadButton > button {
    background: #001a00 !important; color: #00ff00 !important;
    border: 1px solid #004400 !important; border-radius: 0 !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 10px !important; font-weight: 700 !important;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.stDownloadButton > button:hover { background: #002a00 !important; border-color: #00ff00 !important; }

/* ── Inputs ── */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #0a0800 !important; color: #ff8c00 !important;
    border: 1px solid #333300 !important; border-radius: 0 !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 11px !important;
}
.stNumberInput input {
    background: #0a0800 !important; color: #ffff00 !important;
    border: 1px solid #333300 !important; border-radius: 0 !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 11px !important;
}
.stTextInput input {
    background: #0a0800 !important; color: #ffff00 !important;
    border: 1px solid #333300 !important; border-radius: 0 !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 11px !important;
}
.stRadio label, .stCheckbox label {
    color: #ff8c00 !important; font-size: 11px !important;
    font-family: 'Roboto Mono', monospace !important;
}

/* ── Expanders ── */
details {
    background: #000000 !important;
    border: 1px solid #333300 !important; border-radius: 0 !important;
    margin: 2px 0 !important;
}
details summary {
    color: #ff8c00 !important; font-size: 11px !important; font-weight: 700 !important;
    padding: 5px 10px !important; background: #050400 !important;
    font-family: 'Roboto Mono', monospace !important; text-transform: uppercase;
}
details[open] summary { color: #ffff00 !important; border-bottom: 1px solid #333300 !important; }

/* ── Dividers ── */
hr { border: 0 !important; border-top: 1px solid #222200 !important; margin: 3px 0 !important; }

/* ── DataFrames ── */
.stDataFrame { background: #000000 !important; }
.stDataFrame iframe { background: #000000 !important; }

/* ── Alerts ── */
.stAlert { background: #050400 !important; border-left: 3px solid #ff8c00 !important; }

/* ── Color picker ── */
.stColorPicker { background: #000000 !important; }

/* ── Custom classes ── */
.bb-bar {
    background: #000000; border-bottom: 2px solid #ff8c00;
    padding: 3px 8px; margin-bottom: 4px; display: flex; align-items: center;
    font-family: 'Roboto Mono', monospace; gap: 16px;
}
.bb-fn { color: #ffff00; font-size: 10px; font-weight: 700; padding: 2px 6px;
          border: 1px solid #ff8c00; cursor: pointer; letter-spacing: 0.5px; }
.bb-hdr {
    font-size: 11px; font-weight: 700; color: #ffff00;
    letter-spacing: 1.5px; text-transform: uppercase;
    border-bottom: 1px solid #333300; padding: 2px 0 2px 4px; margin: 6px 0 4px 0;
    font-family: 'Roboto Mono', monospace; background: #030200;
}
.bb-price { color: #ffff00; font-weight: 700; }
.bb-green { color: #00ff00; font-weight: 700; }
.bb-red   { color: #ff3333; font-weight: 700; }
.bb-cyan  { color: #00ffff; font-weight: 700; }
.bb-white { color: #ffffff; font-weight: 700; }
.bb-dim   { color: #666600; }

.bb-box-green { background:#001a00; border-left:3px solid #00aa00; padding:6px 12px;
                font-size:11px; color:#88ee88; font-family:monospace; margin:3px 0; }
.bb-box-amber { background:#1a0e00; border-left:3px solid #ff8c00; padding:6px 12px;
                font-size:11px; color:#ffcc88; font-family:monospace; margin:3px 0; }
.bb-box-blue  { background:#000a1a; border-left:3px solid #0088ff; padding:6px 12px;
                font-size:11px; color:#88bbff; font-family:monospace; margin:3px 0; }
.bb-box-red   { background:#1a0000; border-left:3px solid #ff3333; padding:6px 12px;
                font-size:11px; color:#ff9999; font-family:monospace; margin:3px 0; }
.bb-ticker {
    background:#000000; border:1px solid #333300; padding:4px 10px;
    font-family:'Roboto Mono',monospace; font-size:11px; display:inline-block;
    margin:2px; vertical-align:middle;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
MONTHS     = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONTH_FULL = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

# Bloomberg-accurate STIR color palette
COLORS = [
    "#ff8c00","#00ff00","#00ffff","#ff3333","#cc44ff",
    "#ffff00","#00cc88","#ff6688","#44aaff","#ff9944",
    "#88ff44","#ff44cc","#44ffff","#ffaa44","#4488ff",
    "#ff4444","#44ff88","#cc88ff","#ffcc00","#00ffcc",
    "#ff88aa","#88ffcc","#ccff44","#ff44aa","#44ccff",
    "#ffcc44","#44ff44","#cc44aa","#44ccaa","#aaff44",
]

DEFAULT_MEETINGS = [
    date(2026,1,28), date(2026,3,18), date(2026,4,29), date(2026,6,17),
    date(2026,7,29), date(2026,9,16), date(2026,10,28), date(2026,12,9),
]

PRESETS = {
    "No Change":                    [ 0,   0,   0,   0,   0,   0,   0,   0],
    "1 Cut -25 Jan":                [-25,  0,   0,   0,   0,   0,   0,   0],
    "1 Cut -25 Mar":                [ 0, -25,   0,   0,   0,   0,   0,   0],
    "1 Cut -25 Apr":                [ 0,   0, -25,   0,   0,   0,   0,   0],
    "1 Cut -25 Jun":                [ 0,   0,   0, -25,   0,   0,   0,   0],
    "1 Cut -25 Jul":                [ 0,   0,   0,   0, -25,   0,   0,   0],
    "1 Cut -25 Sep":                [ 0,   0,   0,   0,   0, -25,   0,   0],
    "1 Cut -25 Oct":                [ 0,   0,   0,   0,   0,   0, -25,   0],
    "1 Cut -25 Dec":                [ 0,   0,   0,   0,   0,   0,   0, -25],
    "2 Cuts (Jun+Sep)":             [ 0,   0,   0, -25,   0, -25,   0,   0],
    "2 Cuts (Sep+Dec)":             [ 0,   0,   0,   0,   0, -25,   0, -25],
    "3 Cuts (Jun+Sep+Dec)":         [ 0,   0,   0, -25,   0, -25,   0, -25],
    "4 Cuts (Mar+Jun+Sep+Dec)":     [ 0, -25,   0, -25,   0, -25,   0, -25],
    "5 Cuts (Jan+Mar+Jun+Sep+Dec)": [-25,-25,   0, -25,   0, -25,   0, -25],
    "Hike +25 Mar":                 [ 0,  25,   0,   0,   0,   0,   0,   0],
    "2 Hikes (Mar+Jun)":            [ 0,  25,   0,  25,   0,   0,   0,   0],
    "Aggressive -50 Sep":           [ 0,   0,   0,   0,   0, -50,   0,   0],
    "Custom":                       [ 0,   0,   0,   0,   0,   0,   0,   0],
}
PRESET_NAMES = list(PRESETS.keys())

# Bloomberg chart theme
BB_CHART = dict(
    plot_bgcolor  = "#000000",
    paper_bgcolor = "#000000",
    font = dict(color="#ff8c00", size=11, family="Roboto Mono, Courier New, monospace"),
    xaxis = dict(
        gridcolor="#111100", showgrid=True, zeroline=False,
        tickfont=dict(size=10, color="#ff8c00", family="Roboto Mono, monospace"),
        linecolor="#333300", showline=True, tickangle=-40,
        title_font=dict(size=10, color="#888800"),
    ),
    yaxis = dict(
        gridcolor="#111100", showgrid=True, zeroline=False,
        tickfont=dict(size=10, color="#ff8c00", family="Roboto Mono, monospace"),
        linecolor="#333300", showline=True,
        title_font=dict(size=10, color="#888800"),
    ),
    legend = dict(
        bgcolor="rgba(0,0,0,0.95)", bordercolor="#333300", borderwidth=1,
        font=dict(size=10, color="#ff8c00", family="Roboto Mono, monospace"),
        x=1.01, y=1,
    ),
    hoverlabel = dict(
        bgcolor="#0a0800", bordercolor="#ff8c00",
        font=dict(size=11, color="#ffff00", family="Roboto Mono, monospace"),
        namelength=-1,
    ),
    hovermode = "x unified",
    margin     = dict(l=65, r=200, t=45, b=75),
)

# ══════════════════════════════════════════════════════════════════
# PRICING ENGINE
# ══════════════════════════════════════════════════════════════════
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
            if d >= eff: r = val
        return r

    prices = {}
    for mo_idx in range(1, 13):
        n_days   = calendar.monthrange(year, mo_idx)[1]
        last_biz = get_last_biz_day(year, mo_idx)
        me_days  = set()
        d = last_biz
        while d.month == mo_idx:
            me_days.add(d); d += timedelta(days=1)
        prev_mo  = mo_idx - 1 or 12
        prev_yr  = year if mo_idx > 1 else year - 1
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
        prices[MONTHS[mo_idx-1]] = round(100.0 - (total / n_days) * 100.0, 6)
    return prices

# ══════════════════════════════════════════════════════════════════
# ANALYTICS — CME-ACCURATE CONVENTIONS
# ══════════════════════════════════════════════════════════════════
def compute_analytics(results, cases):
    """
    CALENDAR SPREAD: Front − Back  (STIR market convention)
        Jun/Jul = SR1_Jun − SR1_Jul
        Negative = cuts priced (back month higher → lower rate)
        Positive = flat/hikes priced

    BUTTERFLY: +Front − 2×Belly + Back  (CME BUY-fly convention)
        Source: CME Globex Strategy Guide — "Buying a butterfly buys leg1, sells 2*leg2, buys leg3"
        Positive = belly low price (high rate at belly) → belly cheap → BUY the fly
        Negative = belly high price (low rate at belly) → belly rich → SELL the fly
    """
    sp_labels  = [f"{MONTHS[i]}/{MONTHS[i+1]}" for i in range(11)]
    fly_labels = [f"{MONTHS[i-1]}/{MONTHS[i]}/{MONTHS[i+1]}" for i in range(1, 11)]
    sp_data, fly_data, rate_data = {}, {}, {}
    for case in cases:
        nm = case["name"]
        if nm not in results: continue
        p = [results[nm][m] for m in MONTHS]
        # Calendar spread: FRONT minus BACK
        sp_data[nm]   = [round((p[i] - p[i+1]) * 100, 3) for i in range(11)]
        # Butterfly: +Front - 2×Belly + Back  (CME BUY fly)
        fly_data[nm]  = [round((p[i-1] - 2*p[i] + p[i+1]) * 100, 3) for i in range(1, 11)]
        rate_data[nm] = [round(100 - v, 4) for v in p]
    return (
        pd.DataFrame(sp_data,  index=sp_labels).T,
        pd.DataFrame(fly_data, index=fly_labels).T,
        pd.DataFrame(rate_data, index=MONTHS).T,
    )

def compute_probabilities(sp_df):
    """Convert calendar spreads to FOMC cut probabilities."""
    # Prob(cut) = -spread / 25  (negative spread = cuts priced, positive prob)
    return (-sp_df / 25.0 * 100).round(1)

# ══════════════════════════════════════════════════════════════════
# EXCEL EXPORT
# ══════════════════════════════════════════════════════════════════
def build_excel(sr1_res, zq_res, sr1_cases, zq_cases, year, yr2, meeting_dates):
    buf = io.BytesIO()
    mtg_lbl = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        def write_product(results, cases, prod):
            if not results or not cases: return
            px, sp, fly, rt, pb = [], [], [], [], []
            for c in cases:
                nm = c["name"]
                if nm not in results: continue
                p  = results[nm]; pl = [p[m] for m in MONTHS]
                px.append({**{"Case":nm},  **{f"{prod} {m}'{yr2}":p[m] for m in MONTHS}})
                spr = {f"{MONTHS[i]}/{MONTHS[i+1]}":round((pl[i]-pl[i+1])*100,3) for i in range(11)}
                sp.append({**{"Case":nm}, **spr})
                prb = {k: round(-v/25*100,1) for k,v in spr.items()}
                pb.append({**{"Case":nm}, **prb})
                fly.append({**{"Case":nm},
                             **{f"{MONTHS[i-1]}/{MONTHS[i]}/{MONTHS[i+1]}":
                                round((pl[i-1]-2*pl[i]+pl[i+1])*100,3) for i in range(1,11)}})
                rt.append({**{"Case":nm}, **{f"{prod} {m}'{yr2}":round(100-p[m],4) for m in MONTHS}})
            pd.DataFrame(px).set_index("Case").to_excel(w, sheet_name=f"{prod} Prices")
            pd.DataFrame(sp).set_index("Case").to_excel(w, sheet_name=f"{prod} Spreads(bp)")
            pd.DataFrame(pb).set_index("Case").to_excel(w, sheet_name=f"{prod} Cut Probs(%)")
            pd.DataFrame(fly).set_index("Case").to_excel(w, sheet_name=f"{prod} Flies(bp)")
            pd.DataFrame(rt).set_index("Case").to_excel(w, sheet_name=f"{prod} Impl Rates")

        write_product(sr1_res, sr1_cases, "SR1")
        write_product(zq_res,  zq_cases,  "ZQ")

        if sr1_res and zq_res:
            rows = []
            for sc in sr1_cases:
                for zc in zq_cases:
                    if sc["name"] in sr1_res and zc["name"] in zq_res:
                        row = {"SR1 Case":sc["name"], "ZQ Case":zc["name"]}
                        for m in MONTHS:
                            row[f"Basis {m}(bp)"] = round(
                                (sr1_res[sc["name"]][m]-zq_res[zc["name"]][m])*100, 3)
                        rows.append(row)
            if rows: pd.DataFrame(rows).to_excel(w, sheet_name="SR1-ZQ Basis(bp)", index=False)

        cfg = []
        for c in sr1_cases:
            r = {"Product":"SR1","Case":c["name"]}
            for i,l in enumerate(mtg_lbl): r[l]=c["changes"][i]
            cfg.append(r)
        for c in zq_cases:
            r = {"Product":"ZQ","Case":c["name"]}
            for i,l in enumerate(mtg_lbl): r[l]=c["changes"][i]
            cfg.append(r)
        pd.DataFrame(cfg).to_excel(w, sheet_name="Case Config", index=False)

    buf.seek(0); return buf.getvalue()

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
def _defaults():
    return [
        {"name":"No Change",  "changes":[0]*8,              "color":COLORS[0]},
        {"name":"2C Jun+Sep", "changes":[0,0,0,-25,0,-25,0,0], "color":COLORS[1]},
    ]

for k in ["sr1_cases","zq_cases"]:
    if k not in st.session_state: st.session_state[k] = _defaults()
if "meeting_dates" not in st.session_state:
    st.session_state.meeting_dates = DEFAULT_MEETINGS[:]
if "mkt_prices_sr1" not in st.session_state:
    st.session_state.mkt_prices_sr1 = {m: 0.0 for m in MONTHS}
if "mkt_prices_zq" not in st.session_state:
    st.session_state.mkt_prices_zq  = {m: 0.0 for m in MONTHS}

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div style='color:#ffff00;font-size:13px;font-weight:700;letter-spacing:2px;border-bottom:1px solid #ff8c00;padding-bottom:4px;'>◈ STIR TERMINAL</div>", unsafe_allow_html=True)
    year = int(st.number_input("YEAR", value=2026, step=1, min_value=2020, max_value=2035))
    yr2  = str(year)[2:]

    st.markdown("<div style='color:#888800;font-size:9px;letter-spacing:1px;margin-top:6px;'>FOMC MEETING DATES</div>", unsafe_allow_html=True)
    meeting_dates = []
    for i, dfl in enumerate(st.session_state.meeting_dates):
        meeting_dates.append(st.date_input(f"MTG {i+1}", value=dfl, key=f"mtg_{i}"))
    if st.button("↺ RESET 2026"):
        st.session_state.meeting_dates = DEFAULT_MEETINGS[:]
        st.rerun()
    st.markdown("---")

    st.markdown("<div style='color:#888800;font-size:9px;letter-spacing:1px;'>SR1  ONE-MONTH SOFR</div>", unsafe_allow_html=True)
    sofr_base = st.number_input("Base SOFR %", value=4.25, step=0.25, format="%.2f",
                                 min_value=0.0, max_value=15.0, key="sb") / 100
    sofr_me = st.number_input("ME adj bp",  value=1.0, step=0.5, format="%.1f", key="sm") / 10000
    sofr_qe = st.number_input("QE adj bp",  value=0.0, step=0.5, format="%.1f", key="sq") / 10000
    sofr_ye = st.number_input("YE adj bp",  value=0.0, step=0.5, format="%.1f", key="sy") / 10000

    st.markdown("<div style='color:#888800;font-size:9px;letter-spacing:1px;margin-top:6px;'>ZQ  30-DAY FED FUNDS</div>", unsafe_allow_html=True)
    effr_base = st.number_input("Base EFFR %", value=4.33, step=0.25, format="%.2f",
                                 min_value=0.0, max_value=15.0, key="eb") / 100
    effr_me = st.number_input("ME adj bp",  value=0.0, step=0.5, format="%.1f", key="em") / 10000
    effr_qe = st.number_input("QE adj bp",  value=0.0, step=0.5, format="%.1f", key="eq") / 10000
    effr_ye = st.number_input("YE adj bp",  value=8.0, step=0.5, format="%.1f", key="ey") / 10000

    st.markdown("---")
    show_mkr  = st.checkbox("FOMC MARKERS",   value=True)
    show_diff = st.checkbox("SHOW Δ VS BASE", value=True)

mtg_labels = [f"M{i+1} {d.strftime('%b %d')}" for i, d in enumerate(meeting_dates)]

# ══════════════════════════════════════════════════════════════════
# STYLING HELPERS
# ══════════════════════════════════════════════════════════════════
def hl_price(s):
    return ["background:#001a00;color:#00ff00;font-weight:bold" if v==s.max()
            else "background:#1a0000;color:#ff3333;font-weight:bold" if v==s.min()
            else "color:#ff8c00" for v in s]

def hl_spread(s):
    # Negative spread = cuts priced = highlight red (rates falling)
    # Positive spread = flat/hike = highlight green
    return ["background:#1a0000;color:#ff4444;font-weight:bold" if v < -0.5
            else "background:#001a00;color:#00ff00;font-weight:bold" if v > 0.5
            else "color:#888800" for v in s]

def hl_fly(s):
    # Positive = belly cheap (buy the fly) = cyan/blue
    # Negative = belly rich (sell the fly) = amber
    return ["background:#001a1a;color:#00ffff;font-weight:bold" if v > 0.5
            else "background:#1a0e00;color:#ff8c00;font-weight:bold" if v < -0.5
            else "color:#666600" for v in s]

def hl_prob(s):
    # High probability = red (market pricing in cuts aggressively)
    return ["background:#2a0000;color:#ff4444;font-weight:bold" if v > 75
            else "background:#1a0800;color:#ff8c44;font-weight:bold" if v > 40
            else "background:#001a00;color:#44ff44;font-weight:bold" if v < -10
            else "color:#888800" for v in s]

def hl_rate(s):
    return ["background:#1a0000;color:#ff4444;font-weight:bold" if v==s.max()
            else "background:#001a00;color:#00ff00;font-weight:bold" if v==s.min()
            else "color:#ff8c00" for v in s]

def hl_diff(s):
    return ["background:#001a00;color:#00ff00;font-weight:bold" if v > 0.5
            else "background:#1a0000;color:#ff4444;font-weight:bold" if v < -0.5
            else "color:#888800" for v in s]

def hl_pnl(s):
    return ["background:#001a00;color:#00ff00;font-weight:bold" if v > 0
            else "background:#1a0000;color:#ff4444;font-weight:bold" if v < 0
            else "color:#888800" for v in s]

# ══════════════════════════════════════════════════════════════════
# CHART HELPERS
# ══════════════════════════════════════════════════════════════════
def clbl(prod, mo): return f"{prod} {mo}'{yr2}"

def price_chart(results, cases, product, meeting_dates, show_mkr, sub=""):
    fig = go.Figure()
    xlabels = [clbl(product, m) for m in MONTHS]
    for case in cases:
        nm = case["name"]
        if nm not in results: continue
        fig.add_trace(go.Scatter(
            x=xlabels, y=[results[nm][m] for m in MONTHS],
            mode="lines+markers", name=nm,
            line=dict(color=case["color"], width=2),
            marker=dict(size=5, symbol="circle"),
            hovertemplate=f"<b style='color:{case['color']}'>{nm}</b><br>%{{x}}: <b>%{{y:.4f}}</b><extra></extra>",
        ))
    if show_mkr:
        for d in meeting_dates:
            xl = clbl(product, MONTHS[d.month-1])
            fig.add_shape(type="line", x0=xl, x1=xl, y0=0, y1=1,
                          xref="x", yref="paper",
                          line=dict(color="rgba(255,255,0,0.35)", width=1, dash="dot"))
            fig.add_annotation(x=xl, y=1.05, xref="x", yref="paper",
                               text=d.strftime("%b%d"), showarrow=False,
                               font=dict(size=9, color="#ffff00", family="Roboto Mono"),
                               xanchor="center", yanchor="bottom")
    layout = {**BB_CHART,
              "title": f"{product} PRICE CURVE — {year} | {sub}",
              "xaxis_title": "CONTRACT",
              "yaxis_title": "PRICE",
              "height": 380}
    fig.update_layout(**layout)
    return fig

def bar_chart(df, title, unit="bp", height=330):
    fig = go.Figure()
    for i, (idx, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Bar(
            name=idx, x=list(row.index), y=list(row.values),
            marker_color=COLORS[i % len(COLORS)],
            hovertemplate=f"<b>{idx}</b><br>%{{x}}: %{{y:+.3f}} {unit}<extra></extra>",
        ))
    layout = {**BB_CHART, "title": title, "yaxis_title": unit,
              "barmode": "group", "height": height,
              "margin": dict(l=60, r=20, t=40, b=75)}
    fig.update_layout(**layout)
    fig.update_yaxes(zeroline=True, zerolinecolor="#333300", zerolinewidth=1.5)
    return fig

# ══════════════════════════════════════════════════════════════════
# CASE EDITOR
# ══════════════════════════════════════════════════════════════════
def case_manager(pk):
    cases = st.session_state[f"{pk}_cases"]
    c1, c2, c3, c4 = st.columns([1,1,1,1])
    with c1:
        if st.button("+ ADD", key=f"add_{pk}", use_container_width=True):
            n = len(cases)
            if n < 30: cases.append({"name":f"Case {n+1}","changes":[0]*8,"color":COLORS[n%len(COLORS)]})
            st.rerun()
    with c2:
        if st.button("✕ CLEAR", key=f"clr_{pk}", use_container_width=True):
            st.session_state[f"{pk}_cases"] = []; st.rerun()
    with c3:
        exp = json.dumps([{"name":c["name"],"changes":c["changes"]} for c in cases], indent=2)
        st.download_button("⬇ JSON", data=exp, file_name=f"{pk}_cases.json",
                           mime="application/json", use_container_width=True, key=f"exp_{pk}")
    with c4:
        up = st.file_uploader("IMPORT", type="json", key=f"up_{pk}", label_visibility="collapsed")
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
                with st.expander(f"▶ {case['name'].upper()}", expanded=False):
                    a, b = st.columns([4,1])
                    with a:
                        nn = st.text_input("", value=case["name"],
                                           key=f"nm_{pk}_{gi}", label_visibility="collapsed",
                                           placeholder="Case name")
                        cases[gi]["name"] = nn
                    with b:
                        nc = st.color_picker("", value=case["color"],
                                             key=f"cl_{pk}_{gi}", label_visibility="collapsed")
                        cases[gi]["color"] = nc
                    sel = st.selectbox("PRESET", PRESET_NAMES,
                                       index=len(PRESET_NAMES)-1, key=f"ps_{pk}_{gi}")
                    base_chg = PRESETS[sel] if sel!="Custom" else case["changes"]
                    new_ch = []
                    st.markdown("<div style='color:#888800;font-size:9px;letter-spacing:1px;'>RATE CHANGES AT EACH FOMC MEETING (bp)</div>", unsafe_allow_html=True)
                    for mi, d in enumerate(meeting_dates):
                        lbl = f"{d.strftime('%b %d')} ({['Jan','Mar','Apr','Jun','Jul','Sep','Oct','Dec'][mi]})"
                        v = st.number_input(lbl, value=float(base_chg[mi] if sel!="Custom" else case["changes"][mi]),
                                            step=25.0, format="%.0f", key=f"ch_{pk}_{gi}_{mi}")
                        new_ch.append(v)
                    cases[gi]["changes"] = new_ch
                    if st.button("✕ REMOVE", key=f"del_{pk}_{gi}", use_container_width=True):
                        to_del.append(gi)
    for i in sorted(to_del, reverse=True): cases.pop(i)
    if to_del: st.rerun()

# ══════════════════════════════════════════════════════════════════
# COMPUTE
# ══════════════════════════════════════════════════════════════════
def compute_all(pk, base_rate, me, qe, ye):
    res = {}
    for c in st.session_state[f"{pk}_cases"]:
        res[c["name"]] = compute_prices(base_rate, me, qe, ye,
                                         meeting_dates, c["changes"], year)
    return res

sr1_res = compute_all("sr1", sofr_base, sofr_me, sofr_qe, sofr_ye)
zq_res  = compute_all("zq",  effr_base, effr_me, effr_qe, effr_ye)

# ══════════════════════════════════════════════════════════════════
# HEADER BAR — Bloomberg-style function bar
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='background:#000000;border-bottom:2px solid #ff8c00;padding:4px 8px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;'>
    <span style='color:#ffff00;font-size:14px;font-weight:700;font-family:Roboto Mono,monospace;letter-spacing:2px;'>◈ STIR TERMINAL</span>
    <span style='color:#ff8c00;font-size:10px;font-family:Roboto Mono,monospace;'>|</span>
    <span style='color:#ff8c00;font-size:11px;font-family:Roboto Mono,monospace;'>SR1 · ZQ · SPREADS · FLIES · INTER-PRODUCT</span>
    <span style='color:#ff8c00;font-size:10px;font-family:Roboto Mono,monospace;'>|</span>
    <span class='bb-ticker'><span style='color:#888800;'>SOFR</span> <span style='color:#ffff00;font-weight:700;'>{sofr_base*100:.2f}%</span></span>
    <span class='bb-ticker'><span style='color:#888800;'>EFFR</span> <span style='color:#ffff00;font-weight:700;'>{effr_base*100:.2f}%</span></span>
    <span class='bb-ticker'><span style='color:#888800;'>BASIS</span> <span style='color:#00ffff;font-weight:700;'>{(sofr_base-effr_base)*10000:+.1f}bp</span></span>
    <span class='bb-ticker'><span style='color:#888800;'>YEAR</span> <span style='color:#ffff00;font-weight:700;'>{year}</span></span>
    <span class='bb-ticker'><span style='color:#888800;'>CASES</span> <span style='color:#00ff00;font-weight:700;'>SR1:{len(st.session_state.sr1_cases)} ZQ:{len(st.session_state.zq_cases)}</span></span>
</div>
""", unsafe_allow_html=True)

# Global export button
ex_col1, ex_col2, ex_col3 = st.columns([5,1,1])
with ex_col2:
    if sr1_res or zq_res:
        xl = build_excel(sr1_res, zq_res, st.session_state.sr1_cases,
                         st.session_state.zq_cases, year, yr2, meeting_dates)
        st.download_button("⬇ EXPORT XLSX", data=xl, file_name=f"STIR_{year}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
with ex_col3:
    all_cases = st.session_state.sr1_cases + st.session_state.zq_cases
    all_json = json.dumps([{"name":c["name"],"changes":c["changes"]} for c in all_cases], indent=2)
    st.download_button("⬇ ALL JSON", data=all_json, file_name=f"all_cases_{year}.json",
                       mime="application/json", use_container_width=True)

st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SHARED PRODUCT RENDERER
# ══════════════════════════════════════════════════════════════════
def render_product(pk, product, base_rate, results, rate_label):
    cases = st.session_state[f"{pk}_cases"]
    st.markdown(f"<div class='bb-hdr'>◈ {product} — {rate_label}: {base_rate*100:.2f}% — {len(cases)} SCENARIOS LOADED</div>",
                unsafe_allow_html=True)
    case_manager(pk)
    st.markdown("<hr>", unsafe_allow_html=True)
    if not results:
        st.warning("ADD AT LEAST ONE CASE.")
        return

    base_name = cases[0]["name"] if cases else ""
    base_p    = results.get(base_name, {})

    # Metric bar
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric(f"{rate_label}", f"{base_rate*100:.2f}%")
    m2.metric(f"{product} JAN '{yr2}", f"{base_p.get('Jan',0):.4f}")
    m3.metric(f"{product} JUN '{yr2}", f"{base_p.get('Jun',0):.4f}")
    m4.metric(f"{product} DEC '{yr2}", f"{base_p.get('Dec',0):.4f}")
    m5.metric("SCENARIOS", str(len(cases)))
    if len(results) > 1:
        decs = [results[c["name"]]["Dec"] for c in cases if c["name"] in results]
        m6.metric("DEC RANGE (bp)", f"{(max(decs)-min(decs))*100:.2f}")

    st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

    sp_df, fly_df, rate_df = compute_analytics(results, cases)
    prob_df = compute_probabilities(sp_df)

    # ── MARKET PRICE INPUT ──
    mkt_key = f"mkt_prices_{pk}"
    with st.expander("◈ MARKET PRICE INPUT — Enter live screen prices to show dislocation vs your scenario", expanded=False):
        st.markdown("<div class='bb-box-amber'>Enter current CME screen prices for each contract. Dashboard will calculate your scenario vs market = EDGE/DISLOCATION.</div>", unsafe_allow_html=True)
        mc = st.columns(6)
        for mi, mo in enumerate(MONTHS):
            with mc[mi % 6]:
                v = st.number_input(
                    f"{clbl(product,mo)}", value=st.session_state[mkt_key][mo],
                    step=0.01, format="%.4f", key=f"mkt_{pk}_{mi}",
                    label_visibility="visible"
                )
                st.session_state[mkt_key][mo] = v

    t_chart, t_tbl, t_sp, t_fly, t_prob, t_pnl = st.tabs([
        "PRICE CHART", "PRICE TABLE", "CAL SPREADS", "BUTTERFLIES", "CUT PROBABILITIES", "P&L MATRIX"
    ])

    def make_price_table():
        pt = pd.DataFrame(
            {c["name"]: [results[c["name"]][m] for m in MONTHS]
             for c in cases if c["name"] in results}, index=MONTHS
        ).T
        pt.columns = [clbl(product, m) for m in MONTHS]
        pt.index.name = "SCENARIO"
        return pt

    with t_chart:
        st.plotly_chart(
            price_chart(results, cases, product, meeting_dates, show_mkr,
                        f"{rate_label} {base_rate*100:.2f}%"),
            use_container_width=True
        )
        # Price table inline under chart
        st.markdown("<div class='bb-hdr'>CONTRACT PRICES — ALL SCENARIOS</div>", unsafe_allow_html=True)
        pt = make_price_table()
        st.dataframe(pt.style.apply(hl_price, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(90+32*len(pt), 480))

        # Market dislocation
        mkt_vals = [st.session_state[mkt_key][m] for m in MONTHS]
        if any(v > 0 for v in mkt_vals):
            st.markdown("<div class='bb-hdr'>SCENARIO vs MARKET — DISLOCATION (bp)</div>", unsafe_allow_html=True)
            st.markdown("<div class='bb-box-amber'>GREEN = your scenario richer than market (buy opp). RED = your scenario cheaper (sell opp).</div>", unsafe_allow_html=True)
            dis_data = {}
            for c in cases:
                nm = c["name"]
                if nm not in results: continue
                dis_data[nm] = [round((results[nm][m]-mkt_vals[mi])*100, 2) for mi,m in enumerate(MONTHS)]
            dis_df = pd.DataFrame(dis_data, index=MONTHS).T
            dis_df.columns = [clbl(product, m) for m in MONTHS]
            dis_df.index.name = "SCENARIO"
            st.dataframe(dis_df.style.apply(hl_diff, axis=1).format("{:+.2f}"),
                         use_container_width=True, height=min(90+32*len(dis_df), 400))

        if show_diff and len(results) > 1 and base_name in pt.index:
            st.markdown(f"<div class='bb-hdr'>Δ VS BASE SCENARIO: '{base_name}' (bp)</div>", unsafe_allow_html=True)
            diff = (pt.subtract(pt.loc[base_name]) * 100).drop(index=base_name, errors="ignore").round(2)
            if not diff.empty:
                st.dataframe(diff.style.apply(hl_diff, axis=1).format("{:+.2f}"),
                             use_container_width=True, height=min(90+32*len(diff), 360))

    with t_tbl:
        pt2 = make_price_table()
        st.markdown("<div class='bb-hdr'>PRICES</div>", unsafe_allow_html=True)
        st.dataframe(pt2.style.apply(hl_price, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(90+32*len(pt2), 600))
        rd = rate_df.copy()
        rd.columns = [clbl(product, m) for m in MONTHS]; rd.index.name = "SCENARIO"
        st.markdown("<div class='bb-hdr'>IMPLIED RATES (%)</div>", unsafe_allow_html=True)
        st.dataframe(rd.style.apply(hl_rate, axis=0).format("{:.4f}"),
                     use_container_width=True, height=min(90+32*len(rd), 500))
        st.download_button(f"⬇ {product} PRICES CSV", pt2.to_csv(), f"{pk}_{year}.csv", "text/csv")

    with t_sp:
        sp_disp = sp_df.copy()
        sp_disp.columns = [f"{product} {c}" for c in sp_disp.columns]
        st.plotly_chart(bar_chart(sp_disp, f"{product} CALENDAR SPREADS — FRONT MINUS BACK (bp)"),
                        use_container_width=True)
        st.markdown("<div class='bb-hdr'>SPREAD TABLE (bp) — FRONT − BACK</div>", unsafe_allow_html=True)
        st.markdown("""<div class='bb-box-blue'>
        CONVENTION: Front − Back &nbsp;|&nbsp; Source: CME Globex SR1 calendar spread convention<br>
        <span style='color:#ff4444;'>NEGATIVE</span> = back month higher price = cuts priced between these months<br>
        <span style='color:#00ff00;'>POSITIVE</span> = flat or hikes priced<br>
        Jun/Jul spread = SR1_Jun − SR1_Jul. If −25bp → one full 25bp cut priced between Jun and Jul meetings.
        </div>""", unsafe_allow_html=True)
        st.dataframe(sp_disp.style.apply(hl_spread, axis=1).format("{:+.3f}"),
                     use_container_width=True)

    with t_fly:
        fly_disp = fly_df.copy()
        st.plotly_chart(bar_chart(fly_disp, f"{product} BUTTERFLIES — +FRONT −2×BELLY +BACK (bp) [CME BUY-FLY]"),
                        use_container_width=True)
        st.markdown("<div class='bb-hdr'>FLY TABLE (bp) — CME CONVENTION: +FRONT − 2×BELLY + BACK</div>", unsafe_allow_html=True)
        st.markdown("""<div class='bb-box-blue'>
        CME OFFICIAL: Buying a butterfly = +Leg1 − 2×Leg2 + Leg3 (Globex Strategy Guide)<br>
        <span style='color:#00ffff;'>POSITIVE VALUE</span>: belly price LOW (high rate) vs wings = belly CHEAP → BUY THE FLY → profit if belly richens<br>
        <span style='color:#ff8c00;'>NEGATIVE VALUE</span>: belly price HIGH (low rate) vs wings = belly RICH → SELL THE FLY → profit if belly cheapens<br>
        Best trade: fly centred on the meeting month where your rate path diverges most from market consensus.
        </div>""", unsafe_allow_html=True)
        st.dataframe(fly_disp.style.apply(hl_fly, axis=1).format("{:+.3f}"),
                     use_container_width=True)

    with t_prob:
        st.markdown("<div class='bb-hdr'>IMPLIED CUT PROBABILITIES (%) — |SPREAD| ÷ 25bp</div>", unsafe_allow_html=True)
        st.markdown("""<div class='bb-box-amber'>
        Prob(25bp cut between two meetings) = −Spread ÷ 25 × 100%<br>
        Negative spread = cuts priced. A spread of −12.5bp = 50% prob. −25bp = 100% prob of one cut.<br>
        <span style='color:#ff4444;'>>75%</span> = market almost fully pricing a cut &nbsp;|&nbsp;
        <span style='color:#ff8c44;'>40–75%</span> = live meeting &nbsp;|&nbsp;
        <span style='color:#44ff44;'>&lt;10%</span> = cut mostly priced out
        </div>""", unsafe_allow_html=True)
        prob_disp = prob_df.copy()
        prob_disp.columns = [f"Prob {c}" for c in prob_disp.columns]
        prob_disp.index.name = "SCENARIO"
        st.dataframe(prob_disp.style.apply(hl_prob, axis=1).format("{:+.1f}%"),
                     use_container_width=True)
        # Meeting-level summary
        st.markdown("<div class='bb-hdr'>MEETING-LEVEL CUT PROBABILITY SUMMARY</div>", unsafe_allow_html=True)
        mtg_data = {}
        for case in cases:
            nm = case["name"]
            if nm not in results: continue
            row = {}
            for i, (mtg, chg) in enumerate(zip(meeting_dates, case["changes"])):
                row[f"{mtg.strftime('%b %d')} Mtg"] = f"{chg:+.0f}bp"
            mtg_data[nm] = row
        mtg_df = pd.DataFrame(mtg_data).T
        mtg_df.index.name = "SCENARIO"
        st.dataframe(mtg_df, use_container_width=True)

    with t_pnl:
        st.markdown("<div class='bb-hdr'>P&L SCENARIO MATRIX — ENTER YOUR POSITION</div>", unsafe_allow_html=True)
        st.markdown("""<div class='bb-box-amber'>
        Enter your position. DV01 = $41.67/bp/contract for SR1 and ZQ.
        P&L calculated vs your first (base) scenario across all other scenarios.
        </div>""", unsafe_allow_html=True)
        pc1, pc2, pc3, pc4 = st.columns([2,2,1,1])
        with pc1:
            pos_mo = st.selectbox("BUY CONTRACT", MONTHS, index=8, key=f"pos_mo_{pk}")
        with pc2:
            pos_mo2 = st.selectbox("SELL CONTRACT (or NONE)", ["NONE"]+MONTHS, index=0, key=f"pos_mo2_{pk}")
        with pc3:
            pos_lots = st.number_input("LOTS", value=100, step=10, min_value=1, max_value=10000, key=f"pos_lots_{pk}")
        with pc4:
            pos_entry = st.number_input("ENTRY PRICE", value=0.0, step=0.01, format="%.4f", key=f"pos_entry_{pk}")

        if cases and results:
            pnl_rows = []
            for c in cases:
                nm = c["name"]
                if nm not in results: continue
                p_buy  = results[nm][pos_mo]
                p_sell = results[nm][pos_mo2] if pos_mo2 != "NONE" and pos_mo2 in results[nm] else None
                entry  = pos_entry if pos_entry > 0 else (results[cases[0]["name"]][pos_mo]
                                                           - (results[cases[0]["name"]][pos_mo2] if p_sell else 0)
                                                           if cases and cases[0]["name"] in results else 0)
                pos_price = p_buy - (p_sell if p_sell else 0)
                pnl_bp    = (pos_price - entry) * 100
                pnl_usd   = pnl_bp * 41.67 * pos_lots
                pnl_rows.append({
                    "SCENARIO": nm,
                    f"BUY {clbl(product,pos_mo)}": f"{p_buy:.4f}",
                    f"SELL {clbl(product,pos_mo2)}" if pos_mo2!="NONE" else "OUTRIGHT": f"{p_sell:.4f}" if p_sell else "—",
                    "NET PRICE": f"{pos_price:.4f}",
                    "ENTRY": f"{entry:.4f}",
                    "P&L (bp)": round(pnl_bp, 2),
                    "P&L (USD)": round(pnl_usd, 0),
                })
            pnl_df = pd.DataFrame(pnl_rows).set_index("SCENARIO")

            def hl_pnl_col(s):
                if s.name in ("P&L (bp)","P&L (USD)"):
                    return hl_pnl(s)
                return ["color:#ff8c00"]*len(s)

            st.dataframe(
                pnl_df.style.apply(hl_pnl_col).format({
                    "P&L (bp)": "{:+.2f}", "P&L (USD)": "${:+,.0f}"
                }),
                use_container_width=True
            )
            if pos_lots:
                total_dv01 = pos_lots * 41.67
                st.markdown(f"<div class='bb-box-green'>POSITION DV01: <b>${total_dv01:,.0f}</b> per bp &nbsp;|&nbsp; "
                            f"LOTS: <b>{pos_lots}</b> &nbsp;|&nbsp; PRODUCT: <b>{product}</b></div>",
                            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════
TAB_SR1, TAB_ZQ, TAB_SPD, TAB_IPC, TAB_GUIDE = st.tabs([
    "SR1  ONE-MONTH SOFR",
    "ZQ  30-DAY FED FUNDS",
    "SPREADS & FLIES BUILDER",
    "INTER-PRODUCT  SR1/ZQ",
    "TRADING GUIDE & CRITIQUE",
])

with TAB_SR1:
    render_product("sr1", "SR1", sofr_base, sr1_res, "SOFR")

with TAB_ZQ:
    render_product("zq", "ZQ", effr_base, zq_res, "EFFR")

# ══════════════════════════════════════════════════════════════════
# SPREADS & FLIES BUILDER
# ══════════════════════════════════════════════════════════════════
with TAB_SPD:
    st.markdown("<div class='bb-hdr'>◈ SPREAD & FLY BUILDER — CUSTOM MULTI-LEG STRUCTURES</div>", unsafe_allow_html=True)
    col_cfg, col_res = st.columns([1,2])
    with col_cfg:
        prod_sel  = st.selectbox("PRODUCT", ["SR1","ZQ"], key="sp_prod")
        leg_type  = st.radio("STRUCTURE", ["2-LEG SPREAD","3-LEG BUTTERFLY","CUSTOM WEIGHTS"])
        res_sel   = sr1_res if prod_sel=="SR1" else zq_res
        cases_sel = st.session_state.sr1_cases if prod_sel=="SR1" else st.session_state.zq_cases
        if leg_type == "2-LEG SPREAD":
            l1 = st.selectbox("BUY LEG (FRONT)",  MONTHS, index=2, key="l1")
            l2 = st.selectbox("SELL LEG (BACK)",  MONTHS, index=3, key="l2")
            legs  = [(l1,+1),(l2,-1)]
            label = f"{prod_sel} {l1}/{l2}'{yr2} SPREAD"
        elif leg_type == "3-LEG BUTTERFLY":
            fr = st.selectbox("FRONT (+1)", MONTHS, index=2, key="fr")
            be = st.selectbox("BELLY (−2)", MONTHS, index=3, key="be")
            bk = st.selectbox("BACK  (+1)", MONTHS, index=4, key="bk")
            legs  = [(fr,+1),(be,-2),(bk,+1)]
            label = f"{prod_sel} {fr}/{be}/{bk}'{yr2} FLY"
            st.markdown("<div class='bb-box-blue'>CME BUY-FLY: +Front −2×Belly +Back</div>", unsafe_allow_html=True)
        else:
            legs = []
            for mi, mo in enumerate(MONTHS):
                w = st.number_input(f"{prod_sel} {mo}'{yr2}", value=0, step=1,
                                    key=f"cw_{mi}", format="%d")
                if w != 0: legs.append((mo, w))
            label = f"{prod_sel} CUSTOM'{yr2}"

    with col_res:
        if res_sel and legs and cases_sel:
            sv = {}
            for c in cases_sel:
                nm = c["name"]
                if nm not in res_sel: continue
                sv[nm] = round(sum(res_sel[nm][mo]*w for mo,w in legs)*100, 3)
            names_s  = list(sv.keys())
            vals_s   = list(sv.values())
            fig_sp = go.Figure(go.Bar(
                x=names_s, y=vals_s,
                marker_color=[COLORS[i%len(COLORS)] for i in range(len(names_s))],
                hovertemplate="<b>%{x}</b><br>%{y:+.3f} bp<extra></extra>",
            ))
            layout = {**BB_CHART, "title": label, "yaxis_title": "bp",
                      "height": 300, "margin": dict(l=60,r=20,t=40,b=100)}
            fig_sp.update_layout(**layout)
            fig_sp.update_yaxes(zeroline=True, zerolinecolor="#333300")
            fig_sp.update_xaxes(tickangle=-40)
            st.plotly_chart(fig_sp, use_container_width=True)
            sv_df = pd.DataFrame.from_dict(sv, orient="index", columns=[f"{label} (bp)"])
            sv_df.index.name = "SCENARIO"
            base_v = sv_df.iloc[0,0] if not sv_df.empty else 0
            sv_df["Δ vs Base (bp)"] = (sv_df.iloc[:,0] - base_v).round(3)
            st.dataframe(sv_df.style.apply(hl_spread).format("{:+.3f}"), use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='bb-hdr'>FULL SPREAD & FLY MATRIX</div>", unsafe_allow_html=True)
    mat_prod  = st.selectbox("PRODUCT", ["SR1","ZQ"], key="mat_p")
    mat_res   = sr1_res if mat_prod=="SR1" else zq_res
    mat_cases = st.session_state.sr1_cases if mat_prod=="SR1" else st.session_state.zq_cases
    if mat_res and mat_cases:
        sp2, fly2, _ = compute_analytics(mat_res, mat_cases)
        prob2 = compute_probabilities(sp2)
        sp2.columns   = [f"{mat_prod} {c}" for c in sp2.columns]
        prob2.columns  = [f"{mat_prod} {c}" for c in prob2.columns]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div class='bb-hdr'>SPREADS (bp) FRONT−BACK</div>", unsafe_allow_html=True)
            st.dataframe(sp2.style.apply(hl_spread, axis=1).format("{:+.3f}"), use_container_width=True)
        with c2:
            st.markdown("<div class='bb-hdr'>FLIES (bp) +F−2B+K</div>", unsafe_allow_html=True)
            st.dataframe(fly2.style.apply(hl_fly, axis=1).format("{:+.3f}"), use_container_width=True)
        with c3:
            st.markdown("<div class='bb-hdr'>CUT PROBS (%)</div>", unsafe_allow_html=True)
            st.dataframe(prob2.style.apply(hl_prob, axis=1).format("{:+.1f}%"), use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# INTER-PRODUCT
# ══════════════════════════════════════════════════════════════════
with TAB_IPC:
    st.markdown("<div class='bb-hdr'>◈ INTER-PRODUCT: SR1 vs ZQ — SOFR/EFFR BASIS</div>", unsafe_allow_html=True)
    st.markdown("""<div class='bb-box-blue'>
    <b>SR1−ZQ BASIS = SR1 price − ZQ price (same delivery month)</b><br>
    CME Globex convention: display as "SER price minus FF price" (SR1 − ZQ).<br><br>
    <b>WHY THE BASIS DOES NOT CHANGE WITH MEETING SCENARIOS:</b><br>
    Fed cuts/hikes affect SOFR and EFFR <b>identically and simultaneously</b> — both track the FOMC target rate.
    A 25bp cut moves SR1 and ZQ by the same amount in the same month. The net effect on SR1−ZQ = zero.<br>
    In our model this is correct: same rate path → same impact on both products → basis driven only by the
    structural SOFR−EFFR spread you set (sidebar Base SOFR vs Base EFFR) and the ME/QE/YE adj differences.<br><br>
    <b>REAL-WORLD BASIS DRIVERS</b> (not captured in scenarios — these are exogenous to Fed policy):<br>
    • Reserve scarcity / QT — SOFR rises relative to EFFR when repo markets tight<br>
    • Quarter-end balance sheet stress — SOFR spikes, ZQ more stable (widens basis at QE)<br>
    • Treasury settlement / tax flows — temporary SOFR spikes (Sep 15, 2025: SOFR +18bp vs EFFR)<br>
    • YE window dressing — EFFR can drop more than SOFR in Dec → basis widens<br>
    • Current regime (2025): SOFR ≈ EFFR + 5–8bp; forward SOFR contracts price ~7–8bp above EFFR
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([1,3])
    with c1:
        sr1_n = [c["name"] for c in st.session_state.sr1_cases]
        zq_n  = [c["name"] for c in st.session_state.zq_cases]
        sel_s = st.selectbox("SR1 SCENARIO", sr1_n, index=0, key="ip_s") if sr1_n else None
        sel_z = st.selectbox("ZQ SCENARIO",  zq_n,  index=0, key="ip_z") if zq_n  else None
        overlay = st.checkbox("OVERLAY PRICE CURVES", value=True)

    with c2:
        if sel_s and sel_z and sel_s in sr1_res and sel_z in zq_res:
            sp_v = [sr1_res[sel_s][m] for m in MONTHS]
            zp_v = [zq_res[sel_z][m]  for m in MONTHS]
            basis = [round((s-z)*100, 3) for s,z in zip(sp_v, zp_v)]
            fig_ip = go.Figure()
            if overlay:
                fig_ip.add_trace(go.Scatter(
                    x=[clbl("SR1",m) for m in MONTHS], y=sp_v, name=f"SR1: {sel_s}",
                    line=dict(color="#ff8c00",width=2), marker=dict(size=5), yaxis="y1",
                    hovertemplate="SR1 %{x}: <b>%{y:.4f}</b><extra></extra>"))
                fig_ip.add_trace(go.Scatter(
                    x=[clbl("ZQ",m) for m in MONTHS], y=zp_v, name=f"ZQ:  {sel_z}",
                    line=dict(color="#00ff00",width=2,dash="dash"), marker=dict(size=5), yaxis="y1",
                    hovertemplate="ZQ %{x}: <b>%{y:.4f}</b><extra></extra>"))
            fig_ip.add_trace(go.Bar(
                x=MONTHS, y=basis, name="Basis (bp)",
                marker_color=["#00ff00" if v>=0 else "#ff3333" for v in basis],
                yaxis="y2", opacity=0.75,
                hovertemplate="%{x} BASIS: <b>%{y:+.2f} bp</b><extra></extra>"))
            layout = {**BB_CHART, "title": f"SR1 vs ZQ | {sel_s} / {sel_z}",
                      "height": 380, "barmode": "overlay",
                      "yaxis2": dict(title="Basis(bp)", overlaying="y", side="right",
                                     zeroline=True, zerolinecolor="#333300", showgrid=False,
                                     tickfont=dict(size=10, color="#888800"))}
            fig_ip.update_layout(**layout)
            st.plotly_chart(fig_ip, use_container_width=True)

            bdf = pd.DataFrame({
                "CONTRACT":           [clbl("SR1",m) for m in MONTHS],
                f"SR1 ({sel_s})":     [f"{v:.4f}" for v in sp_v],
                f"ZQ  ({sel_z})":     [f"{v:.4f}" for v in zp_v],
                "BASIS (bp)":         [f"{v:+.3f}" for v in basis],
                "SOFR−EFFR RATE(bp)": [f"{(sofr_base-effr_base)*10000:+.1f}" for _ in MONTHS],
            }).set_index("CONTRACT")
            st.dataframe(bdf, use_container_width=True)
            st.markdown(f"""<div class='bb-box-amber'>
            STRUCTURAL BASIS = {(sofr_base-effr_base)*10000:+.1f}bp (set by Base SOFR {sofr_base*100:.2f}% − Base EFFR {effr_base*100:.2f}%).<br>
            Basis is CONSTANT across all meeting scenarios because Fed cuts affect SOFR and EFFR equally.<br>
            To model QE/YE basis widening: adjust ZQ YE adj bp vs SR1 YE adj bp in the sidebar.
            </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='bb-hdr'>ALL-CASE BASIS TABLE</div>", unsafe_allow_html=True)
    bmo = st.selectbox("DELIVERY MONTH", MONTHS, index=8, key="bm")
    rows_b = []
    for sc in st.session_state.sr1_cases:
        for zc in st.session_state.zq_cases:
            if sc["name"] in sr1_res and zc["name"] in zq_res:
                b = round((sr1_res[sc["name"]][bmo]-zq_res[zc["name"]][bmo])*100, 3)
                rows_b.append({"SR1 SCENARIO":sc["name"],"ZQ SCENARIO":zc["name"],
                                f"BASIS {bmo}(bp)":b})
    if rows_b:
        bdf2 = pd.DataFrame(rows_b); col = f"BASIS {bmo}(bp)"
        st.dataframe(bdf2.style.apply(
            lambda s: ["background:#001a00;color:#00ff00" if v>0
                       else "background:#1a0000;color:#ff4444" for v in s]
            if s.name==col else [""]*len(s), axis=0).format({col:"{:+.3f}"}),
            use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# TRADING GUIDE & CRITIQUE
# ══════════════════════════════════════════════════════════════════
with TAB_GUIDE:
    st.markdown("<div class='bb-hdr'>◈ STIR TRADING GUIDE — CME-ACCURATE CONVENTIONS</div>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)

    with g1:
        st.markdown("""
### SR1 — One-Month SOFR Futures
`Price = 100 − arithmetic avg(daily SOFR) for delivery month`
`DV01 = $41.67 per bp per contract ($5M × 1/12 × 1/100)`

- Tracks Fed target ≈ exactly (SOFR ≈ FF upper bound −1 to −3bp in normal conditions)
- Post-Sep 2024, SOFR daily vol has **increased** due to reserve scarcity
- SOFR currently prices **5–8bp above EFFR** on deferred contracts (market-implied)
- Settlement = arithmetic average of daily SOFR fixings (same as ZQ but different reference rate)

### ZQ — 30-Day Fed Funds Futures
`Price = 100 − arithmetic avg(daily EFFR) for delivery month`
`DV01 = $41.67 per bp per contract (identical to SR1)`

- EFFR has been remarkably **stable** — near zero daily std dev even as SOFR moves
- EFFR = Fed's main operating target; rarely strays from FF target range midpoint
- ZQ Dec richens at YE due to window dressing → Fed Funds falls sharply
- Historically the **primary** STIR product; SR1 gaining since SOFR transition
        """)

    with g2:
        st.markdown("""
### Calendar Spreads — FRONT minus BACK (CME convention)
`Jun/Jul Spread = SR1_Jun − SR1_Jul`
| Value | Meaning | Action |
|---|---|---|
| **−25 bp** | One full 25bp cut priced Jun→Jul | Sell if no cut expected |
| **−12.5 bp** | 50% probability of a 25bp cut | High-conviction binary trade |
| **0 bp** | No cut priced (flat curve) | Buy if you expect cuts |
| **+25 bp** | Hike priced | Rare; sell if on hold |

`Prob(cut) = −spread ÷ 25bp × 100%`

### Butterflies — CME BUY-FLY Convention
`BUY FLY = +Front − 2×Belly + Back` ← **THIS IS THE CME DEFINITION**

Source: *CME Globex Strategy Guide* — "Buying a butterfly buys leg1, sells 2×leg2, buys leg3"

| Fly Value | Belly vs Wings | Trade |
|---|---|---|
| **Positive** | Belly cheap (high rate) | **BUY the fly** — profit if belly richens |
| **Negative** | Belly rich (low rate)  | **SELL the fly** — profit if belly cheapens |
| **Near zero** | Linear curve | No edge |
        """)

    st.markdown("---")
    st.markdown("""
### SR1−ZQ BASIS — WHY IT'S CONSTANT ACROSS SCENARIOS

*From CME SOFRWatch methodology:* "The tool adds to this value the **average spread between EFFR and O/N SOFR** for the upcoming three calendar months, as observed by the prices of our One-Month SOFR futures versus Fed Funds futures spreads (SR1−ZQ). This final calculated spread is saved as a **fixed constant**."

**The structural SR1−ZQ basis is exogenous to Fed rate decisions.** Both SOFR and EFFR move identically when the Fed cuts/hikes — they both track the FOMC target. The basis (SOFR − EFFR) is driven by:
1. **Reserve scarcity / QT** — fewer reserves → repo rates rise → SOFR rises relative to EFFR
2. **QE/QT balance sheet cycle** — QT drains reserves, widening the SOFR−EFFR spread
3. **Turn effects** — QE and YE: EFFR can drop (window dressing) while SOFR is stickier
4. **Treasury supply shocks** — large settlements drain cash → SOFR spikes temporarily

**In 2025**: SOFR ≈ EFFR + 5–8bp on deferred contracts. Your model captures this via the Base SOFR vs Base EFFR spread in the sidebar. **To model QE widening**: increase SR1 QE adj bp relative to ZQ.
    """)

    st.markdown("---")
    st.markdown("""<div class='bb-box-red'>
<b>◈ CRITICAL SELF-CRITIQUE OF THIS DASHBOARD (Pro Trader View)</b><br><br>

<b>WHAT'S CORRECT:</b><br>
✓ Butterfly: Fixed to CME convention (+Front −2×Belly +Back)<br>
✓ Spread: Front−Back convention, negative=cuts priced<br>
✓ Cut probability table (|spread|/25bp)<br>
✓ Basis explanation: correctly constant across scenarios, driven by structural SOFR−EFFR<br>
✓ P&L matrix with DV01 calculation<br>
✓ Market price input / dislocation vs scenario<br><br>

<b>STILL MISSING FOR REAL TRADING:</b><br>
① PARTIAL MEETING WEIGHT: SR1 Jan prices only PARTIAL Jan 28 meeting (days after meeting ÷ days in month).
   Current model applies full rate change on day after meeting but doesn't weight the probability.
   e.g. Jan 28 in a 31-day month = only 2/31 = 6.5% of the month is post-meeting → only 1.6bp of a 25bp cut hits SR1 Jan.<br>
② CARRY/ROLL-DOWN TABLE: each spread has daily carry = how much value it loses/gains per day if rates are unchanged.
   A steep spread earns carry; a flat spread has zero carry. Critical for position sizing and hold-time.<br>
③ SCENARIO PROBABILITY WEIGHTING: ability to assign probabilities to each case and compute the probability-weighted price.
   This is what dealers use to mark books.<br>
④ LIVE CME PRICE FEED: the market price input is manual. A real terminal would pull from CME via API.<br>
⑤ HISTORICAL CONTEXT: show where current implied probabilities sit vs historical range.
   A 50% probability of a cut in Jun is "normal" in some cycles, "extreme" in others.<br>
⑥ CONVEXITY ADJUSTMENT: SR1 is linear; OTC OIS has convexity. Not needed for scenario work but relevant for hedging.
</div>""", unsafe_allow_html=True)

    st.markdown("""<div class='bb-box-amber'>
MEETING → CONTRACT MAPPING 2026 (CME RULE: effective date = day after meeting)<br>
Jan 28 → eff Jan 29 → SR1 Jan captures 2/31 days post-meeting (6.5% partial) | SR1 Feb is first full post-meeting<br>
Mar 18 → eff Mar 19 → SR1 Mar partial | SR1 Apr first full | Jun 17 → SR1 Jul first full<br>
Jul 29 → SR1 Aug first full | Sep 16 → SR1 Oct first full | Oct 28 → SR1 Nov first full | Dec 9 → SR1 Jan'27 first full<br>
RULE: partial-month contract = days_after_meeting ÷ days_in_month × cut_size (weighted avg rate)
</div>""", unsafe_allow_html=True)

st.markdown(
    f"<div style='font-size:9px;color:#333300;font-family:Roboto Mono,monospace;margin-top:6px;padding:2px 6px;"
    f"border-top:1px solid #111100;'>STIR TERMINAL v3.0 | CME-ACCURATE BUTTERFLY: +F−2B+K | "
    f"SR1 SOFR {sofr_base*100:.2f}% | ZQ EFFR {effr_base*100:.2f}% | "
    f"ME {sofr_me*10000:.1f}bp | YE(ZQ) {effr_ye*10000:.1f}bp | {year} | "
    f"SR1−ZQ BASIS: {(sofr_base-effr_base)*10000:+.1f}bp STRUCTURAL</div>",
    unsafe_allow_html=True
)
