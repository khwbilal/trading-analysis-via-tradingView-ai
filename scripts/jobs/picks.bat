@echo off
rem Daily Top 10 picks per style (WL-037), then paper trades from them (WL-038).
rem Started by Task Scheduler (see register.ps1); also fine to run by hand.
rem Paths come from this file's own folder, so PATH and the start folder do not matter.
setlocal
cd /d "%~dp0..\..\backend" || exit /b 1
".venv\Scripts\python.exe" -m app.jobs picks %*
exit /b %ERRORLEVEL%
