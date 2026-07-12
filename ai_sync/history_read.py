"""Pass 4 — History aggregate: parse each tool's native store into Sessions.

Every parser is defensive: any failure logs a warning and yields nothing rather
than aborting the run. Sessions already produced by ai-sync are skipped (loop
guard). The normalized archive is written to the hub for durability.
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from .ctx import Ctx
from .history_model import ORIGINATOR, SYNCED_PREFIX, Msg, Session
from .state import canonical_project_key
from .util import LOG, write_json

MAX_TEXT = 200_000  # guard against pathological blobs


def _ro_sqlite(path: Path) -> sqlite3.Connection | None:
    try:
        return sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
    except sqlite3.Error as exc:
        LOG.warning("history: cannot open %s: %s", path, exc)
        return None


def _as_ms(value) -> int:
    """Coerce a created/timestamp field to epoch-ms; ISO strings -> 0 (unknown)."""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _mk(tool, sid, path, title, created, msgs, injected=False) -> Session:
    return Session(tool=tool, session_id=sid, project_path=path or "",
                   project_key=canonical_project_key(path or ""), title=title or "",
                   created_ms=_as_ms(created), messages=msgs, injected=injected)


# --------------------------------------------------------------------------- #
# Claude — projects/<mangled>/<sessionId>.jsonl
# --------------------------------------------------------------------------- #
def read_claude(tool) -> list[Session]:
    root = tool.path("history_dir")
    out: list[Session] = []
    if not root or not root.is_dir():
        return out
    for proj_dir in root.iterdir():
        if not proj_dir.is_dir():
            continue
        for jf in proj_dir.glob("*.jsonl"):
            if jf.name.startswith(SYNCED_PREFIX):
                continue  # our own injection
            try:
                msgs, cwd, injected = [], "", False
                with open(jf, "r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        rec = json.loads(line)
                        if rec.get("originator") == ORIGINATOR:
                            injected = True
                        cwd = rec.get("cwd") or cwd
                        m = rec.get("message")
                        if not isinstance(m, dict):
                            continue
                        role = m.get("role")
                        if role not in ("user", "assistant"):
                            continue
                        text = _flatten_content(m.get("content"))
                        if text:
                            msgs.append(Msg(role, text))
                if msgs and not injected:
                    out.append(_mk("claude", jf.stem, cwd, "", 0, msgs))
            except (OSError, json.JSONDecodeError) as exc:
                LOG.warning("claude: skip %s (%s)", jf.name, exc)
    return out


_TEXT_TYPES = {"text", "input_text", "output_text"}


def _flatten_content(content) -> str:
    if isinstance(content, str):
        return content[:MAX_TEXT]
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") in _TEXT_TYPES or "text" in c:
                    parts.append(c.get("text", ""))
            elif isinstance(c, str):
                parts.append(c)
        return "\n".join(p for p in parts if p)[:MAX_TEXT]
    return ""


# --------------------------------------------------------------------------- #
# Codex — sessions/**/rollout-*.jsonl  (+ session_meta first line)
# --------------------------------------------------------------------------- #
def read_codex(tool) -> list[Session]:
    root = tool.path("history_dir")
    out: list[Session] = []
    if not root or not root.is_dir():
        return out
    for jf in root.rglob("rollout-*.jsonl"):
        if SYNCED_PREFIX in jf.name:
            continue
        try:
            sid, cwd, created, msgs, injected = jf.stem, "", 0, [], False
            with open(jf, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    if rec.get("type") == "session_meta":
                        p = rec.get("payload", {})
                        cwd = p.get("cwd", cwd)
                        sid = p.get("id", sid)
                        created = p.get("timestamp") or created
                        if p.get("originator") == ORIGINATOR:
                            injected = True
                        continue
                    payload = rec.get("payload", {})
                    role = payload.get("role")
                    if role in ("user", "assistant"):
                        text = _flatten_content(payload.get("content"))
                        if text:
                            msgs.append(Msg(role, text))
            if msgs and not injected:
                out.append(_mk("codex", sid, cwd, "", 0, msgs))
        except (OSError, json.JSONDecodeError) as exc:
            LOG.warning("codex: skip %s (%s)", jf.name, exc)
    return out


# --------------------------------------------------------------------------- #
# Gemini — tmp/<projectHash>/chats/session-*.json
# --------------------------------------------------------------------------- #
def read_gemini(tool) -> list[Session]:
    tmp = tool.path("history_tmp")
    out: list[Session] = []
    if not tmp or not tmp.is_dir():
        return out
    hash_to_path = _gemini_hash_map(tool)
    for hash_dir in tmp.iterdir():
        chats = hash_dir / "chats"
        if not chats.is_dir():
            continue
        proj = hash_to_path.get(hash_dir.name, "")
        for cf in chats.glob("session-*.json"):
            if SYNCED_PREFIX in cf.name:
                continue
            try:
                d = json.loads(cf.read_text(encoding="utf-8", errors="replace"))
                msgs = []
                for m in d.get("messages", []):
                    t = m.get("type")
                    role = "user" if t == "user" else "assistant"
                    text = m.get("content")
                    if isinstance(text, str) and text.strip():
                        msgs.append(Msg(role, text[:MAX_TEXT]))
                if msgs:
                    out.append(_mk("gemini", d.get("sessionId", cf.stem), proj,
                                   "", d.get("startTime", 0), msgs))
            except (OSError, json.JSONDecodeError) as exc:
                LOG.warning("gemini: skip %s (%s)", cf.name, exc)
    return out


def _gemini_hash_map(tool) -> dict[str, str]:
    """Map projectHash -> real path using projects.json (needs original case)."""
    pj = tool.path("projects_json")
    mapping = {}
    if pj and pj.is_file():
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
            from .history_model import gemini_project_hash
            for path in (data.get("projects") or {}):
                mapping[gemini_project_hash(path)] = path
        except (OSError, json.JSONDecodeError):
            pass
    return mapping


# --------------------------------------------------------------------------- #
# OpenCode — SQLite session / message / part
# --------------------------------------------------------------------------- #
def read_opencode(tool) -> list[Session]:
    db = tool.path("history_db")
    out: list[Session] = []
    if not db or not db.is_file():
        return out
    con = _ro_sqlite(db)
    if con is None:
        return out
    try:
        cur = con.cursor()
        sessions = cur.execute(
            "SELECT id, directory, title, time_created FROM session"
        ).fetchall()
        # message role/time + concatenated text parts
        for sid, directory, title, created in sessions:
            if str(sid).startswith("syn_"):
                continue
            msgs = []
            rows = cur.execute(
                "SELECT id, data FROM message WHERE session_id=? ORDER BY time_created", (sid,)
            ).fetchall()
            for mid, mdata in rows:
                try:
                    md = json.loads(mdata)
                except (json.JSONDecodeError, TypeError):
                    continue
                role = md.get("role")
                if role not in ("user", "assistant"):
                    continue
                texts = []
                for (pdata,) in cur.execute(
                    "SELECT data FROM part WHERE message_id=? ORDER BY time_created", (mid,)
                ):
                    try:
                        pd = json.loads(pdata)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if pd.get("type") == "text" and pd.get("text"):
                        texts.append(pd["text"])
                if texts:
                    msgs.append(Msg(role, "\n".join(texts)[:MAX_TEXT]))
            if msgs:
                out.append(_mk("opencode", str(sid), directory, title, created, msgs))
    except sqlite3.Error as exc:
        LOG.warning("opencode: sqlite error %s", exc)
    finally:
        con.close()
    return out


# --------------------------------------------------------------------------- #
# Cursor — state.vscdb cursorDiskKV composerData/bubbleId (composers are global)
# --------------------------------------------------------------------------- #
def read_cursor(tool) -> list[Session]:
    db = tool.path("global_vscdb")
    out: list[Session] = []
    if not db or not db.is_file():
        return out
    con = _ro_sqlite(db)
    if con is None:
        return out
    try:
        cur = con.cursor()
        composers = cur.execute(
            "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"
        ).fetchall()
        for key, val in composers:
            try:
                d = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                continue
            cid = d.get("composerId") or key.split(":", 1)[-1]
            if str(cid).startswith(SYNCED_PREFIX):
                continue
            headers = d.get("fullConversationHeadersOnly") or []
            msgs = []
            for h in headers:
                bid = h.get("bubbleId") if isinstance(h, dict) else None
                if not bid:
                    continue
                row = cur.execute(
                    "SELECT value FROM cursorDiskKV WHERE key=?",
                    (f"bubbleId:{cid}:{bid}",),
                ).fetchone()
                if not row:
                    continue
                try:
                    b = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    continue
                role = "user" if b.get("type") == 1 else "assistant"
                text = b.get("text")
                if isinstance(text, str) and text.strip():
                    msgs.append(Msg(role, text[:MAX_TEXT]))
            if msgs:
                out.append(_mk("cursor", str(cid), "", d.get("name", ""),
                               d.get("createdAt", 0), msgs))
    except sqlite3.Error as exc:
        LOG.warning("cursor: sqlite error %s", exc)
    finally:
        con.close()
    return out


# --------------------------------------------------------------------------- #
# Devin — sessions.db (schema present, usually empty / cloud-driven)
# --------------------------------------------------------------------------- #
def read_devin(tool) -> list[Session]:
    db = tool.path("history_db")
    out: list[Session] = []
    if not db or not db.is_file():
        return out
    con = _ro_sqlite(db)
    if con is None:
        return out
    try:
        cur = con.cursor()
        rows = cur.execute(
            "SELECT id, working_directory, title, created_at FROM sessions"
        ).fetchall()
        for sid, wd, title, created in rows:
            msgs = []
            for (chat, ) in cur.execute(
                "SELECT chat_message FROM message_nodes WHERE session_id=? ORDER BY created_at",
                (sid,),
            ):
                try:
                    m = json.loads(chat)
                except (json.JSONDecodeError, TypeError):
                    continue
                role = m.get("role") or ("user" if m.get("is_user") else "assistant")
                text = m.get("text") or m.get("content")
                if isinstance(text, str) and text.strip():
                    msgs.append(Msg("user" if role == "user" else "assistant", text[:MAX_TEXT]))
            if msgs:
                out.append(_mk("devin", str(sid), wd, title, created, msgs))
    except sqlite3.Error as exc:
        LOG.warning("devin: sqlite error %s", exc)
    finally:
        con.close()
    return out


READERS = {
    "claude": read_claude,
    "codex": read_codex,
    "gemini": read_gemini,
    "opencode": read_opencode,
    "cursor": read_cursor,
    "devin": read_devin,
    # antigravity: protobuf, deferred (no reader yet)
}


def run(ctx: Ctx) -> list[Session]:
    LOG.info("== Pass 4: history aggregate ==")
    all_sessions: list[Session] = []
    for name, tool in ctx.tools.items():
        if not tool.enabled:
            continue
        reader = READERS.get(name)
        if not reader:
            continue
        try:
            found = reader(tool)
        except Exception as exc:  # defensive: never let one tool abort the run
            LOG.warning("history: %s reader failed: %s", name, exc)
            found = []
        LOG.info("  %-10s %d sessions", name, len(found))
        all_sessions.extend(found)

    _persist(ctx, all_sessions)
    return all_sessions


def _persist(ctx: Ctx, sessions: list[Session]) -> None:
    hist_root = ctx.data_dir / "history"
    for s in sessions:
        key = s.project_key or "_unknown"
        safe = key.replace(":", "").replace("/", "_").strip("_") or "_unknown"
        out_dir = hist_root / safe
        rec = {
            "tool": s.tool, "session_id": s.session_id, "project_key": s.project_key,
            "project_path": s.project_path, "title": s.title, "created_ms": s.created_ms,
            "messages": [{"role": m.role, "text": m.text, "ts_ms": m.ts_ms} for m in s.messages],
        }
        if ctx.apply:
            out_dir.mkdir(parents=True, exist_ok=True)
            write_json(out_dir / f"{s.tool}__{s.session_id}.jsonl", rec)
    ctx.note(f"history archive: {len(sessions)} sessions normalized")
