#!/usr/bin/env bash
set -e

# ─── Colors ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Environment ──────────────────────────────────────────────────────────
export HEADROOM_REQUIRE_RUST_CORE=false
export HEADROOM_TELEMETRY=off

HEADROOM_PORT=8787
MANAGER_PORT=3001
PROXY_PORT=8788
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_LIST=()

cleanup() {
    info "Shutting down TokenSaver..."
    for pid in "${PID_LIST[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
    done
    ok "All processes stopped. Goodbye!"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ─── 1. Start Headroom proxy ──────────────────────────────────────────────
info "Starting Headroom proxy on port ${HEADROOM_PORT}..."
headroom proxy --port "$HEADROOM_PORT" --no-telemetry &
HEADROOM_PID=$!
PID_LIST+=("$HEADROOM_PID")
sleep 4

# Health check
if curl -sf "http://127.0.0.1:${HEADROOM_PORT}/health" > /dev/null 2>&1; then
    ok "Headroom proxy is healthy on :${HEADROOM_PORT}"
else
    warn "Headroom health check did not respond (non-critical)"
fi

# ─── 2. Start Caching Proxy ─────────────────────────────────────────────
info "Starting Caching Proxy on port ${PROXY_PORT}..."
uvicorn proxy.server:app --host 0.0.0.0 --port "$PROXY_PORT" &
PROXY_PID=$!
PID_LIST+=("$PROXY_PID")
sleep 2

if curl -sf "http://127.0.0.1:${PROXY_PORT}/health" > /dev/null 2>&1; then
    ok "Caching Proxy is live on :${PROXY_PORT}"
else
    warn "Caching Proxy health check failed"
fi

# ─── 3. Start Manager ────────────────────────────────────────────────────
info "Starting Manager server on port ${MANAGER_PORT}..."
uvicorn manager.server:app --host 0.0.0.0 --port "$MANAGER_PORT" &
MANAGER_PID=$!
PID_LIST+=("$MANAGER_PID")
sleep 3

if curl -sf "http://127.0.0.1:${MANAGER_PORT}/manager/health" > /dev/null 2>&1; then
    ok "Manager is live at http://127.0.0.1:${MANAGER_PORT}/manager/"
else
    warn "Manager may still be starting up..."
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   TokenSaver is running!${NC}"
echo -e "${GREEN}   Manager     : http://127.0.0.1:${MANAGER_PORT}/manager/${NC}"
echo -e "${GREEN}   Headroom    : http://127.0.0.1:${HEADROOM_PORT}${NC}"
echo -e "${GREEN}   Caching Proxy: http://127.0.0.1:${PROXY_PORT}${NC}"
echo -e "${GREEN}   Press Ctrl+C to stop all services${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Wait for any process to exit (or Ctrl+C)
wait
