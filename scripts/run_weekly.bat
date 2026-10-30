@echo off
rem ==============================================================================
rem Meal Planner Dashboard — Friday Morning Automation Runner
rem Windows Task Scheduler Target Script
rem
rem Scheduled Task Installation Command (Run in elevated CMD or PowerShell):
rem schtasks /create /tn "MealPlannerWeeklyOrchestrator" /tr "C:\Users\david\Desktop\Progetti\meal-planner-dashboard\scripts\run_weekly.bat" /sc weekly /d FRI /st 08:00 /f
rem
rem To run or test immediately:
rem schtasks /run /tn "MealPlannerWeeklyOrchestrator"
rem
rem To delete task:
rem schtasks /delete /tn "MealPlannerWeeklyOrchestrator" /f
rem ==============================================================================

setlocal enabledelayedexpansion

set "PROJECT_DIR=C:\Users\david\Desktop\Progetti\meal-planner-dashboard"
set "PYTHON_EXE=C:\Users\david\AppData\Local\Programs\Python\Python313\python.exe"
set "LOG_DIR=%PROJECT_DIR%\logs"
set "LOG_FILE=%LOG_DIR%\orchestrator.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ============================================================ >> "%LOG_FILE%"
echo [%DATE% %TIME%] Starting Friday Weekly Orchestrator Runner >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

cd /d "%PROJECT_DIR%"

if exist "%PYTHON_EXE%" (
    set "PY_CMD=%PYTHON_EXE%"
) else (
    set "PY_CMD=python"
)

"%PY_CMD%" scripts\weekly_orchestrator.py >> "%LOG_FILE%" 2>&1
set EXIT_CODE=%ERRORLEVEL%

echo [%DATE% %TIME%] Orchestrator finished with exit code: %EXIT_CODE% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

exit /b %EXIT_CODE%
