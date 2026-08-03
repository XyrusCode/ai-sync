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

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .ctx import Ctx
from .history_model import (ORIGINATOR, SYNCED_PREFIX, Msg, Session,
                            claude_mangle, gemini_project_hash, ledger_key,
                            synthetic_id)
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


# --------------------------------------------------------------------------- #
# OpenCode injector — SQLite session / message / part
# --------------------------------------------------------------------------- #
def inject_opencode(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    db = tool.path("history_db")
    if not db or not db.is_file():
        return False

    project_path = s.project_path or ""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    created_ms = s.created_ms or now_ms
    norm_path = project_path.replace("\\", "/") if project_path else ""
    ses_id = "ses_" + synth[len(SYNCED_PREFIX):]

    try:
        con = sqlite3.connect(str(db))
        with con:
            if norm_path:
                row = con.execute(
                    "SELECT id FROM project WHERE worktree = ?", (norm_path,)
                ).fetchone()
                if row:
                    project_id = row[0]
                else:
                    raw = norm_path.encode("utf-8")
                    project_id = hashlib.sha1(raw).hexdigest()
                    con.execute(
                        "INSERT OR IGNORE INTO project "
                        "(id, worktree, name, time_created, time_updated, sandboxes) "
                        "VALUES (?, ?, ?, ?, ?, '[]')",
                        (project_id, norm_path, Path(project_path).name,
                         created_ms, now_ms),
                    )
                    con.execute(
                        "INSERT OR IGNORE INTO project_directory "
                        "(project_id, directory, time_created) VALUES (?, ?, ?)",
                        (project_id, norm_path, now_ms),
                    )
            else:
                project_id = "global"

            tag = f"[ai-sync] {s.tool}/{s.session_id[:8]}"
            title = (f"{tag}: {s.title}" if s.title else tag)[:500]
            metadata = json.dumps({"originator": ORIGINATOR, "source_tool": s.tool,
                                   "source_session": s.session_id})
            con.execute(
                "INSERT INTO session "
                "(id, project_id, slug, directory, title, version, "
                "time_created, time_updated, metadata) "
                "VALUES (?, ?, ?, ?, ?, 'local', ?, ?, ?)",
                (ses_id, project_id, ses_id[:20], norm_path,
                 title, created_ms, now_ms, metadata),
            )

            if s.messages:
                prompt = s.messages[0].text[:2000]
                con.execute(
                    "INSERT INTO session_input "
                    "(id, session_id, prompt, delivery, admitted_seq, promoted_seq, time_created) "
                    "VALUES (?, ?, ?, 'user', 1, 1, ?)",
                    (_det_uuid(f"{synth}:input"), ses_id, prompt, created_ms),
                )

            for i, m in enumerate(s.messages):
                msg_seed = f"{synth}:msg:{i}"
                msg_id = "msg_" + _det_uuid(msg_seed)
                msg_ts = created_ms + i
                parent = None if i == 0 else "msg_" + _det_uuid(f"{synth}:msg:{i - 1}")
                msg_data = json.dumps({
                    "parentID": parent, "role": m.role,
                    "mode": "build", "agent": "build",
                })
                con.execute(
                    "INSERT INTO message "
                    "(id, session_id, time_created, time_updated, data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (msg_id, ses_id, msg_ts, msg_ts, msg_data),
                )
                part_id = "prt_" + _det_uuid(f"{synth}:part:{i}")
                part_data = json.dumps({"type": "text", "text": m.text})
                con.execute(
                    "INSERT INTO part "
                    "(id, message_id, session_id, time_created, time_updated, data) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (part_id, msg_id, ses_id, msg_ts, msg_ts, part_data),
                )
        con.close()
        return True
    except sqlite3.Error as exc:
        LOG.warning("opencode inject failed: %s", exc)
        return False


# --------------------------------------------------------------------------- #
# Kiro injector — projects/<mangled>/synced-*.jsonl (same layout as Claude)
# --------------------------------------------------------------------------- #
def inject_kiro(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    if not s.project_path:
        return False
    root = tool.path("history_dir")
    if not root:
        return False
    from .history_model import claude_mangle
    proj_dir = root / claude_mangle(s.project_path)
    out_file = proj_dir / f"{synth}.jsonl"
    lines, prev = [], None
    header = (f"[Imported by ai-sync from {s.tool} session {s.session_id}. "
              f"Read-only copy for cross-tool visibility.]")
    msgs = [Msg("user", header)] + s.messages
    for i, m in enumerate(msgs):
        uid = _det_uuid(f"{synth}:{i}")
        lines.append({
            "parentUuid": prev, "isSidechain": False, "type": m.role,
            "message": {"role": m.role, "content": [{"type": "text", "text": m.text}]},
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
# Copilot injector — session-store.db  (sessions + turns)
# --------------------------------------------------------------------------- #
def inject_copilot(tool, s: Session, synth: str, ctx: Ctx) -> bool:
    db = tool.path("history_db")
    if not db or not db.is_file():
        return False

    try:
        con = sqlite3.connect(str(db))
        with con:
            ses_id = synth[:36]  # UUID-format session id
            created = _iso(s.created_ms)
            tag = f"[ai-sync] {s.tool}/{s.session_id[:8]}"
            title = (f"{tag}: {s.title}" if s.title else tag)[:500]

            # Upsert session row
            con.execute(
                "INSERT OR REPLACE INTO sessions "
                "(id, cwd, repository, branch, summary, host_type, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ses_id, s.project_path or "", "", "",
                 title, "", created, created),
            )

            # Insert turns
            turn_index = 0
            for m in s.messages:
                if m.role == "user":
                    con.execute(
                        "INSERT OR REPLACE INTO turns "
                        "(session_id, turn_index, user_message, assistant_response, timestamp) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (ses_id, turn_index, m.text[:200000], None, created),
                    )
                else:
                    # Attach assistant message to previous turn if exists,
                    # else create a synthetic turn pair
                    prev = con.execute(
                        "SELECT turn_index FROM turns "
                        "WHERE session_id = ? ORDER BY turn_index DESC LIMIT 1",
                        (ses_id,),
                    ).fetchone()
                    if prev:
                        con.execute(
                            "UPDATE turns SET assistant_response = ? "
                            "WHERE session_id = ? AND turn_index = ?",
                            (m.text[:200000], ses_id, prev[0]),
                        )
                    else:
                        con.execute(
                            "INSERT OR REPLACE INTO turns "
                            "(session_id, turn_index, user_message, assistant_response, timestamp) "
                            "VALUES (?, ?, ?, ?, ?)",
                            (ses_id, turn_index, "[ai-sync import]", m.text[:200000], created),
                        )
                        turn_index += 1
                if m.role == "user":
                    turn_index += 1

        con.close()
        return True
    except sqlite3.Error as exc:
        LOG.warning("copilot inject failed: %s", exc)
        return False


INJECTORS = {"claude": inject_claude, "codex": inject_codex,
             "copilot": inject_copilot,
             "gemini": inject_gemini, "opencode": inject_opencode,
             "kiro": inject_kiro}
DEFERRED = {"cursor", "antigravity", "devin", "kimi", "qwen", "windsurf"}


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
