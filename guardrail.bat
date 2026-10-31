@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
"%~dp0.venv\Scripts\python.exe" "%~dp0reid_guardrail\test_text.py" %*
endlocal
