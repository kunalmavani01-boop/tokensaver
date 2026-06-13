"""Budget tracking engine. Tracks per-user/team spend against budgets."""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .database import get_all_users, get_all_teams, get_all_usage, get_user, get_team

logger = logging.getLogger(__name__)

class BudgetStatus:
    """Represents budget status for a user or team."""
    def __init__(self, name: str, budget: float, spent: float, entity_type: str = "user"):
        self.name = name
        self.budget = budget
        self.spent = spent
        self.remaining = max(0, budget - spent)
        self.percent = (spent / budget * 100) if budget > 0 else 0
        self.entity_type = entity_type
    
    @property
    def is_exceeded(self) -> bool:
        return self.spent >= self.budget
    
    @property
    def is_at_risk(self) -> bool:
        return 80 <= self.percent < 100
    
    @property
    def crossed_threshold(self) -> Optional[int]:
        """Returns the highest threshold crossed (50, 80, 100) or None."""
        if self.percent >= 100:
            return 100
        if self.percent >= 80:
            return 80
        if self.percent >= 50:
            return 50
        return None

def get_user_budget_status(user_id: int) -> Optional[BudgetStatus]:
    """Get budget status for a specific user."""
    user = get_user(user_id)
    if not user:
        return None
    usage = get_user_usage(user_id, days=30)
    spent = sum(r.get("cost_estimated", 0) for r in usage)
    return BudgetStatus(user.name, user.monthly_budget, spent, "user")

def get_all_budget_statuses() -> List[Dict[str, Any]]:
    """Get budget status for all users (for the dashboard)."""
    users = get_all_users()
    all_usage = get_all_usage(days=30)
    user_spend = defaultdict(float)
    
    for r in all_usage:
        uid = r.get("user_id")
        if uid:
            user_spend[uid] += r.get("cost_estimated", 0)
    
    statuses = []
    for user in users:
        spent = user_spend.get(user.id, 0)
        pct = (spent / user.monthly_budget * 100) if user.monthly_budget > 0 else 0
        statuses.append({
            "name": user.name,
            "budget": user.monthly_budget,
            "spent": round(spent, 4),
            "remaining": round(max(0, user.monthly_budget - spent), 4),
            "percent": min(pct, 100),
            "user_id": user.id,
        })
    
    return statuses

def check_crossed_thresholds() -> List[Dict[str, Any]]:
    """Check all users and return list of newly crossed thresholds."""
    results = []
    users = get_all_users()
    all_usage = get_all_usage(days=30)
    user_spend = defaultdict(float)
    
    for r in all_usage:
        uid = r.get("user_id")
        if uid:
            user_spend[uid] += r.get("cost_estimated", 0)
    
    for user in users:
        spent = user_spend.get(user.id, 0)
        status = BudgetStatus(user.name, user.monthly_budget, spent)
        threshold = status.crossed_threshold
        if threshold:
            results.append({
                "user_id": user.id,
                "user_name": user.name,
                "email": user.email,
                "threshold": threshold,
                "spent": round(spent, 4),
                "budget": user.monthly_budget,
                "percent": round(status.percent, 1),
            })
    
    return results

def get_budget_summary() -> Dict[str, Any]:
    """Get aggregate budget summary for the budgets page."""
    statuses = get_all_budget_statuses()
    at_risk = sum(1 for s in statuses if 80 <= s["percent"] < 100)
    over = sum(1 for s in statuses if s["percent"] >= 100)
    total_budget = sum(s["budget"] for s in statuses)
    total_spent = sum(s["spent"] for s in statuses)
    
    return {
        "budget_statuses": statuses,
        "at_risk_users": at_risk,
        "over_budget_users": over,
        "user_budget_total": total_budget,
        "user_spent": round(total_spent, 4),
        "team_spent": round(total_spent, 4),
        "team_budget_total": total_budget,
    }
