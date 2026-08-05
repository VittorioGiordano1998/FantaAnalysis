# Links .opencode/{agents,commands} to .claude/{agents,commands}.
#
# Agent and command definitions live once, in .claude/. Claude Code reads them there;
# opencode only scans .opencode/, so we point it at the same files with a junction.
# Skills need no link — opencode already reads .claude/skills/ directly.
#
# Junctions need no admin rights on Windows. Run once per clone:
#   powershell -ExecutionPolicy Bypass -File tools/link-agent-config.ps1

$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot

foreach ($name in @('agents', 'commands')) {
    $link   = Join-Path $repo ".opencode\$name"
    $target = Join-Path $repo ".claude\$name"

    if (-not (Test-Path $target)) {
        throw "Missing source directory: $target"
    }

    $existing = Get-Item $link -Force -ErrorAction SilentlyContinue
    if ($null -ne $existing) {
        if ($existing.LinkType -eq 'Junction' -or $existing.LinkType -eq 'SymbolicLink') {
            Write-Host "ok    .opencode/$name -> .claude/$name (already linked)"
            continue
        }
        throw ".opencode/$name exists and is a real directory. Delete it first, then re-run."
    }

    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "link  .opencode/$name -> .claude/$name"
}
