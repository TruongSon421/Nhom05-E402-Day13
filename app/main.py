from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .alert_evaluator import get_alert_status
from .incidents import disable, enable, status
from .logging_config import configure_logging, get_logger
from .metrics import record_error, snapshot
from .middleware import CorrelationIdMiddleware
from .pii import hash_user_id, summarize_text
from .schemas import ChatRequest, ChatResponse
from .slo_monitor import get_slo_status
from .tracing import tracing_enabled

configure_logging()
log = get_logger()
app = FastAPI(title="Day 13 Observability Lab")
app.add_middleware(CorrelationIdMiddleware)
agent = LabAgent()


@app.on_event("startup")
async def startup() -> None:
    log.info(
        "app_started",
        service=os.getenv("APP_NAME", "day13-observability-lab"),
        env=os.getenv("APP_ENV", "dev"),
        payload={"tracing_enabled": tracing_enabled()},
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "tracing_enabled": tracing_enabled(), "incidents": status()}


@app.get("/metrics")
async def metrics() -> dict:
    return snapshot()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    # Enrich logs with request context (user_id_hash, session_id, feature, model, env)
    user_id_hash = hash_user_id(body.user_id)
    bind_contextvars(
        user_id_hash=user_id_hash,
        session_id=body.session_id,
        feature=body.feature,
        model=body.model,
        env=os.getenv("APP_ENV", "dev"),
    )
    
    log.info(
        "request_received",
        service="api",
        payload={"message_preview": summarize_text(body.message)},
    )
    try:
        result = agent.run(
            user_id=body.user_id,
            feature=body.feature,
            session_id=body.session_id,
            message=body.message,
            correlation_id=request.state.correlation_id,
        )
        log.info(
            "response_sent",
            service="api",
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            payload={"answer_preview": summarize_text(result.answer)},
        )
        return ChatResponse(
            answer=result.answer,
            correlation_id=request.state.correlation_id,
            latency_ms=result.latency_ms,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            quality_score=result.quality_score,
        )
    except Exception as exc:  # pragma: no cover
        error_type = type(exc).__name__
        record_error(error_type)
        log.error(
            "request_failed",
            service="api",
            error_type=error_type,
            payload={"detail": str(exc), "message_preview": summarize_text(body.message)},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/slo/status")
async def slo_status() -> dict:
    """Return current SLO compliance status for all SLIs."""
    try:
        return get_slo_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"SLO config not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SLO calculation failed: {exc}") from exc


@app.get("/alerts/status")
async def alerts_status() -> dict:
    """Return current alert evaluation status for all configured rules."""
    try:
        return get_alert_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=f"Alert config not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Alert evaluation failed: {exc}") from exc


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    """6-panel real-time Chart.js dashboard with SLO threshold lines."""
    metrics_data = snapshot()
    html = _build_dashboard_html(metrics_data)
    return HTMLResponse(content=html)


def _build_dashboard_html(metrics_data: dict) -> str:  # noqa: PLR0915
    """Build a self-contained Chart.js dashboard with 6 panels and SLO lines."""
    import json

    # Safely extract metrics values
    latency_p50 = metrics_data.get("latency_p50", 0)
    latency_p95 = metrics_data.get("latency_p95", 0)
    latency_p99 = metrics_data.get("latency_p99", 0)
    traffic = metrics_data.get("traffic", 0)
    error_breakdown: dict = metrics_data.get("error_breakdown", {})
    total_cost = metrics_data.get("total_cost_usd", 0)
    tokens_in = metrics_data.get("tokens_in_total", 0)
    tokens_out = metrics_data.get("tokens_out_total", 0)
    quality_avg = metrics_data.get("quality_avg", 0)

    error_labels = json.dumps(list(error_breakdown.keys()) or ["none"])
    error_values = json.dumps(list(error_breakdown.values()) or [0])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Day 13 Observability Dashboard – Nhóm 5 E402</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117; --card: #1a1d27; --border: #2a2d3a;
    --text: #e2e8f0; --muted: #64748b; --red: #ef4444;
    --green: #22c55e; --blue: #3b82f6; --yellow: #f59e0b;
    --purple: #a855f7; --cyan: #06b6d4;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; padding: 1.5rem; }}
  h1 {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem; }}
  .subtitle {{ color: var(--muted); font-size: 0.8rem; margin-bottom: 1.5rem; }}
  .meta {{ color: var(--cyan); font-size: 0.75rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; }}
  .card h2 {{ font-size: 0.8rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; }}
  canvas {{ max-height: 200px; }}
  .stat-row {{ display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; }}
  .stat-val {{ font-weight: 700; color: var(--text); }}
  @media (max-width: 900px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  @media (max-width: 600px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<h1>📊 Observability Dashboard</h1>
<p class="subtitle">Nhóm 5 E402 · Day 13 Lab · <span class="meta">Auto-refresh every 15s</span></p>

<div class="grid">
  <!-- Panel 1: Latency -->
  <div class="card">
    <h2>⚡ Latency P50 / P95 / P99</h2>
    <canvas id="latencyChart"></canvas>
    <div class="stat-row">
      <span>P95 <span class="stat-val">{latency_p95:.0f}ms</span></span>
      <span>SLO <span class="stat-val" style="color:var(--red)">3000ms</span></span>
    </div>
  </div>

  <!-- Panel 2: Traffic -->
  <div class="card">
    <h2>🚦 Total Requests</h2>
    <canvas id="trafficChart"></canvas>
    <div class="stat-row">
      <span>Total <span class="stat-val">{traffic}</span></span>
    </div>
  </div>

  <!-- Panel 3: Error Breakdown -->
  <div class="card">
    <h2>❌ Error Breakdown</h2>
    <canvas id="errorChart"></canvas>
  </div>

  <!-- Panel 4: Cost -->
  <div class="card">
    <h2>💰 Total Cost (USD)</h2>
    <canvas id="costChart"></canvas>
    <div class="stat-row">
      <span>Cost <span class="stat-val">${total_cost:.4f}</span></span>
      <span>Budget <span class="stat-val" style="color:var(--red)">$2.50/day</span></span>
    </div>
  </div>

  <!-- Panel 5: Tokens -->
  <div class="card">
    <h2>🔤 Tokens In / Out</h2>
    <canvas id="tokenChart"></canvas>
    <div class="stat-row">
      <span>In <span class="stat-val">{tokens_in}</span></span>
      <span>Out <span class="stat-val">{tokens_out}</span></span>
    </div>
  </div>

  <!-- Panel 6: Quality Score -->
  <div class="card">
    <h2>⭐ Quality Score Avg</h2>
    <canvas id="qualityChart"></canvas>
    <div class="stat-row">
      <span>Score <span class="stat-val">{quality_avg:.3f}</span></span>
      <span>SLO <span class="stat-val" style="color:var(--red)">≥ 0.75</span></span>
    </div>
  </div>
</div>

<script>
const CHART_DEFAULTS = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{ legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }},
  scales: {{
    x: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e2233' }} }},
    y: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e2233' }} }},
  }},
}};

// Panel 1 – Latency bar chart
new Chart(document.getElementById('latencyChart'), {{
  type: 'bar',
  data: {{
    labels: ['P50', 'P95', 'P99'],
    datasets: [{{
      label: 'Latency (ms)',
      data: [{latency_p50:.1f}, {latency_p95:.1f}, {latency_p99:.1f}],
      backgroundColor: ['#3b82f6', '#f59e0b', '#ef4444'],
    }}],
  }},
  options: {{
    ...CHART_DEFAULTS,
    plugins: {{
      ...CHART_DEFAULTS.plugins,
      annotation: void 0,
    }},
    scales: {{
      ...CHART_DEFAULTS.scales,
      y: {{ ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max({latency_p99:.1f} * 1.3, 3200) }},
    }},
  }},
}});

// Panel 2 – Traffic doughnut
new Chart(document.getElementById('trafficChart'), {{
  type: 'doughnut',
  data: {{
    labels: ['Requests'],
    datasets: [{{ data: [{traffic}, 0], backgroundColor: ['#3b82f6', '#1e2233'], borderWidth: 0 }}],
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{ callbacks: {{ label: (ctx) => ` ${{ctx.raw}} total requests` }} }},
    }},
  }},
}});

// Panel 3 – Error breakdown doughnut
new Chart(document.getElementById('errorChart'), {{
  type: 'doughnut',
  data: {{
    labels: {error_labels},
    datasets: [{{
      data: {error_values},
      backgroundColor: ['#ef4444','#f59e0b','#a855f7','#06b6d4'],
      borderWidth: 0,
    }}],
  }},
  options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }} }},
}});

// Panel 4 – Cost bar
new Chart(document.getElementById('costChart'), {{
  type: 'bar',
  data: {{
    labels: ['Total Cost'],
    datasets: [{{
      label: 'USD',
      data: [{total_cost:.4f}],
      backgroundColor: ['#22c55e'],
    }}],
  }},
  options: {{
    ...CHART_DEFAULTS,
    scales: {{
      ...CHART_DEFAULTS.scales,
      y: {{ ...CHART_DEFAULTS.scales.y, suggestedMax: 2.5 }},
    }},
  }},
}});

// Panel 5 – Tokens grouped bar
new Chart(document.getElementById('tokenChart'), {{
  type: 'bar',
  data: {{
    labels: ['Tokens'],
    datasets: [
      {{ label: 'In', data: [{tokens_in}], backgroundColor: '#3b82f6' }},
      {{ label: 'Out', data: [{tokens_out}], backgroundColor: '#a855f7' }},
    ],
  }},
  options: CHART_DEFAULTS,
}});

// Panel 6 – Quality score gauge (bar)
new Chart(document.getElementById('qualityChart'), {{
  type: 'bar',
  data: {{
    labels: ['Quality Avg'],
    datasets: [{{
      label: 'Score',
      data: [{quality_avg:.4f}],
      backgroundColor: [{quality_avg:.4f} >= 0.75 ? '#22c55e' : '#ef4444'],
    }}],
  }},
  options: {{
    ...CHART_DEFAULTS,
    scales: {{
      ...CHART_DEFAULTS.scales,
      y: {{ ...CHART_DEFAULTS.scales.y, min: 0, max: 1 }},
    }},
  }},
}});

// Auto-refresh every 15 seconds
setTimeout(() => location.reload(), 15000);
</script>
</body>
</html>"""
