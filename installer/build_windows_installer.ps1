param(
    [string]$AppName = "TokenSaver"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dist = Join-Path $root "dist"
$setup = Join-Path $dist "$AppName-Setup.exe"

if (-not (Get-Command iscc.exe -ErrorAction SilentlyContinue)) {
    throw "Inno Setup compiler (iscc.exe) not found."
}

Push-Location $root
try {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller
    python build_installer.py
    & iscc.exe (Join-Path $root "installer\$AppName.iss")
} finally {
    Pop-Location
}

if (-not (Test-Path $setup)) {
    throw "Expected installer not found: $setup"
}
