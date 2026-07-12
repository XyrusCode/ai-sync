"""Pass 2 — Memory / instructions reconcile (newest-wins global AGENTS.md)."""
from __future__ import annotations

from pathlib import Path

from .ctx import Ctx
from .util import LOG, newest_mtime, sha256_file, sha256_text

BANNER = "<!-- ai-sync: canonical global instructions. Edit any tool's copy; newest wins. -->"


def _memory_files(ctx: Ctx) -> list[tuple[str, Path]]:
    out = []
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        mf = tool.path("memory_file")
        if mf is not None:
            out.append((tool.name, mf))
    return out


def run(ctx: Ctx) -> None:
    LOG.info("== Pass 2: memory ==")
    files = _memory_files(ctx)
    if not files:
        LOG.info("no global memory files configured")
        return

    hub_file = ctx.data_dir / "memory" / "AGENTS.md"
    hub_file.parent.mkdir(parents=True, exist_ok=True)

    # Pick the newest non-empty memory file as canonical source.
    best: tuple[float, str, str] | None = None  # (mtime, owner, text)
    for owner, path in files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        mt = newest_mtime(path)
        if best is None or mt > best[0]:
            best = (mt, owner, text)

    # Include the hub's own copy as a candidate (so manual hub edits win too).
    if hub_file.is_file():
        htext = hub_file.read_text(encoding="utf-8", errors="replace")
        hmt = newest_mtime(hub_file)
        if htext.strip() and (best is None or hmt > best[0]):
            best = (hmt, "hub", htext)

    if best is None:
        LOG.info("all memory files empty; nothing to reconcile")
        return

    _mt, owner, canonical = best
    canonical_body = _ensure_banner(canonical)
    canonical_hash = sha256_text(canonical_body)

    if sha256_file(hub_file) != canonical_hash:
        ctx.record(f"memory: hub <- {owner} (newest)")
        if ctx.apply:
            hub_file.write_text(canonical_body, encoding="utf-8")

    # Fan out to every tool's global memory file.
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        mf = tool.path("memory_file")
        if mf is None:
            continue
        if not ctx.writable(tool):
            continue
        if sha256_file(mf) == canonical_hash:
            continue
        ctx.record(f"memory: {tool.name} <- hub ({mf.name})")
        if ctx.apply:
            mf.parent.mkdir(parents=True, exist_ok=True)
            mf.write_text(canonical_body, encoding="utf-8")


def _ensure_banner(text: str) -> str:
    if text.lstrip().startswith(BANNER):
        return text
    return f"{BANNER}\n\n{text.strip()}\n"
