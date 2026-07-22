#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
echo "==================================================="
echo "🏥 正在啟動 MedFlow 滴護寶跨平台動態監測系統 (macOS)..."
echo "==================================================="
if command -v python3 &>/dev/null; then
    python3 server.py
else
    open mqtt_dashboard.html
fi
