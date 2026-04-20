#!/usr/bin/env python3
"""Cost optimization analysis script.

Bonus item: +3 điểm – Tối ưu chi phí (số liệu trước/sau).

Usage:
    python scripts/cost_report.py

Reads data/logs.jsonl and prints a before/after cost breakdown,
identifies expensive features/models, and suggests optimizations.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

LOG_PATH = Path("data/logs.jsonl")
CHEAP_MODEL = "claude-haiku-4-5"
EXPENSIVE_MODELS = {"claude-opus-4-5", "claude-sonnet-4-5"}


def load_response_logs() -> list[dict]:
    if not LOG_PATH.exists():
        print(f"[!] Log file not found: {LOG_PATH}")
        return []
    events = []
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            try:
                ev = json.loads(line)
                if ev.get("event") == "response_sent":
                    events.append(ev)
            except json.JSONDecodeError:
                continue
    return events


def analyse(logs: list[dict]) -> None:
    if not logs:
        print("No response_sent events found. Run load_test.py first.")
        return

    total_cost = sum(e.get("cost_usd", 0) for e in logs)
    total_tokens_in = sum(e.get("tokens_in", 0) for e in logs)
    total_tokens_out = sum(e.get("tokens_out", 0) for e in logs)
    avg_latency = mean(e.get("latency_ms", 0) for e in logs)
    n = len(logs)

    print("=" * 60)
    print("  COST OPTIMIZATION REPORT  –  Day 13 Observability Lab")
    print("=" * 60)
    print(f"\n{'Requests analysed':<30} {n}")
    print(f"{'Total cost (USD)':<30} ${total_cost:.4f}")
    print(f"{'Avg cost per request':<30} ${total_cost/n:.4f}")
    print(f"{'Avg latency':<30} {avg_latency:.1f}ms")
    print(f"{'Tokens in (total)':<30} {total_tokens_in}")
    print(f"{'Tokens out (total)':<30} {total_tokens_out}")
    print(f"{'Output/Input ratio':<30} {total_tokens_out/max(total_tokens_in,1):.2f}x")

    # Per-model breakdown
    by_model: dict[str, list[dict]] = defaultdict(list)
    for e in logs:
        model = e.get("model", "unknown")
        by_model[model].append(e)

    if len(by_model) > 1:
        print("\n-- Per-model breakdown ------------------------------------------")
        for model, evs in sorted(by_model.items()):
            m_cost = sum(e.get("cost_usd", 0) for e in evs)
            m_lat = mean(e.get("latency_ms", 0) for e in evs)
            print(f"  {model:<35} n={len(evs):>3}  cost=${m_cost:.4f}  avg_lat={m_lat:.0f}ms")

    # Per-feature breakdown
    by_feature: dict[str, list[dict]] = defaultdict(list)
    for e in logs:
        feat = e.get("feature", "unknown")
        by_feature[feat].append(e)

    print("\n-- Per-feature breakdown ----------------------------------------")
    for feat, evs in sorted(by_feature.items(), key=lambda x: -sum(e.get("cost_usd", 0) for e in x[1])):
        f_cost = sum(e.get("cost_usd", 0) for e in evs)
        f_pct = f_cost / total_cost * 100 if total_cost else 0
        print(f"  {feat:<30} cost=${f_cost:.4f} ({f_pct:.1f}% of total)")

    # Optimization recommendations
    print("\n-- Optimization recommendations ---------------------------------")
    expensive_reqs = [e for e in logs if e.get("tokens_out", 0) > 200]
    if expensive_reqs:
        avg_exp_cost = mean(e.get("cost_usd", 0) for e in expensive_reqs)
        print(f"  [!] {len(expensive_reqs)} requests with tokens_out > 200 (avg ${avg_exp_cost:.4f}/req)")
        print(f"      -> Set max_tokens=200 to cap output: saves ~{len(expensive_reqs)*avg_exp_cost*0.5:.4f} USD")

    ratio = total_tokens_out / max(total_tokens_in, 1)
    if ratio > 1.5:
        print(f"  [!] Output/Input ratio = {ratio:.2f}x (high) - consider shorter prompts")
        print(f"      -> Reducing prompt size by 30% could save ~${total_cost*0.3:.4f} USD")

    baseline_cost_per_req = total_cost / n
    haiku_cost_per_req = baseline_cost_per_req * 0.25  # Haiku ~4x cheaper
    print(f"\n  [OK] Routing non-critical features to {CHEAP_MODEL}:")
    print(f"       Current avg: ${baseline_cost_per_req:.4f}/req -> Haiku est: ${haiku_cost_per_req:.4f}/req")
    print(f"       Potential saving (50% traffic on Haiku): ${(baseline_cost_per_req - haiku_cost_per_req)*n*0.5:.4f} USD")

    print("\n  [OK] Already implemented in this lab:")
    print("       - PII scrubbing prevents re-processing sensitive data")
    print("       - SHA-256 user_id hashing avoids full ID in every log line")
    print("       - Langfuse usage_details tracks tokens per span for cost attribution")
    print()
    print("=" * 60)


if __name__ == "__main__":
    logs = load_response_logs()
    analyse(logs)
