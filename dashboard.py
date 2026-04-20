"""
Member E — Day 13 Observability Dashboard
6 required panels with SLO lines, units, auto-refresh
"""

import time
import requests
import streamlit as st
import pandas as pd

# ── Config ────────────────────────────────────────────────────────────────────
METRICS_URL = "http://127.0.0.1:8000/metrics"
REFRESH_INTERVAL = 15  # seconds

# SLO thresholds (from config/slo.yaml)
SLO_LATENCY_P95_MS = 3000
SLO_ERROR_RATE_PCT = 2.0
SLO_DAILY_COST_USD = 2.5
SLO_QUALITY_AVG    = 0.75

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Day 13 Observability Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Day 13 Observability Dashboard")
st.caption(f"Auto-refresh every {REFRESH_INTERVAL}s · SLOs from config/slo.yaml · Nhóm 5 – E402")

# ── Fetch metrics ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_INTERVAL)
def fetch_metrics() -> dict:
    try:
        r = requests.get(METRICS_URL, timeout=3)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Cannot reach {METRICS_URL}: {e}")
        return {}

m = fetch_metrics()

if not m:
    st.warning("No data yet. Make sure the app is running and you have sent some requests.")
    st.stop()

# ── Derived values ────────────────────────────────────────────────────────────
traffic       = m.get("traffic", 0)
error_total   = sum(m.get("error_breakdown", {}).values())
error_rate    = (error_total / traffic * 100) if traffic > 0 else 0.0
latency_p50   = m.get("latency_p50", 0)
latency_p95   = m.get("latency_p95", 0)
latency_p99   = m.get("latency_p99", 0)
avg_cost      = m.get("avg_cost_usd", 0)
total_cost    = m.get("total_cost_usd", 0)
tokens_in     = m.get("tokens_in_total", 0)
tokens_out    = m.get("tokens_out_total", 0)
quality       = m.get("quality_avg", 0)

# ── Top KPI row ───────────────────────────────────────────────────────────────
st.subheader("Live Snapshot")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Requests", traffic)
k2.metric("Error Rate", f"{error_rate:.1f}%",
          delta=f"SLO: <{SLO_ERROR_RATE_PCT}%",
          delta_color="inverse" if error_rate > SLO_ERROR_RATE_PCT else "normal")
k3.metric("P95 Latency", f"{latency_p95:.0f} ms",
          delta=f"SLO: <{SLO_LATENCY_P95_MS} ms",
          delta_color="inverse" if latency_p95 > SLO_LATENCY_P95_MS else "normal")
k4.metric("Quality Avg", f"{quality:.2f}",
          delta=f"SLO: >{SLO_QUALITY_AVG}",
          delta_color="normal" if quality >= SLO_QUALITY_AVG else "inverse")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PANEL 1 — Latency P50 / P95 / P99
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Panel 1 · Latency P50 / P95 / P99 (ms)")

latency_df = pd.DataFrame({
    "Percentile": ["P50", "P95", "P99"],
    "Latency (ms)": [latency_p50, latency_p95, latency_p99],
})

col1, col2 = st.columns([2, 1])
with col1:
    import altair as alt
    slo_line = pd.DataFrame({"y": [SLO_LATENCY_P95_MS], "label": [f"SLO P95 < {SLO_LATENCY_P95_MS} ms"]})

    bars = alt.Chart(latency_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Percentile", sort=["P50", "P95", "P99"]),
        y=alt.Y("Latency (ms)", title="ms"),
        color=alt.condition(
            alt.datum["Latency (ms)"] > SLO_LATENCY_P95_MS,
            alt.value("#e74c3c"),
            alt.value("#2ecc71"),
        ),
        tooltip=["Percentile", "Latency (ms)"],
    )
    rule = alt.Chart(slo_line).mark_rule(color="orange", strokeDash=[6, 4], strokeWidth=2).encode(
        y="y:Q",
        tooltip=["label:N"],
    )
    st.altair_chart(bars + rule, use_container_width=True)

with col2:
    st.metric("P50", f"{latency_p50:.0f} ms")
    st.metric("P95", f"{latency_p95:.0f} ms")
    st.metric("P99", f"{latency_p99:.0f} ms")
    if latency_p95 > SLO_LATENCY_P95_MS:
        st.error(f"⚠️ P95 breaches SLO ({SLO_LATENCY_P95_MS} ms)")
    else:
        st.success("✅ Within SLO")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PANEL 2 — Traffic
# PANEL 3 — Error Rate
# (side by side)
# ══════════════════════════════════════════════════════════════════════════════
p2, p3 = st.columns(2)

with p2:
    st.subheader("Panel 2 · Traffic (Request Count)")
    traffic_df = pd.DataFrame({
        "Status": ["Success", "Error"],
        "Count": [traffic - error_total, error_total],
    })
    pie = alt.Chart(traffic_df).mark_arc(innerRadius=50).encode(
        theta=alt.Theta("Count:Q"),
        color=alt.Color("Status:N", scale=alt.Scale(
            domain=["Success", "Error"],
            range=["#2ecc71", "#e74c3c"]
        )),
        tooltip=["Status", "Count"],
    )
    st.altair_chart(pie, use_container_width=True)
    st.caption(f"Total: **{traffic}** requests  |  Success: **{traffic - error_total}**  |  Error: **{error_total}**")

with p3:
    st.subheader("Panel 3 · Error Rate (%)")
    error_breakdown = m.get("error_breakdown", {})
    slo_color = "#e74c3c" if error_rate > SLO_ERROR_RATE_PCT else "#2ecc71"

    gauge_df = pd.DataFrame({
        "Category": ["Error Rate", "Headroom"],
        "Value": [min(error_rate, 100), max(0, 100 - error_rate)],
    })
    arc = alt.Chart(gauge_df).mark_arc(innerRadius=60, outerRadius=90).encode(
        theta="Value:Q",
        color=alt.Color("Category:N", scale=alt.Scale(
            domain=["Error Rate", "Headroom"],
            range=[slo_color, "#ecf0f1"]
        )),
    )
    st.altair_chart(arc, use_container_width=True)
    st.metric("Error Rate", f"{error_rate:.1f}%", delta=f"SLO < {SLO_ERROR_RATE_PCT}%",
              delta_color="inverse" if error_rate > SLO_ERROR_RATE_PCT else "normal")
    if error_breakdown:
        st.write("**Error breakdown:**", error_breakdown)
    else:
        st.success("✅ No errors")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PANEL 4 — Cost Over Time
# PANEL 5 — Tokens In / Out
# (side by side)
# ══════════════════════════════════════════════════════════════════════════════
p4, p5 = st.columns(2)

with p4:
    st.subheader("Panel 4 · Cost (USD)")
    # Extrapolate daily cost from current avg × estimated 1000 req/day
    est_daily = avg_cost * 1000
    cost_df = pd.DataFrame({
        "Category": ["Accumulated Cost", "Per Request (avg)"],
        "USD": [total_cost, avg_cost],
    })
    bars_cost = alt.Chart(cost_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Category:N"),
        y=alt.Y("USD:Q", title="USD"),
        color=alt.value("#3498db"),
        tooltip=["Category", "USD"],
    )
    slo_cost_line = pd.DataFrame({"y": [SLO_DAILY_COST_USD / 1000], "label": ["SLO per-req budget"]})
    rule_cost = alt.Chart(slo_cost_line).mark_rule(color="orange", strokeDash=[6, 4], strokeWidth=2).encode(
        y="y:Q", tooltip=["label:N"],
    )
    st.altair_chart(bars_cost + rule_cost, use_container_width=True)
    st.caption(f"Total: **${total_cost:.4f}**  |  Avg/req: **${avg_cost:.4f}**  |  Daily SLO: **< ${SLO_DAILY_COST_USD}**")

with p5:
    st.subheader("Panel 5 · Tokens In / Out")
    token_df = pd.DataFrame({
        "Direction": ["Tokens In", "Tokens Out"],
        "Count": [tokens_in, tokens_out],
    })
    bars_tok = alt.Chart(token_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Direction:N"),
        y=alt.Y("Count:Q", title="Token Count"),
        color=alt.Color("Direction:N", scale=alt.Scale(
            domain=["Tokens In", "Tokens Out"],
            range=["#9b59b6", "#e67e22"]
        )),
        tooltip=["Direction", "Count"],
    )
    st.altair_chart(bars_tok, use_container_width=True)
    ratio = (tokens_out / tokens_in) if tokens_in > 0 else 0
    st.caption(f"In: **{tokens_in}**  |  Out: **{tokens_out}**  |  Ratio: **{ratio:.2f}×**")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PANEL 6 — Quality Score
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("Panel 6 · Quality Score (avg)")

q_col1, q_col2 = st.columns([2, 1])
with q_col1:
    quality_df = pd.DataFrame({
        "Metric": ["Quality Score", "SLO Target"],
        "Value": [quality, SLO_QUALITY_AVG],
    })
    bars_q = alt.Chart(quality_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Metric:N"),
        y=alt.Y("Value:Q", scale=alt.Scale(domain=[0, 1]), title="Score (0–1)"),
        color=alt.Color("Metric:N", scale=alt.Scale(
            domain=["Quality Score", "SLO Target"],
            range=["#1abc9c" if quality >= SLO_QUALITY_AVG else "#e74c3c", "#f39c12"]
        )),
        tooltip=["Metric", "Value"],
    )
    st.altair_chart(bars_q, use_container_width=True)

with q_col2:
    st.metric("Quality Avg", f"{quality:.3f}")
    st.metric("SLO Target", f"> {SLO_QUALITY_AVG}")
    if quality >= SLO_QUALITY_AVG:
        st.success("✅ Within SLO")
    else:
        st.error("⚠️ Below SLO")

# ── Footer / auto-refresh ─────────────────────────────────────────────────────
st.divider()
st.caption(f"Last fetched: {time.strftime('%H:%M:%S')}  ·  Data source: `{METRICS_URL}`")

# Auto-refresh
time.sleep(REFRESH_INTERVAL)
st.rerun()
