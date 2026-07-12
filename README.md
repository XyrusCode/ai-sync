# ai-sync

Keep your AI coding assistants in agreement. `ai-sync` reconciles **skills**,
**memory/instructions**, **MCP servers** and **chat history** across six tools on
one machine, and can **inject each tool's past sessions into the others** so that
when several of them work in the same project directory, they can see each other's
history. It runs once a day from Windows Task Scheduler.

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
| **Cursor** | ✅ (19) | reads `AGENTS.md` | ✅ JSON | ✅ SQLite | ⚙️ opt-in |
| **Devin** | – | reads `AGENTS.md` | – (cloud/ACP) | ✅ SQLite | ⏸ deferred |

✅ on by default · ⚙️ implemented, opt-in via `inject_history: true` · ⏸ deferred
(needs schema/cloud work). Injection confidence and rationale are in
[the design notes](#injection-feasibility).

## How it works

A canonical hub (`~/.ai-sync/`) is the source of truth; conflicts resolve
**newest-wins**. One Python engine runs five ordered passes:

1. **Skills** — union every tool's skills, newest copy wins, fan out to all.
2. **Memory** — reconcile one canonical `AGENTS.md`, write it to each tool's
   global memory file (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`).
3. **MCP** — parse JSON-inline, TOML and standalone-JSON configs into one model
   and **add** missing servers to each tool. **Non-secret only:** real inline
   tokens are redacted to `${REDACTED}`, `${ENV}` indirection is preserved, and
   existing credentials are never touched.
4. **History aggregate** — normalize every tool's sessions (JSONL / SQLite /
   per-project JSON) into `~/.ai-sync/history/<project>/`.
5. **History inject** — write each tool's sessions into the *others'* native
   stores, tagged so they can never loop or duplicate.

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

```powershell
pip install -r requirements.txt
Copy-Item config.example.yaml config.local.yaml     # adjust paths only if non-default
python -m ai_sync                                   # DRY-RUN: review what would change
python -m ai_sync --apply                           # actually sync
.\install-schedule.ps1                              # run daily at 08:30 local time
```

`config.local.yaml` is gitignored — it is the only file with real paths, and it
never leaves your machine.

### CLI

```
python -m ai_sync                 # dry-run (default)
python -m ai_sync --apply         # write changes
python -m ai_sync --only mcp      # one pass: skills | memory | mcp | history
python -m ai_sync --apply --log   # also write ~/.ai-sync/logs/sync-YYYY-MM-DD.log
```

### Schedule

`install-schedule.ps1` registers a Task Scheduler job **AI-Toolchain-Sync** that
runs `python -m ai_sync --apply --log` daily at 08:30 local time (08:30 WAT on a
UTC+1 machine), whether or not you are logged in, catching up missed runs.

```powershell
Start-ScheduledTask -TaskName AI-Toolchain-Sync         # run now
Get-ScheduledTask -TaskName AI-Toolchain-Sync | Get-ScheduledTaskInfo
.\install-schedule.ps1 -Unregister                       # remove
```

## Injection feasibility

| Target | Method | Status |
|---|---|---|
| Claude | write `projects/<mangled>/synced-*.jsonl` | on |
| Codex | write `sessions/…/rollout-synced-*.jsonl` + index | on |
| Gemini | write `tmp/<projectHash>/chats/session-synced-*.json` | on |
| OpenCode | INSERT `session`/`message`/`part` (closed + backup) | opt-in |
| Cursor | INSERT `cursorDiskKV` composer rows | opt-in¹ |
| Antigravity | protobuf `conversations/*.pb` | deferred² |
| Devin | INSERT `sessions.db` | deferred³ |

¹ Cursor's `state.vscdb` carries per-composer encryption-key fields; enable only
after validating against a backup. ² Needs the Antigravity protobuf schema.
³ Devin's local `sessions.db` is cloud-driven and normally empty.

## Development

```powershell
python -m pytest tests/ -q
```

Tests cover secret redaction, MCP format round-trips, the loop/idempotency
guard, and the Gemini project-hash algorithm.

## License

MIT — see [LICENSE](LICENSE).
