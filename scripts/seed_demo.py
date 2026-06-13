"""Seed the database with realistic demo data for screenshots and evaluation."""
import sys, os, random, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from manager.database import init_db, get_db
from manager.models import UserCreate, TeamCreate, BudgetAlertCreate
from manager.database import create_user, create_team, create_alert, insert_usage, insert_anomaly, set_license
from manager.anomaly import Anomaly

random.seed(42)

TEAMS = [
    {"name": "Engineering", "monthly_budget": 5000},
    {"name": "Research", "monthly_budget": 3000},
]

USERS = [
    {"name": "Ravi Kumar", "email": "ravi@example.com", "team": "Engineering", "budget": 800},
    {"name": "Priya Sharma", "email": "priya@example.com", "team": "Engineering", "budget": 1200},
    {"name": "Ankit Patel", "email": "ankit@example.com", "team": "Research", "budget": 600},
]

MODELS = ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "claude-3-haiku", "gemini-1.5-pro"]
PROVIDERS = ["openai", "anthropic", "google"]

def main():
    init_db()

    # Clear existing demo data
    with get_db() as c:
        c.execute("DELETE FROM usage_records")
        c.execute("DELETE FROM anomalies")
        c.execute("DELETE FROM budget_alerts")
        c.execute("DELETE FROM users")
        c.execute("DELETE FROM teams")
        c.execute("DELETE FROM license")

    # Create teams
    team_ids = {}
    for t in TEAMS:
        team = create_team(TeamCreate(**t))
        team_ids[t["name"]] = team.id
        print(f"  Team: {t['name']} (id={team.id})")

    # Create users
    user_ids = {}
    for u in USERS:
        user = create_user(UserCreate(
            name=u["name"],
            email=u["email"],
            team_id=team_ids[u["team"]],
            monthly_budget=u["budget"],
        ))
        user_ids[u["name"]] = user.id
        print(f"  User: {u['name']} (id={user.id}, team={u['team']}, budget=Rs.{u['budget']})")

    # Generate 7 days of usage data
    now = datetime.now(timezone.utc)
    total_cost = 0
    for day_offset in range(6, -1, -1):
        day = now - timedelta(days=day_offset)
        for user_name, uid in user_ids.items():
            # Each user makes 3-8 calls per day
            for _ in range(random.randint(3, 8)):
                model = random.choice(MODELS)
                provider = model.split("-")[0]
                tokens_before = random.randint(500, 5000)
                tokens_saved = random.randint(100, tokens_before)
                cost = round(random.uniform(0.005, 0.15), 4)
                total_cost += cost
                timestamp = day + timedelta(
                    hours=random.randint(6, 22),
                    minutes=random.randint(0, 59),
                )
                insert_usage({
                    "timestamp": timestamp.isoformat(),
                    "user_id": uid,
                    "team_id": team_ids[USERS[[n["name"] for n in USERS].index(user_name)]["team"]],
                    "model": model,
                    "provider": provider,
                    "endpoint": "/v1/chat/completions",
                    "tokens_before": tokens_before,
                    "tokens_after": max(0, tokens_before - tokens_saved),
                    "tokens_saved": tokens_saved,
                    "cost_estimated": cost,
                    "cache_hits": random.randint(0, 5),
                })

    print(f"  Generated ~{7 * sum(random.randint(3, 8) for _ in range(3))} usage records across 7 days")

    # Add sample anomalies
    anomalies_data = [
        Anomaly(id=0, timestamp=(now - timedelta(hours=6)).isoformat(),
                metric="cost_estimated", value=2.45, baseline=0.32,
                deviation=6.8, severity="high",
                message="Cost spike: ₹2.45 in last hour (₹0.32 baseline, 6.8x stddev)"),
        Anomaly(id=0, timestamp=(now - timedelta(hours=24)).isoformat(),
                metric="savings_percent", value=12.3, baseline=68.5,
                deviation=4.2, severity="medium",
                message="Compression rate dropped: 12.3% (68.5% baseline)"),
    ]
    for a in anomalies_data:
        insert_anomaly(a)
    print(f"  Added {len(anomalies_data)} sample anomalies")

    # Create a sample Slack alert config
    alert = create_alert(BudgetAlertCreate(
        name="Engineering Budget Alert",
        slack_webhook="https://hooks.slack.com/services/xxx/yyy/zzz",
        threshold_50=True,
        threshold_80=True,
        threshold_100=True,
    ))
    print(f"  Alert: {alert.name} (id={alert.id})")

    print(f"  Demo data seeded: {len(team_ids)} teams, {len(user_ids)} users, total cost Rs.{total_cost:.2f}")

if __name__ == "__main__":
    main()
