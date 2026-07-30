# ai-sync

Keep your AI coding assistants in agreement. `ai-sync` reconciles **skills**,
**memory/instructions**, **MCP servers** and **chat history** across eleven AI
tools on one Windows machine, and can **inject each tool's past sessions into
the others** so that when several work in the same project, they see each
other's history. Runs daily from Windows Task Scheduler.

> **This repo is code only.** It never contains your paths, config data, or
> secrets. All machine-specific values live in a local, gitignored
> `config.local.yaml`; the runtime hub lives at `~/.ai-sync/` and is never
> committed.

## Supported tools

| Tool | Skills | Memory | MCP | History (read) | History (inject) |
|---|:--:|:--:|:--:|:--:|:--:|
| **Claude Code** | ✅ | ✅ `CLAUDE.md` | ✅ JSON | ✅ | ✅ high |
| **OpenCode** | ✅ | ✅ `AGENTS.md` | ✅ JSON-inline | ✅ SQLite | ⚙️ opt-in |
| **Codex** | ✅ | ✅ `AGENTS.md` | ✅ TOML | ✅ | ✅ high |
| **Gemini / Antigravity** | – | ✅ `GEMINI.md` | ✅ JSON | ✅ Gemini | ✅ Gemini · ⏸ Antigravity |
| **Cursor** | ✅ | reads `AGENTS.md` | ✅ JSON | ✅ SQLite | ⚙️ opt-in |
| **Kimi** | ✅ | ✅ `index.md` | – | ✅ SQLite | ⏸ deferred |
| **Devin** | – | reads `AGENTS.md` | – (cloud/ACP) | ✅ SQLite | ⏸ deferred |
| **Kiro** | – | ✅ `KIRO.md` | ✅ JSON | ✅ JSONL | ⏸ deferred |
| **Qwen** | – | ✅ `QWEN.md` | ✅ JSON | ✅ JSONL | ⏸ deferred |
| **Windsurf** | ✅ | reads `.cursorrules` | ✅ JSON | ✅ SQLite | ⏸ deferred |

✅ on by default · ⚙️ implemented, opt-in via `inject_history: true` · ⏸ deferred

## Design inspiration

This project is heavily inspired by the [agents](https://github.com/9jaGuy/agents)
repo — the canonical multi-agent configuration hub. Key patterns adopted:

- **Agents repo bridge**: `agents_repo` config points to the shared `~/.agents/`
  checkout; its `AGENTS.md` and `mcp/servers.json` are the highest-priority
  canonical source for memory and MCP configuration ([docs/architecture.md](docs/architecture.md))
- **CLI tools**: `bin/ai-sync-mcp` (standalone MCP generator) and
  `bin/ai-sync-status` (live hub dashboard) mirror the agents repo's
  `sync-mcp` and `agent-limits` CLI tools
- **Idempotent install**: `install.ps1` automates the full setup (deps, symlinks,
  scheduled task, completions) — port of `agents/install.sh`
- **Rate-limit bridge**: the `agent_limits` pass reads the agents repo's
  `agent-limits` data files into the hub for cross-tool reporting
- **Tiered docs**: `docs/` directory with architecture, config, and safety-model
  guides — following the agents repo documentation pattern
- **Task tracking**: `tasks/todo.md` and `tasks/lessons.md` for session continuity

## How it works

A canonical hub (`~/.ai-sync/`) is the source of truth. One Python engine runs
five ordered passes:

1. **Skills** — union every tool's skills, newest copy wins, fan out to all.
2. **Memory** — reconcile one canonical `AGENTS.md` (agents repo copy has
   highest priority), write to each tool's global memory file.
3. **MCP** — parse JSON-inline, TOML and standalone-JSON configs into one model
   and **add** missing servers to each tool. The agents repo's `mcp/servers.json`
   catalog is merged in as the authoritative per-agent source.
4. **History aggregate** — normalize every tool's sessions (JSONL / SQLite /
   per-project JSON) into `~/.ai-sync/history/<project>/`.
5. **History inject** — write each tool's sessions into the *others'* native
   stores, tagged so they can never loop or duplicate.
6. **Agent limits** — read rate-limit event logs and status caches from the
   agents repo's `agent-limits` data into the hub.

### Safety model

- **Dry-run by default.** `python -m ai_sync` reports and populates the hub but
  writes nothing to your tools. Only `--apply` mutates native stores.
- **Running-app guard.** Writes to any tool that is currently open are skipped
  (prevents SQLite/`state.vscdb` corruption).
- **Backups.** Every native file is copied to `~/.ai-sync/backups/<timestamp>/`
  before it is written.
- **Loop / duplicate guard.** Injected sessions carry an `ai-sync` marker and a
  `synced-` id recorded in an inject-ledger; the aggregate pass skips them, so
  re-runs are idempotent.
- **Secrets stay put.** The engine never moves, copies, or overwrites a token.
  See [`config.example.yaml`](config.example.yaml) for the redaction rules.

## Install

Requires Python 3.10+ (Windows).

### Quick install (recommended)

```powershell
.\install.ps1
```

This installs deps, creates config.local.yaml, sets up symlinks, schedules the
daily sync at 08:30, and adds PowerShell completions.

### Manual install

```powershell
pip install -r requirements.txt
Copy-Item config.example.yaml config.local.yaml     # adjust paths
python -m ai_sync                                   # DRY-RUN
python -m ai_sync --apply                           # actually sync
.\install-schedule.ps1                              # daily at 08:30
```

`config.local.yaml` is gitignored — it is the only file with real paths, and it
never leaves your machine.

### CLI

```
python -m ai_sync                          # dry-run (default)
python -m ai_sync --apply                  # write changes
python -m ai_sync --only mcp               # single pass
python -m ai_sync --apply --log            # with log file
python bin/ai-sync-status                  # live hub dashboard
python bin/ai-sync-mcp                     # standalone MCP diff
python bin/ai-sync-mcp generate            # write MCP configs
```

### Schedule

`install-schedule.ps1` or `install.ps1` register a Task Scheduler job
**AI-Toolchain-Sync** that runs `python -m ai_sync --apply --log` daily at
08:30 local time.

```powershell
Start-ScheduledTask -TaskName AI-Toolchain-Sync
Get-ScheduledTask -TaskName AI-Toolchain-Sync | Get-ScheduledTaskInfo
.\install-schedule.ps1 -Unregister
```

## Project layout

```
ai-sync/
  ai_sync/              # Python engine (5+ passes)
    __main__.py         # CLI entry point
    ctx.py              # shared run context
    state.py            # persisted sync state (manifest, ledger)
    tools.py            # per-tool registry + running-app guard
    skills.py           # Pass 1: skill reconciliation
    memory.py           # Pass 2: memory/instructions
    mcp.py              # Pass 3: MCP server sync
    history_read.py     # Pass 4: session aggregation
    history_inject.py   # Pass 5: cross-tool injection
    agent_limits.py     # Pass 6: rate-limit data bridge
    util.py             # shared helpers
  bin/
    ai-sync-mcp         # standalone MCP diff/generate CLI
    ai-sync-status      # live hub status dashboard
  completions/
    ai-sync.ps1         # PowerShell tab completion
  docs/
    architecture.md     # pass design, hub layout, safety model
    configuration.md    # per-tool config reference
    safety-model.md     # dry-run, backups, secrets, loop guard
  tasks/
    todo.md             # work tracking
    lessons.md          # captured learnings
  install.ps1           # idempotent Windows installer
  install-schedule.ps1  # Task Scheduler registration
  config.example.yaml   # template (copy to config.local.yaml)
```

## Injection feasibility

| Target | Method | Status |
|---|---|---|
| Claude | write `projects/<mangled>/synced-*.jsonl` | on |
| Codex | write `sessions/…/rollout-synced-*.jsonl` + index | on |
| Gemini | write `tmp/<projectHash>/chats/session-synced-*.json` | on |
| Kiro | write `projects/<mangled>/synced-*.jsonl` | on |
| OpenCode | INSERT `session`/`message`/`part` (closed + backup) | opt-in |
| Cursor | INSERT `cursorDiskKV` composer rows | opt-in¹ |
| Antigravity | protobuf `conversations/*.pb` | deferred² |
| Devin | INSERT `sessions.db` | deferred³ |
| Kimi | INSERT `conversations.sqlite` | deferred |
| Qwen | flat JSONL | deferred |
| Windsurf | SQLite | deferred |

¹ Cursor's `state.vscdb` carries per-composer encryption-key fields; enable only
after validating against a backup. ² Needs the Antigravity protobuf schema.
³ Devin's local `sessions.db` is cloud-driven and normally empty.

## Development

```powershell
python -m pytest tests/ -q
```

Tests cover secret redaction, MCP format round-trips, loop/idempotency guard,
Gemini project-hash, agents_repo bridge, Kiro/Qwen readers, and agent-limits
TSV parsing.

## License

MIT — see [LICENSE](LICENSE).
