# GitLab CI: Polling and Investigation Patterns

## Prerequisites

`glab` CLI must be authenticated. Verify with `glab auth status`. For API fallback, a `GITLAB_TOKEN` environment variable with `read_api` scope is needed.

## Retrieving a Failing Pipeline

### From a Branch or MR

```powershell
# Get the latest pipeline for the current branch
glab ci status --branch (git branch --show-current)

# Get pipelines for a merge request
glab mr view <mr-id> --web  # opens browser; use API for programmatic access

# List recent pipelines
glab ci list --branch (git branch --show-current) --limit 5
```

### By Pipeline ID

```powershell
# View pipeline details
glab ci view <pipeline-id>

# View pipeline as JSON
glab api projects/{project-id}/pipelines/<pipeline-id>
```

## Extracting Failure Details

### Get Failed Jobs

```powershell
# List jobs for a pipeline, filtered to failed
glab ci view <pipeline-id> --output json | ConvertFrom-Json | Select-Object -ExpandProperty jobs | Where-Object { $_.status -eq "failed" }

# API: get jobs for a pipeline
glab api projects/{project-id}/pipelines/<pipeline-id>/jobs --paginate
```

### Get Job Logs

```powershell
# View a specific job's log (trace), pipe and search
glab ci trace <job-id> | Select-String -Pattern "FAIL|ERROR|assert|panic|failure"

# API: get job trace
glab api projects/{project-id}/jobs/<job-id>/trace
```

### Get Test Reports

If the pipeline produces JUnit reports, retrieve them:

```powershell
# Download job artifacts
glab ci artifact <job-id> <artifact-name>  # interactive
# API
glab api projects/{project-id}/jobs/<job-id>/artifacts --output artifacts.zip
```

## Polling for Completion

### Watch Mode

```powershell
# Blocks until the pipeline completes, refreshes periodically
glab ci status --branch (git branch --show-current) --watch
```

Exits with non-zero if the pipeline fails.

### Manual Polling (for programmatic use)

```powershell
$pipelineId = "<pipeline-id>"
$maxWait = 1800
$interval = 30
$elapsed = 0
do {
    $status = (glab api "projects/{project-id}/pipelines/$pipelineId" | ConvertFrom-Json).status
    if ($status -in @("success", "failed", "canceled", "skipped")) {
        break
    }
    Start-Sleep -Seconds $interval
    $elapsed += $interval
    if ($interval -lt 300) { $interval = [Math]::Min($interval * 2, 300) }
} while ($elapsed -lt $maxWait)
Write-Output "Pipeline $pipelineId: $status"
```

### API Polling

```powershell
glab api "projects/{project-id}/pipelines/$pipelineId" --jq '.status'
```

## Triggering a New Run

### Retry a Pipeline

```powershell
# Retry the entire pipeline
glab ci retry <pipeline-id>

# Retry a specific failed job
glab ci retry <job-id>
```

### Trigger via Push

A regular `git push` triggers the pipeline if the CI config has the branch in its rules. For MR pipelines, push to the source branch.

### Manual Trigger

```powershell
glab ci run --branch (git branch --show-current)
```

## GitLab-Specific Nuances

- **MR pipelines vs branch pipelines**: GitLab distinguishes between pipelines for merge requests and pipelines for branches. Ensure the push triggers the correct pipeline type for the project's CI config.
- **Parent-child pipelines**: If the project uses parent-child pipelines, poll the parent first, then check child pipelines for individual job failures.
- **Manual jobs**: Some jobs require manual approval. Check for `status: "manual"` jobs and either trigger them or note them as blocked.
- **Environments**: Failed deployment jobs may leave environments in a broken state. Note this in the handover if relevant.

## Error Recovery

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| `glab ci status` returns empty | No pipeline for the branch | Check CI config rules; push may not trigger pipeline |
| Pipeline stuck in `pending` | Runner unavailable or tagged runner mismatch | Check runner availability in the project settings; treat as infra failure |
| Job stuck in `running` | Long-running job or hung process | Check job log for progress; timeout after 2x expected job duration |
| `glab ci trace` fails | Job not started or log expired | Re-run the job to generate fresh logs |
