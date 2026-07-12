"""Pass 5 — Cross-tool history injection.

For each project, sessions that originated in tool A are written into the OTHER
tools' native stores so each tool can see the others' past work. Every injected
session is tagged (originator=ai-sync, 'synced-' filenames/ids) and recorded in
the inject-ledger, so Pass 4 skips it and re-runs never duplicate.

File-based targets (Claude, Codex, Gemini) are enabled by default. SQLite /
protobuf / cloud targets (OpenCode, Cursor, Antigravity, Devin) are opt-in via
each tool's `inject_history: true` flag — off by default to protect live DBs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .ctx import Ctx
from .history_model import (ORIGINATOR, Msg, Session, claude_mangle,
                            gemini_project_hash, ledger_key, synthetic_id)
from .util import LOG, write_json


def _iso(ms: int = 0) -> str:
    if ms:
        try:
            return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _det_uuid(seed: str) -> str:
    import hashlib
    h = hashlib.sha256(seed.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# --------------------------------------------------------------------------- #
# Claude injector — projects/<mangled>/synced-*.jsonl
# --------------------------------------------------------------------------- #
def inject_claude(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    if not s.project_path:
        return False
    root = tool.path("history_dir")
    if not root:
        return False
    proj_dir = root / claude_mangle(s.project_path)
    out_file = proj_dir / f"{synth}.jsonl"
    lines, prev = [], None
    header = (f"[Imported by ai-sync from {s.tool} session {s.session_id}. "
              f"Read-only copy for cross-tool visibility.]")
    msgs = [Msg("user", header)] + s.messages
    for i, m in enumerate(msgs):
        uid = _det_uuid(f"{synth}:{i}")
        content = m.text if m.role == "user" else [{"type": "text", "text": m.text}]
        lines.append({
            "parentUuid": prev, "isSidechain": False, "type": m.role,
            "message": {"role": m.role, "content": content},
            "uuid": uid, "timestamp": _iso(s.created_ms),
            "sessionId": synth, "cwd": s.project_path, "gitBranch": "",
            "version": "ai-sync", "originator": ORIGINATOR,
            "syncedFrom": {"tool": s.tool, "session_id": s.session_id},
        })
        prev = uid
    if ctx.apply:
        proj_dir.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as fh:
            for ln in lines:
                fh.write(json.dumps(ln, ensure_ascii=False) + "\n")
    return True


# --------------------------------------------------------------------------- #
# Codex injector — sessions/YYYY/MM/DD/rollout-synced-*.jsonl + session_index
# --------------------------------------------------------------------------- #
def inject_codex(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    root = tool.path("history_dir")
    if not root:
        return False
    dt = datetime.fromtimestamp(s.created_ms / 1000, tz=timezone.utc) if s.created_ms \
        else datetime.now(timezone.utc)
    day_dir = root / f"{dt:%Y}" / f"{dt:%m}" / f"{dt:%d}"
    out_file = day_dir / f"rollout-{synth}.jsonl"
    meta = {"type": "session_meta", "payload": {
        "id": synth, "timestamp": _iso(s.created_ms), "cwd": s.project_path,
        "originator": ORIGINATOR, "source": "ai-sync",
        "instructions": None, "syncedFrom": {"tool": s.tool, "session_id": s.session_id}}}
    lines = [meta]
    for m in s.messages:
        lines.append({"timestamp": _iso(s.created_ms), "type": "response_item",
                      "payload": {"role": m.role,
                                  "content": [{"type": "text", "text": m.text}]}})
    if ctx.apply:
        day_dir.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as fh:
            for ln in lines:
                fh.write(json.dumps(ln, ensure_ascii=False) + "\n")
        idx = tool.path("session_index")
        if idx:
            with open(idx, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "id": synth,
                    "thread_name": f"[ai-sync] {s.title or s.tool} {s.session_id[:8]}",
                    "updated_at": _iso(s.created_ms)}) + "\n")
    return True


# --------------------------------------------------------------------------- #
# Gemini injector — tmp/<projectHash>/chats/session-synced-*.json
# --------------------------------------------------------------------------- #
def inject_gemini(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    if not s.project_path:
        return False
    tmp = tool.path("history_tmp")
    if not tmp:
        return False
    phash = gemini_project_hash(s.project_path)
    chats = tmp / phash / "chats"
    out_file = chats / f"session-{synth}.json"
    messages = [{"id": i, "timestamp": _iso(s.created_ms),
                 "type": "user" if m.role == "user" else "model",
                 "content": m.text} for i, m in enumerate(s.messages)]
    doc = {"sessionId": synth, "projectHash": phash,
           "startTime": _iso(s.created_ms), "lastUpdated": _iso(s.created_ms),
           "originator": ORIGINATOR,
           "syncedFrom": {"tool": s.tool, "session_id": s.session_id},
           "messages": messages}
    if ctx.apply:
        chats.mkdir(parents=True, exist_ok=True)
        write_json(out_file, doc)
    return True


INJECTORS = {"claude": inject_claude, "codex": inject_codex, "gemini": inject_gemini}
DEFERRED = {"opencode", "cursor", "antigravity", "devin"}


def run(ctx: Ctx, sessions: list[Session]) -> None:
    LOG.info("== Pass 5: history inject ==")
    by_project: dict[str, list[Session]] = {}
    for s in sessions:
        by_project.setdefault(s.project_key, []).append(s)

    injected = 0
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        if not tool.flag("inject_history", tool.name in INJECTORS):
            if tool.name in DEFERRED:
                ctx.note(f"inject: {tool.name} deferred (set inject_history: true to enable)")
            continue
        injector = INJECTORS.get(tool.name)
        if not injector:
            ctx.note(f"inject: {tool.name} enabled but no writer implemented yet")
            continue
        if not ctx.writable(tool):
            continue
        for key, plist in by_project.items():
            for s in plist:
                if s.tool == tool.name or s.injected:
                    continue
                lk = ledger_key(s.tool, s.session_id, tool.name)
                if ctx.state.injected(lk):
                    continue
                synth = synthetic_id(s.tool, s.session_id, tool.name)
                try:
                    ok = injector(tool, s, synth, ctx)
                except Exception as exc:  # defensive
                    LOG.warning("inject %s <- %s/%s failed: %s",
                                tool.name, s.tool, s.session_id, exc)
                    ok = False
                if ok:
                    injected += 1
                    ctx.record(f"inject: {tool.name} <- {s.tool}/{s.session_id[:8]} "
                               f"({len(s.messages)} msgs) [{key or 'no-project'}]")
                    if ctx.apply:
                        ctx.state.mark_injected(lk, {
                            "synth": synth, "source_tool": s.tool,
                            "source_sid": s.session_id, "target": tool.name})
    ctx.note(f"history inject: {injected} session(s) written")
