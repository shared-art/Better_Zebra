@echo off
REM ====================================================================
REM  Print Labels
REM  - Drag a .csv file onto this .bat to print its column B labels
REM  - Or double-click to pick a file
REM ====================================================================

cd /d "%~dp0"

set "PY=python"
where python >nul 2>nul || set "PY=py"

"%PY%" "%~dp0print_labels.py" %*

echo.
pause
