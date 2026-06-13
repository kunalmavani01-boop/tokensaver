"""Anomaly detection for LLM spend patterns.

Uses a simple rolling window approach: compare the last hour's spend
against the mean + 3*stddev of the previous 24 hours.
"""
import logging
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from .database import get_recent_snapshots, get_all_usage, insert_anomaly, get_recent_anomalies
from .models import Anomaly

logger = logging.getLogger(__name__)

def detect_anomalies() -> List[Anomaly]:
    """Run anomaly detection and store results. Returns list of new anomalies."""
    anomalies = []
    now = datetime.now(timezone.utc).isoformat()
    
    # Get recent usage (last 24h for baseline, last 1h for current window)
    all_usage = get_all_usage(days=1)
    
    if not all_usage or len(all_usage) < 5:
        logger.debug("Not enough data for anomaly detection")
        return []
    
    # Split into current (last 1 hour) and baseline (rest)
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    
    current_window = [r for r in all_usage if r.get("timestamp", "") >= one_hour_ago]
    baseline = [r for r in all_usage if r.get("timestamp", "") < one_hour_ago]
    
    if not current_window or not baseline:
        return []
    
    # --- Cost anomaly ---
    current_cost = sum(r.get("cost_estimated", 0) for r in current_window)
    baseline_costs = [r.get("cost_estimated", 0) for r in baseline]
    
    if len(baseline_costs) >= 5:
        mean = statistics.mean(baseline_costs)
        stdev = statistics.stdev(baseline_costs) if len(baseline_costs) > 1 else 0
        
        if stdev > 0 and current_cost > mean + (3 * stdev):
            deviation = (current_cost - mean) / stdev if stdev > 0 else 0
            severity = "high" if deviation > 5 else "medium"
            anomaly = Anomaly(
                id=0,
                timestamp=now,
                metric="cost_estimated",
                value=current_cost,
                baseline=mean,
                deviation=round(deviation, 2),
                severity=severity,
                message=f"Cost spike: Rs.{current_cost:.4f} in last hour (Rs.{mean:.4f} baseline, {deviation:.1f}x stddev)"
            )
            insert_anomaly(anomaly)
            anomalies.append(anomaly)
            logger.warning("Cost anomaly detected: %s", anomaly.message)
    
    # --- Token savings drop anomaly ---
    snapshots = get_recent_snapshots(hours=24)
    if len(snapshots) >= 10:
        recent_snapshots = [s for s in snapshots if s.get("timestamp", "") >= one_hour_ago]
        baseline_snapshots = [s for s in snapshots if s.get("timestamp", "") < one_hour_ago]
        
        if recent_snapshots and baseline_snapshots:
            current_savings = sum(s.get("savings_percent", 0) or 0 for s in recent_snapshots) / len(recent_snapshots)
            baseline_savings = [s.get("savings_percent", 0) or 0 for s in baseline_snapshots]
            
            if len(baseline_savings) >= 5:
                b_mean = statistics.mean(baseline_savings)
                b_stdev = statistics.stdev(baseline_savings) if len(baseline_savings) > 1 else 0
                
                if b_stdev > 0 and current_savings < b_mean - (2 * b_stdev):
                    deviation = (b_mean - current_savings) / b_stdev if b_stdev > 0 else 0
                    anomaly = Anomaly(
                        id=0,
                        timestamp=now,
                        metric="savings_percent",
                        value=current_savings,
                        baseline=b_mean,
                        deviation=round(deviation, 2),
                        severity="medium",
                        message=f"Compression rate dropped: {current_savings:.1f}% ({b_mean:.1f}% baseline)"
                    )
                    insert_anomaly(anomaly)
                    anomalies.append(anomaly)
                    logger.warning("Savings anomaly detected: %s", anomaly.message)
    
    return anomalies

def get_anomalies(hours: int = 48) -> List[Anomaly]:
    """Get recent anomalies from the database."""
    return get_recent_anomalies(hours=hours)
