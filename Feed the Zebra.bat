@echo off
REM ====================================================================
REM  Feed the Zebra
REM  Double-click to launch the label-printing GUI in your browser.
REM ====================================================================

cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul || set "PY=py"

"%PY%" "%~dp0gui\server.py"
