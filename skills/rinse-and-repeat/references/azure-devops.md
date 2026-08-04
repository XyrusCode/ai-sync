# Azure DevOps: Polling and Investigation Patterns

## Prerequisites

Azure CLI with the `azure-devops` extension. Verify with `az devops configure --list`. For REST API fallback, a Personal Access Token (PAT) with `Build (Read)` scope is needed.

```powershell
# Install the extension if missing
az extension add --name azure-devops

# Set defaults (avoids repeating --org --project each time)
az devops configure --defaults organization=https://dev.azure.com/{org} project={project}
```

## Retrieving a Failing Build

### From a Branch

```powershell
# Get the latest build for the current branch
az pipelines runs list --branch (git branch --show-current) --top 1

# List recent builds
az pipelines runs list --top 5
```

### By Build ID

```powershell
# View build details
az pipelines runs show --id <build-id>

# View with specific fields
az pipelines runs show --id <build-id> --query "{id: id, status: status, result: result, reason: reason}" -o json
```

### By PR

```powershell
# Get build for a PR (requires knowing the PR ID and build definition)
az pipelines runs list --branch refs/pull/<pr-id>/merge --top 1

# Or search by source branch
az pipelines runs list --branch <source-branch> --top 1
```

## Extracting Failure Details

### Get Timeline (Failed Tasks)

```powershell
# Retrieve the timeline for a build to see individual task results
az pipelines runs show --id <build-id> --query "timeline"  # incomplete, use API

# REST API for full timeline with task details
az devops invoke --area build --resource timeline --organization $org --query-parameters buildId=<build-id> | ConvertFrom-Json | Select-Object -ExpandProperty records | Where-Object { $_.result -eq "failed" }
```

### Get Task Logs

```powershell
# Download logs for a failed task (requires log ID from timeline)
az devops invoke --area build --resource logs --organization $org --route-parameters buildId=<build-id> logId=<log-id> --api-version 6.0
```

### Get Test Results

```powershell
# If the pipeline publishes test results
az devops invoke --area test --resource results --organization $org --route-parameters project=<project> runId=<run-id> --api-version 6.0
```

### Alternative: Use the Web Portal

Azure DevOps log retrieval via CLI is cumbersome. For quick investigation, open the build in a browser:

```powershell
az pipelines runs show --id <build-id> --open
```

Extract relevant error output from the browser and paste into the investigation.

## Polling for Completion

### No Built-In Watch

Azure DevOps `az pipelines runs` has no built-in watch mode. Use manual polling:

```powershell
$buildId = "<build-id>"
$maxWait = 1800
$interval = 30
$elapsed = 0
do {
    $build = (az pipelines runs show --id $buildId --query "{status: status, result: result}" -o json | ConvertFrom-Json)
    if ($build.status -eq "completed") {
        break
    }
    Write-Output "Build $buildId: $($build.status)..."
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    if ($interval -lt 300) { $interval = [Math]::Min($interval * 2, 300) }
} while ($elapsed -lt $maxWait)
Write-Output "Build $buildId: status=$($build.status), result=$($build.result)"
```

### REST API Polling

```powershell
az devops invoke --area build --resource builds --organization $org --route-parameters buildId=$buildId --query-parameters api-version=6.0 --query "status" -o tsv
```

## Triggering a New Run

### Queue a New Build

```powershell
# Queue a new build for a pipeline definition
az pipelines run --name "<pipeline-name>" --branch (git branch --show-current)

# Queue with variables
az pipelines run --name "<pipeline-name>" --branch (git branch --show-current) --variables key1=value1 key2=value2
```

### Trigger via Push

A regular `git push` triggers the CI build if the pipeline's trigger settings include the branch. For PR builds (build validation policies), push to the source branch.

## Azure DevOps-Specific Nuances

- **Build vs Release**: CI runs are "builds" (build pipelines). Deployment pipelines are "releases". This skill focuses on build pipelines.
- **Build policies**: PR builds may not trigger on every push if the branch policy has path filters. Check the PR's "Required checks" section.
- **YAML vs Classic**: The pipeline definition format (YAML or classic editor) affects how triggers and variables work but not the CLI interaction pattern.
- **Multi-stage pipelines**: A single build may have multiple stages (build, test, deploy). Check each stage's result; a build may show "succeeded" while a later stage failed.
- **Agent pools**: Self-hosted agents may be offline or busy. A build stuck in `notStarted` likely means no agent is available. Treat as infrastructure failure.

## Error Recovery

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Build stuck in `notStarted` | No agent available | Check agent pool status; treat as infra failure, retry once |
| Build stuck in `inProgress` | Hung task or timeout | Check the timeline for the stuck task; cancel if no progress after 2x expected |
| `az pipelines runs show` returns 404 | Wrong build ID or project | List recent builds to find the correct ID |
| Log ID not found | Task hasn't started yet or logs expired | Wait for task to start, or re-run the build |
| Auth error | PAT expired or scope insufficient | Regenerate PAT with `Build (Read)` scope |
