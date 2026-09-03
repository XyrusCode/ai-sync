# Cross-Agent Memory Index

Shared state and context for AI agents operating on this machine. Persists across sessions and tools.

> **Memory Hub:** `~/.ai-sync/memory/`
> **Primary Index:** This file (canonical reference for what's tracked)
> **Per-Tool Mirrors:** Each tool reads via its memory_file config entry

## Structure

Memory is organized by scope:
- **Global** — XyrusCode machine state, multi-tool coordination
- **Per-Project** — Repository-specific context (auto-generated per session)
- **Per-Agent** — Tool-specific state (Claude, Codex, Gemini, etc.)

## Global Memory Entries

### Active Work Tracking

| Entry | Format | Source | Updated By |
|-------|--------|--------|------------|
| `work-in-flight.md` | Markdown list | User + sessions | End-of-session teardown |
| `pr-watch.json` | JSON array | PR watcher | `pr_watch.py` daemon |
| `context-limits.json` | JSON object | Context rust guard | Measurement pass (daily) |

### Preferences & Settings

| Entry | Format | Owner | Purpose |
|-------|--------|-------|---------|
| `user-prefs.yaml` | YAML | User setup | Persistent user preferences (model, reasoning_effort, etc.) |
| `agent-switch-profiles.json` | JSON | Auth tools | Auth profiles (Claude, Codex, Gemini) |
| `tool-availability.json` | JSON | Health check | Which tools are running/available |

### MCP & Configuration

| Entry | Format | Source | Purpose |
|-------|--------|--------|---------|
| `mcp-servers.json` | JSON | Canonical catalog | Authoritative MCP server list (separate from config.yaml) |
| `mcp-overrides.yaml` | YAML | Per-tool config | Tool-specific MCP command/args overrides |

### Shared Learning

| Entry | Format | Owner | Purpose |
|-------|--------|-------|---------|
| `lessons-learned.md` | Markdown | Sessions | Captured corrections & patterns (cross-session reference) |
| `integration-notes.md` | Markdown | Integration work | Notes on tool integrations, breaking changes, workarounds |

## Memory Lifecycle

### Creation
- **Session start** — Context injection reads per-project history
- **First reference** — Auto-create entry if needed (e.g., new worktree)

### Update
- **Mid-session** — Sessions update work-in-flight, PR watch on state change
- **End-of-session** — Teardown pass records final state (merged PRs, torn-down worktrees)
- **Daemon processes** — Background watchers update incrementally (PR watcher, health check)

### Cleanup
- **Expiration** — Entries >30 days old marked for cleanup (manual review before deletion)

## Integration with ai-sync Passes

1. **Skills Pass** — No memory output
2. **Memory Pass** — Reads all tool memory files, picks canonical source (agents repo or hub), fans out
3. **MCP Pass** — Uses canonical `mcp-servers.json` (separated from config.yaml)
4. **History Pass** — Populates per-project session history
5. **Agent Limits Pass** — Writes `context-limits.json` with measurements

## Best Practices

1. **Keep AGENTS.md canonical** — All agent-specific mirrors are derived from here
2. **Index new entries here** — When adding new memory entries, document them in this file
3. **Expire old entries explicitly** — Mark stale entries with `<!-- EXPIRES: YYYY-MM-DD -->` comments
4. **Use memory for state, skills for procedures** — Memory tracks *who/what/when*; skills encode *how*
5. **Measure context cost** — Top sessions are tracked in `context-limits.json`; respect the handoff/pickup guard

## Related

- [ai-sync Architecture](docs/architecture.md)
- [AGENTS.md](AGENTS.md) — Canonical instruction set
- [Instruction Tiering](~/.agents/docs/instructions-tiering.md)
- [Context Rot Prevention](~/.agents/docs/context-rot.md)