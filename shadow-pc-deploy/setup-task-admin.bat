@echo off
echo Type Beat Auto-Trainer - Task Scheduler Setup
echo.
echo This script requires Administrator privileges.
echo Right-click this file and select "Run as administrator"
echo.
pause

PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%~dp0setup-auto-trainer-task.ps1'"

pause
