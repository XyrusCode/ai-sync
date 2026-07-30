# Safety Model

ai-sync is designed to never lose data, corrupt configs, or leak secrets.

## Dry-run first

Every run defaults to dry-run: the hub is populated and changes are reported, but no tool-native files are written. Only `--apply` performs writes. Review the dry-run output before applying:

```
python -m ai_sync              # review what would change
python -m ai_sync --apply      # actually write
```

## Running-app guard

Before writing to any tool, ai-sync checks whether that tool's process is running (via `tasklist` on Windows). Writes to a running tool are skipped to prevent:

- SQLite database corruption (OpenCode, Cursor, Kimi, Devin)
- Config file races (Claude, Codex reading while being written)

## Backups

Every native file is backed up before being written:

```
~/.ai-sync/backups/<timestamp>/CLAUDE.md.<hash>
~/.ai-sync/backups/<timestamp>/mcp.json.<hash>
~/.ai-sync/backups/<timestamp>/config.toml.<hash>
```

Each backup filename includes a content hash of the original path to prevent collisions.

## Loop / duplicate guard

Injected sessions carry:

- `originator: "ai-sync"` marker in the metadata
- `synced-` prefix in filenames and session IDs
- A ledger entry in `~/.ai-sync/state/inject-ledger.json`

The aggregate pass skips sessions with the ai-sync marker, re-runs are idempotent.

## Secrets

ai-sync **never** copies credentials between tools. The secret model:

1. **Config files are read** and a canonical registry is built
2. **Values matching `secret_value_patterns`** are redacted to `${REDACTED}` in the registry
3. **Values under `secret_field_keys`** that are raw strings (no `${ENV}` indirection) are redacted
4. **`${ENV}` indirection** is preserved as-is (e.g. `Bearer ${GITHUB_TOKEN}` stays)
5. **Non-secret env values** (e.g. `MEMORY_FILE_PATH`) pass through unchanged
6. **The registry is add-only**: existing servers in a tool's config are never modified
7. **Tool-native files are read; only missing servers are written**

The agents repo `mcp/servers.json` format includes `required_env` arrays — servers whose env vars are unsatisfied are skipped entirely, preventing broken configs from being written.
