@echo off
rem Runs start.ps1 without needing to change the system's PowerShell execution policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
