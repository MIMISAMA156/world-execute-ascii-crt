@echo off
setlocal
set "ASCII_PROJECT_DIR=%~dp0"
set "CRT_TERMINAL=%~dp0terminal-runtime\terminal-1.24.11911.0\WindowsTerminal.exe"
if not exist "%CRT_TERMINAL%" (
  echo Windows Terminal portable runtime is missing. Run setup.cmd first.
  pause
  exit /b 1
)
start "" "%CRT_TERMINAL%" -w new --maximized new-tab -p "{ce905063-94a0-4b45-82e8-8f62e24561bd}" -d "%~dp0." cmd.exe /d /c run-terminal.cmd --keep-font %*
endlocal
