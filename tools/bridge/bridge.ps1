# bridge.ps1 - command line for the bridge system. Use through bridge.cmd in the workspace root.
#   bridge.cmd status
#   bridge.cmd use coffee | use eda
#   bridge.cmd force coffee | force eda    (skip checks, use only if a check is wrong)
#   bridge.cmd release                      (mark no bridge active)
#   bridge.cmd recover                      (popup for a crashed/paused script engine)
#   bridge.cmd popup <id>                   (exit 0 = user pressed Retry, 1 = Cancel)
param([string]$Cmd = 'status', [string]$Arg = '')
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\lib.ps1"

switch ($Cmd) {
    'status' {
        $s = Get-State
        $kill = 'off'
        if (Test-Path $LockFile) { $kill = 'ENGAGED' }
        $e = Test-EdaLoop
        $eText = 'unknown'
        if ($e -eq $true) { $eText = 'responding' } elseif ($e -eq $false) { $eText = 'not responding' }
        "Active bridge  : $($s.active)"
        "Health         : $($s.health)"
        "Since          : $($s.since)"
        "Kill switch    : $kill"
        "Altium running : $(Test-Altium)"
        "eda-agent loop : $eText"
    }
    'use' {
        $r = Switch-Bridge $Arg
        if ($r.ok) { "OK: $($r.msg)"; exit 0 } else { "FAILED: $($r.msg)"; exit 1 }
    }
    'force' {
        if (($Arg -ne 'coffee') -and ($Arg -ne 'eda')) { 'Usage: bridge.cmd force coffee|eda'; exit 1 }
        if (Test-Path $LockFile) { 'Kill switch is engaged; run REARM.cmd first.'; exit 1 }
        Set-State $Arg 'ok'
        Write-Log "FORCED state -> $Arg (checks skipped)"
        "State forced to $Arg"
    }
    'release' {
        Set-State 'none' 'ok'
        Write-Log 'released: no bridge active'
        'No bridge active.'
    }
    'recover' {
        if (Show-Popup 'script_crashed') {
            $s = Get-State
            Set-State $s.active 'ok'
            Write-Log 'recover: user reported script engine restored'
            exit 0
        }
        exit 1
    }
    'popup' {
        if (Show-Popup $Arg) { exit 0 } else { exit 1 }
    }
    default {
        'Commands: status | use coffee|eda | force coffee|eda | release | recover | popup <id>'
        exit 1
    }
}
