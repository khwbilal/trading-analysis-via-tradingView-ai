@echo off
rem Every 4 hours: close paper trades that hit stop, target or the horizon (WL-038).
rem Started by Task Scheduler (see register.ps1); also fine to run by hand.
rem Paths come from this file's own folder, so PATH and the start folder do not matter.
setlocal
cd /d "%~dp0..\..\backend" || exit /b 1
".venv\Scripts\python.exe" -m app.jobs paper %*
exit /b %ERRORLEVEL%
