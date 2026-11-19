<#
.SYNOPSIS
    Installs Windows Scheduled Tasks for unattended local Instagram autoposting.
.DESCRIPTION
    Creates two scheduled tasks:
    1. ShipStack-MorningPipeline: Runs every morning at 09:00 AM IST to generate
       the 25 daily posts (15 Pubity-style single news cards + 5 physics reels + 5 ball reels).
    2. ShipStack-Dispatcher: Runs every 35 minutes throughout the day to automatically
       publish the next due post to Instagram.
#>

param(
    [switch]$Uninstall
)

$TaskPrefix = "ShipStack"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = (Get-Command python.exe -ErrorAction Stop).Source

if ($Uninstall) {
    Write-Host "Removing existing scheduled tasks..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName "$TaskPrefix-MorningPipeline" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "$TaskPrefix-Dispatcher" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "$TaskPrefix-DailyPost" -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "$TaskPrefix-CalendarReels" -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Uninstalled ShipStack scheduled tasks." -ForegroundColor Green
    return
}

Write-Host "Registering Windows Scheduled Tasks for ShipStack 25-Post Daily Workflow..." -ForegroundColor Cyan

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# 1. Morning Generation Pipeline: 09:00 AM IST Daily
$ActionMorning = New-ScheduledTaskAction -Execute $PythonExe -Argument "$RepoDir\morning_pipeline.py" -WorkingDirectory $RepoDir
$TriggerMorning = New-ScheduledTaskTrigger -Daily -At "09:00"

Register-ScheduledTask -TaskName "$TaskPrefix-MorningPipeline" -Action $ActionMorning -Trigger $TriggerMorning -Principal $Principal -Description "ShipStack Morning 25-Post Multi-Agent Builder (09:00 AM IST)" -Force | Out-Null
Write-Host " [OK] Registered task: $TaskPrefix-MorningPipeline (Runs daily at 09:00 AM IST)" -ForegroundColor Green

# 2. Automated Dispatcher: Runs every 35 minutes
$ActionDispatcher = New-ScheduledTaskAction -Execute $PythonExe -Argument "$RepoDir\daily_publisher.py" -WorkingDirectory $RepoDir
$TriggerInterval = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 35) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "$TaskPrefix-Dispatcher" -Action $ActionDispatcher -Trigger $TriggerInterval -Principal $Principal -Description "ShipStack 35-minute automated Instagram dispatcher" -Force | Out-Null
Write-Host " [OK] Registered task: $TaskPrefix-Dispatcher (Runs every 35 minutes throughout the day)" -ForegroundColor Green

Write-Host "`nAll scheduled tasks registered! Your laptop will automatically build the 25 posts each morning at 09:00 AM and publish them hands-off throughout the day." -ForegroundColor Cyan
