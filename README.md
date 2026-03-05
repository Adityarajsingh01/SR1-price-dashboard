# SR1 SOFR Pricing Dashboard

Interactive dashboard to model and compare up to **30 SR1 scenario cases** across
all 8 FOMC meetings in a given year.

## Quick Start

```bash
# 1. Install dependencies (one time)
pip install -r requirements.txt

# 2. Launch the dashboard
streamlit run sr1_dashboard.py
```
Your browser will open automatically at http://localhost:8501

---

## What the dashboard does

| Feature | Details |
|---|---|
| **Pricing engine** | Replicates your Excel logic exactly: base SOFR + ME/QE/YE adjustments + per-meeting rate changes → daily rates → monthly avg → Price = 100 − R_eff×100 |
| **Up to 30 cases** | Each case has independent bps changes at each of the 8 FOMC meetings |
| **Preset scenarios** | 8 built-in presets (no change, 1–4 cuts, 1 hike, aggressive easing) + Custom |
| **Price chart** | Line chart of monthly SR1 prices with optional FOMC date markers |
| **Δ vs Base chart** | Grouped bar chart of price difference vs your chosen base case |
| **Comparison table** | Full price matrix, color-scaled, downloadable as CSV |
| **Rate path detail** | Cumulative SOFR path after each meeting per case |
| **Import / Export** | Save and reload your case configurations as JSON |

---

## Pricing Logic (from your Excel)

```
For each calendar day d in month M:
    rate(d) = base_SOFR
            + Σ(rate_changes of meetings with effective date ≤ d)
            + ME_adj  [if d = last business day or carry-in weekend of prior month-end]
            + QE_adj  [if M is Mar/Jun/Sep/Dec and d = last business day]
            + YE_adj  [if M is Dec and d = last business day]

Monthly average  = Σ rate(d) / days_in_month
Price            = 100 − monthly_average × 100
```

Rate changes take effect the **calendar day after** the FOMC meeting date (standard SOFR convention).

---

## Typical Usage

1. Set **Base SOFR** in the sidebar (default 5.00%)
2. Verify or edit the **8 FOMC meeting dates**
3. Click **➕ Add Case** for each scenario you want to compare
4. For each case: pick a **preset** or enter **custom bps** at each meeting
5. View results in the **Price Chart**, **Δ vs Base**, or **Table** tabs
6. Download the CSV or export your case set as JSON for later

---

## Files

```
sr1_dashboard.py   – the full Streamlit application
requirements.txt   – Python dependencies
README.md          – this file
```
