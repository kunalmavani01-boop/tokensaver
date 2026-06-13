from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    name: str
    email: str
    team_id: Optional[int] = None
    monthly_budget: float = 100.0
    is_active: bool = True

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    api_key: str
    created_at: str

class TeamBase(BaseModel):
    name: str
    monthly_budget: float = 1000.0

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    created_at: str

class UsageRecord(BaseModel):
    id: int
    timestamp: str
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    tokens_before: int = 0
    tokens_after: int = 0
    tokens_saved: int = 0
    cost_estimated: float = 0.0
    cache_hits: int = 0

class BudgetAlertBase(BaseModel):
    name: str
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    slack_webhook: Optional[str] = None
    email: Optional[str] = None
    threshold_50: bool = False
    threshold_80: bool = True
    threshold_100: bool = True

class BudgetAlertCreate(BudgetAlertBase):
    pass

class BudgetAlert(BudgetAlertBase):
    id: int
    created_at: str

class LicenseValidate(BaseModel):
    license_key: str

class LicenseInfo(BaseModel):
    license_key: str
    customer_email: str
    max_users: int = 5
    is_valid: bool = True
    expires_at: Optional[str] = None

class HeadroomSnapshot(BaseModel):
    timestamp: str
    total_requests: int = 0
    tokens_saved: int = 0
    savings_percent: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    total_cost_saved: float = 0.0

class Anomaly(BaseModel):
    id: int
    timestamp: str
    metric: str
    value: float
    baseline: float
    deviation: float
    severity: str  # low, medium, high
    message: str

class StatusResponse(BaseModel):
    headroom: str
    manager: str
    uptime_seconds: float
    total_users: int
    total_teams: int
    total_savings: float
    license_status: str
