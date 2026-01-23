@echo off
setlocal

cd /d "%~dp0"
set "ENTRYPOINT=main.py"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

:: Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    uv run python "%ENTRYPOINT%" %*
    goto :EOF
)

:: Check for virtual environment
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%ENTRYPOINT%" %*
    goto :EOF
)

:: Fallback to global python
python "%ENTRYPOINT%" %*
