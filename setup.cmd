@echo off
setlocal
set "PYTHONUTF8=1"
if exist "%~dp0runtime\python.exe" (
  "%~dp0runtime\python.exe" -X utf8 "%~dp0tools\setup.py" %*
  goto finished
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "%~dp0tools\setup.py" %*
  goto finished
)
python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if not errorlevel 1 (
  python -X utf8 "%~dp0tools\setup.py" %*
  goto finished
)
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>&1
if not errorlevel 1 (
  py -3 -X utf8 "%~dp0tools\setup.py" %*
  goto finished
)
echo Python 3.10+ not found. Install Python from https://www.python.org/downloads/windows/
pause
exit /b 1
:finished
set "SETUP_EXIT=%ERRORLEVEL%"
if errorlevel 1 pause
endlocal & exit /b %SETUP_EXIT%
