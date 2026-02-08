@echo off
REM Quick demo script for Windows users
REM This script provides an easy way to test the pipeline orchestration

setlocal enabledelayedexpansion

echo.
echo ================================================================================
echo   PIPELINE ORCHESTRATION - QUICK DEMO
echo ================================================================================
echo.

REM Check if API is running
echo [*] Checking if API is running...
curl -s http://localhost:8000/docs > nul
if errorlevel 1 (
    echo.
    echo [!] ERROR: API is not running!
    echo.
    echo Please start the API first:
    echo   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    echo.
    pause
    exit /b 1
)

echo [+] API is running!
echo.

echo Select a demo:
echo.
echo 1. Basic Topology (3 routers, 1 switch)
echo 2. Medium Topology (5 routers, 3 switches, with seed)
echo 3. Large Topology (8 routers, 4 switches)
echo 4. Fast Demo (skip analysis, 3 routers, 1 switch)
echo 5. Run Python Demo Script
echo 6. Open API Documentation
echo 0. Exit
echo.

set /p choice="Enter your choice (0-6): "

if "%choice%"=="0" (
    echo Goodbye!
    exit /b 0
)

if "%choice%"=="1" (
    echo.
    echo [*] Executing Basic Topology Pipeline...
    echo.
    powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/run-pipeline' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{\"topology_name\":\"basic-demo\",\"num_routers\":3,\"num_switches\":1,\"run_analysis\":true}' | ConvertTo-Json -Depth 10 | Write-Host"
    pause
)

if "%choice%"=="2" (
    echo.
    echo [*] Executing Medium Topology Pipeline...
    echo.
    powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/run-pipeline' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{\"topology_name\":\"medium-demo\",\"num_routers\":5,\"num_switches\":3,\"seed\":42,\"run_analysis\":true}' | ConvertTo-Json -Depth 10 | Write-Host"
    pause
)

if "%choice%"=="3" (
    echo.
    echo [*] Executing Large Topology Pipeline...
    echo.
    powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/run-pipeline' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{\"topology_name\":\"large-demo\",\"num_routers\":8,\"num_switches\":4,\"seed\":123,\"run_analysis\":true}' | ConvertTo-Json -Depth 10 | Write-Host"
    pause
)

if "%choice%"=="4" (
    echo.
    echo [*] Executing Fast Demo (no analysis)...
    echo.
    powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/run-pipeline' -Method POST -Headers @{'Content-Type'='application/json'} -Body '{\"topology_name\":\"fast-demo\",\"num_routers\":3,\"num_switches\":1,\"run_analysis\":false}' | ConvertTo-Json -Depth 10 | Write-Host"
    pause
)

if "%choice%"=="5" (
    echo.
    echo [*] Running Python Demo Script...
    python demo_pipeline.py
    pause
)

if "%choice%"=="6" (
    echo.
    echo [*] Opening API Documentation in browser...
    start http://localhost:8000/docs
    echo Done!
    pause
)

endlocal
