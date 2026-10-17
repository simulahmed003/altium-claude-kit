# guard.ps1 - Claude Code PreToolUse hook for every mcp__altium-* tool call.
# Reads the hook JSON from stdin. Exit 0 = allow. Exit 2 = block (stderr is shown to Claude).
# Fails CLOSED: any error blocks the call.
function Deny {
    param([string]$Msg)
    [Console]::Error.WriteLine($Msg)
    exit 2
}
try {
    $raw = [Console]::In.ReadToEnd()
    $tool = ''
    if ($raw) { $tool = [string](($raw | ConvertFrom-Json).tool_name) }
    . "$PSScriptRoot\lib.ps1"

    if (Test-Path $LockFile) {
        Deny 'KILL SWITCH IS ENGAGED. All Altium MCP calls are blocked. Tell the user and stop. Do not try to bypass this.'
    }
    if ($tool -notmatch '^mcp__altium-(lib|coffee|eda)__') {
        Deny "guard: unrecognised tool name '$tool'"
    }
    $server = $Matches[1]
    if ($server -eq 'lib') { exit 0 }    # offline library server never touches the live Altium engine

    $r = Switch-Bridge $server
    if ($r.ok) { exit 0 }
    Deny ("Bridge switch to '$server' failed: " + $r.msg + ". Do NOT retry in a loop. Tell the user what the popup asked for and wait.")
} catch {
    [Console]::Error.WriteLine("guard error (blocked for safety): $_")
    exit 2
}
