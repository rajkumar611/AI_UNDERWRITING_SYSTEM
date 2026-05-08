@echo off
set VIRTUAL_ENV=
uv run uvicorn main:app --port 8081
