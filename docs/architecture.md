# Architecture

ai-sync keeps your AI coding assistants in agreement through five ordered passes:

## Passes

1. **Skills** — Union every tool's skills, newest copy wins, fan out to all
2. **Memory** — Reconcile one canonical AGENTS.md, write to each tool's global memory file (agents repo copy has highest priority)
3. **MCP** — Parse JSON-inline, TOML, and standalone-JSON configs; add missing servers from the agents repo catalog; build a redacted canonical registry
4. **History aggregate** — Normalize every tool's sessions (JSONL / SQLite / per-project JSON) into `~/.ai-sync/history/<project>/`
5. **History inject** — Write each tool's sessions into the others' native stores, tagged to prevent loops

## Data flow

```
  Tool A ──> Pass 1 (skills) ──> Hub ──> Pass 1 ──> Tool B
  Tool A ──> Pass 2 (memory) ──> Hub ──> Pass 2 ──> Tool B
  Tool A ──> Pass 3 (MCP)    ──> Hub ──> Pass 3 ──> Tool B
  Tool A ──> Pass 4 (history) ──> Hub
  Hub     ──> Pass 5 (inject)  ──> Tool B
```

## Hub layout

```
~/.ai-sync/
  state/manifest.json         # newest-wins change detection
  state/inject-ledger.json    # loop/duplicate guard
  state/project-map.json      # canonical project key ↔ per-tool representations
  memory/AGENTS.md            # canonical global instructions
  skills/<name>/              # canonical skill directories
  mcp/registry.json           # redacted MCP server union
  mcp/agents-repo-catalog.json # per-agent MCP servers from agents repo
  history/<project>/          # normalized sessions
  agent-limits/rate-limits.json  # rate-limit data from agent-limits
  backups/<timestamp>/        # pre-write backups
  logs/sync-YYYY-MM-DD.log    # dated run logs
```

## Safety model

- **Dry-run by default** — `--apply` required to write
- **Running-app guard** — skips writes to open tools (prevents SQLite corruption)
- **Backups** — every native file copied to `~/.ai-sync/backups/<timestamp>/` before write
- **Loop/duplicate guard** — injected sessions carry `ai-sync` marker + `synced-` prefix; aggregate pass skips them
- **Secrets stay put** — never moves, copies, or overwrites a token
