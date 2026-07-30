# install.ps1 — Idempotent ai-sync setup for a new Windows machine
# Run from the repo root: cd ai-sync && .\install.ps1
#
# Ported from agents/install.sh patterns:
#   - Creates symlinks to shared AGENTS.md
#   - Installs Python dependencies
#   - Schedules daily sync via Task Scheduler
#   - Non-destructive: never clobbers existing files

param(
    [switch]$Unregister,
    [switch]$Quiet
)

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentsDir = if (Test-Path "$env:USERPROFILE\Desktop\XyrusCode\agents") {
    "$env:USERPROFILE\Desktop\XyrusCode\agents"
} elseif (Test-Path "$env:USERPROFILE\.agents") {
    "$env:USERPROFILE\.agents"
} else {
    Write-Warning "agents repo not found. Set AGENTS_REPO env var or clone to ~/Desktop/XyrusCode/agents"
    $null
}

$HubDir = "$env:USERPROFILE\.ai-sync"
$Python = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

function Write-Step {
    param([string]$Message)
    if (-not $Quiet) { Write-Host "  → $Message" }
}

function Install-Deps {
    Write-Step "Installing Python dependencies..."
    & $Python -m pip install -r "$RepoDir\requirements.txt" -q 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Dependencies installed."
    } else {
        Write-Warning "pip install failed. Run: pip install -r requirements.txt"
    }
}

function Install-Symlinks {
    if (-not $AgentsDir) { return }
    Write-Step "Creating symlinks to shared AGENTS.md..."

    $links = @(
        @{Target = "$AgentsDir\AGENTS.md"; Link = "$env:USERPROFILE\.config\opencode\AGENTS.md"; Dir = "$env:USERPROFILE\.config\opencode" }
        @{Target = "$AgentsDir\AGENTS.md"; Link = "$env:USERPROFILE\.codex\AGENTS.md"; Dir = "$env:USERPROFILE\.codex" }
    )

    foreach ($entry in $links) {
        $dir = $entry.Dir
        $link = $entry.Link
        $target = $entry.Target
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        if (Test-Path $link) {
            $item = Get-Item $link -Force
            if ($item.LinkType -eq 'SymbolicLink') {
                Write-Step "  ✓ $($entry.Link) (already correct)"
            } else {
                Write-Warning "  ⚠ $link exists and is not a symlink — skipping"
            }
        } else {
            New-Item -ItemType SymbolicLink -Path $link -Target $target -Force | Out-Null
            Write-Step "  → $link -> $target"
        }
    }
}

function Install-Schedule {
    $taskName = "AI-Toolchain-Sync"
    $action = New-ScheduledTaskAction -Execute "$Python" -Argument "-m ai_sync --apply --log" -WorkingDirectory $RepoDir
    $trigger = New-ScheduledTaskTrigger -Daily -At 08:30
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited

    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
        Write-Step "Scheduled daily sync: 08:30 daily ($taskName)"
    } catch {
        Write-Warning "Failed to register scheduled task: $_"
    }
}

function Install-Completions {
    Write-Step "Adding PowerShell completion..."
    $profileDir = Split-Path -Parent $PROFILE
    if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
    $completionLine = "if (Test-Path '$RepoDir\completions\ai-sync.ps1') { . '$RepoDir\completions\ai-sync.ps1' }"
    $profileContent = if (Test-Path $PROFILE) { Get-Content $PROFILE -Raw } else { "" }
    if ($profileContent -notmatch [regex]::Escape($completionLine)) {
        Add-Content -Path $PROFILE -Value "`n$completionLine" -Encoding utf8
        Write-Step "Added completion to PowerShell profile"
    } else {
        Write-Step "✓ Completions already in profile"
    }
}

function Test-Setup {
    Write-Step "Running dry-run to verify setup..."
    & $Python -m ai_sync
    if ($LASTEXITCODE -eq 0) {
        Write-Step "Dry-run succeeded."
    } else {
        Write-Warning "Dry-run failed. Check config.local.yaml"
    }
}

# --- Main ---

if ($Unregister) {
    $taskName = "AI-Toolchain-Sync"
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "  → Removed scheduled task '$taskName'"
    } else {
        Write-Host "  Task '$taskName' not found."
    }
    return
}

Write-Host ""
Write-Host "  ai-sync install"
Write-Host "  Repo: $RepoDir"
Write-Host "  Hub:  $HubDir"
Write-Host ""

# 1. Install deps
Install-Deps

# 2. Create hub directory
if (-not (Test-Path $HubDir)) {
    New-Item -ItemType Directory -Path $HubDir -Force | Out-Null
    Write-Step "Created hub $HubDir"
}

# 3. Create config.local.yaml if missing
$localConfig = "$RepoDir\config.local.yaml"
if (-not (Test-Path $localConfig)) {
    Copy-Item "$RepoDir\config.example.yaml" $localConfig
    Write-Step "Created $localConfig from template"
    Write-Host "       EDIT IT to match your tool paths before running sync"
}

# 4. Symlinks
Install-Symlinks

# 5. Schedule
Install-Schedule

# 6. Completions
Install-Completions

# 7. Verify
Test-Setup

Write-Host ""
Write-Host "Done!"
Write-Host "  - Daily sync scheduled at 08:30"
Write-Host "  - Run manually: python -m ai_sync --apply"
Write-Host "  - View status: python bin/ai-sync-status"
Write-Host "  - Edit config: $localConfig"
Write-Host ""
