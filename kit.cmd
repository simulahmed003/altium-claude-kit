@echo off
rem kit.cmd - run any kit tool from any folder in cmd.exe:  kit <tool> [arguments]
rem   kit                       list the tools and where the guide is
rem   kit cpl_check --help      help of one tool
rem   kit bom_check "D:\Work\Board1\Manufacturing_B_Rev1.0\B_BOM.csv"
rem Guide with copy-paste commands: docs\TOOLS_GUIDE.md
setlocal
if "%~1"=="" (
  echo Kit tools ^(kit ^<tool^> --help for each; guide: %~dp0docs\TOOLS_GUIDE.md^):
  for %%f in ("%~dp0tools\scripts\*.py") do echo   %%~nf
  echo   selftest
  exit /b 0
)
set "TOOL=%~1"
if /i "%TOOL%"=="selftest" (set "SCRIPT=%~dp0tools\selftest.py") else (set "SCRIPT=%~dp0tools\scripts\%TOOL%.py")
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
