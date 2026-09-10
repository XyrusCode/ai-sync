# PowerShell script to close Antigravity and run ai-sync
param(
    [int]$GracePeriodSeconds = 10
)

$ErrorActionPreference = "Continue"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  ai-sync: Post-Antigravity Close Runner" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

if ($GracePeriodSeconds -gt 0) {
    Write-Host "Waiting $GracePeriodSeconds seconds before closing Antigravity..." -ForegroundColor Yellow
    Start-Sleep -Seconds $GracePeriodSeconds
}

Write-Host "Closing Antigravity and Antigravity IDE processes..." -ForegroundColor Yellow
Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$waiting = 0
while (Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue) {
    Write-Host "Waiting for Antigravity processes to completely exit... ($waiting s)" -ForegroundColor Gray
    Start-Sleep -Seconds 1
    $waiting++
    if ($waiting -ge 15) {
        Write-Host "Force-killing remaining Antigravity processes..." -ForegroundColor Red
        Get-Process -Name "Antigravity", "Antigravity IDE" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        break
    }
}

Write-Host "Antigravity is closed. Running full ai-sync (--apply --log)..." -ForegroundColor Green
Write-Host ""

$repoRoot = $PSScriptRoot
if (-not (Test-Path "$repoRoot\ai_sync")) {
    $repoRoot = "C:\Users\Xyrus\Desktop\XyrusCode\ai-sync"
}
Set-Location $repoRoot

python -m ai_sync --apply --log

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  ai-sync completed successfully!" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "Logs saved under: $env:USERPROFILE\.ai-sync\logs\" -ForegroundColor Gray
Write-Host ""
