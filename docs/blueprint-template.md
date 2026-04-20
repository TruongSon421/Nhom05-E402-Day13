# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Nhóm 5 - E402
- [REPO_URL]: https://github.com/TruongSon421/Nhom05-E402-Day13.git
- [MEMBERS]:
  - Member A: [Trần Thượng Trường Sơn] | Role: Logging & PII
  - Member B: [Bùi Lâm Tiến] | Role: Tracing & Enrichment
  - Member C: [Trương Đăng Nghĩa] | Role: SLO & Alerts
  - Member D: [Bùi Thế Công] | Role: Load Test & Incident Injection
  - Member E: [Trần Ngọc Huy] | Role: Dashboard + Evidence
  - Member F: [Nông Trung Kiên] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 41
- [PII_LEAKS_FOUND]: 0 

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: [Path to image]
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: [Path to image]
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: [Path to image]
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/evidence/04_dashboard_6_panels.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 151.0ms (baseline), 2651.0ms (rag_slow) |
| Error Rate | < 2% | 28d | 0% (baseline), 100% (tool_fail) |
| Cost Budget | < $2.5/day | 1d | $0.0409/day (baseline), $0.1303/day (cost_spike 3.2×) |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)

### Incident 1: rag_slow (Latency Spike)
- **Scenario**: rag_slow
- **Symptoms Observed**: 
  - P95 latency spike: 151.0ms → 2651.0ms (+1652% increase)
  - Request duration: ~156ms → ~2657ms per request
  - Total cost increased due to more backend overhead
  - Throughput degraded: concurrent requests showed latency hotspot

- **Root Cause (Proved By)**: 
  - Code: `app/mock_rag.py:18` — `time.sleep(2.5)` when `STATE["rag_slow"] == True`
  - Trace structure: `LabAgent.run()` → `retrieve()` (RAG span ~2503ms) + `generate()` (LLM span ~150ms)
  - Evidence: Each request added exactly 2.5 seconds delay to RAG retrieval

- **Fix Action**: 
  - `python scripts/inject_incident.py --scenario rag_slow --disable`
  - Verified incident disabled by checking: `curl http://127.0.0.1:8000/health` shows `rag_slow: false`

- **Preventive Measure**: 
  - Implement timeout on RAG retrieval call (e.g., 1 second max)
  - Use circuit breaker pattern to fail fast if RAG is slow
  - Add SLO alert at 3000ms (current threshold is >5000ms, creating a gap)
  - Implement request queueing and rate limiting

### Incident 2: tool_fail (Error Rate Spike)
- **Scenario**: tool_fail
- **Symptoms Observed**: 
  - Error rate spike: 0% → 100% (all 10 requests failed)
  - HTTP 500 responses for all requests
  - error_breakdown in metrics: `{"RuntimeError": 10}`
  - Request latency dropped to 3-10ms (fast failure)
  - Quality score remained at 0.88 (cached from earlier successful requests)

- **Root Cause (Proved By)**: 
  - Code: `app/mock_rag.py:16` — `raise RuntimeError("Vector store timeout")` when `STATE["tool_fail"] == True`
  - Exception flow: `/chat` → `agent.run()` → `retrieve()` raises RuntimeError → caught in `main.py:88-97` → logged as `request_failed` with `error_type: RuntimeError`
  - Evidence: Logs show `"error_type": "RuntimeError"`, `"detail": "Vector store timeout"`

- **Fix Action**: 
  - `python scripts/inject_incident.py --scenario tool_fail --disable`
  - Verified: metrics show error_breakdown still has RuntimeError but new requests should pass

- **Preventive Measure**: 
  - Implement retry logic with exponential backoff for RAG calls (max 3 retries)
  - Add fallback retrieval source when vector store fails
  - Deploy circuit breaker to prevent cascading failures
  - Monitor error_type distribution in real-time dashboard

### Incident 3: cost_spike (Token/Cost Spike)
- **Scenario**: cost_spike
- **Symptoms Observed**: 
  - Cost per request spike: $0.002 → $0.0033 (1.65× increase)
  - Total accumulated cost: $0.0601 → $0.1303 (after cost_spike requests)
  - Token output increase: 2590 → 8416 total tokens (3.25× multiplier in output)
  - Token ratio: baseline output ~80-180 → spiked output ~320-720 (exact 4× multiplier)
  - Request latency unchanged (~156ms), only cost increased

- **Root Cause (Proved By)**: 
  - Code: `app/mock_llm.py:32` — `output_tokens *= 4` when `STATE["cost_spike"] == True`
  - Cost formula: `output_cost = (output_tokens / 1,000,000) * $15` → multiplying tokens by 4 multiplies cost by 4
  - Evidence: Trace field `tokens_out` = baseline 95 → spiked 380 (3.93× ≈ 4×)

- **Fix Action**: 
  - `python scripts/inject_incident.py --scenario cost_spike --disable`
  - Verified: new requests after disable return to baseline cost $0.002

- **Preventive Measure**: 
  - Set max_tokens limit on LLM calls (e.g., max_tokens=200)
  - Implement real-time token ratio monitoring (alert if output_tokens > 200)
  - Route expensive features to cheaper models
  - Apply prompt caching to reduce token regeneration

---

## 5. Individual Contributions & Evidence

### Member A - Trần Thượng Trường Sơn
- [TASKS_COMPLETED]: Correlation ID middleware implementation (app/middleware.py), Log enrichment with user context binding (app/main.py), PII scrubbing processor activation (app/logging_config.py), Enhanced ChatRequest schema with model field (app/schemas.py) - Validation Score: 100/100
- [EVIDENCE_LINK]: Commit 25ba3d2 (logging & PII foundation), Commit 67f4939 (schema enhancement) - Implementation with 100/100 validation score 

### Member B - Bùi Lâm Tiến
- [TASKS_COMPLETED]: Tracing with Langfuse (app/agent.py), Correlation ID propagation to traces, Enhanced trace metadata (correlation_id, env, tags)
- [EVIDENCE_LINK]: Commit 505b18e () - Implementation with 100/100 validation score (Unique correlation IDs found: 21)

### Member C - Trương Đăng Nghĩa
- [TASKS_COMPLETED]: Implemented SLO monitoring and alert evaluation system. Created app/slo_monitor.py for tracking service level objectives and app/alert_evaluator.py for alert rules. Added two new API endpoints for checking SLO compliance and alert status.
- [EVIDENCE_LINK]: Commit 49e9f00 (SLO monitoring and alert evaluation system)

### Member D - Bùi Thế Công
- [TASKS_COMPLETED]:
  1. **Load Test Baseline** — Executed `python scripts/load_test.py` (10 sequential requests + 5 concurrent requests)
     - Baseline metrics: avg_latency=150ms, p95=151ms, p99=151ms, zero errors
     - Validation score: 100/100 (all required fields present, correlation IDs valid, PII scrubbed)
  2. **Incident 1: rag_slow Debug** — Injected 2.5s latency in RAG retrieval
     - Observed: P95 latency 151ms → 2651ms (17.5× increase)
     - Root cause confirmed: `app/mock_rag.py:18` `time.sleep(2.5)`
     - Evidence: Metrics snapshot before/after, load test output shows ~2657ms per request
  3. **Incident 2: tool_fail Debug** — Injected RuntimeError in RAG retrieval
     - Observed: 100% error rate, error_breakdown={RuntimeError: 10}
     - Root cause confirmed: `app/mock_rag.py:16` `raise RuntimeError("Vector store timeout")`
     - Evidence: HTTP 500 responses, metrics show error_breakdown updated
  4. **Incident 3: cost_spike Debug** — Injected 4× output token multiplier
     - Observed: Cost 3.25× increase ($0.0601 → $0.1303), tokens_out ratio 4×
     - Root cause confirmed: `app/mock_llm.py:32` `output_tokens *= 4`
     - Evidence: Metrics show tokens_in_total=1360, tokens_out_total=8416 (3.25× vs baseline)
  5. **Documentation** — Filled Section 4 (Incident Response) with detailed root cause analysis
  6. **SLO Update** — Recorded observed baseline and spiked metrics in Section 3.2 table

- [EVIDENCE_LINK]:
  - Load test execution: Terminal output shows 20 successful requests with valid correlation IDs
  - Incident injection commands: Verified via health endpoint status changes
  - Metrics before/after: Captured via `curl http://127.0.0.1:8000/metrics` for each scenario. (Link: [screenshots](../screenshots/incident_injection))
  - Commit: `c61e2d1 update blueprint-template.md with load test and incident injection`
  - Commit: `188a8ec complete load test adn incident injection`

### Member E — Trần Ngọc Huy
- [TASKS_COMPLETED]:
  1. Build Observability Dashboard 6 panels bằng Streamlit (`dashboard.py`):
     - Panel 1: Latency P50/P95/P99 (ms) với SLO threshold line ở 3000ms
     - Panel 2: Traffic — donut chart Success vs Error request count
     - Panel 3: Error Rate (%) với SLO threshold 2%
     - Panel 4: Cost Over Time (USD) — total + avg per request, SLO line $2.5/day
     - Panel 5: Tokens In / Out với output/input ratio
     - Panel 6: Quality Score avg vs SLO target 0.75
     - Auto-refresh mỗi 15 giây, hiển thị trực quan thông qua Streamlit Dashboard.
  2. Thu thập và tổ chức toàn bộ bằng chứng screenshots cho nhóm vào `docs/evidence/`
  3. Cập nhật [DASHBOARD_6_PANELS_SCREENSHOT] trong Section 3.2

- [EVIDENCE_LINK]:
  - `dashboard.py` — Streamlit dashboard 6 panels (commit 57dde06)
  - `docs/evidence/04_dashboard_6_panels.png` — Screenshot dashboard đầy đủ 6 panels
  - `docs/evidence/` — Bộ screenshots bằng chứng tổng hợp của nhóm

### Member F - Nông Trung Kiên
- [TASKS_COMPLETED]: Restored missing API routes /slo/status and /alerts/status into app/main.py. Added 4th alert rule low_quality_score to config/alert_rules.yaml, implemented evaluate_low_quality_score_alert() in app/alert_evaluator.py, and wrote corresponding runbook in docs/alerts.md. Authored guide-evidence.md and member-role-status.md tracking all member progress and evidence checklist. Prepared incident response narrative and demo script for group presentation.
- [EVIDENCE_LINK]: guide-evidence.md, app/alert_evaluator.py, config/alert_rules.yaml, docs/alerts.md, member-role-status.md

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
