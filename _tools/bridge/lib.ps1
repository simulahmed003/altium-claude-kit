# lib.ps1 - shared helpers for the Altium MCP bridge system.
# ASCII only, PowerShell 5.1 compatible. Dot-source it:  . "$PSScriptRoot\lib.ps1"

$Here       = $PSScriptRoot
$Root       = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$StateFile  = Join-Path $Here 'bridge_state.json'
$LockFile   = Join-Path $Here 'KILLED.lock'
$PopupFile  = Join-Path $Here 'popups.json'
$LogFile    = Join-Path $Root '_logs\MCP_LOG.md'
$McpJson    = Join-Path $Root '.mcp.json'
$McpOff     = Join-Path $Here 'mcp.disabled.json'
$MaxRetries = 2

function Write-Utf8 {
    param([string]$Path, [string]$Text)
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

function Write-Log {
    param([string]$Msg)
    $dir = Split-Path $LogFile
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    if (-not (Test-Path $LogFile)) {
        Write-Utf8 $LogFile ("# MCP log`r`n`r`n| time | event |`r`n|---|---|`r`n")
    }
    $clean = $Msg -replace '\|', '/'
    Add-Content -Path $LogFile -Value ("| {0} | {1} |" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $clean)
}

function Get-State {
    if (Test-Path $StateFile) {
        try { return (Get-Content -Path $StateFile -Raw | ConvertFrom-Json) } catch { }
    }
    return [pscustomobject]@{ active = 'none'; since = ''; health = 'ok' }
}

function Set-State {
    param([string]$Active, [string]$Health = 'ok')
    $obj = [pscustomobject]@{ active = $Active; since = (Get-Date -Format 's'); health = $Health }
    Write-Utf8 $StateFile ($obj | ConvertTo-Json)
}

function Show-Popup {
    # Returns $true on Retry/OK, $false on Cancel.
    param([string]$Id, [switch]$InfoOnly)
    $title = 'Bridge problem'
    $steps = @("Problem id: $Id")
    try {
        $all  = Get-Content -Path $PopupFile -Raw | ConvertFrom-Json
        $prop = $all.PSObject.Properties[$Id]
        if ($prop) { $title = $prop.Value.title; $steps = @($prop.Value.steps) }
    } catch { }
    $n = 0
    $lines = foreach ($s in $steps) { $n++; "$n. $s" }
    $text = $title + "`r`n`r`n" + ($lines -join "`r`n")
    if (-not $InfoOnly) { $text += "`r`n`r`nPress Retry after you have done this, or Cancel to stop." }
    Add-Type -AssemblyName System.Windows.Forms
    $owner = New-Object System.Windows.Forms.Form
    $owner.TopMost = $true
    $buttons = 'RetryCancel'
    if ($InfoOnly) { $buttons = 'OK' }
    $res = [System.Windows.Forms.MessageBox]::Show($owner, $text, 'Altium MCP bridge', $buttons, 'Warning')
    $owner.Dispose()
    Write-Log "popup $Id -> $res"
    return (($res -eq 'Retry') -or ($res -eq 'OK'))
}

function Test-Altium {
    # Altium Designer runs as X2.EXE
    return [bool](Get-Process -Name 'X2' -ErrorAction SilentlyContinue)
}

function Find-EdaExe {
    $p = Join-Path $Root '_tools\mcp\eda-agent\.venv\Scripts\eda-agent.exe'
    if (Test-Path $p) { return $p }
    return $null
}

function Test-EdaLoop {
    # $true = eda-agent polling loop responds, $false = it does not, $null = cannot tell.
    # Read-only ping of the polling loop (~0.7 s). Do NOT use `eda-agent doctor`: its canary sends
    # application.save_all, which silently saves every open Altium document (found in phase 0).
    # If this check misbehaves, use:  bridge.cmd force eda
    $exe = Find-EdaExe
    if (-not $exe) { return $null }
    $py = Join-Path (Split-Path $exe) 'python.exe'
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $ok = $false
    try {
        & $py -c "import sys; from eda_agent.bridge import get_bridge; sys.exit(0 if get_bridge().ping() else 1)" > $null 2>&1
        $ok = ($LASTEXITCODE -eq 0)
    } catch { $ok = $false } finally { $ErrorActionPreference = $old }
    return $ok
}

function Wait-Until {
    # Runs $Check until it returns $true. Shows a popup between attempts.
    param([scriptblock]$Check, [string]$PopupId, [string]$What)
    $fails = 0
    while ($true) {
        if (& $Check) { return $true }
        if ($fails -ge $MaxRetries) {
            Show-Popup 'restart_needed' -InfoOnly | Out-Null
            Set-State 'none' 'unhealthy'
            Write-Log "FAILED: $What (gave up after $fails retries)"
            return $false
        }
        if (-not (Show-Popup $PopupId)) {
            Write-Log "cancelled by user: $What"
            return $false
        }
        $fails++
    }
}

function New-Result {
    param([bool]$Ok, [string]$Msg = '')
    return [pscustomobject]@{ ok = $Ok; msg = $Msg }
}

function Switch-Bridge {
    param([string]$Target)
    if (($Target -ne 'coffee') -and ($Target -ne 'eda')) { return (New-Result $false "Unknown bridge '$Target'") }
    if (Test-Path $LockFile) {
        return (New-Result $false 'KILL SWITCH is engaged. Tell the user. Do not try to work around it.')
    }
    $st = Get-State

    # Coffee needs Altium's single scripting engine. Check the eda-agent loop on EVERY coffee call,
    # whatever the state file says: the user may have started the loop by hand. Phase 0 test 3b
    # proved it: Altium refuses coffee's script ("cannot run another script while one is running").
    if (($Target -eq 'coffee') -and (Test-Altium)) {
        $released = Wait-Until -Check { (Test-EdaLoop) -ne $true } -PopupId 'eda_loop_active' -What 'release eda-agent loop'
        if (-not $released) { return (New-Result $false 'eda-agent loop still holds the Altium scripting engine') }
    }
    if (($st.active -eq $Target) -and ($st.health -eq 'ok')) { return (New-Result $true 'already active') }
    # Entering eda-agent: Altium must be up and the loop started by the user.
    if ($Target -eq 'eda') {
        $up = Wait-Until -Check { Test-Altium } -PopupId 'altium_not_running' -What 'Altium running'
        if (-not $up) { return (New-Result $false 'Altium is not running') }
        $loop = Wait-Until -Check { (Test-EdaLoop) -ne $false } -PopupId 'eda_loop_not_started' -What 'eda-agent loop started'
        if (-not $loop) { return (New-Result $false 'eda-agent polling loop is not running in Altium') }
    }
    Set-State $Target 'ok'
    Write-Log ("switched {0} -> {1}" -f $st.active, $Target)
    return (New-Result $true 'switched')
}
