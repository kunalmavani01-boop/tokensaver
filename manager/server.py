"""TokenSaver Management Server — FastAPI application."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from .config import config
from .database import (
    init_db, create_user, get_user, get_all_users, delete_user,
    create_team, get_all_teams,
    create_alert, get_all_alerts, get_db,
    get_user_count, get_team_count, get_total_savings,
    insert_usage, record_proxy_stats, get_proxy_stats,
    get_model_breakdown, get_user_daily_usage,
    resolve_usage_identity, UserCreate, TeamCreate, BudgetAlertCreate,
)
from .headroom_client import get_headroom_status, periodic_poll, poll_and_store
from .budget_engine import get_budget_summary
from .alerts import check_and_alert
from .anomaly import detect_anomalies, get_anomalies
from .reports import generate_usage_csv, generate_budget_csv, generate_anomalies_csv, get_dashboard_stats
from .license import validate_key, save_license, get_license_info, check_user_limit
from .ingestion import (
    validate_manual_entry, record_from_form, parse_usage_csv,
    generate_csv_template, bulk_insert_records,
    MODEL_OPTIONS, PROVIDER_OPTIONS,
)

logger = logging.getLogger(__name__)

# Paths
HERE = Path(__file__).resolve().parent
TEMPLATES_DIR = HERE / "templates"

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Background task reference
_poller_task: Optional[asyncio.Task] = None


def _verify_internal_request(request: Request) -> None:
    if not config.internal_token:
        return
    received = request.headers.get("x-tokensaver-internal-token", "")
    if received != config.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")

def get_license_tier() -> str:
    """Determine license tier: free, pro, or enterprise."""
    info = get_license_info()
    if not info.get("is_valid"):
        return "free"
    max_users = info.get("max_users", 5)
    if max_users >= 999:
        return "enterprise"
    return "pro"

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup: init DB, start background poller (unless standalone). Shutdown: clean up."""
    global _poller_task
    init_db()
    logger.info("Database initialized at %s", config.db_path)

    if config.standalone_mode:
        logger.info("Running in STANDALONE mode — Headroom polling disabled")
    else:
        try:
            await poll_and_store()
            logger.info("Initial Headroom poll complete")
        except Exception as e:
            logger.warning("Initial poll failed (Headroom may not be running): %s", e)

        _poller_task = asyncio.create_task(periodic_poll())
        logger.info("Background poller started (interval: %ss)", config.poll_interval_seconds)

    yield

    if _poller_task:
        _poller_task.cancel()
        logger.info("Background poller stopped")

app = FastAPI(title="TokenSaver Manager", lifespan=lifespan, version="1.0.0")

def render(request: Request, template: str, **extra):
    """Helper to render templates with common context."""
    license_info = get_license_info()
    ctx = {
        "request": request,
        "standalone_mode": config.standalone_mode,
        "license_tier": get_license_tier(),
        "license_valid": license_info.get("is_valid", False),
        "license_email": license_info.get("customer_email", ""),
        "license_max_users": license_info.get("max_users", 5),
        "manager_port": config.port,
        "poll_interval": config.poll_interval_seconds,
        "user_count": get_user_count(),
        "team_count": get_team_count(),
        "total_savings": get_total_savings(),
        **extra,
    }
    if "headroom_status" not in ctx:
        ctx["headroom_status"] = "standalone" if config.standalone_mode else "running"
    return templates.TemplateResponse(request, template, ctx)

# ─── HTML Pages ─────────────────────────────────────────────────────────────

@app.get("/manager/", response_class=HTMLResponse)
async def overview(request: Request):
    stats = get_dashboard_stats()
    headroom = await get_headroom_status()
    anomalies = get_anomalies(hours=24)
    return render(request, "overview.html", 
                  active_page="overview",
                  headroom_status=headroom,
                  top_users=stats.get("top_users", []),
                  recent_records=stats.get("recent_records", []),
                  chart_labels=stats.get("chart_labels", "[]"),
                  chart_data=stats.get("chart_data", "[]"),
                  anomalies=anomalies)

@app.get("/manager/users", response_class=HTMLResponse)
async def users_page(request: Request):
    users = get_all_users()
    teams = get_all_teams()
    return render(request, "users.html",
                  active_page="users",
                  users=users,
                  teams=teams)

@app.post("/manager/users/create")
async def users_create(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    monthly_budget: float = Form(100.0),
    team_id: Optional[int] = Form(None),
):
    try:
        current = get_user_count()
        if not check_user_limit(current):
            return render(request, "users.html",
                          active_page="users",
                          users=get_all_users(),
                          teams=get_all_teams(),
                          flash_message=f"User limit reached ({get_license_info().get('max_users', 5)}). Purchase a Pro license at kunalmavani@outlook.com.",
                          flash_type="error")
        user_data = UserCreate(name=name, email=email, monthly_budget=monthly_budget, team_id=team_id)
        user = create_user(user_data)
        logger.info("Created user: %s (%s)", user.name, user.email)
        return RedirectResponse(url="/manager/users", status_code=303)
    except Exception as e:
        logger.error("Failed to create user: %s", e)
        return render(request, "users.html",
                      active_page="users",
                      users=get_all_users(),
                      teams=get_all_teams(),
                      flash_message=f"Error: {e}",
                      flash_type="error")

@app.post("/manager/users/{user_id}/delete")
async def users_delete(user_id: int):
    deleted = delete_user(user_id)
    if not deleted:
        logger.warning("User %d not found", user_id)
    return RedirectResponse(url="/manager/users", status_code=303)

@app.get("/manager/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    teams = get_all_teams()
    users = get_all_users()
    team_data = []
    for t in teams:
        member_count = sum(1 for u in users if u.team_id == t.id)
        team_data.append({
            "id": t.id,
            "name": t.name,
            "monthly_budget": t.monthly_budget,
            "member_count": member_count,
            "created_at": t.created_at,
        })
    return render(request, "teams.html",
                  active_page="teams",
                  teams=team_data)

@app.post("/manager/teams/create")
async def teams_create(
    request: Request,
    name: str = Form(...),
    monthly_budget: float = Form(1000.0),
):
    try:
        team_data = TeamCreate(name=name, monthly_budget=monthly_budget)
        team = create_team(team_data)
        logger.info("Created team: %s", team.name)
        return RedirectResponse(url="/manager/teams", status_code=303)
    except Exception as e:
        logger.error("Failed to create team: %s", e)
        return render(request, "teams.html",
                      active_page="teams",
                      teams=get_all_teams(),
                      flash_message=f"Error: {e}",
                      flash_type="error")

@app.get("/manager/budgets", response_class=HTMLResponse)
async def budgets_page(request: Request):
    summary = get_budget_summary()
    return render(request, "budgets.html",
                  active_page="budgets",
                  **summary)

@app.get("/manager/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    alerts = get_all_alerts()
    return render(request, "alerts.html",
                  active_page="alerts",
                  alerts=alerts)

@app.post("/manager/alerts/create")
async def alerts_create(
    request: Request,
    name: str = Form(...),
    slack_webhook: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    threshold_50: Optional[str] = Form(None),
    threshold_80: Optional[str] = Form(None),
    threshold_100: Optional[str] = Form(None),
):
    try:
        alert_data = BudgetAlertCreate(
            name=name,
            slack_webhook=slack_webhook or None,
            email=email or None,
            threshold_50=bool(threshold_50),
            threshold_80=bool(threshold_80),
            threshold_100=bool(threshold_100),
        )
        alert = create_alert(alert_data)
        logger.info("Created alert: %s", alert.name)
        return RedirectResponse(url="/manager/alerts", status_code=303)
    except Exception as e:
        logger.error("Failed to create alert: %s", e)
        return render(request, "alerts.html",
                      active_page="alerts",
                      alerts=get_all_alerts(),
                      flash_message=f"Error: {e}",
                      flash_type="error")

@app.post("/manager/alerts/{alert_id}/delete")
async def alerts_delete(alert_id: int):
    with get_db() as c:
        c.execute("DELETE FROM budget_alerts WHERE id = ?", (alert_id,))
    return RedirectResponse(url="/manager/alerts", status_code=303)

@app.get("/manager/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    teams = get_all_teams()
    anomalies = get_anomalies(hours=48)
    return render(request, "reports.html",
                  active_page="reports",
                  teams=teams,
                  anomalies=anomalies)

@app.get("/manager/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    headroom = await get_headroom_status()
    return render(request, "settings.html",
                  active_page="settings",
                  headroom_status=headroom)

@app.post("/manager/settings/license")
async def settings_license(
    request: Request,
    license_key: str = Form(...),
    email: str = Form(...),
):
    result = validate_key(license_key.strip(), email.strip())
    if result.get("is_valid"):
        save_license(license_key.strip(), email.strip(), result.get("max_users", 5))
        logger.info("License activated: %s users for %s", result.get("max_users"), result.get("customer_email"))
        return RedirectResponse(url="/manager/settings?activated=true", status_code=303)
    else:
        return render(request, "settings.html",
                      active_page="settings",
                      headroom_status=await get_headroom_status(),
                      flash_message="Invalid license key. Please check and try again.",
                      flash_type="error")

# ─── Data Ingestion (Standalone / Enterprise) ───────────────────────────────

def _require_enterprise(request: Request):
    """Gate standalone-mode features behind Enterprise license."""
    info = get_license_info()
    if not info.get("is_valid") or info.get("max_users", 5) < 999:
        return render(request, "settings.html",
                      active_page="settings",
                      headroom_status="standalone" if config.standalone_mode else "running",
                      flash_message="Data ingestion is an Enterprise feature. Upgrade to activate.",
                      flash_type="error")
    return None

@app.get("/manager/usage/add", response_class=HTMLResponse)
async def usage_add_page(request: Request):
    gate = _require_enterprise(request)
    if gate:
        return gate
    return render(request, "usage_add.html",
                  active_page="settings",
                  users=get_all_users(),
                  models=MODEL_OPTIONS,
                  providers=PROVIDER_OPTIONS)

@app.post("/manager/usage/add")
async def usage_add_submit(
    request: Request,
    user_id: int = Form(...),
    model: str = Form("custom"),
    provider: str = Form("other"),
    cost_estimated: float = Form(0.0),
    tokens_saved: int = Form(0),
    tokens_before: int = Form(0),
):
    gate = _require_enterprise(request)
    if gate:
        return gate

    data = {"user_id": user_id, "cost_estimated": cost_estimated,
            "tokens_saved": tokens_saved, "tokens_before": tokens_before,
            "model": model, "provider": provider}
    errors = validate_manual_entry(data)
    if errors:
        return render(request, "usage_add.html",
                      active_page="settings",
                      users=get_all_users(),
                      models=MODEL_OPTIONS,
                      providers=PROVIDER_OPTIONS,
                      flash_message="; ".join(errors),
                      flash_type="error")

    record = record_from_form(data)
    insert_usage(record)
    logger.info("Manual usage entry: user=%s model=%s cost=%.4f", user_id, model, cost_estimated)
    return RedirectResponse(url="/manager/?added=true", status_code=303)

@app.get("/manager/usage/import", response_class=HTMLResponse)
async def usage_import_page(request: Request):
    gate = _require_enterprise(request)
    if gate:
        return gate
    return render(request, "usage_import.html", active_page="settings")

@app.post("/manager/usage/import")
async def usage_import_submit(request: Request, csv_file: UploadFile = File(...)):
    gate = _require_enterprise(request)
    if gate:
        return gate

    content = (await csv_file.read()).decode("utf-8-sig")
    records = parse_usage_csv(content)
    if not records:
        return render(request, "usage_import.html",
                      active_page="settings",
                      flash_message="No valid records found in CSV. Check the format and try again.",
                      flash_type="error")

    count = bulk_insert_records(records)
    logger.info("CSV import: %d/%d records inserted", count, len(records))
    return RedirectResponse(url=f"/manager/?imported={count}", status_code=303)

@app.get("/manager/usage/import/template")
async def usage_import_template():
    content = generate_csv_template()
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="usage-template.csv"'}
    )

@app.post("/manager/api/usage")
async def api_usage_ingest(records: List[Dict[str, Any]]):
    """Bulk JSON API for programmatic usage ingestion."""
    info = get_license_info()
    if not info.get("is_valid") or info.get("max_users", 5) < 999:
        raise HTTPException(status_code=402, detail="Enterprise license required")

    count = bulk_insert_records(records)
    return {"inserted": count, "total": len(records)}

# ─── API Endpoints ──────────────────────────────────────────────────────────

@app.get("/manager/api/status")
async def api_status():
    headroom = await get_headroom_status()
    license_info = get_license_info()
    return {
        "headroom": headroom,
        "manager": "running",
        "users": get_user_count(),
        "teams": get_team_count(),
        "total_savings": get_total_savings(),
        "license": license_info,
    }

@app.get("/manager/api/users")
async def api_users():
    users = get_all_users()
    return [{"id": u.id, "name": u.name, "email": u.email, "team_id": u.team_id,
             "monthly_budget": u.monthly_budget, "is_active": u.is_active} for u in users]

@app.get("/manager/api/budgets")
async def api_budgets():
    return get_budget_summary()

@app.get("/manager/api/anomalies")
async def api_anomalies():
    anomalies = get_anomalies(hours=48)
    return [{"id": a.id, "timestamp": a.timestamp, "metric": a.metric, "value": a.value,
             "baseline": a.baseline, "deviation": a.deviation, "severity": a.severity,
             "message": a.message} for a in anomalies]

@app.get("/manager/api/license")
async def api_license():
    return get_license_info()

@app.post("/manager/api/license/validate")
async def api_validate_license(key: str = ""):
    return validate_key(key)

# ─── CSV Reports ────────────────────────────────────────────────────────────

@app.get("/manager/reports/usage.csv")
async def csv_usage(days: int = 30, team_id: Optional[int] = None):
    content = generate_usage_csv(days=days, team_id=team_id)
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="usage-{days}d.csv"'}
    )

@app.get("/manager/reports/budget.csv")
async def csv_budget():
    content = generate_budget_csv()
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="budget-report.csv"'}
    )

@app.get("/manager/reports/anomalies.csv")
async def csv_anomalies():
    content = generate_anomalies_csv()
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="anomalies.csv"'}
    )

# ─── Health ─────────────────────────────────────────────────────────────────

# ─── Proxy Caching Page ─────────────────────────────────────────────────

@app.get("/manager/proxy", response_class=HTMLResponse)
async def proxy_page(request: Request):
    stats = get_proxy_stats()
    headroom = await get_headroom_status()
    return render(request, "proxy.html",
                  active_page="proxy",
                  headroom_status=headroom,
                  proxy_stats=stats,
                  proxy_port=8788)

@app.post("/manager/api/proxy/stats")
async def api_proxy_stats(hits: int = 0, misses: int = 0, tokens_saved: int = 0, cost_saved: float = 0.0, total: int = 0):
    record_proxy_stats(hits, misses, tokens_saved, cost_saved, total)
    return {"status": "recorded"}

@app.post("/manager/api/proxy/stats/json")
async def api_proxy_stats_json(request: Request, data: Dict[str, Any]):
    _verify_internal_request(request)
    record_proxy_stats(
        hits=data.get("cache_hits", 0),
        misses=data.get("cache_misses", 0),
        tokens_saved=data.get("tokens_saved", 0),
        cost_saved=data.get("cost_saved", 0.0),
        total=data.get("total_requests", 0)
    )
    return {"status": "recorded"}


@app.post("/manager/api/proxy/usage")
async def api_proxy_usage(request: Request, data: Dict[str, Any]):
    _verify_internal_request(request)
    identity = resolve_usage_identity(
        user_id=data.get("user_id"),
        email=data.get("user_email"),
        api_key=data.get("user_api_key"),
        team_id=data.get("team_id"),
    )
    insert_usage(
        {
            "timestamp": data.get("timestamp"),
            "user_id": identity["user_id"],
            "team_id": identity["team_id"],
            "model": data.get("model"),
            "provider": data.get("provider"),
            "endpoint": data.get("endpoint", "/v1/chat/completions"),
            "tokens_before": data.get("tokens_before", 0),
            "tokens_after": data.get("tokens_after", 0),
            "tokens_saved": data.get("tokens_saved", 0),
            "cost_estimated": data.get("cost_estimated", 0.0),
            "cache_hits": data.get("cache_hits", 0),
        }
    )
    if identity["user_id"] is not None:
        await check_and_alert()
    return {"status": "recorded", "user_id": identity["user_id"], "team_id": identity["team_id"]}

@app.get("/manager/api/proxy/stats")
async def api_get_proxy_stats():
    return get_proxy_stats()

# ─── Model Analytics ──────────────────────────────────────────────────

@app.get("/manager/models", response_class=HTMLResponse)
async def models_page(request: Request):
    models = get_model_breakdown()
    headroom = await get_headroom_status()
    return render(request, "models.html",
                  active_page="models",
                  headroom_status=headroom,
                  models=models)

@app.get("/manager/api/models")
async def api_models(days: int = 30):
    return get_model_breakdown(days=days)

@app.get("/manager/api/usage/daily")
async def api_usage_daily(days: int = 7):
    return get_user_daily_usage(days=days)

# ─── Health ─────────────────────────────────────────────────

@app.get("/manager/health")
async def health():
    return {"status": "ok", "service": "tokensaver-manager", "version": "1.0.0"}

# ─── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = config.port
    logger.info("Starting TokenSaver Manager on port %s", port)
    uvicorn.run(app, host="127.0.0.1", port=port)
