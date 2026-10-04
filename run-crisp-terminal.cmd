@echo off
setlocal
rem Open a dedicated classic console so the player can select its own font.
start "" "%SystemRoot%\System32\conhost.exe" "%ComSpec%" /d /c ""%~dp0run-terminal.cmd" %*"
endlocal
