:: Copyright (c) [2026] NirrussVn0
@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "ENTRYPOINT=%SCRIPT_DIR%\main.py"

if defined PYTHONPATH (
    set "PYTHONPATH=%SCRIPT_DIR%\src;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%SCRIPT_DIR%\src"
)

chcp 65001 >nul


where uv >nul 2>nul
if %ERRORLEVEL% NEQ 0 goto :CheckVenv

echo [INFO] Detected uv in system.

if not exist "%SCRIPT_DIR%\.venv" goto :RunUV
if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" goto :RunUV

echo.
echo [WARNING] Phat hien .venv khong tuong thich (co the do copy tu Linux).
echo [AUTO-FIX] Dang xoa .venv cu va cap nhat lai moi truong...
rmdir /s /q "%SCRIPT_DIR%\.venv"

if exist "%SCRIPT_DIR%\.venv" (
    echo [ERROR] Khong the xoa .venv. Hay tat cac chuong trinh dang dung no.
    goto :ErrorExit
)
echo [SUCCESS] Da xoa .venv loi.
echo.

:RunUV
echo [EXEC] Running with uv...
uv run python "%ENTRYPOINT%" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto :Finish

:CheckVenv
if exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
    echo [INFO] Detected manual .venv. Running...
    "%SCRIPT_DIR%\.venv\Scripts\python.exe" "%ENTRYPOINT%" %*
    set "EXIT_CODE=!ERRORLEVEL!"
    goto :Finish
)

echo [INFO] Using system python...
python "%ENTRYPOINT%" %*
set "EXIT_CODE=%ERRORLEVEL%"


:Finish
if %EXIT_CODE% NEQ 0 goto :ErrorExit

echo.
echo [INFO] Chuong trinh chay xong thanh cong.
pause
exit /b 0

:ErrorExit
echo.
echo [ERROR] Chuong trinh gap loi (Exit Code: %EXIT_CODE%).
echo [HINT] Kiem tra lai log o tren.
pause
exit /b %EXIT_CODE%