---
name: Rinse and Repeat
description: This skill should be used when the user asks to "rinse and repeat", "fix CI", "fix this CI failure", "get CI green", "poll for results", "CI loop", "fix failing tests and wait", "keep fixing until it passes", "semi-auto CI", "paste CI output", or describes a failing CI/test pipeline on GitHub Actions, GitLab CI, or Azure DevOps and wants an automated investigate-fix-push-poll loop until the pipeline passes or the retry budget is exhausted. Supports full-auto (agent polls CI) and semi-auto (user pastes CI output) modes.
version: 0.1.0
---

# Rinse and Repeat

## Overview

A systematic loop for fixing CI/test failures: investigate the failure, apply a fix, push, poll the CI platform for results, and repeat until the pipeline passes or the retry budget runs out. When the budget is exhausted or the failure proves unfixable in the current session, hand over with a clear summary.

**Core cycle:** Investigate → Fix → Push → Poll → { Pass: done | Fail: repeat | Budget exhausted: handover }

## When to Use

Engage this skill when:

- A CI pipeline is failing and the user wants to fix it iteratively
- Tests fail and the user asks to "keep fixing until green"
- The user explicitly invokes "rinse and repeat" or "CI loop"
- A PR has red checks and the user wants an automated remediation loop
- The user describes a test/CI failure and expects an investigative fix cycle

Do not engage for one-off fixes where the user explicitly wants a single attempt.

## Operating Modes

Two modes, chosen at the start of each loop based on what is possible in the environment:

### Full-Auto Mode

The agent polls the CI platform and retrieves logs automatically using the platform's CLI or API. Use when:

- The platform CLI is installed and authenticated (`gh`, `glab`, or `az devops`)
- The agent can poll without exhausting rate limits
- The CI run ID or pipeline ID is known or discoverable

Workflow: investigate failure from fetched logs → fix → push → poll → repeat.

### Semi-Auto Mode

The agent cannot reach the CI platform directly (no CLI, no auth, air-gapped, or the platform blocks automated log retrieval). The user acts as the relay for CI results.

Workflow:

1. Agent applies a fix and pushes.
2. Agent tells the user: "Pushed. Let me know when CI completes and paste the failure output if it fails."
3. Agent waits. **Do not poll or make repeated status calls.**
4. User pastes the CI output (logs, error text, screenshot description).
5. Agent investigates the pasted output and either fixes again or reports success.

Ask upfront which mode to use if it is unclear. Default to full-auto when the platform CLI is available; fall back to semi-auto when any step (auth, discovery, polling) fails.

**Semi-auto prompt template:**

> Pushed commit `<sha>`. CI is running. Paste the output when it finishes, or let me know if it passes.

## The Loop

### Step 1: Assess the Failure

Before touching any code, understand the failure:

1. Retrieve the failing CI run details from the platform. Use the platform-specific CLI or API patterns in the reference files below.
2. Extract the failure output: logs, test names, stack traces, assertion diffs.
3. Categorize the failure: flaky test, genuine regression, infrastructure/timeout, lint/format, build error, or dependency issue.
4. If the failure is clearly infrastructure (runner died, network timeout, capacity), retry the job once before proceeding. If it persists after one retry, treat it as a genuine failure.

### Step 2: Investigate Locally

Reproduce the failure locally when possible:

1. Run the failing test or build command in the local checkout. If it passes locally, note the discrepancy (environment, seed, ordering, platform).
2. If it fails locally, use standard debugging: read the failing code, trace callers, check recent changes (`git log` for related commits).
3. Form a hypothesis before making changes. State it briefly (one line).

### Step 3: Apply a Fix

Apply the smallest change that addresses the root cause:

- **Flaky test**: Add wait/retry, fix ordering dependency, or stabilize the assertion.
- **Regression**: Fix the code, not the test (unless the test expectation was wrong).
- **Lint/format**: Run the project's formatter/linter.
- **Build error**: Fix type errors, missing imports, or dependency issues.
- **Dependency**: Pin versions, update lockfiles, or fix breaking API usage.

Commit the fix with a clear message describing what was wrong and how it was fixed. Push immediately.

### Step 4: Poll for Results (Full-Auto) or Wait for User (Semi-Auto)

**Full-auto**: After pushing, poll the CI platform until the run completes:

1. Trigger a new CI run if the platform does not auto-trigger on push.
2. Poll at increasing intervals: start at 30 seconds, back off to 60, then 120.
3. Retrieve the full run status when complete.

Platform-specific polling commands and patterns are documented in:
- **`references/github-actions.md`** — `gh run watch`, `gh run view`, API polling
- **`references/gitlab-ci.md`** — `glab ci status`, `glab ci view`, pipeline polling
- **`references/azure-devops.md`** — `az pipelines runs`, build polling

**Semi-auto**: Tell the user CI is running and wait for them to paste the results. Do not poll.

### Step 5: Decide

On poll completion, branch on the result:

| Result | Action |
|--------|--------|
| **All green** | Done. Report success and stop. |
| **Still failing** | Increment attempt counter. If under budget: go to Step 1 with the new failure. If budget exhausted: handover. |
| **Different failure** | Same as "still failing" but note the regression introduced by the fix. Revert if needed. |
| **Timeout / stuck** | Cancel the run, note it, and treat as a failure for budgeting purposes. |

## Configuration

Default values; override per-task based on user input:

- **Max retries**: 5 (range: 3–10)
- **Poll initial interval**: 30 seconds
- **Poll backoff**: double each interval, cap at 300 seconds
- **Retry infrastructure failures**: 1 automatic retry before counting as a genuine failure

## Handover

When the retry budget is exhausted or the failure cannot be fixed:

1. **Summarize** what was tried, what each attempt changed, and what the remaining failure looks like.
2. **Recommend** next steps: is this a deeper bug needing a specialist, a flaky test needing quarantine, or an infrastructure issue needing platform admin?
3. **Handover format** — choose based on context:
   - **PR open**: If a PR exists and the branch has partial progress worth reviewing, summarize in a PR comment and leave the branch for the user.
   - **Issue**: If the failure is a pre-existing bug or needs tracking, create an issue with the investigation summary, reproduction steps, and attempted fixes.
   - **Plain summary**: In all cases, produce a concise summary of what happened, what was attempted, and what remains.

## Anti-Patterns to Avoid

- **Shotgun debugging**: Do not make random changes hoping something sticks. Each fix must have a hypothesis.
- **Endless loop**: Always track attempts against the budget. Never retry more than the configured max without explicit user consent.
- **Silent handover**: Never stop without a summary. Even on success, state what fixed it.
- **Ignoring local reproduction**: Always attempt to reproduce locally. A fix without local verification is a guess.
- **Force-pushing**: Never force-push. Use regular push only.

## Tracking State

Maintain minimal state across the loop:

- **Attempt counter**: Start at 1, increment each cycle.
- **Failure log**: One line per attempt: what failed, what was changed, what happened next.
- **Budget remaining**: Max retries minus attempts used.

Use the session database (SQL `todos` table or a dedicated tracking table) for structured tracking.

## Quick Reference

### CLI Polling (one-liners)

| Platform | Watch command |
|----------|--------------|
| GitHub Actions | `gh run watch <run-id>` |
| GitLab CI | `glab ci status --watch` |
| Azure DevOps | `az pipelines runs show --id <id> --query "status" -o tsv` |

Full patterns, API fallback, and error handling in the platform reference files.

## Additional Resources

### Reference Files

- **`references/github-actions.md`** — gh CLI and API patterns for GitHub Actions
- **`references/gitlab-ci.md`** — glab CLI and API patterns for GitLab CI
- **`references/azure-devops.md`** — az CLI and REST API patterns for Azure DevOps

### Related Skills

- **Peer Review workflow** (`~/.agents/docs/git-workflow.md`): For opening PRs and managing review cycles after CI passes.
- **Testing** (`~/.agents/docs/testing.md`): For TDD and test-writing conventions.
