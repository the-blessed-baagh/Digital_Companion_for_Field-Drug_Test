@echo off
setlocal
cd /d "%~dp0"
echo =================================================================
echo        KAVACH PROTOCOL - TEAM A LIVE PROTOTYPE DEMONSTRATION
echo =================================================================
echo.
echo Running standalone Computer Vision algorithm on camera JPG...
echo.

set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"

"%PY_EXE%" kavach_cv.py tests\sample_positive.jpg --output output\live_demo

echo.
echo =================================================================
echo Demonstration Complete!
echo Generated visual artifacts in: output\live_demo\
echo   - 01_input.jpg
echo   - 02_aruco_detected.jpg
echo   - 03_warped.jpg
echo   - 04_rois.jpg
echo   - 05_analysis_dashboard.jpg
echo   - result.json
echo =================================================================
echo.
pause
