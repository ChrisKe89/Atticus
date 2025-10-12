@echo off
setlocal ENABLEDELAYEDEXPANSION

set "PYTHON_CMD=python"
if exist "%~dp0\.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0\.venv\Scripts\python.exe"
)

if /I "%1"=="run" (
    if /I "%2"=="db:seed" (
        shift
        shift
        "%PYTHON_CMD%" -m scripts.db_seed %*
        exit /b %errorlevel%
    )
)

set "FALLBACK="
for %%E in (npm.cmd npm.exe npm) do (
    for /f "delims=" %%P in ('where %%E 2^>nul') do (
        if /I not "%%~fP"=="%~f0" (
            set "FALLBACK=%%~fP"
            goto delegate
        )
    )
)

:delegate
if defined FALLBACK (
    if exist "%FALLBACK%" (
        call "%FALLBACK%" %*
        exit /b %errorlevel%
    )
)

echo npm command not available for arguments: %*
exit /b 1
