@echo off
rem Dublu-clic: intreaba calea proiectului si copiaza project-starter in ea.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0new-project.ps1" %*
echo.
pause
