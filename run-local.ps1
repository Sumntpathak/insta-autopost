<#
.SYNOPSIS
    Convenience PowerShell launcher for ShipStack workflows.

.EXAMPLE
    .\run-local.ps1 morning            # Runs 09:00 AM multi-agent pipeline (15 news + 5 physics + 5 ball)
    .\run-local.ps1 dispatch           # Publishes next due slot from today's schedule
    .\run-local.ps1 dispatch --daemon  # Runs continuous background publishing loop
    .\run-local.ps1 status             # Checks tokens & API connectivity
#>

param(
    [Parameter(Position=0)]
    [string]$Command = "status",

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

if ($Command -eq "morning") {
    python "$RepoRoot\morning_pipeline.py" $RemainingArgs
} elseif ($Command -eq "dispatch") {
    python "$RepoRoot\daily_publisher.py" $RemainingArgs
} else {
    python "$RepoRoot\local_runner.py" $Command $RemainingArgs
}
