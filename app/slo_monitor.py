from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import metrics


def calculate_error_rate(metrics_data: dict) -> float:
    """
    Calculate error rate percentage from metrics snapshot.
    
    Args:
        metrics_data: Metrics snapshot from metrics.snapshot()
        
    Returns:
        Error rate as percentage (0.0 to 100.0)
    """
    traffic = metrics_data.get("traffic", 0)
    error_breakdown = metrics_data.get("error_breakdown", {})
    
    # Handle zero traffic case
    if traffic == 0:
        return 0.0
    
    # Calculate total errors
    total_errors = sum(error_breakdown.values())
    
    # Calculate error rate percentage
    error_rate = (total_errors / traffic) * 100
    
    # Round to two decimal places
    return round(error_rate, 2)


def calculate_sli_compliance(
    sli_name: str,
    current_value: float,
    objective: float,
    comparison: str
) -> bool:
    """
    Determine if an SLI meets its objective.
    
    Args:
        sli_name: Name of the SLI
        current_value: Current measured value
        objective: Target value from config
        comparison: Direction of comparison ("less_than" or "greater_than")
        
    Returns:
        True if SLI meets objective, False otherwise
    """
    if comparison == "less_than":
        return current_value <= objective
    elif comparison == "greater_than":
        return current_value >= objective
    else:
        raise ValueError(f"Invalid comparison type: {comparison}")


_PROJECT_ROOT = Path(__file__).parent.parent


def load_slo_config(config_path: str = "config/slo.yaml") -> dict:
    """
    Load and parse SLO configuration from YAML file.
    
    Args:
        config_path: Path to SLO configuration file
        
    Returns:
        Parsed SLO configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
        ValueError: If required fields are missing
    """
    path = Path(config_path) if Path(config_path).is_absolute() else _PROJECT_ROOT / config_path

    if not path.exists():
        raise FileNotFoundError(f"SLO configuration file not found: {config_path}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML: {e}") from e
    
    # Validate required fields
    if not config:
        raise ValueError("SLO configuration is empty")
    
    if "service" not in config:
        raise ValueError("Missing required field: service")
    
    if "window" not in config:
        raise ValueError("Missing required field: window")
    
    if "slis" not in config:
        raise ValueError("Missing required field: slis")
    
    # Validate each SLI has required fields
    for sli_name, sli_config in config["slis"].items():
        if "objective" not in sli_config:
            raise ValueError(f"Missing required field 'objective' for SLI: {sli_name}")
        if "target" not in sli_config:
            raise ValueError(f"Missing required field 'target' for SLI: {sli_name}")
    
    return config


def calculate_compliance(metrics_data: dict, slo_config: dict) -> dict:
    """
    Calculate compliance status for all SLIs.
    
    Args:
        metrics_data: Current metrics snapshot
        slo_config: SLO configuration
        
    Returns:
        Dictionary with compliance data for each SLI
    """
    slis = slo_config["slis"]
    compliance_results = {}
    
    # Calculate compliance for latency_p95_ms
    if "latency_p95_ms" in slis:
        sli_config = slis["latency_p95_ms"]
        current_value = metrics_data.get("latency_p95", 0.0)
        objective = sli_config["objective"]
        target_pct = sli_config["target"]
        compliant = calculate_sli_compliance("latency_p95_ms", current_value, objective, "less_than")
        
        compliance_results["latency_p95_ms"] = {
            "current_value": current_value,
            "objective": objective,
            "target_pct": target_pct,
            "compliant": compliant
        }
    
    # Calculate compliance for error_rate_pct
    if "error_rate_pct" in slis:
        sli_config = slis["error_rate_pct"]
        current_value = calculate_error_rate(metrics_data)
        objective = sli_config["objective"]
        target_pct = sli_config["target"]
        compliant = calculate_sli_compliance("error_rate_pct", current_value, objective, "less_than")
        
        compliance_results["error_rate_pct"] = {
            "current_value": current_value,
            "objective": objective,
            "target_pct": target_pct,
            "compliant": compliant
        }
    
    # Calculate compliance for daily_cost_usd
    if "daily_cost_usd" in slis:
        sli_config = slis["daily_cost_usd"]
        current_value = metrics_data.get("total_cost_usd", 0.0)
        objective = sli_config["objective"]
        target_pct = sli_config["target"]
        compliant = calculate_sli_compliance("daily_cost_usd", current_value, objective, "less_than")
        
        compliance_results["daily_cost_usd"] = {
            "current_value": current_value,
            "objective": objective,
            "target_pct": target_pct,
            "compliant": compliant
        }
    
    # Calculate compliance for quality_score_avg
    if "quality_score_avg" in slis:
        sli_config = slis["quality_score_avg"]
        current_value = metrics_data.get("quality_avg", 0.0)
        objective = sli_config["objective"]
        target_pct = sli_config["target"]
        compliant = calculate_sli_compliance("quality_score_avg", current_value, objective, "greater_than")
        
        compliance_results["quality_score_avg"] = {
            "current_value": current_value,
            "objective": objective,
            "target_pct": target_pct,
            "compliant": compliant
        }
    
    return compliance_results


def get_slo_status() -> dict:
    """
    Main entry point for /slo/status endpoint.
    
    Returns:
        JSON-serializable dictionary with SLO status
    """
    # Load SLO configuration
    slo_config = load_slo_config()
    
    # Fetch current metrics
    metrics_data = metrics.snapshot()
    
    # Calculate compliance for all SLIs
    compliance_results = calculate_compliance(metrics_data, slo_config)
    
    # Calculate overall compliance percentage
    total_slis = len(compliance_results)
    compliant_slis = sum(1 for sli in compliance_results.values() if sli["compliant"])
    overall_compliance_pct = round((compliant_slis / total_slis) * 100, 2) if total_slis > 0 else 0.0
    
    # Return formatted response
    return {
        "service": slo_config["service"],
        "window": slo_config["window"],
        "overall_compliance_pct": overall_compliance_pct,
        "slis": compliance_results
    }
