@echo off
setlocal
cd /d "%~dp0"
echo =================================================================
echo         KAVACH PROTOCOL - AUTOMATED CV SUITE TEST HARNESS
echo =================================================================
echo.

set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

"%PY_EXE%" test_harness.py

echo.
pause
