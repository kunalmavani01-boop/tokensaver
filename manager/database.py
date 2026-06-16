import sqlite3
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import config
from .models import User, UserCreate, Team, TeamCreate, UsageRecord, BudgetAlert, BudgetAlertCreate, HeadroomSnapshot, Anomaly

DB_PATH = config.db_path

def init_db():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            team_id INTEGER,
            monthly_budget REAL DEFAULT 100.0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monthly_budget REAL DEFAULT 1000.0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS usage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id INTEGER,
            team_id INTEGER,
            model TEXT,
            provider TEXT,
            endpoint TEXT,
            tokens_before INTEGER DEFAULT 0,
            tokens_after INTEGER DEFAULT 0,
            tokens_saved INTEGER DEFAULT 0,
            cost_estimated REAL DEFAULT 0.0,
            cache_hits INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        );
        
        CREATE TABLE IF NOT EXISTS budget_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER,
            team_id INTEGER,
            slack_webhook TEXT,
            email TEXT,
            threshold_50 INTEGER DEFAULT 0,
            threshold_80 INTEGER DEFAULT 1,
            threshold_100 INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (team_id) REFERENCES teams(id)
        );
        
        CREATE TABLE IF NOT EXISTS license (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            customer_email TEXT NOT NULL,
            max_users INTEGER DEFAULT 5,
            expires_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        
        CREATE TABLE IF NOT EXISTS headroom_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_requests INTEGER DEFAULT 0,
            tokens_saved INTEGER DEFAULT 0,
            savings_percent REAL DEFAULT 0.0,
            cache_hits INTEGER DEFAULT 0,
            cache_misses INTEGER DEFAULT 0,
            total_cost_saved REAL DEFAULT 0.0
        );
        
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL DEFAULT 0.0,
            baseline REAL DEFAULT 0.0,
            deviation REAL DEFAULT 0.0,
            severity TEXT DEFAULT 'medium',
            message TEXT DEFAULT ''
        );
        
        CREATE TABLE IF NOT EXISTS proxy_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cache_hits INTEGER DEFAULT 0,
            cache_misses INTEGER DEFAULT 0,
            tokens_saved INTEGER DEFAULT 0,
            cost_saved REAL DEFAULT 0.0,
            requests_total INTEGER DEFAULT 0
        );
    """)
    
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    """Context manager for database cursor."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()

# --- User CRUD ---

def create_user(user: UserCreate) -> User:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    api_key = f"ts_{uuid.uuid4().hex[:24]}"
    c.execute(
        "INSERT INTO users (name, email, api_key, team_id, monthly_budget) VALUES (?, ?, ?, ?, ?)",
        (user.name, user.email, api_key, user.team_id, user.monthly_budget)
    )
    user_id = c.lastrowid
    conn.commit()
    conn.close()
    return get_user(user_id)

def get_user(user_id: int) -> Optional[User]:
    with get_db() as c:
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return User(**dict(row))
    return None

def get_user_by_email(email: str) -> Optional[User]:
    with get_db() as c:
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        if row:
            return User(**dict(row))
    return None

def get_user_by_api_key(api_key: str) -> Optional[User]:
    with get_db() as c:
        c.execute("SELECT * FROM users WHERE api_key = ?", (api_key,))
        row = c.fetchone()
        if row:
            return User(**dict(row))
    return None

def get_all_users() -> List[User]:
    with get_db() as c:
        c.execute("SELECT * FROM users ORDER BY name")
        return [User(**dict(row)) for row in c.fetchall()]

def delete_user(user_id: int) -> bool:
    with get_db() as c:
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return c.rowcount > 0

# --- Team CRUD ---

def create_team(team: TeamCreate) -> Team:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT INTO teams (name, monthly_budget) VALUES (?, ?)",
              (team.name, team.monthly_budget))
    team_id = c.lastrowid
    conn.commit()
    conn.close()
    return get_team(team_id)

def get_team(team_id: int) -> Optional[Team]:
    with get_db() as c:
        c.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = c.fetchone()
        if row:
            return Team(**dict(row))
    return None

def get_all_teams() -> List[Team]:
    with get_db() as c:
        c.execute("SELECT * FROM teams ORDER BY name")
        return [Team(**dict(row)) for row in c.fetchall()]

# --- Usage Records ---

def insert_usage(record: Dict[str, Any]):
    with get_db() as c:
        c.execute(
            """INSERT INTO usage_records 
               (timestamp, user_id, team_id, model, provider, endpoint, tokens_before, tokens_after, tokens_saved, cost_estimated, cache_hits)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.get('timestamp', datetime.now(timezone.utc).isoformat()),
             record.get('user_id'), record.get('team_id'),
             record.get('model'), record.get('provider'), record.get('endpoint'),
             record.get('tokens_before', 0), record.get('tokens_after', 0),
             record.get('tokens_saved', 0), record.get('cost_estimated', 0.0),
             record.get('cache_hits', 0))
        )

def resolve_usage_identity(
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    api_key: Optional[str] = None,
    team_id: Optional[int] = None,
) -> Dict[str, Optional[int]]:
    resolved_user = None
    normalized_user_id = None
    normalized_team_id = None

    if user_id not in (None, ""):
        try:
            normalized_user_id = int(user_id)
        except (TypeError, ValueError):
            normalized_user_id = None
    if team_id not in (None, ""):
        try:
            normalized_team_id = int(team_id)
        except (TypeError, ValueError):
            normalized_team_id = None

    if normalized_user_id is not None:
        resolved_user = get_user(normalized_user_id)
    elif email:
        resolved_user = get_user_by_email(email)
    elif api_key:
        resolved_user = get_user_by_api_key(api_key)

    resolved_team_id = normalized_team_id
    if resolved_user:
        resolved_team_id = resolved_user.team_id

    return {
        "user_id": resolved_user.id if resolved_user else normalized_user_id,
        "team_id": resolved_team_id,
    }

def get_user_usage(user_id: int, days: int = 30) -> List[Dict]:
    with get_db() as c:
        c.execute(
            """SELECT * FROM usage_records 
               WHERE user_id = ? AND timestamp >= datetime('now', ? || ' days')
               ORDER BY timestamp DESC""",
            (user_id, f'-{days}')
        )
        return [dict(row) for row in c.fetchall()]

def get_team_usage(team_id: int, days: int = 30) -> List[Dict]:
    with get_db() as c:
        c.execute(
            """SELECT * FROM usage_records 
               WHERE team_id = ? AND timestamp >= datetime('now', ? || ' days')
               ORDER BY timestamp DESC""",
            (team_id, f'-{days}')
        )
        return [dict(row) for row in c.fetchall()]

def get_all_usage(days: int = 30) -> List[Dict]:
    with get_db() as c:
        c.execute(
            """SELECT * FROM usage_records 
               WHERE timestamp >= datetime('now', ? || ' days')
               ORDER BY timestamp DESC LIMIT 500""",
            (f'-{days}',)
        )
        return [dict(row) for row in c.fetchall()]

# --- Budget Alerts ---

def create_alert(alert: BudgetAlertCreate) -> BudgetAlert:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute(
        """INSERT INTO budget_alerts (name, user_id, team_id, slack_webhook, email, threshold_50, threshold_80, threshold_100)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (alert.name, alert.user_id, alert.team_id, alert.slack_webhook,
         alert.email, int(alert.threshold_50), int(alert.threshold_80), int(alert.threshold_100))
    )
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    return get_alert(alert_id)

def get_alert(alert_id: int) -> Optional[BudgetAlert]:
    with get_db() as c:
        c.execute("SELECT * FROM budget_alerts WHERE id = ?", (alert_id,))
        row = c.fetchone()
        if row:
            return BudgetAlert(**dict(row))
    return None

def get_all_alerts() -> List[BudgetAlert]:
    with get_db() as c:
        c.execute("SELECT * FROM budget_alerts ORDER BY name")
        return [BudgetAlert(**dict(row)) for row in c.fetchall()]

# --- License ---

def get_license() -> Optional[Dict]:
    with get_db() as c:
        c.execute("SELECT * FROM license ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
            return dict(row)
    return None

def set_license(key: str, email: str, max_users: int = 5):
    with get_db() as c:
        c.execute("DELETE FROM license")
        c.execute(
            "INSERT INTO license (license_key, customer_email, max_users) VALUES (?, ?, ?)",
            (key, email, max_users)
        )

# --- Headroom Snapshots ---

def insert_snapshot(snapshot: HeadroomSnapshot):
    with get_db() as c:
        c.execute(
            """INSERT INTO headroom_snapshots (timestamp, total_requests, tokens_saved, savings_percent, cache_hits, cache_misses, total_cost_saved)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (snapshot.timestamp, snapshot.total_requests, snapshot.tokens_saved,
             snapshot.savings_percent, snapshot.cache_hits, snapshot.cache_misses,
             snapshot.total_cost_saved)
        )

def get_recent_snapshots(hours: int = 24) -> List[Dict]:
    with get_db() as c:
        c.execute(
            """SELECT * FROM headroom_snapshots 
               WHERE timestamp >= datetime('now', ? || ' hours')
               ORDER BY timestamp DESC""",
            (f'-{hours}',)
        )
        return [dict(row) for row in c.fetchall()]

# --- Anomalies ---

def insert_anomaly(anomaly: Anomaly):
    with get_db() as c:
        c.execute(
            "INSERT INTO anomalies (timestamp, metric, value, baseline, deviation, severity, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (anomaly.timestamp, anomaly.metric, anomaly.value, anomaly.baseline, anomaly.deviation, anomaly.severity, anomaly.message)
        )

def get_recent_anomalies(hours: int = 48) -> List[Anomaly]:
    with get_db() as c:
        c.execute(
            """SELECT * FROM anomalies 
               WHERE timestamp >= datetime('now', ? || ' hours')
               ORDER BY timestamp DESC LIMIT 50""",
            (f'-{hours}',)
        )
        return [Anomaly(**dict(row)) for row in c.fetchall()]

# --- Proxy Stats ---

def record_proxy_stats(hits: int, misses: int, tokens_saved: int, cost_saved: float, total: int):
    with get_db() as c:
        now = datetime.now(timezone.utc).isoformat()
        c.execute(
            "INSERT INTO proxy_stats (timestamp, cache_hits, cache_misses, tokens_saved, cost_saved, requests_total) VALUES (?, ?, ?, ?, ?, ?)",
            (now, hits, misses, tokens_saved, cost_saved, total)
        )

def get_proxy_stats() -> Dict[str, Any]:
    with get_db() as c:
        c.execute("SELECT COALESCE(SUM(cache_hits), 0) as total_hits, COALESCE(SUM(cache_misses), 0) as total_misses, COALESCE(SUM(tokens_saved), 0) as tokens_saved, COALESCE(SUM(cost_saved), 0) as cost_saved FROM proxy_stats")
        row = c.fetchone()
        totals = dict(row) if row else {"total_hits": 0, "total_misses": 0, "tokens_saved": 0, "cost_saved": 0}
        c.execute("SELECT * FROM proxy_stats ORDER BY timestamp DESC LIMIT 20")
        history = [dict(r) for r in c.fetchall()]
        return {**totals, "history": history}

# --- Aggregation ---

def get_model_breakdown(days: int = 30) -> List[Dict[str, Any]]:
    with get_db() as c:
        c.execute("""
            SELECT model, COUNT(*) as requests, 
                   COALESCE(SUM(cost_estimated), 0) as total_cost,
                   COALESCE(SUM(tokens_saved), 0) as tokens_saved,
                   COALESCE(SUM(tokens_before), 0) as tokens_before,
                   COALESCE(AVG(cost_estimated), 0) as avg_cost
            FROM usage_records 
            WHERE timestamp >= datetime('now', ? || ' days')
            GROUP BY model ORDER BY total_cost DESC
        """, (f'-{days}',))
        return [dict(r) for r in c.fetchall()]

def get_user_daily_usage(days: int = 7) -> List[Dict[str, Any]]:
    with get_db() as c:
        c.execute("""
            SELECT u.name as user_name, u.id as user_id,
                   DATE(r.timestamp) as day,
                   COALESCE(SUM(r.cost_estimated), 0) as daily_cost,
                   COALESCE(SUM(r.tokens_saved), 0) as daily_tokens
            FROM usage_records r
            JOIN users u ON u.id = r.user_id
            WHERE r.timestamp >= datetime('now', ? || ' days')
            GROUP BY u.id, DATE(r.timestamp)
            ORDER BY u.name, day
        """, (f'-{days}',))
        return [dict(r) for r in c.fetchall()]

def get_total_savings() -> float:
    with get_db() as c:
        c.execute("SELECT COALESCE(SUM(cost_estimated), 0) as total FROM usage_records")
        row = c.fetchone()
        return row['total'] if row else 0.0

def get_user_count() -> int:
    with get_db() as c:
        c.execute("SELECT COUNT(*) as count FROM users")
        row = c.fetchone()
        return row['count'] if row else 0

def get_team_count() -> int:
    with get_db() as c:
        c.execute("SELECT COUNT(*) as count FROM teams")
        row = c.fetchone()
        return row['count'] if row else 0
