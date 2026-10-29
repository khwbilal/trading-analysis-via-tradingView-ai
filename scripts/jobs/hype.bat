@echo off
rem Daily hype radar (WL-042): trending, Reddit mentions, volume and OI jumps.
rem Started by Task Scheduler (see register.ps1); also fine to run by hand.
rem Paths come from this file's own folder, so PATH and the start folder do not matter.
setlocal
cd /d "%~dp0..\..\backend" || exit /b 1
".venv\Scripts\python.exe" -m app.jobs hype %*
exit /b %ERRORLEVEL%
