"""Pass 3 — MCP server reconcile (newest-wins, NON-SECRET only).

Parses OpenCode JSON-inline, Codex TOML, and standalone-JSON (Claude/Gemini/
Antigravity/Cursor) into a normalized model, builds a redacted canonical registry,
then ADD-ONLY fans out missing servers into each tool's native format. Existing
servers (and their credentials) are never modified.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import tomli
import tomli_w

from .ctx import Ctx
from .util import (LOG, compile_secret_matchers, newest_mtime, read_json,
                   redact_secrets, write_json)


# --------------------------------------------------------------------------- #
# Tool MCP descriptors
# --------------------------------------------------------------------------- #
def _descriptor(tool) -> dict | None:
    """Return {path, fmt, key, create} for a tool's MCP config, or None."""
    if tool.cfg.get("mcp_toml"):
        return {"path": tool.path("mcp_toml"), "fmt": "toml", "key": "mcp_servers", "create": False}
    if tool.cfg.get("mcp_json"):
        key = tool.cfg.get("mcp_key", "mcpServers")
        # Cursor's global mcp.json may not exist yet — we create it.
        return {"path": tool.path("mcp_json"), "fmt": "json", "key": key,
                "create": tool.name == "cursor"}
    return None


# --------------------------------------------------------------------------- #
# Normalized model:  {transport: stdio|http, command, args, env, url, headers}
# --------------------------------------------------------------------------- #
def _parse_server(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    # http / remote
    if raw.get("url") or raw.get("type") in ("http", "remote", "sse"):
        return {
            "transport": "http",
            "url": raw.get("url", ""),
            "headers": dict(raw.get("headers") or raw.get("http_headers") or {}),
            "env": dict(raw.get("env") or {}),
        }
    # stdio / local
    cmd = raw.get("command")
    if isinstance(cmd, list):
        command, args = (cmd[0] if cmd else ""), list(cmd[1:])
    else:
        command, args = (cmd or ""), list(raw.get("args") or [])
    return {
        "transport": "stdio",
        "command": command,
        "args": args,
        "env": dict(raw.get("env") or {}),
    }


def _load_servers(desc: dict) -> dict[str, dict]:
    path: Path = desc["path"]
    if not path or not path.is_file():
        return {}
    try:
        if desc["fmt"] == "toml":
            with open(path, "rb") as fh:
                data = tomli.load(fh)
            raw = data.get(desc["key"], {})
        else:
            data = read_json(path, {}) or {}
            raw = data.get(desc["key"], {})
    except (OSError, tomli.TOMLDecodeError) as exc:
        LOG.warning("MCP: could not parse %s: %s", path, exc)
        return {}
    return {name: _parse_server(s) for name, s in (raw or {}).items() if isinstance(s, dict)}


# --------------------------------------------------------------------------- #
# Emit normalized server -> native shape per format
# --------------------------------------------------------------------------- #
def _emit(server: dict, fmt: str, key: str) -> dict:
    http = server.get("transport") == "http"
    env = server.get("env") or {}
    if fmt == "toml" or key == "mcp_servers":  # Codex
        if http:
            out = {"url": server.get("url", "")}
            if server.get("headers"):
                out["http_headers"] = server["headers"]
        else:
            out = {"command": server.get("command", ""), "args": server.get("args", [])}
        if env:
            out["env"] = env
        return out
    # OpenCode JSON-inline uses type local/remote + command-as-list
    if key == "mcp":
        if http:
            out = {"type": "remote", "url": server.get("url", "")}
            if server.get("headers"):
                out["headers"] = server["headers"]
        else:
            out = {"type": "local",
                   "command": [server.get("command", "")] + list(server.get("args", []))}
            if env:
                out["env"] = env
        return out
    # Standard mcpServers (Claude / Gemini / Antigravity / Cursor)
    if http:
        out = {"type": "http", "url": server.get("url", "")}
        if server.get("headers"):
            out["headers"] = server["headers"]
    else:
        out = {"command": server.get("command", ""), "args": server.get("args", [])}
        if env:
            out["env"] = env
    return out


def _write_servers(desc: dict, servers_native: dict, ctx: Ctx) -> None:
    """Merge servers_native into the tool's config (add-only) and write."""
    path: Path = desc["path"]
    if ctx.apply:
        ctx.backup(path)
        path.parent.mkdir(parents=True, exist_ok=True)
    if desc["fmt"] == "toml":
        try:
            with open(path, "rb") as fh:
                doc = tomli.load(fh)
        except (OSError, FileNotFoundError, tomli.TOMLDecodeError):
            doc = {}
        block = doc.setdefault(desc["key"], {})
        block.update(servers_native)
        if ctx.apply:
            with open(path, "wb") as fh:
                tomli_w.dump(doc, fh)
    else:
        doc = read_json(path, {}) if path.exists() else {}
        if not isinstance(doc, dict):
            doc = {}
        block = doc.setdefault(desc["key"], {})
        block.update(servers_native)
        if ctx.apply:
            write_json(path, doc)


# --------------------------------------------------------------------------- #
# Pass entry point
# --------------------------------------------------------------------------- #
def run(ctx: Ctx) -> None:
    LOG.info("== Pass 3: MCP servers ==")
    matchers = compile_secret_matchers(ctx.cfg)

    # 1. Load every tool's servers + config mtime (proxy for newest-wins).
    per_tool: dict[str, tuple[dict, dict, float]] = {}  # tool -> (desc, servers, mtime)
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        desc = _descriptor(tool)
        if not desc or not desc["path"]:
            continue
        servers = _load_servers(desc)
        mtime = newest_mtime(desc["path"]) if desc["path"].exists() else 0.0
        per_tool[tool.name] = (desc, servers, mtime)

    if not per_tool:
        LOG.info("no MCP configs found")
        return

    # 2. Build canonical registry: union by name, newest config wins, redacted.
    registry: dict[str, dict] = {}
    origin: dict[str, tuple[str, float]] = {}
    for tname, (_desc, servers, mtime) in per_tool.items():
        for sname, model in servers.items():
            if sname not in registry or mtime > origin[sname][1]:
                red, had = redact_secrets(model, matchers)
                registry[sname] = red
                origin[sname] = (tname, mtime)
                if had:
                    LOG.info("MCP: '%s' carries a credential — redacted in registry", sname)

    write_json(ctx.data_dir / "mcp" / "registry.json", registry)
    ctx.note(f"MCP registry: {len(registry)} servers from {len(per_tool)} tools")

    # 3. Add-only fan-out: give each tool the servers it is missing.
    for tname, (desc, servers, _mtime) in per_tool.items():
        tool = ctx.tools[tname]
        missing = {n: s for n, s in registry.items() if n not in servers}
        if not missing:
            continue
        if not ctx.writable(tool):
            continue
        if not desc["path"].exists() and not desc["create"]:
            ctx.note(f"MCP: {tname} config absent and not auto-created; skipping {list(missing)}")
            continue
        native = {n: _emit(s, desc["fmt"], desc["key"]) for n, s in missing.items()}
        for n, s in missing.items():
            _, had = redact_secrets(s, matchers)
            tag = " (needs credential)" if _emit_has_placeholder(native[n]) else ""
            ctx.record(f"MCP: {tname} <- add '{n}' from {origin[n][0]}{tag}")
        _write_servers(desc, native, ctx)


def _emit_has_placeholder(obj: Any) -> bool:
    from .util import PLACEHOLDER
    if isinstance(obj, str):
        return PLACEHOLDER in obj
    if isinstance(obj, dict):
        return any(_emit_has_placeholder(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_emit_has_placeholder(v) for v in obj)
    return False
