# newproject.ps1 - create a project from the template (wrapper for tools\scripts\new_project.py).
#   powershell -NoProfile -ExecutionPolicy Bypass -File D:\EDA\tools\newproject.ps1 -Name my-board
param([Parameter(Mandatory = $true)][string]$Name)
$ErrorActionPreference = 'Stop'
& python (Join-Path $PSScriptRoot 'scripts\new_project.py') $Name
exit $LASTEXITCODE
