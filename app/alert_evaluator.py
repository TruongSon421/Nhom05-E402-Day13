from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import metrics
from .slo_monitor import calculate_error_rate

_PROJECT_ROOT = Path(__file__).parent.parent


def load_alert_rules(config_path: str = "config/alert_rules.yaml") -> list[dict]:
    """
    Load and parse alert rules from YAML file.
    
    Args:
        config_path: Path to alert rules configuration file
        
    Returns:
        List of alert rule dictionaries
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
        ValueError: If required fields are missing
    """
    path = Path(config_path) if Path(config_path).is_absolute() else _PROJECT_ROOT / config_path

    if not path.exists():
        raise FileNotFoundError(f"Alert rules configuration file not found: {config_path}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML: {e}") from e
    
    # Validate required fields
    if not config:
        raise ValueError("Alert rules configuration is empty")
    
    if "alerts" not in config:
        raise ValueError("Missing required field: alerts")
    
    alerts = config["alerts"]
    
    # Validate each alert has required fields
    required_fields = ["name", "severity", "condition", "type", "owner", "runbook"]
    for alert in alerts:
        for field in required_fields:
            if field not in alert:
                raise ValueError(f"Missing required field '{field}' in alert: {alert.get('name', 'unknown')}")
    
    return alerts


def calculate_baseline_cost(metrics_data: dict) -> float:
    """
    Calculate baseline hourly cost for cost spike detection.
    
    Args:
        metrics_data: Current metrics snapshot
        
    Returns:
        Baseline hourly cost in USD
    """
    traffic = metrics_data.get("traffic", 0)
    
    # Use default baseline when traffic < 10
    if traffic < 10:
        return 0.10
    
    # Calculate baseline from total cost
    # Simplified approach: use total accumulated cost as baseline
    total_cost = metrics_data.get("total_cost_usd", 0.0)
    
    # Return total cost as baseline (represents session average)
    return total_cost if total_cost > 0 else 0.10


def evaluate_high_latency_alert(metrics_data: dict, threshold: float = 5000.0) -> dict:
    """
    Evaluate high_latency_p95 alert condition.
    
    Args:
        metrics_data: Current metrics snapshot
        threshold: Latency threshold in milliseconds
        
    Returns:
        Alert evaluation result with firing status and values
    """
    current_value = metrics_data.get("latency_p95", 0.0)
    firing = current_value > threshold
    
    return {
        "firing": firing,
        "current_value": current_value,
        "threshold": threshold
    }


def evaluate_high_error_rate_alert(metrics_data: dict, threshold: float = 5.0) -> dict:
    """
    Evaluate high_error_rate alert condition.
    
    Args:
        metrics_data: Current metrics snapshot
        threshold: Error rate threshold as percentage
        
    Returns:
        Alert evaluation result with firing status and values
    """
    current_value = calculate_error_rate(metrics_data)
    firing = current_value > threshold
    
    return {
        "firing": firing,
        "current_value": current_value,
        "threshold": threshold
    }


def evaluate_cost_spike_alert(
    metrics_data: dict,
    baseline: float,
    multiplier: float = 2.0
) -> dict:
    """
    Evaluate cost_budget_spike alert condition.

    Args:
        metrics_data: Current metrics snapshot
        baseline: Baseline hourly cost
        multiplier: Spike detection multiplier

    Returns:
        Alert evaluation result with firing status and values
    """
    # Calculate current hourly cost rate
    avg_cost = metrics_data.get("avg_cost_usd", 0.0)
    traffic = metrics_data.get("traffic", 0)

    # Estimate current hourly cost (simplified)
    current_hourly_cost = avg_cost * traffic if traffic > 0 else 0.0

    # Calculate threshold
    threshold = baseline * multiplier

    # Check if current cost exceeds threshold
    firing = current_hourly_cost > threshold

    return {
        "firing": firing,
        "current_value": round(current_hourly_cost, 4),
        "threshold": round(threshold, 4)
    }


def evaluate_low_quality_score_alert(metrics_data: dict, threshold: float = 0.60) -> dict:
    """
    Evaluate low_quality_score alert condition.

    Fires when the rolling average quality score drops below the threshold,
    indicating model degradation or poor retrieval quality.

    Args:
        metrics_data: Current metrics snapshot
        threshold: Minimum acceptable quality score (default 0.60)

    Returns:
        Alert evaluation result with firing status and values
    """
    current_value = metrics_data.get("quality_avg", 1.0)
    firing = current_value < threshold

    return {
        "firing": firing,
        "current_value": round(current_value, 4),
        "threshold": threshold,
    }


def get_alert_status() -> dict:
    """
    Main entry point for /alerts/status endpoint.
    
    Returns:
        JSON-serializable dictionary with alert status
    """
    # Load alert rules
    alert_rules = load_alert_rules()
    
    # Fetch current metrics
    metrics_data = metrics.snapshot()
    
    # Calculate baseline cost
    baseline_cost = calculate_baseline_cost(metrics_data)
    
    # Evaluate each alert
    alert_results = []
    
    for rule in alert_rules:
        alert_name = rule["name"]
        
        # Evaluate based on alert name
        if alert_name == "high_latency_p95":
            evaluation = evaluate_high_latency_alert(metrics_data)
        elif alert_name == "high_error_rate":
            evaluation = evaluate_high_error_rate_alert(metrics_data)
        elif alert_name == "cost_budget_spike":
            evaluation = evaluate_cost_spike_alert(metrics_data, baseline_cost)
        elif alert_name == "low_quality_score":
            evaluation = evaluate_low_quality_score_alert(metrics_data)
        else:
            # Unknown alert type, skip
            continue
        
        # Build alert result
        alert_results.append({
            "name": alert_name,
            "severity": rule["severity"],
            "firing": evaluation["firing"],
            "current_value": evaluation["current_value"],
            "threshold": evaluation["threshold"],
            "runbook": rule["runbook"]
        })
    
    # Count firing alerts
    firing_count = sum(1 for alert in alert_results if alert["firing"])
    
    # Return formatted response
    return {
        "firing_count": firing_count,
        "baseline_hourly_cost_usd": round(baseline_cost, 4),
        "alerts": alert_results
    }
