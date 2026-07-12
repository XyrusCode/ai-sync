@echo off
REM ai-sync scheduler wrapper. Runs the daily sync (apply + dated log).
REM Task Scheduler invokes python.exe directly (see install-schedule.ps1); this
REM file is a convenience for running the same thing by hand.
setlocal
cd /d "%~dp0"
if "%AISYNC_PYTHON%"=="" (set "AISYNC_PYTHON=python")
"%AISYNC_PYTHON%" -m ai_sync --apply --log
endlocal
