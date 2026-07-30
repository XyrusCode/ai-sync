# Configuration

All machine-specific values live in `config.local.yaml` (gitignored). The template is `config.example.yaml`.

## Top-level keys

| Key | Description |
|-----|-------------|
| `data_dir` | Hub directory (`~/.ai-sync` by default) |
| `conflict` | Resolution strategy (`newest-wins` only currently) |
| `mcp_memory_json` | Path to shared cross-tool memory JSON |
| `agents_repo` | Path to the canonical agents repo (`AGENTS.md` + `mcp/servers.json`) |
| `agent_limits_data` | Path to agent-limits runtime data (`~/.agents/data/agent-limits`) |
| `secret_field_keys` | Field names that always carry secrets |
| `secret_value_patterns` | Regex patterns that match credential values |

## Per-tool keys

Each tool under `tools:` supports these config keys:

| Key | Type | Description |
|-----|------|-------------|
| `enabled` | bool | Skip tool entirely when false |
| `skills_dirs` | list[str] | Directories containing SKILL.md subdirs |
| `memory_file` | str | Path to global instructions file (AGENTS.md / CLAUDE.md / etc.) |
| `mcp_json` | str | MCP config in JSON format |
| `mcp_toml` | str | MCP config in TOML format |
| `mcp_key` | str | JSON key for MCP servers (default: `mcpServers`) |
| `history_dir` | str | Directory with session files (JSONL per project) |
| `history_db` | str | SQLite database with session data |
| `global_vscdb` | str | Cursor's `state.vscdb` path |
| `session_index` | str | Codex session index file |
| `history_tmp` | str | Gemini tmp directory for per-project chats |
| `projects_json` | str | Gemini projects.json path |
| `inject_history` | bool | Enable history injection into this tool |
| `process_names` | list[str] | Process names for running-app guard |

## Adding a new tool

1. Add a block to `tools:` in `config.local.yaml`
2. Add a reader function in `history_read.py` and add it to `READERS`
3. Optionally add an injector in `history_inject.py` and `INJECTORS`
4. If the tool has skills, add its skills dir to the skills pass
5. If the tool has MCP, its config path will be auto-discovered via `mcp_json` or `mcp_toml`

## Agents repo integration

When `agents_repo` is set:

- **Memory pass**: the repo's `AGENTS.md` gets highest priority (beats tool copies)
- **MCP pass**: the repo's `mcp/servers.json` is parsed as a per-agent catalog; servers are added to each tool's config
