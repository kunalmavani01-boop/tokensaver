"""CSV report generation for TokenSaver."""
import csv
import io
import logging
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from .database import get_all_users, get_all_teams, get_all_usage, get_recent_anomalies, get_total_savings

logger = logging.getLogger(__name__)

def generate_usage_csv(days: int = 30, team_id: Optional[int] = None) -> str:
    """Generate a CSV string of usage records."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Model", "Provider", "Endpoint", "Tokens Before", "Tokens After", 
                     "Tokens Saved", "Cost Estimated", "Cache Hits", "User ID", "Team ID"])
    
    records = get_all_usage(days=days)
    for r in records:
        if team_id and r.get("team_id") != team_id:
            continue
        writer.writerow([
            r.get("timestamp", ""),
            r.get("model", ""),
            r.get("provider", ""),
            r.get("endpoint", ""),
            r.get("tokens_before", 0),
            r.get("tokens_after", 0),
            r.get("tokens_saved", 0),
            r.get("cost_estimated", 0),
            r.get("cache_hits", 0),
            r.get("user_id", ""),
            r.get("team_id", ""),
        ])
    
    return output.getvalue()

def generate_budget_csv() -> str:
    """Generate CSV comparing budget vs actual spend per user."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User", "Email", "Team", "Monthly Budget", "Current Spend", 
                     "Remaining", "Usage %", "Status"])
    
    users = get_all_users()
    all_usage = get_all_usage(days=30)
    
    for user in users:
        user_spend = sum(r.get("cost_estimated", 0) for r in all_usage 
                        if r.get("user_id") == user.id)
        budget = user.monthly_budget
        remaining = budget - user_spend
        pct = (user_spend / budget * 100) if budget > 0 else 0
        
        if pct >= 100:
            status = "OVER BUDGET"
        elif pct >= 80:
            status = "AT RISK"
        else:
            status = "OK"
        
        writer.writerow([
            user.name, user.email, user.team_id or "",
            budget, round(user_spend, 4), round(remaining, 4),
            round(pct, 1), status
        ])
    
    return output.getvalue()

def generate_anomalies_csv(hours: int = 48) -> str:
    """Generate CSV of recent anomalies."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Metric", "Value", "Baseline", "Deviation", "Severity", "Message"])
    
    anomalies = get_recent_anomalies(hours=hours)
    for a in anomalies:
        writer.writerow([
            a.timestamp, a.metric, a.value, a.baseline, a.deviation,
            a.severity, a.message
        ])
    
    return output.getvalue()

def get_dashboard_stats():
    """Aggregate stats for the dashboard overview."""
    users = get_all_users()
    teams = get_all_teams()
    all_usage = get_all_usage(days=30)
    total_savings = sum(r.get("cost_estimated", 0) for r in all_usage)
    
    # Per-user aggregates
    user_spend = defaultdict(float)
    for r in all_usage:
        uid = r.get("user_id")
        if uid:
            user_spend[uid] += r.get("cost_estimated", 0)
    
    top_users = []
    for user in users:
        cost = user_spend.get(user.id, 0)
        if cost > 0:
            top_users.append({"name": user.name, "cost": cost})
    top_users.sort(key=lambda x: x["cost"], reverse=True)
    top_users = top_users[:5]
    
    # Per-user daily spend (for sparkline charts)
    user_daily = defaultdict(lambda: defaultdict(float))
    for r in all_usage:
        uid = r.get("user_id")
        if uid:
            day = r.get("timestamp", "")[:10]
            user_daily[uid][day] += r.get("cost_estimated", 0)
    
    user_chart_data = []
    for user in users[:5]:
        if user.id in user_daily:
            costs = [user_daily[user.id].get(
                (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat(), 0
            ) for i in range(6, -1, -1)]
            user_chart_data.append({"name": user.name, "data": costs})
    
    # Model breakdown
    from .database import get_model_breakdown
    models = get_model_breakdown()
    top_model = models[0]["model"] if models else "—"
    model_count = len(models)
    
    # Budget statuses
    budget_statuses = []
    at_risk = 0
    over_budget = 0
    total_team_budget = sum(t.monthly_budget for t in teams) if teams else 0
    total_user_spend = sum(user_spend.values())
    total_user_budget = sum(u.monthly_budget for u in users) if users else 0
    
    for user in users:
        spent = user_spend.get(user.id, 0)
        pct = (spent / user.monthly_budget * 100) if user.monthly_budget > 0 else 0
        budget_statuses.append({
            "name": user.name,
            "budget": user.monthly_budget,
            "spent": spent,
            "remaining": user.monthly_budget - spent,
            "percent": min(pct, 100),
        })
        if pct >= 100:
            over_budget += 1
        elif pct >= 80:
            at_risk += 1
    
    # Chart data (last 7 days)
    chart_days = []
    chart_costs = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        chart_days.append(day.strftime("%b %d"))
        day_cost = sum(r.get("cost_estimated", 0) for r in all_usage
                      if r.get("timestamp", "").startswith(day.isoformat()))
        chart_costs.append(round(day_cost, 4))
    
    return {
        "total_savings": total_savings,
        "user_count": len(users),
        "team_count": len(teams),
        "top_users": top_users,
        "recent_records": all_usage[:20],
        "budget_statuses": budget_statuses,
        "at_risk_users": at_risk,
        "over_budget_users": over_budget,
        "chart_labels": str(chart_days),
        "chart_data": str(chart_costs),
        "user_spent": total_user_spend,
        "user_budget_total": total_user_budget,
        "team_spent": total_user_spend,
        "team_budget_total": total_team_budget,
        "model_count": model_count,
        "top_model": top_model,
        "user_chart_data": user_chart_data,
    }
