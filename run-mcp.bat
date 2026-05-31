@echo off
:: Xero MCP Server — Windows launcher
:: Reads credentials from scripts\.env

set SKILL_DIR=%~dp0
set ENV_FILE=%SKILL_DIR%scripts\.env

if not exist "%ENV_FILE%" (
    echo ERROR: %ENV_FILE% not found. Copy scripts\.env.example to scripts\.env and fill in your credentials. 1>&2
    exit /b 1
)

:: Load .env variables
for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
    set line=%%A
    if not "!line:~0,1!"=="#" if not "%%A"=="" (
        set %%A=%%B
    )
)

uv run --project "%SKILL_DIR%" python "%SKILL_DIR%mcp_server.py"
