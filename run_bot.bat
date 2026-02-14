@echo off
cd /d %~dp0
if not exist .env if exist .env.example copy /Y .env.example .env >nul
if exist .venv\Scripts\python.exe (
  set PY=.venv\Scripts\python.exe
) else (
  set PY=python
)
%PY% -m app.main
