@echo off
chcp 65001 >nul
title MedFlow 滴護寶監測牆 1-Click Launcher (Windows)
echo ===================================================
echo 🏥 正在啟動 MedFlow 滴護寶跨平台動態監測系統...
echo ===================================================
cd /d "%~dp0"
where python >nul 2>&1
if %errorlevel% equ 0 (
    python server.py
) else (
    echo Python 未安裝，直接以瀏覽器獨立視窗開啟...
    start "" "mqtt_dashboard.html"
)
pause
