$ErrorActionPreference = "Stop"

$env:HEADROOM_REQUIRE_RUST_CORE = "false"
$env:HEADROOM_TELEMETRY = "off"

$script:childPids = @()

function Cleanup {
    Write-Host "`nStopping TokenSaver services..." -ForegroundColor Yellow
    foreach ($pid in $script:childPids) {
        if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped PID $pid" -ForegroundColor Gray
        }
    }
    Write-Host "TokenSaver stopped." -ForegroundColor Green
}

# Ensure required commands are available
foreach ($cmd in @("headroom", "python", "uvicorn")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[FATAL] '$cmd' not found. Please install it and try again." -ForegroundColor Red
        exit 1
    }
}

try {
    Write-Host "==============================" -ForegroundColor Green
    Write-Host "  TokenSaver - Starting Stack" -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Green
    Write-Host ""

    # Start Headroom proxy
    Write-Host "[1/3] Starting Headroom proxy on port 8787..."
    $hrProc = Start-Process -WindowStyle Hidden -PassThru -FilePath "headroom" -ArgumentList "proxy --port 8787 --no-telemetry"
    $script:childPids += $hrProc.Id
    Start-Sleep 4
    try {
        curl.exe -s http://127.0.0.1:8787/health | Out-Null
        Write-Host "  [OK] Headroom is running (PID: $($hrProc.Id))" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Headroom health check failed. It may still be starting." -ForegroundColor Yellow
    }

    # Start Caching Proxy
    Write-Host "[2/3] Starting Caching Proxy on port 8788..."
    $proxyProc = Start-Process -WindowStyle Hidden -PassThru -FilePath "uvicorn" -ArgumentList "proxy.server:app --host 0.0.0.0 --port 8788"
    $script:childPids += $proxyProc.Id
    Start-Sleep 3
    try {
        curl.exe -s http://127.0.0.1:8788/health | Out-Null
        Write-Host "  [OK] Proxy running (PID: $($proxyProc.Id))" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Proxy health check failed" -ForegroundColor Yellow
    }

    # Start Manager server
    Write-Host "[3/3] Starting Manager Server on http://127.0.0.1:3001..."
    $mgrProc = Start-Process -WindowStyle Hidden -PassThru -FilePath "uvicorn" -ArgumentList "manager.server:app --host 0.0.0.0 --port 3001"
    $script:childPids += $mgrProc.Id
    Start-Sleep 4
    try {
        curl.exe -s http://127.0.0.1:3001/manager/health | Out-Null
        Write-Host "  [OK] Manager running (PID: $($mgrProc.Id))" -ForegroundColor Green
    } catch {
        Write-Host "  [WARN] Manager health check failed" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "==============================" -ForegroundColor Green
    Write-Host "  TokenSaver Stack Running!" -ForegroundColor Green
    Write-Host "==============================" -ForegroundColor Green
    Write-Host "  Manager:       http://127.0.0.1:3001/manager/" -ForegroundColor Cyan
    Write-Host "  Headroom:      http://127.0.0.1:8787" -ForegroundColor Cyan
    Write-Host "  Caching Proxy: http://127.0.0.1:8788" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Press any key to stop all services."

    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} finally {
    Cleanup
}
