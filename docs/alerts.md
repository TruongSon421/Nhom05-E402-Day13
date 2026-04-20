# Alert Rules and Runbooks

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95_ms > 5000 for 30m`
- Impact: tail latency breaches SLO
- First checks:
  1. Open top slow traces in the last 1h
  2. Compare RAG span vs LLM span
  3. Check if incident toggle `rag_slow` is enabled
- Mitigation:
  - truncate long queries
  - fallback retrieval source
  - lower prompt size

## 2. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 5 for 5m`
- Impact: users receive failed responses
- First checks:
  1. Group logs by `error_type`
  2. Inspect failed traces
  3. Determine whether failures are LLM, tool, or schema related
- Mitigation:
  - rollback latest change
  - disable failing tool
  - retry with fallback model

## 3. Cost budget spike
- Severity: P2
- Trigger: `hourly_cost_usd > 2x_baseline for 15m`
- Impact: burn rate exceeds budget
- First checks:
  1. Split traces by feature and model
  2. Compare tokens_in/tokens_out
  3. Check if `cost_spike` incident was enabled
- Mitigation:
  - shorten prompts
  - route easy requests to cheaper model
  - apply prompt cache

## 4. Low quality score
- Severity: P3
- Trigger: `quality_score_avg < 0.60 for 10m`
- Impact: model responses degrade below acceptable threshold; user satisfaction affected
- First checks:
  1. Check `quality_avg` in `/metrics` – confirm sustained drop, not a single outlier
  2. Open Langfuse traces filtered by low quality spans
  3. Compare RAG `doc_count` in trace metadata – low doc count may indicate retrieval failure
  4. Check if `rag_slow` or `cost_spike` incident toggles are enabled
- Mitigation:
  - Re-index or warm RAG vector store
  - Increase `doc_count` retrieval limit in `mock_rag.py`
  - Switch to a higher-quality model tier for affected feature
  - If systematic: disable affected feature endpoint and page on-call

