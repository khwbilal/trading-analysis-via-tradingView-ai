@echo off
rem Daily Arena run (WL-069): the trading agents replayed on fresh candles, daily table rebuilt.
rem Started by Task Scheduler (see register.ps1); also fine to run by hand.
rem Paths come from this file's own folder, so PATH and the start folder do not matter.
setlocal
cd /d "%~dp0..\..\backend" || exit /b 1
".venv\Scripts\python.exe" -m app.jobs arena %*
exit /b %ERRORLEVEL%
