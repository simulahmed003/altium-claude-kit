@echo off
rem install.cmd - one command to set up (or update) the kit on a Windows PC. Safe to re-run.
rem   install.cmd            check Python / Git / Claude Code, install the three Altium MCP servers (tools\setup.ps1),
rem                          run the selftest and the session preflight, then print what is left to do by hand
rem   install.cmd /full      also install the Python packages of the library tools (tools\requirements-library.txt:
rem                          batch builder, review document, 3D models)
rem   install.cmd /update    git pull first (keeps your local changes; stops if the pull fails)
rem Missing Python or Git: installed with winget when winget is present (you confirm in winget). Nothing is deleted.
setlocal EnableExtensions
cd /d "%~dp0"
set "FULL="
set "UPDATE="
for %%a in (%*) do (
  if /i "%%~a"=="/full" set "FULL=1"
  if /i "%%~a"=="/update" set "UPDATE=1"
)
echo === 1/5 prerequisites
call :need python "Python.Python.3.12" || goto fail
call :need git "Git.Git" || goto fail
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" || (echo Python 3.9 or newer is needed & goto fail)
where claude >nul 2>nul || echo   Claude Code not found: install it from https://code.claude.com/docs (Setup) and re-run.
if defined UPDATE (
  echo === git pull
  git pull --ff-only || (echo git pull failed: commit or stash your changes, then re-run & goto fail)
)
echo === 2/5 Altium MCP servers (tools\setup.ps1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup.ps1"
if errorlevel 1 echo   setup.ps1 reported a problem: read its SUMMARY above (re-running is safe).
echo === 3/5 Python packages
if defined FULL (
  python -m pip install --user -r "%~dp0tools\requirements-library.txt" || echo   pip failed: the offline checkers still work; the library builder and review document need these packages.
) else (
  echo   skipped: the checkers need none. For the library builder / review document: install.cmd /full
)
echo === 4/5 selftest
python "%~dp0tools\selftest.py"
echo === 5/5 preflight
python "%~dp0tools\scripts\doctor.py" --offline
echo.
echo Left to do by hand (once):
echo   1 Altium: register the eda-agent scripts, see docs\SETUP.md "manual Altium step"
echo   2 New terminal: cd /d "%~dp0" ^&^& claude, then type /mcp: altium-lib, altium-coffee, altium-eda are listed
echo   3 A project in your own folder: kit start "D:\Work\Board1"   (kit.cmd is in this folder)
exit /b 0

:need
where %1 >nul 2>nul && exit /b 0
where winget >nul 2>nul || (echo   %1 not found and winget is missing: install it by hand, then re-run & exit /b 1)
echo   %1 not found: winget install %~2
winget install -e --id %~2 || exit /b 1
echo   %1 installed: open a NEW cmd window and run install.cmd again (PATH changes need a new window)
exit /b 1

:fail
echo install stopped. Fix the line above and run install.cmd again.
exit /b 1
