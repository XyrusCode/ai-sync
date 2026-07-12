<#
.SYNOPSIS
  Register (or refresh) the daily ai-sync scheduled task at 08:30 local time.

.DESCRIPTION
  The machine's timezone is used as-is; on a WAT (UTC+1) machine 08:30 local is
  08:30 WAT. The task runs whether or not you are logged in (S4U, no stored
  password), at highest run level, and catches up if a run was missed.

.PARAMETER Time
  HH:mm 24-hour local start time. Default 08:30.

.PARAMETER TaskName
  Scheduled task name. Default "AI-Toolchain-Sync".

.PARAMETER Unregister
  Remove the task instead of creating it.
#>
[CmdletBinding()]
param(
    [string]$Time = "08:30",
    [string]$TaskName = "AI-Toolchain-Sync",
    [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot

if ($Unregister) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'."
    } else {
        Write-Host "No task named '$TaskName'."
    }
    return
}

# Resolve a real python.exe (avoid WindowsApps alias stubs).
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python -or $python -match "WindowsApps") {
    $python = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $python) { throw "Could not find python on PATH. Install Python 3.10+ first." }
Write-Host "Using python: $python"
Write-Host "Repo:         $repo"

$action = New-ScheduledTaskAction -Execute $python `
    -Argument "-m ai_sync --apply --log" -WorkingDirectory $repo
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force `
    -Description "Sync skills/memory/MCP/history across AI coding assistants (ai-sync)." | Out-Null

Write-Host "Registered '$TaskName' to run daily at $Time (local time)."
Write-Host "Run now:   Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Inspect:   Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host "Remove:    .\install-schedule.ps1 -Unregister"
