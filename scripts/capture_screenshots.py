"""Take screenshots of all manager pages using Playwright."""
import sys, os, json, time, subprocess, signal
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["TOKENSAVER_DB_PATH"] = os.path.join(os.path.dirname(__file__), "..", "data", "savings.db")

# Seed demo data
from scripts.seed_demo import main as seed_demo
print("Seeding demo data...")
seed_demo()
print("Demo data seeded.")

# Start manager server
import uvicorn
import threading

from manager.server import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=3001, log_level="error")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(5)
# Verify server is up
import urllib.request
for attempt in range(5):
    try:
        urllib.request.urlopen("http://127.0.0.1:3001/manager/health", timeout=2)
        print("Manager started on :3001")
        break
    except:
        time.sleep(2)
else:
    print("WARN: Manager may not be fully up yet")

# Take screenshots with Playwright
from playwright.sync_api import sync_playwright

pages = {
    "overview": "/manager/",
    "users": "/manager/users",
    "teams": "/manager/teams",
    "budgets": "/manager/budgets",
    "models": "/manager/models",
    "alerts": "/manager/alerts",
    "reports": "/manager/reports",
    "settings": "/manager/settings",
    "proxy": "/manager/proxy",
}

output_dir = os.path.join(os.path.dirname(__file__), "..", "promotion", "screenshots")
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    for name, path in pages.items():
        url = f"http://127.0.0.1:3001{path}"
        for attempt in range(3):
            try:
                page.goto(url, timeout=15000)
                page.wait_for_load_state("networkidle")
                time.sleep(1)
                screenshot_path = os.path.join(output_dir, f"{name}.png")
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"  Captured {name} -> {screenshot_path}")
                break
            except Exception as e:
                if attempt < 2:
                    print(f"  Retry {name} (attempt {attempt+1})...")
                    time.sleep(2)
                else:
                    print(f"  FAIL {name}: {e}")

    browser.close()

print(f"\nAll screenshots saved to {output_dir}")
