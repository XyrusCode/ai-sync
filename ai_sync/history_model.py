"""Normalized cross-tool conversation model + shared id/path helpers."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

# Marker stamped on every session we inject, so the aggregate pass skips it
# and we never form a feedback loop.
ORIGINATOR = "ai-sync"
SYNCED_PREFIX = "synced-"


@dataclass
class Msg:
    role: str          # "user" | "assistant"
    text: str
    ts_ms: int = 0


@dataclass
class Session:
    tool: str                       # source tool name
    session_id: str
    project_path: str               # original-case absolute path (may be "")
    project_key: str                # canonical (lowercased, forward-slash)
    title: str = ""
    created_ms: int = 0
    messages: list[Msg] = field(default_factory=list)
    injected: bool = False          # True if this session was produced by ai-sync

    def digest(self) -> str:
        return hashlib.sha256(f"{self.tool}:{self.session_id}".encode()).hexdigest()[:16]


def synthetic_id(source_tool: str, source_sid: str, target_tool: str) -> str:
    """Deterministic id for an injected copy → idempotent across runs."""
    raw = f"{source_tool}|{source_sid}|{target_tool}"
    return SYNCED_PREFIX + hashlib.sha256(raw.encode()).hexdigest()[:24]


def ledger_key(source_tool: str, source_sid: str, target_tool: str) -> str:
    return f"{target_tool}<-{source_tool}:{source_sid}"


def claude_mangle(path: str) -> str:
    """Absolute path -> Claude project folder name (':','/','\\' -> '-')."""
    return re.sub(r"[:\\/]", "-", path)


def gemini_project_hash(path: str) -> str:
    """SHA-256 of the ORIGINAL-CASE backslash absolute path (verified on-machine)."""
    norm = path.replace("/", "\\").rstrip("\\")
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()
