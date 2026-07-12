"""Unit tests for the safety-critical bits: secret redaction, loop guard,
MCP translators, and the Gemini project-hash algorithm."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_sync.util import compile_secret_matchers, redact_secrets, contains_secret, PLACEHOLDER
from ai_sync.mcp import _parse_server, _emit
from ai_sync.history_model import (synthetic_id, ledger_key, claude_mangle,
                                   gemini_project_hash, SYNCED_PREFIX)

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


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
