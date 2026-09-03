# AGENTS — Global instructions and critical rules

## PR/MR Creation — CLI Auto-Detection

When creating a pull request or merge request, detect the remote and use the appropriate CLI:

- **GitHub** (`github.com`) → Use `gh pr create`
- **Azure DevOps** (`dev.azure.com` or `*.visualstudio.com`) → Use `az repos pr create`
- **GitLab** (`gitlab.com` or self-hosted) → Use `gl mr create`

**Implementation:**
1. Check the repo remote with `git remote get-url origin`
2. Route to the appropriate CLI based on domain
3. If CLI is not installed, assist with manual creation via web UI
4. Assume CLIs are installed; they are standard on this machine

## Critical Rules

- Prevent context rot: When a session grows heavy (many turns, many files, re-deriving state), split the work into a fresh, nested context before output quality degrades. Use a native nested-session primitive if available; otherwise emit a self-contained handoff prompt. Checkpoint before splitting. See `docs/context-rot.md` for full procedure and templates.

- Never commit directly to main. Always create a branch and open a Pull Request for review and CI before merging. This repository enforces review-first changes.

(Other global rules and conventions live here.)
