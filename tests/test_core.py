"""Unit tests for the safety-critical bits: secret redaction, loop guard,
MCP translators, Gemini project-hash, agents-repo bridge, and
Kiro/Qwen/Windsurf readers."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_sync.util import compile_secret_matchers, redact_secrets, contains_secret, PLACEHOLDER
from ai_sync.mcp import _parse_server, _emit, _agents_repo_servers
from ai_sync.history_model import (synthetic_id, ledger_key, claude_mangle,
                                   gemini_project_hash, SYNCED_PREFIX)
from ai_sync.history_read import read_kiro, read_qwen

CFG = {
    "secret_field_keys": ["headers", "Authorization", "token", "api_key"],
    "secret_value_patterns": [
        r"ghp_[A-Za-z0-9]{20,}", r"sbp_[A-Za-z0-9]{20,}",
        r"AQ\.[A-Za-z0-9_\-]{20,}", r"AIza[A-Za-z0-9_\-]{20,}",
    ],
}


# --------------------------------------------------------------------------- #
# Secret handling
# --------------------------------------------------------------------------- #
def test_inline_token_is_redacted():
    m = compile_secret_matchers(CFG)
    fake = "AQ.FAKEFAKEFAKEFAKEFAKEFAKEFAKE0123456789"  # not a real credential
    server = {"command": "npx", "args": [
        "-y", "mcp-remote", "https://x/mcp",
        "--header", f"X-Goog-Api-Key: {fake}"]}
    red, had = redact_secrets(server, m)
    assert had is True
    flat = " ".join(red["args"])
    assert fake not in flat
    assert PLACEHOLDER in flat


def test_env_indirection_is_preserved():
    m = compile_secret_matchers(CFG)
    server = {"type": "remote", "url": "https://api/mcp",
              "headers": {"Authorization": "Bearer ${GITHUB_TOKEN}"}}
    red, had = redact_secrets(server, m)
    assert had is False  # ${...} indirection is NOT a secret
    assert red["headers"]["Authorization"] == "Bearer ${GITHUB_TOKEN}"


def test_non_secret_env_value_preserved():
    m = compile_secret_matchers(CFG)
    server = {"command": "npx", "args": ["-y", "server-memory"],
              "env": {"MEMORY_FILE_PATH": "C:\\Users\\x\\mcp-memory.json"}}
    red, had = redact_secrets(server, m)
    # 'env' is not secret-classed, and a file path matches no token pattern.
    assert had is False
    assert red["env"]["MEMORY_FILE_PATH"] == "C:\\Users\\x\\mcp-memory.json"


def test_real_secret_inside_env_is_redacted():
    m = compile_secret_matchers(CFG)
    server = {"command": "x", "env": {"SUPABASE_KEY": "sbp_" + "a" * 30}}
    red, had = redact_secrets(server, m)
    assert had is True
    assert red["env"]["SUPABASE_KEY"] == PLACEHOLDER


def test_ghp_token_detected():
    m = compile_secret_matchers(CFG)
    assert contains_secret({"headers": {"Authorization": "Bearer ghp_" + "a" * 30}}, m)


# --------------------------------------------------------------------------- #
# MCP parse/emit round-trips
# --------------------------------------------------------------------------- #
def test_parse_opencode_local():
    s = _parse_server({"type": "local", "command": ["npx", "-y", "pkg"]})
    assert s["transport"] == "stdio"
    assert s["command"] == "npx"
    assert s["args"] == ["-y", "pkg"]


def test_parse_remote():
    s = _parse_server({"type": "remote", "url": "https://x/mcp",
                       "headers": {"H": "v"}})
    assert s["transport"] == "http"
    assert s["url"] == "https://x/mcp"


def test_emit_codex_toml_stdio():
    s = {"transport": "stdio", "command": "npx", "args": ["-y", "pkg"], "env": {}}
    out = _emit(s, "toml", "mcp_servers")
    assert out["command"] == "npx"
    assert out["args"] == ["-y", "pkg"]
    assert "env" not in out  # empty env omitted


def test_emit_opencode_stdio_is_command_list():
    s = {"transport": "stdio", "command": "npx", "args": ["-y", "pkg"], "env": {}}
    out = _emit(s, "json", "mcp")
    assert out["type"] == "local"
    assert out["command"] == ["npx", "-y", "pkg"]


def test_emit_standard_http():
    s = {"transport": "http", "url": "https://x/mcp", "headers": {"H": "v"}}
    out = _emit(s, "json", "mcpServers")
    assert out["type"] == "http"
    assert out["url"] == "https://x/mcp"


# --------------------------------------------------------------------------- #
# Loop guard / idempotency
# --------------------------------------------------------------------------- #
def test_synthetic_id_is_deterministic_and_tagged():
    a = synthetic_id("codex", "sess-1", "claude")
    b = synthetic_id("codex", "sess-1", "claude")
    c = synthetic_id("codex", "sess-1", "gemini")
    assert a == b            # idempotent across runs
    assert a != c            # per-target distinct
    assert a.startswith(SYNCED_PREFIX)


def test_ledger_key_unique_per_pair():
    assert ledger_key("codex", "s1", "claude") != ledger_key("claude", "s1", "codex")


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #
def test_claude_mangle():
    assert claude_mangle("C:/Users/Example/Desktop/Code/XMDB") == \
        "C--Users-Example-Desktop-Code-XMDB"
    assert claude_mangle("C:\\Users\\Example\\tasks") == "C--Users-Example-tasks"


def test_gemini_hash_algorithm():
    # Gemini's projectHash = SHA-256 of the original-case BACKSLASH absolute path
    # (verified against a live tmp/<hash> dir on a real machine). Test the formula
    # with a neutral path so no real username lands in the repo.
    import hashlib
    backslash = "C:\\Users\\Example\\Desktop\\proj"
    expected = hashlib.sha256(backslash.encode("utf-8")).hexdigest()
    assert gemini_project_hash(backslash) == expected
    assert gemini_project_hash("C:/Users/Example/Desktop/proj") == expected  # slash-normalized
    assert gemini_project_hash("C:/Users/Example/Desktop/proj/") == expected  # trailing slash
    assert len(expected) == 64


# --------------------------------------------------------------------------- #
# agents_repo bridge
# --------------------------------------------------------------------------- #
def test_agents_repo_servers_catalog(tmp_path):
    """_agents_repo_servers parses the agents-repo servers.json format."""
    from ai_sync.ctx import Ctx
    from ai_sync.state import State
    from ai_sync.tools import Tool
    mcp_dir = tmp_path / "mcp"
    mcp_dir.mkdir()
    manifest = mcp_dir / "servers.json"
    manifest.write_text(json.dumps({
        "servers": {
            "chrome-devtools": {
                "enabled": True,
                "agents": {
                    "claude": {"command": "npx", "args": ["-y", "cdt"]},
                    "codex": {"command": "npx", "args": ["cdt"]},
                },
            },
            "sentry": {
                "enabled": True,
                "agents": {
                    "claude": {"command": "sentry-mcp", "args": ["--org", "test"]},
                    "codex": {"command": "npx", "args": ["-y", "mcp-remote", "https://sentry/mcp"]},
                },
            },
            "disabled-srv": {
                "enabled": False,
                "agents": {"claude": {"command": "nope"}},
            },
        },
    }), encoding="utf-8")

    cfg = {"agents_repo": str(tmp_path)}
    ctx = Ctx(cfg=cfg, data_dir=tmp_path / "hub", tools={},
              guard=None, state=State(tmp_path / "hub"), apply=False)
    matchers = compile_secret_matchers({})
    catalog = _agents_repo_servers(ctx, matchers)

    assert "claude" in catalog
    assert "codex" in catalog
    assert "chrome-devtools" in catalog["claude"]
    assert "sentry" in catalog["claude"]
    # disabled server should NOT appear
    assert "disabled-srv" not in catalog.get("claude", {})


def test_agents_repo_servers_no_repo():
    """Returns empty dict when agents_repo not configured."""
    from ai_sync.ctx import Ctx
    from ai_sync.state import State
    cfg = {}
    ctx = Ctx(cfg=cfg, data_dir=Path("/tmp/_test_hub"), tools={},
              guard=None, state=State(Path("/tmp/_test_hub")), apply=False)
    matchers = compile_secret_matchers({})
    assert _agents_repo_servers(ctx, matchers) == {}


# --------------------------------------------------------------------------- #
# Kiro history reader
# --------------------------------------------------------------------------- #
def test_read_kiro_jsonl(tmp_path):
    """read_kiro parses Claude-style per-project JSONL."""
    proj = tmp_path / "projects" / "C--Users-test-proj"
    proj.mkdir(parents=True)
    sess_file = proj / "sess-001.jsonl"
    sess_file.write_text(
        '{"message":{"role":"user","content":"hello"}}\n'
        '{"message":{"role":"assistant","content":"hi there"}}\n',
        encoding="utf-8",
    )
    tool = type("Tool", (), {"name": "kiro", "cfg": {"history_dir": str(tmp_path / "projects")},
                             "enabled": True, "path": lambda _, k: Path(tmp_path / "projects"),
                             "paths": lambda _, k: [], "flag": lambda *a: True})()
    sessions = read_kiro(tool)
    assert len(sessions) == 1
    assert len(sessions[0].messages) == 2
    assert sessions[0].messages[0].text == "hello"


def test_read_kiro_skips_synced(tmp_path):
    """read_kiro skips ai-sync injected files."""
    proj = tmp_path / "projects" / "C--Users-test-proj"
    proj.mkdir(parents=True)
    (proj / "synced-abc123.jsonl").write_text(
        '{"message":{"role":"user","content":"skip"}}\n', encoding="utf-8")
    tool = type("Tool", (), {"name": "kiro", "cfg": {"history_dir": str(tmp_path / "projects")},
                             "enabled": True, "path": lambda _, k: Path(tmp_path / "projects"),
                             "paths": lambda _, k: [], "flag": lambda *a: True})()
    assert len(read_kiro(tool)) == 0


# --------------------------------------------------------------------------- #
# Qwen history reader
# --------------------------------------------------------------------------- #
def test_read_qwen_jsonl(tmp_path):
    """read_qwen parses flat JSONL sessions."""
    sess_dir = tmp_path / "sessions"
    sess_dir.mkdir(parents=True)
    (sess_dir / "sess-a.jsonl").write_text(
        '{"role":"user","content":"hello qwen"}\n'
        '{"role":"assistant","content":"hello from qwen"}\n',
        encoding="utf-8",
    )
    tool = type("Tool", (), {"name": "qwen", "cfg": {"history_dir": str(sess_dir)},
                             "enabled": True, "path": lambda _, k: sess_dir,
                             "paths": lambda _, k: [], "flag": lambda *a: True})()
    sessions = read_qwen(tool)
    assert len(sessions) == 1
    assert sessions[0].messages[0].text == "hello qwen"
    assert sessions[0].messages[1].text == "hello from qwen"


# --------------------------------------------------------------------------- #
# agent-limits data model
# --------------------------------------------------------------------------- #
def test_agent_limits_tsv_parse(tmp_path):
    """agent_limits pass parses TSV event logs."""
    from ai_sync.agent_limits import _read_events_tsv
    log = tmp_path / "events.tsv"
    log.write_text("timestamp\tagent\tevent\tdetails\n"
                   "100\tclaude\tstart\tok\n"
                   "200\tclaude\trate_limit\tover\n",
                   encoding="utf-8")
    rows = _read_events_tsv(log)
    assert len(rows) == 2
    assert rows[1]["event"] == "rate_limit"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
