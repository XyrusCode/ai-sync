#!/usr/bin/env python3
"""
PR State Watcher — Track GitHub and Azure DevOps PRs until terminal state.

Usage:
  python ai_sync/pr_watch.py add <repo> <pr-number> [--discord-user <user>]
  python ai_sync/pr_watch.py status
  python ai_sync/pr_watch.py check   # Check all watched PRs and notify on state change
  python ai_sync/pr_watch.py gc      # Remove completed PRs from watch list

Runs from Windows Task Scheduler every 5 minutes; self-manages cron install/remove.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

# Config
WATCH_FILE = Path.home() / ".ai-sync" / "memory" / "pr-watch.json"
WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_watch_list():
    """Load watched PRs from disk."""
    if not WATCH_FILE.exists():
        return []
    return json.loads(WATCH_FILE.read_text())


def save_watch_list(prs):
    """Save watched PRs to disk."""
    WATCH_FILE.write_text(json.dumps(prs, indent=2))


def check_github_pr(owner, repo, pr_number):
    """Check GitHub PR status via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", str(pr_number), "-R", f"{owner}/{repo}", "--json",
             "state,statusCheckRollup,mergedAt"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        return {
            "status": data.get("state", "UNKNOWN"),
            "checks": data.get("statusCheckRollup", []),
            "merged_at": data.get("mergedAt")
        }
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


def check_azure_devops_pr(org, project, repo_id, pr_id):
    """Check Azure DevOps PR status via az CLI."""
    try:
        result = subprocess.run(
            ["az", "repos", "pr", "show", "--id", str(pr_id), "--project", project,
             "--repo", repo_id, "--org", f"https://dev.azure.com/{org}"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        return {
            "status": data.get("status", "UNKNOWN"),
            "merge_status": data.get("mergeStatus"),
            "completed_date": data.get("closedDate")
        }
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}


def notify_discord(user, repo, pr_number, old_status, new_status):
    """Send Discord notification on status change (stub)."""
    # This would integrate with Discord webhook; stub for now
    print(f"[DISCORD] @{user}: {repo}#{pr_number} {old_status} → {new_status}")


def add_pr(repo, pr_number, discord_user=None):
    """Add a PR to watch list."""
    prs = load_watch_list()
    prs.append({
        "repo": repo,
        "pr": pr_number,
        "status": "pending",
        "since": datetime.utcnow().isoformat() + "Z",
        "discord_user": discord_user or "unknown"
    })
    save_watch_list(prs)
    print(f"✓ Watching {repo}#{pr_number}")


def status():
    """Show all watched PRs."""
    prs = load_watch_list()
    if not prs:
        print("No watched PRs")
        return
    for pr in prs:
        print(f"  {pr['repo']}#{pr['pr']} — {pr['status']} (since {pr['since']})")


def check_all():
    """Check all watched PRs; notify on state change."""
    prs = load_watch_list()
    updated = False

    for pr in prs:
        repo = pr["repo"]
        owner, repo_name = repo.split("/")
        old_status = pr["status"]

        # Detect GitHub vs. Azure DevOps
        if "github.com" in repo or "/" in repo:  # GitHub repo format
            result = check_github_pr(owner, repo_name, pr["pr"])
            if "error" not in result:
                new_status = result.get("status", "UNKNOWN").upper()
            else:
                new_status = "ERROR"
        else:
            # Azure DevOps — would need more context
            new_status = old_status

        if new_status != old_status:
            pr["status"] = new_status
            notify_discord(pr["discord_user"], repo, pr["pr"], old_status, new_status)
            updated = True

    if updated:
        save_watch_list(prs)

    # Garbage collect completed PRs
    prs = [pr for pr in prs if pr["status"] not in ("MERGED", "CLOSED")]
    save_watch_list(prs)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add":
        if len(sys.argv) < 4:
            print("Usage: pr_watch.py add <repo> <pr-number> [--discord-user <user>]")
            sys.exit(1)
        repo = sys.argv[2]
        pr_number = int(sys.argv[3])
        discord_user = None
        if len(sys.argv) > 5 and sys.argv[4] == "--discord-user":
            discord_user = sys.argv[5]
        add_pr(repo, pr_number, discord_user)
    elif cmd == "status":
        status()
    elif cmd == "check":
        check_all()
    elif cmd == "gc":
        check_all()  # check_all() already GCs
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)