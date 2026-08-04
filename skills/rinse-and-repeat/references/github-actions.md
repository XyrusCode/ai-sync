# GitHub Actions: Polling and Investigation Patterns

## Prerequisites

`gh` CLI must be authenticated. Verify with `gh auth status`. For API fallback, a `GITHUB_TOKEN` environment variable with `actions:read` scope is needed.

## Retrieving a Failing Run

### From a PR

```powershell
# Get the latest run for the current branch
gh run list --branch (git branch --show-current) --limit 1 --json databaseId,status,conclusion,headSha

# Get the latest run for a specific PR
gh pr checks <pr-number>
```

### By Run ID

```powershell
# View run details
gh run view <run-id> --json status,conclusion,jobs,workflowName

# View run with full log (truncated by default)
gh run view <run-id> --log
```

### By Workflow

```powershell
# List recent runs for a workflow
gh run list --workflow "<workflow-name>" --limit 5
```

## Extracting Failure Details

### Get Failed Jobs

```powershell
gh run view <run-id> --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name: .name, url: .url, steps: [.steps[] | select(.conclusion == "failure") | {name: .name, number: .number}]}'
```

### Download Full Logs

```powershell
# Download all logs for a run (produces a zip)
gh run download <run-id>

# View a specific job's log (piped, no pagination)
gh run view <run-id> --log | Select-String -Pattern "FAIL|ERROR|assert|panic"
```

### Get Failure Annotations

```powershell
# Annotations (lint failures, type errors, test failures surfaced by problem matchers)
gh api repos/{owner}/{repo}/actions/runs/<run-id>/annotations
```

## Polling for Completion

### Watch Mode (simplest)

```powershell
# Blocks until the run completes, refreshes every few seconds
gh run watch <run-id>
```

If `gh run watch` exits with a non-zero code, the run failed. Exit code 0 means success.

### Manual Polling (for programmatic use)

```powershell
# Poll loop pattern in PowerShell
$runId = "<run-id>"
$maxWait = 1800  # 30 minutes
$interval = 30
$elapsed = 0
do {
    $status = (gh run view $runId --json status,conclusion | ConvertFrom-Json)
    if ($status.status -eq "completed") {
        break
    }
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    if ($interval -lt 300) { $interval = [Math]::Min($interval * 2, 300) }
} while ($elapsed -lt $maxWait)
Write-Output "Run $runId: status=$($status.status), conclusion=$($status.conclusion)"
```

### API Fallback (when gh CLI is unavailable)

Use the REST API directly for maximum control:

```powershell
# Check run status
gh api repos/{owner}/{repo}/actions/runs/<run-id> --jq '.status, .conclusion'

# List jobs for a run
gh api repos/{owner}/{repo}/actions/runs/<run-id>/jobs --jq '.jobs[] | {name: .name, status: .status, conclusion: .conclusion}'

# Get job logs URL
gh api repos/{owner}/{repo}/actions/jobs/<job-id>/logs --include
```

## Triggering a New Run

### Re-run a Failed Run

```powershell
# Re-run only failed jobs
gh run rerun <run-id> --failed

# Re-run all jobs
gh run rerun <run-id>
```

### Trigger via Push

A regular `git push` to a branch with an active PR triggers the workflow automatically. No explicit re-run needed unless the push hook is disabled or the workflow filters by path.

### Manual Dispatch

```powershell
gh workflow run "<workflow-name>" --ref (git branch --show-current)
```

## Error Recovery

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| `gh run watch` hangs | Runner queued or stuck | Check `gh run view <id> --json status`, cancel if `queued` > 10 min |
| `gh run view` returns empty | Wrong run ID or repo | Verify with `gh run list --limit 1` |
| Log download fails | Logs expired (90 days) | Re-run the failed job to generate fresh logs |
| API rate limit | Too many requests | Wait, or use `gh run watch` instead of manual polling |
