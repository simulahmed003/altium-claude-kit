@echo off
rem kit.cmd - run any kit tool from any folder in cmd.exe:  kit <tool> [arguments]
rem   kit                       list the tools and where the guide is
rem   kit cpl_check --help      help of one tool
rem   kit bom_check "D:\Work\Board1\Manufacturing_B_Rev1.0\B_BOM.csv"
rem   kit doctor                session preflight (servers, hook, git up to date, one Altium)
rem   kit start "D:\Work\Board1" start Claude Code in this workspace with that project folder added (WF-10)
rem   kit lib_build plan.json   batch library build (tools\library_build\build.py, P13)
rem   kit install [/full]       re-run the installer (install.cmd)
rem Guide with copy-paste commands: docs\TOOLS_GUIDE.md
setlocal
if "%~1"=="" (
  echo Kit tools ^(kit ^<tool^> --help for each; guide: %~dp0docs\TOOLS_GUIDE.md^):
  for %%f in ("%~dp0tools\scripts\*.py") do echo   %%~nf
  echo   selftest
  echo   start ["project folder"]
  echo   lib_build plan.json
  echo   install [/full] [/update]
  exit /b 0
)
set "TOOL=%~1"
if /i "%TOOL%"=="start" (
  cd /d "%~dp0"
  python "%~dp0tools\scripts\doctor.py" --offline
  if "%~2"=="" (claude) else (claude --add-dir "%~2")
  exit /b %ERRORLEVEL%
)
if /i "%TOOL%"=="install" (
  call "%~dp0install.cmd" %2 %3
  exit /b %ERRORLEVEL%
)
if /i "%TOOL%"=="selftest" (set "SCRIPT=%~dp0tools\selftest.py") else if /i "%TOOL%"=="lib_build" (set "SCRIPT=%~dp0tools\library_build\build.py") else (set "SCRIPT=%~dp0tools\scripts\%TOOL%.py")
if not exist "%SCRIPT%" (
  echo No tool named %TOOL%. Run "kit" for the list.
  exit /b 1
)
set "ARGS="
:loop
shift
if "%~1"=="" goto run
set ARGS=%ARGS% %1
goto loop
:run
python "%SCRIPT%" %ARGS%
exit /b %ERRORLEVEL%
