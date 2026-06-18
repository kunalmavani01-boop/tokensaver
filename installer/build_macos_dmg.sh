#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
APP_NAME="TokenSaver"
APP_BUNDLE="$DIST/${APP_NAME}.app"
DMG_PATH="$DIST/${APP_NAME}-macOS.dmg"

mkdir -p "$DIST"
python -m pip install --upgrade pip
pip install -r "$ROOT/requirements.txt"
pip install pyinstaller create-dmg
python "$ROOT/build_installer.py"

if [[ ! -d "$APP_BUNDLE" ]]; then
  mkdir -p "$APP_BUNDLE/Contents/MacOS"
  cp "$DIST/$APP_NAME" "$APP_BUNDLE/Contents/MacOS/$APP_NAME" || true
fi

create-dmg \
  --volname "$APP_NAME" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --app-drop-link 600 185 \
  "$DMG_PATH" \
  "$APP_BUNDLE"

test -f "$DMG_PATH"
