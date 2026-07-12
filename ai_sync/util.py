"""Shared helpers: config loading, path expansion, hashing, logging, safe IO."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

LOG = logging.getLogger("ai_sync")


# --------------------------------------------------------------------------- #
# Paths & config
# --------------------------------------------------------------------------- #
def expand(value: Any) -> Any:
    """Recursively expand ${USERPROFILE}/${ENV} and ~ in strings."""
    if isinstance(value, str):
        return os.path.expanduser(os.path.expandvars(value))
    if isinstance(value, list):
        return [expand(v) for v in value]
    if isinstance(value, dict):
        return {k: expand(v) for k, v in value.items()}
    return value


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config(explicit: str | None = None) -> dict:
    """Load config.local.yaml (falling back to config.example.yaml) and expand paths."""
    root = repo_root()
    if explicit:
        path = Path(explicit)
    else:
        path = root / "config.local.yaml"
        if not path.exists():
            path = root / "config.example.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No config found at {path}")
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    cfg = expand(raw)
    cfg["_config_path"] = str(path)
    cfg["_data_dir"] = Path(cfg.get("data_dir", os.path.expanduser("~/.ai-sync")))
    return cfg


# --------------------------------------------------------------------------- #
# Hashing / snapshots
# --------------------------------------------------------------------------- #
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | Path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: str | Path) -> str | None:
    """Content hash of a directory tree (names + bytes), order-independent."""
    p = Path(path)
    if not p.is_dir():
        return None
    parts = []
    for f in sorted(p.rglob("*")):
        if f.is_file():
            rel = f.relative_to(p).as_posix()
            parts.append(f"{rel}:{sha256_file(f)}")
    return sha256_text("\n".join(parts))


def newest_mtime(path: str | Path) -> float:
    """Newest mtime across a file or a directory tree (0.0 if missing)."""
    p = Path(path)
    if p.is_file():
        return p.stat().st_mtime
    if p.is_dir():
        best = 0.0
        for f in p.rglob("*"):
            if f.is_file():
                best = max(best, f.stat().st_mtime)
        return best
    return 0.0


# --------------------------------------------------------------------------- #
# Safe JSON IO
# --------------------------------------------------------------------------- #
def read_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        LOG.warning("Could not parse JSON %s: %s", p, exc)
        return default


def write_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    tmp.replace(p)


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def setup_logging(data_dir: Path, to_file: bool = False) -> None:
    LOG.setLevel(logging.INFO)
    LOG.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(message)s", "%H:%M:%S")
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    LOG.addHandler(stream)
    if to_file:
        logs = data_dir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logs / f"sync-{datetime.now():%Y-%m-%d}.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
        LOG.addHandler(fh)


# --------------------------------------------------------------------------- #
# Backups
# --------------------------------------------------------------------------- #
def backup_path(data_dir: Path, run_ts: str, original: str | Path) -> Path:
    """Return a per-run backup destination mirroring the original's basename."""
    dest_dir = data_dir / "backups" / run_ts
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(original)
    # Keep a hint of provenance in the filename to avoid collisions.
    stamp = sha256_text(str(src))[:8]
    return dest_dir / f"{src.name}.{stamp}"


def backup_file(data_dir: Path, run_ts: str, original: str | Path) -> Path | None:
    src = Path(original)
    if not src.exists():
        return None
    dest = backup_path(data_dir, run_ts, src)
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)
    return dest


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# --------------------------------------------------------------------------- #
# Secret handling
#
# Model: REDACT real inline tokens, but PRESERVE ${ENV} indirection and
# non-secret values (e.g. env.MEMORY_FILE_PATH). A value is a real secret if it
# matches a token-shape pattern, or if it sits under a secret-classed key and is
# a non-empty plain string with no ${...} indirection.
# --------------------------------------------------------------------------- #
PLACEHOLDER = "${REDACTED}"
_ENV_INDIRECT = re.compile(r"\$\{[^}]+\}|%[^%]+%")


class SecretMatchers:
    def __init__(self, cfg: dict):
        self.keys = {k.lower() for k in cfg.get("secret_field_keys", [])}
        self.patterns = [re.compile(p) for p in cfg.get("secret_value_patterns", [])]

    def token_in(self, s: str) -> bool:
        return any(p.search(s) for p in self.patterns)

    def redact_string(self, s: str) -> tuple[str, bool]:
        new = s
        for p in self.patterns:
            new = p.sub(PLACEHOLDER, new)
        return new, (new != s)


def compile_secret_matchers(cfg: dict) -> SecretMatchers:
    return SecretMatchers(cfg)


def has_indirection(s: str) -> bool:
    return bool(_ENV_INDIRECT.search(s))


def redact_secrets(obj: Any, m: SecretMatchers, _under_secret_key: bool = False):
    """Return (redacted_copy, had_secret). Preserves structure and ${ENV} refs."""
    had = False
    if isinstance(obj, str):
        new, changed = m.redact_string(obj)
        if changed:
            return new, True
        # Under a secret-classed key: a raw string with no indirection is a token.
        if _under_secret_key and obj.strip() and not has_indirection(obj):
            return PLACEHOLDER, True
        return obj, False
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            under = _under_secret_key or (k.lower() in m.keys)
            nv, h = redact_secrets(v, m, under)
            out[k] = nv
            had = had or h
        return out, had
    if isinstance(obj, list):
        out = []
        for v in obj:
            nv, h = redact_secrets(v, m, _under_secret_key)
            out.append(nv)
            had = had or h
        return out, had
    return obj, False


def contains_secret(obj: Any, m: SecretMatchers) -> bool:
    _, had = redact_secrets(obj, m)
    return had
