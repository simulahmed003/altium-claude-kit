# killswitch.ps1 - emergency stop for the whole Altium MCP system.
#   kill   : lock all MCP calls, disable .mcp.json, stop the MCP server processes
#   rearm  : undo the kill (does not start anything)
#   status : show whether the kill switch is engaged
# It NEVER closes or touches Altium itself.
param([string]$Action = 'kill')
$ErrorActionPreference = 'Continue'
. "$PSScriptRoot\lib.ps1"

switch ($Action) {
    'kill' {
        Set-Content -Path $LockFile -Value ("killed " + (Get-Date -Format 's'))

        $disabled = $false
        if (Test-Path $McpJson) {
            Move-Item -Path $McpJson -Destination $McpOff -Force
            $disabled = $true
        }

        # Allow-list by process name so Altium (X2.exe) and Claude are never touched.
        $pat = '_tools[\\/]mcp[\\/](altium-mcp|eda-agent|altium-designer-mcp)|altium-designer-mcp|eda-agent'
        $victims = Get-CimInstance Win32_Process | Where-Object {
            ($_.ProcessId -ne $PID) -and $_.CommandLine -and ($_.CommandLine -match $pat) -and
            ($_.Name -match '^(python|pythonw|py|altium-designer-mcp|eda-agent)(\.exe)?$')
        }
        $count = 0
        foreach ($v in $victims) {
            try { Stop-Process -Id $v.ProcessId -Force -ErrorAction Stop; $count++ } catch { }
        }

        Set-State 'none' 'killed'
        Write-Log "KILL SWITCH engaged: mcp.json disabled=$disabled, processes stopped=$count"
        Show-Popup 'kill_engaged' -InfoOnly | Out-Null
    }
    'rearm' {
        if (Test-Path $LockFile) { Remove-Item $LockFile -Force }
        if (Test-Path $McpOff) { Move-Item -Path $McpOff -Destination $McpJson -Force }
        Set-State 'none' 'ok'
        Write-Log 'KILL SWITCH rearmed'
        Show-Popup 'kill_rearmed' -InfoOnly | Out-Null
    }
    'status' {
        if (Test-Path $LockFile) { 'Kill switch: ENGAGED' } else { 'Kill switch: off' }
    }
    default { 'Usage: killswitch.ps1 kill|rearm|status' }
}
