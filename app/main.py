from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # Load .env before any other imports that read env vars

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from structlog.contextvars import bind_contextvars

from .agent import LabAgent
from .alert_evaluator import get_alert_status
from .audit import log_audit_event
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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
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
        log_audit_event(
            action="chat_request",
            user_id_hash=user_id_hash,
            correlation_id=request.state.correlation_id,
            result="success",
            metadata={
                "feature": body.feature,
                "model": body.model,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "tokens_in": result.tokens_in,
                "tokens_out": result.tokens_out,
            },
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
        log_audit_event(
            action="chat_request",
            user_id_hash=user_id_hash,
            correlation_id=request.state.correlation_id,
            result="error",
            metadata={"error_type": error_type},
        )
        raise HTTPException(status_code=500, detail=error_type) from exc


@app.post("/incidents/{name}/enable")
async def enable_incident(name: str) -> JSONResponse:
    try:
        enable(name)
        log.warning("incident_enabled", service="control", payload={"name": name})
        log_audit_event(
            action="incident_enable",
            user_id_hash="system",
            correlation_id="system",
            result="success",
            metadata={"name": name},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/incidents/{name}/disable")
async def disable_incident(name: str) -> JSONResponse:
    try:
        disable(name)
        log.warning("incident_disabled", service="control", payload={"name": name})
        log_audit_event(
            action="incident_disable",
            user_id_hash="system",
            correlation_id="system",
            result="success",
            metadata={"name": name},
        )
        return JSONResponse({"ok": True, "incidents": status()})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# --- Dashboard builder --------------------------------------------------------

def _build_dashboard_html(metrics_data: dict) -> str:
    """Build a self-contained 6-panel Chart.js dashboard with SLO threshold lines."""
    import json

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
    quality_color = "#22c55e" if quality_avg >= 0.75 else "#ef4444"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Day 13 Observability Dashboard - Nhom 5 E402</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg:#0f1117;--card:#1a1d27;--border:#2a2d3a;
    --text:#e2e8f0;--muted:#64748b;--red:#ef4444;
    --green:#22c55e;--blue:#3b82f6;--yellow:#f59e0b;
    --purple:#a855f7;--cyan:#06b6d4;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;padding:1.5rem}}
  h1{{font-size:1.2rem;font-weight:700;margin-bottom:.2rem}}
  .sub{{color:var(--muted);font-size:.75rem;margin-bottom:1.4rem}}
  .cyan{{color:var(--cyan)}}
  .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:.75rem;padding:1rem}}
  .card h2{{font-size:.72rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.6rem}}
  canvas{{max-height:190px}}
  .row{{display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted);margin-top:.4rem}}
  .val{{font-weight:700;color:var(--text)}}
  .slo{{color:var(--red)}}
  @media(max-width:900px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
  @media(max-width:580px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>Observability Dashboard - Nhom 5 E402</h1>
<p class="sub">Day 13 Lab &nbsp;&middot;&nbsp; <span class="cyan">Auto-refresh 15s</span></p>
<div class="grid">
  <div class="card">
    <h2>Latency P50 / P95 / P99</h2>
    <canvas id="cLat"></canvas>
    <div class="row"><span>P95 <span class="val">{latency_p95:.0f}ms</span></span><span>SLO <span class="val slo">3000ms</span></span></div>
  </div>
  <div class="card">
    <h2>Total Requests</h2>
    <canvas id="cTraf"></canvas>
    <div class="row"><span>Total <span class="val">{traffic}</span></span></div>
  </div>
  <div class="card">
    <h2>Error Breakdown</h2>
    <canvas id="cErr"></canvas>
  </div>
  <div class="card">
    <h2>Accumulated Cost (USD)</h2>
    <canvas id="cCost"></canvas>
    <div class="row"><span>Total <span class="val">${total_cost:.4f}</span></span><span>Budget <span class="val slo">$2.50/day</span></span></div>
  </div>
  <div class="card">
    <h2>Tokens In / Out</h2>
    <canvas id="cTok"></canvas>
    <div class="row"><span>In <span class="val">{tokens_in}</span></span><span>Out <span class="val">{tokens_out}</span></span></div>
  </div>
  <div class="card">
    <h2>Quality Score Avg</h2>
    <canvas id="cQual"></canvas>
    <div class="row"><span>Score <span class="val">{quality_avg:.3f}</span></span><span>SLO <span class="val slo">&ge;0.75</span></span></div>
  </div>
</div>
<script>
const D={{responsive:true,maintainAspectRatio:false,
  plugins:{{legend:{{labels:{{color:'#94a3b8',font:{{size:10}}}}}}}},
  scales:{{x:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e2233'}}}},
           y:{{ticks:{{color:'#64748b'}},grid:{{color:'#1e2233'}}}}}}}};
new Chart(document.getElementById('cLat'),{{type:'bar',
  data:{{labels:['P50','P95','P99'],
    datasets:[{{label:'ms',data:[{latency_p50:.1f},{latency_p95:.1f},{latency_p99:.1f}],
      backgroundColor:['#3b82f6','#f59e0b','#ef4444']}}]}},
  options:{{...D,scales:{{...D.scales,y:{{...D.scales.y,suggestedMax:Math.max({latency_p99:.1f}*1.3,3200)}}}}}}}});
new Chart(document.getElementById('cTraf'),{{type:'doughnut',
  data:{{labels:['Requests'],datasets:[{{data:[{traffic},0],backgroundColor:['#3b82f6','#1e2233'],borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}}}}}});
new Chart(document.getElementById('cErr'),{{type:'doughnut',
  data:{{labels:{error_labels},datasets:[{{data:{error_values},
    backgroundColor:['#ef4444','#f59e0b','#a855f7','#06b6d4'],borderWidth:0}}]}},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{labels:{{color:'#94a3b8'}}}}}}}}}});
new Chart(document.getElementById('cCost'),{{type:'bar',
  data:{{labels:['Total Cost'],datasets:[{{label:'USD',data:[{total_cost:.4f}],backgroundColor:['#22c55e']}}]}},
  options:{{...D,scales:{{...D.scales,y:{{...D.scales.y,suggestedMax:2.5}}}}}}}});
new Chart(document.getElementById('cTok'),{{type:'bar',
  data:{{labels:['Tokens'],datasets:[
    {{label:'In',data:[{tokens_in}],backgroundColor:'#3b82f6'}},
    {{label:'Out',data:[{tokens_out}],backgroundColor:'#a855f7'}}]}},
  options:D}});
new Chart(document.getElementById('cQual'),{{type:'bar',
  data:{{labels:['Quality'],datasets:[{{label:'Score',data:[{quality_avg:.4f}],
    backgroundColor:['{quality_color}']}}]}},
  options:{{...D,scales:{{...D.scales,y:{{...D.scales.y,min:0,max:1}}}}}}}});
setTimeout(()=>location.reload(),15000);
</script>
</body></html>"""
