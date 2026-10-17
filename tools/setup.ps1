# setup.ps1 - installs the three Altium MCP servers and registers them for Claude Code.
# Run from any PowerShell (no admin needed):
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\setup.ps1      (from the workspace folder)
# Safe to re-run. One failing server does not stop the others.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
. "$PSScriptRoot\bridge\lib.ps1"      # defines $Root and helpers

$Mcp = Join-Path $Root 'tools\mcp'
foreach ($d in @($Mcp, (Join-Path $Root 'logs'), (Join-Path $Root 'tools\libraries'), (Join-Path $Root 'tools\rules'),
                 (Join-Path $Root 'projects'))) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
$Results = [ordered]@{}
$LibExe = $null; $CoffeePy = $null; $CoffeeStart = $null; $EdaExe = $null

function Fwd { param([string]$p) return ($p -replace '\\', '/') }

function Run {
    param([string]$Exe, [string[]]$ArgList, [string]$Cwd = '')
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    if ($Cwd) { Push-Location $Cwd }
    try { & $Exe @ArgList 2>&1 | ForEach-Object { Write-Host "   $_" } }
    finally { if ($Cwd) { Pop-Location }; $ErrorActionPreference = $old }
    if ($LASTEXITCODE -ne 0) { throw "$Exe $($ArgList -join ' ') failed (exit $LASTEXITCODE)" }
}

function Section {
    param([string]$Name, [scriptblock]$Body)
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
    try { & $Body; $Results[$Name] = 'OK' }
    catch { $Results[$Name] = "FAILED: $($_.Exception.Message)"; Write-Host $_.Exception.Message -ForegroundColor Red }
}

Section 'Preflight' {
    $pv = (& python --version 2>&1 | Out-String).Trim()
    Write-Host "   $pv"
    if ($pv -notmatch 'Python (\d+)\.(\d+)') { throw 'python not found' }
    if (([int]$Matches[1] -lt 3) -or (([int]$Matches[1] -eq 3) -and ([int]$Matches[2] -lt 11))) { throw 'Python 3.11 or newer is required for eda-agent' }
    Write-Host "   $((& git --version 2>&1 | Out-String).Trim())"
    $c = Get-Command claude -ErrorAction SilentlyContinue
    if ($c) { Write-Host "   claude found: $($c.Source)" } else { Write-Host '   WARNING: claude not on PATH in this window (open a new window before using it)' -ForegroundColor Yellow }
}

Section 'Embedded Society: altium-designer-mcp (offline libraries)' {
    $dest = Join-Path $Mcp 'altium-designer-mcp'
    $exe = Get-ChildItem -Path $dest -Recurse -Filter 'altium-designer-mcp.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $exe) {
        $rel = Invoke-RestMethod 'https://api.github.com/repos/embedded-society/altium-designer-mcp/releases/latest' -Headers @{ 'User-Agent' = 'eda-setup' }
        $asset = $rel.assets | Where-Object { ($_.name -match 'windows') -and ($_.name -match '\.zip$') } | Select-Object -First 1
        if (-not $asset) { throw "No Windows .zip in the latest release. Download it from https://github.com/embedded-society/altium-designer-mcp/releases and unzip it into $dest, then re-run." }
        $zip = Join-Path $env:TEMP $asset.name
        Write-Host "   downloading $($asset.name)"
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Expand-Archive -Path $zip -DestinationPath $dest -Force
        $exe = Get-ChildItem -Path $dest -Recurse -Filter 'altium-designer-mcp.exe' | Select-Object -First 1
    }
    if (-not $exe) { throw 'altium-designer-mcp.exe not found after extraction' }
    $script:LibExe = $exe.FullName
    Write-Host "   exe: $script:LibExe"

    $cfgDir = Join-Path $env:USERPROFILE '.altium-designer-mcp'
    $cfg = Join-Path $cfgDir 'config.json'
    # altium-lib may only write inside these folders (the global library needs library)
    $need = @((Fwd (Join-Path $Root 'tools\libraries')), (Fwd (Join-Path $Root 'projects')), (Fwd (Join-Path $Root 'library')))
    if (Test-Path $cfg) {
        Write-Host "   config exists, left unchanged: $cfg" -ForegroundColor Yellow
        $have = @()
        try { $have = @((Get-Content -Raw $cfg | ConvertFrom-Json).allowed_paths | ForEach-Object { (Fwd $_).TrimEnd('/').ToLower() }) }
        catch { Write-Host "   could not read allowed_paths from it: $($_.Exception.Message)" -ForegroundColor Yellow }
        $missing = @($need | Where-Object { $have -notcontains $_.TrimEnd('/').ToLower() })
        if ($missing.Count -eq 0) { Write-Host '   allowed_paths contains every workspace folder' }
        else {
            Write-Host '   allowed_paths is MISSING (add them, then restart Claude Code; see docs\SETUP.md step 4):' -ForegroundColor Yellow
            foreach ($m in $missing) { Write-Host "     $m" -ForegroundColor Yellow }
        }
    } else {
        New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
        $audit = Fwd (Join-Path $Root 'logs\library_audit.jsonl')
        $obj = [ordered]@{
            allowed_paths = $need
            logging       = [ordered]@{ level = 'warn'; audit_log_path = $audit }
        }
        Write-Utf8 $cfg ($obj | ConvertTo-Json -Depth 5)
        Write-Host "   wrote $cfg"
    }
}

Section 'coffeenmusic: altium-mcp (live PCB bridge)' {
    $dest = Join-Path $Mcp 'altium-mcp'
    if (Test-Path (Join-Path $dest '.git')) {
        # Sandbox.pas is scratch that run_altium_script rewrites on every call; a local copy blocks the pull
        Run 'git' @('checkout', '--', 'server/SandboxScript/Sandbox.pas') $dest
        Run 'git' @('pull', '--ff-only') $dest
    }
    else { Run 'git' @('clone', '--depth', '1', 'https://github.com/coffeenmusic/altium-mcp', $dest) $Mcp }
    $start = Join-Path $dest 'start_server.py'
    if (-not (Test-Path $start)) { throw 'start_server.py missing - the repository layout changed' }
    $venv = Join-Path $dest 'server\.venv'
    $py = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path $py)) { Run 'python' @('-m', 'venv', $venv) }
    # start_server.py ignores server\.venv and runs from its own venv in %USERPROFILE%\.altium-mcp\venvs\<hash>.
    # Build that venv now (takes ~45 s, too close to the launcher's 50 s limit on first start).
    Run $py @($start, '--build') $dest
    # mcp 1.5.0 breaks with pydantic >= 2.12; pin the versions from the repo's requirements.txt
    $cv = Get-ChildItem -Path (Join-Path $env:USERPROFILE '.altium-mcp\venvs') -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $cpy = Join-Path $cv.FullName 'Scripts\python.exe'
    Run $cpy @('-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', 'pydantic==2.10.6', 'pydantic-core==2.27.2')
    Run $cpy @('-c', 'from mcp.server.fastmcp import FastMCP')
    $script:CoffeePy = $py
    $script:CoffeeStart = $start
}

Section 'eda-agent (live Altium bridge, review and audit)' {
    $dest = Join-Path $Mcp 'eda-agent'
    if (Test-Path (Join-Path $dest '.git')) { Run 'git' @('pull', '--ff-only') $dest }
    else { Run 'git' @('clone', '--depth', '1', 'https://github.com/salitronic/eda-agent', $dest) $Mcp }
    $venv = Join-Path $dest '.venv'
    $py = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path $py)) { Run 'python' @('-m', 'venv', $venv) }
    Run $py @('-m', 'pip', 'install', '--quiet', '-e', '.') $dest
    $exe = Join-Path $venv 'Scripts\eda-agent.exe'
    if (-not (Test-Path $exe)) { throw 'eda-agent.exe was not created by pip install' }
    $script:EdaExe = $exe   # register the server even if the script copy below fails
    # --force: without it a re-run fails because the folder exists; with it, scripts follow git pull
    # (reload the script project in Altium afterwards)
    Run $exe @('install-scripts', '--force') $dest
}

Section 'Register servers in .mcp.json' {
    $servers = [ordered]@{}
    if ($script:LibExe) {
        $cfgPath = Fwd (Join-Path $env:USERPROFILE '.altium-designer-mcp\config.json')
        $servers['altium-lib'] = [ordered]@{ type = 'stdio'; command = (Fwd $script:LibExe); args = @($cfgPath) }
    }
    if ($script:CoffeePy) {
        $servers['altium-coffee'] = [ordered]@{ type = 'stdio'; command = (Fwd $script:CoffeePy); args = @((Fwd $script:CoffeeStart)) }
    }
    if ($script:EdaExe) {
        $servers['altium-eda'] = [ordered]@{ type = 'stdio'; command = (Fwd $script:EdaExe); args = @('serve') }
    }
    if ($servers.Count -eq 0) { throw 'no server installed successfully, nothing to register' }
    $json = ([ordered]@{ mcpServers = $servers } | ConvertTo-Json -Depth 6)
    if (Test-Path $LockFile) {
        Write-Utf8 $McpOff $json
        Write-Host '   kill switch is engaged: wrote the disabled copy only (run REARM.cmd)' -ForegroundColor Yellow
    } else {
        Write-Utf8 $McpJson $json
        Write-Host "   wrote $McpJson ($($servers.Count) servers)"
    }
    Set-State 'none' 'ok'
}

Section 'Claude Code hook and permissions (.claude\settings.json)' {
    $dir = Join-Path $Root '.claude'
    $file = Join-Path $dir 'settings.json'
    if (Test-Path $file) {
        Write-Host "   $file already exists, left unchanged." -ForegroundColor Yellow
        Write-Host "   It must contain the PreToolUse hook for mcp__altium-.* that runs tools/bridge/guard.ps1 (see README.md)."
    } else {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        $hookCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File ' + (Fwd (Join-Path $Root 'tools\bridge\guard.ps1'))
        $settings = [ordered]@{
            hooks = [ordered]@{
                PreToolUse = @(
                    [ordered]@{
                        matcher = 'mcp__altium-.*'
                        # onFailure=block: a timed-out or crashed hook must block the call, not let it through
                        hooks   = @([ordered]@{ type = 'command'; command = $hookCmd; timeout = 600; onFailure = 'block' })
                    }
                )
            }
            enabledMcpjsonServers = @('altium-lib', 'altium-coffee', 'altium-eda')
            permissions = [ordered]@{ deny = @('Edit(/tools/bridge/**)', 'Edit(/.mcp.json)', 'Edit(/.claude/**)') }
        }
        Write-Utf8 $file ($settings | ConvertTo-Json -Depth 8)
        Write-Host "   wrote $file"
    }
}

Section 'Git repository' {
    if (-not (Test-Path (Join-Path $Root '.git'))) {
        Run 'git' @('init') $Root
        Run 'git' @('add', '-A') $Root
        try { Run 'git' @('commit', '-m', 'Initial EDA workspace') $Root }
        catch { Run 'git' @('-c', 'user.name=EDA setup', '-c', 'user.email=eda@local', 'commit', '-m', 'Initial EDA workspace') $Root }
    } else { Write-Host '   already a git repository' }
}

Section 'Project folders' {
    foreach ($proj in (Get-ChildItem -Path (Join-Path $Root 'projects') -Directory -ErrorAction SilentlyContinue)) {
        foreach ($sub in @('hw', 'libs', 'docs\datasheets', 'outputs', 'ai')) {
            New-Item -ItemType Directory -Force -Path (Join-Path $proj.FullName $sub) | Out-Null
        }
        Write-Host "   folders ready: $($proj.Name)"
    }
}

Section 'Desktop kill-switch shortcut' {
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'EDA KILL SWITCH.lnk'))
    $lnk.TargetPath = Join-Path $Root 'KILL.cmd'
    $lnk.WorkingDirectory = $Root
    $lnk.Save()
    Write-Host '   created "EDA KILL SWITCH" on the desktop'
}

Write-Host ""
Write-Host "================ SUMMARY ================" -ForegroundColor Cyan
foreach ($k in $Results.Keys) {
    $c = 'Green'; if ($Results[$k] -ne 'OK') { $c = 'Red' }
    Write-Host ("{0,-62} {1}" -f $k, $Results[$k]) -ForegroundColor $c
}
Write-Host ""
Write-Host "STILL MANUAL (see README.md):" -ForegroundColor Yellow
Write-Host " 1. Altium: register the eda-agent scripts (DXP > Preferences > Scripting System > Global Projects)."
Write-Host " 2. Open a NEW terminal:  cd $Root   then   claude   then type /mcp to check the three servers."
Write-Host " 3. Run python tools\selftest.py, then the tests in docs\FIRST_RUN_TESTS.md before trusting the bridge switching."
