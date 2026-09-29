"""Pass 3 — MCP server reconcile (newest-wins, NON-SECRET only).

Parses OpenCode JSON-inline, Codex TOML, and standalone-JSON (Claude/Gemini/
Antigravity/Cursor) into a normalized model, builds a redacted canonical registry,
then ADD-ONLY fans out missing servers into each tool's native format. Existing
servers (and their credentials/disabled status) are never modified.

Also enforces the persistent removal log (mcp-removals.json) so uninstalled MCPs
are purged across all tool configs and never re-installed.
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


def _delete_server(desc: dict, server_name: str, ctx: Ctx) -> None:
    """Delete a server from the tool's native config file."""
    path: Path = desc["path"]
    if not path or not path.is_file():
        return
    if ctx.apply:
        ctx.backup(path)
    if desc["fmt"] == "toml":
        try:
            with open(path, "rb") as fh:
                doc = tomli.load(fh)
        except (OSError, FileNotFoundError, tomli.TOMLDecodeError):
            return
        block = doc.get(desc["key"], {})
        if isinstance(block, dict) and server_name in block:
            del block[server_name]
            if ctx.apply:
                with open(path, "wb") as fh:
                    tomli_w.dump(doc, fh)
    else:
        doc = read_json(path, {})
        if not isinstance(doc, dict):
            return
        block = doc.get(desc["key"], {})
        if isinstance(block, dict) and server_name in block:
            del block[server_name]
            if ctx.apply:
                write_json(path, doc)


# --------------------------------------------------------------------------- #
# Removals log handling
# --------------------------------------------------------------------------- #
def _load_removals(ctx: Ctx) -> set[str]:
    """Load persistent removal log of uninstalled MCPs from all locations."""
    locations: list[Path] = [
        Path(__file__).resolve().parent.parent / "mcp-removals.json",
        ctx.data_dir / "mcp" / "removals.json",
    ]
    repo = ctx.cfg.get("agents_repo")
    if repo:
        locations.append(Path(repo) / "mcp" / "removals.json")

    removals: set[str] = set()
    for loc in locations:
        if loc.is_file():
            try:
                data = read_json(loc, {}) or {}
                items = data.get("removals") or []
                for item in items:
                    if isinstance(item, str) and item.strip():
                        removals.add(item.strip())
            except Exception as exc:
                LOG.warning("MCP: could not parse removals log %s: %s", loc, exc)

    if removals:
        LOG.info("MCP: loaded %d uninstalled servers from removal log: %s",
                 len(removals), ", ".join(sorted(removals)))
    return removals


# --------------------------------------------------------------------------- #
# Pass entry point
# --------------------------------------------------------------------------- #
def _agents_repo_servers(ctx: Ctx, matchers, removals_lower: set[str]) -> dict[str, dict[str, dict]]:
    """Read the canonical MCP catalog from the agents repo (mcp/servers.json).

    Returns {agent_name: {server_name: normalized_model}} so the registry can
    merge the catalog's per-agent definitions into each tool's server pool.
    Excludes any server in the removals set.
    """
    repo = ctx.cfg.get("agents_repo")
    if not repo:
        return {}
    manifest = Path(repo) / "mcp" / "servers.json"
    if not manifest.is_file():
        return {}
    try:
        data = read_json(manifest, {}) or {}
    except Exception as exc:
        LOG.warning("agents_repo mcp/servers.json read failed: %s", exc)
        return {}
    raw_servers = data.get("servers") or {}
    if not raw_servers:
        return {}

    result: dict[str, dict[str, dict]] = {}
    for sname, sdef in raw_servers.items():
        if not isinstance(sdef, dict):
            continue
        if sname.lower() in removals_lower:
            continue
        if not sdef.get("enabled", True):
            continue
        agents_block = sdef.get("agents") or {}
        for agent, acfg in agents_block.items():
            if not isinstance(acfg, dict):
                continue
            model = _parse_server(acfg)
            red, _had = redact_secrets(model, matchers)
            result.setdefault(agent, {})[sname] = red
    total = sum(len(v) for v in result.values())
    LOG.info("MCP: agents_repo catalog: %d servers across %d agents", total, len(result))
    return result


def _agents_repo_add_manifest(ctx: Ctx, catalog: dict[str, dict[str, dict]]) -> None:
    """Write the agents_repo catalog as a separate manifest in the hub."""
    out = ctx.data_dir / "mcp" / "agents-repo-catalog.json"
    write_json(out, catalog)


def run(ctx: Ctx) -> None:
    LOG.info("== Pass 3: MCP servers ==")
    matchers = compile_secret_matchers(ctx.cfg)
    removals = _load_removals(ctx)
    removals_lower = {r.lower() for r in removals}

    # Save removals manifest in hub data dir
    if ctx.apply:
        write_json(ctx.data_dir / "mcp" / "removals.json", {"removals": sorted(list(removals))})

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

    # 1b. Scrub uninstalled/removed MCPs from all enabled tool configurations.
    for tname, (desc, servers, _mtime) in list(per_tool.items()):
        tool = ctx.tools[tname]
        for sname in list(servers.keys()):
            if sname.lower() in removals_lower:
                ctx.record(f"MCP: {tname} -> purge uninstalled '{sname}'")
                if ctx.writable(tool):
                    _delete_server(desc, sname, ctx)
                del servers[sname]

    # 1c. Load canonical catalog from agents repo (if configured), ignoring removals.
    catalog = _agents_repo_servers(ctx, matchers, removals_lower)
    _agents_repo_add_manifest(ctx, catalog)

    # 2. Build canonical registry: union by name, newest config wins, redacted.
    #    Catalog entries from agents_repo get a +0.5s mtime edge so they always
    #    beat an equally-new tool-native copy, asserting the repo's authority.
    #    Excludes any server present in the persistent removal log.
    registry: dict[str, dict] = {}
    origin: dict[str, tuple[str, float]] = {}
    for tname, (_desc, servers, mtime) in per_tool.items():
        for sname, model in servers.items():
            if sname.lower() in removals_lower:
                continue
            if sname not in registry or mtime > origin[sname][1]:
                red, had = redact_secrets(model, matchers)
                registry[sname] = red
                origin[sname] = (tname, mtime)
                if had:
                    LOG.info("MCP: '%s' carries a credential — redacted in registry", sname)
        # Overlay catalog entries for this tool (agents repo is authoritative).
        for sname, model in catalog.get(tname, {}).items():
            if sname.lower() in removals_lower:
                continue
            cat_edge = origin.get(sname, (None, 0.0))[1] + 0.5
            if sname not in registry or cat_edge >= origin.get(sname, (None, 0.0))[1]:
                registry[sname] = model
                origin[sname] = (f"agents_repo/{tname}", cat_edge)
                LOG.info("MCP: agents_repo provides '%s' for %s", sname, tname)

    write_json(ctx.data_dir / "mcp" / "registry.json", registry)
    ctx.note(f"MCP registry: {len(registry)} servers from {len(per_tool)} tools (+ agents_repo catalog)")

    # 3. Add-only fan-out: give each tool the servers it is missing.
    #    New servers are added enabled/turned-on.
    #    Pre-existing servers already present in a tool (including turned-off ones) are left untouched.
    for tname, (desc, servers, _mtime) in per_tool.items():
        tool = ctx.tools[tname]
        missing = {n: s for n, s in registry.items() if n not in servers and n.lower() not in removals_lower}
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
