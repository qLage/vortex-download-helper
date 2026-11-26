@echo off
powershell.exe -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0Vortex-download-helper.ps1" %*
if errorlevel 1 pause
