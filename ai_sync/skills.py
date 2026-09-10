"""Pass 1 — Skills reconcile (newest-wins) across Claude, OpenCode, Codex, Cursor."""
from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

from .ctx import Ctx
from .util import LOG, newest_mtime, repo_root, sha256_dir

SKILL_MARKER = "SKILL.md"


def _is_reparse_point(path: Path) -> bool:
    try:
        st = os.lstat(path)
        return bool(st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False


def _remove_tree(path: Path) -> None:
    """Safely remove a file, symlink, junction, or directory tree on Windows/POSIX."""
    if not path.exists() and not _is_reparse_point(path):
        return
    if path.is_symlink() or _is_reparse_point(path):
        try:
            os.rmdir(path)
            return
        except OSError:
            try:
                os.unlink(path)
                return
            except OSError:
                pass
    if path.is_file():
        try:
            path.unlink(missing_ok=True)
            return
        except OSError:
            try:
                os.chmod(path, stat.S_IWRITE)
                path.unlink(missing_ok=True)
                return
            except OSError:
                pass
    if path.is_dir():
        def _on_error(func, p, exc_info):
            try:
                os.chmod(p, stat.S_IWRITE)
                func(p)
            except Exception:
                pass
        shutil.rmtree(path, onerror=_on_error)
        if path.exists() or _is_reparse_point(path):
            try:
                os.rmdir(path)
            except OSError:
                pass


def _skill_dirs_for(tool) -> list[Path]:
    dirs = [d for d in tool.paths("skills_dirs")]
    # Automatically include the repo's own tracked skills directory
    # so version-controlled skills (e.g. from dissolved repos like
    # XyrusCode/Skills) are synced to every tool.
    repo_skills = repo_root() / "skills"
    if repo_skills.is_dir():
        dirs.append(repo_skills)
    return dirs


def _iter_skills(root: Path):
    """Yield (skill_name, skill_path) for each subdir containing SKILL.md."""
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.name.startswith("."):
            continue  # skip .sync-manifest.json etc.
        if child.is_dir() and (child / SKILL_MARKER).is_file():
            yield child.name, child


def _copy_skill(src: Path, dest: Path, ctx: Ctx) -> None:
    if ctx.apply:
        _remove_tree(dest)
        shutil.copytree(src, dest, dirs_exist_ok=True)


def run(ctx: Ctx) -> None:
    LOG.info("== Pass 1: skills ==")
    hub_skills = ctx.data_dir / "skills"
    hub_skills.mkdir(parents=True, exist_ok=True)

    # Collect target dirs (first skills_dir per tool is the canonical write target).
    targets: list[tuple[str, Path]] = []  # (tool_name, dir)
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        for d in _skill_dirs_for(tool):
            targets.append((tool.name, d))
    if not targets:
        LOG.info("no tools expose a skills dir; skipping")
        return

    # 1. Gather every skill copy and pick the newest per name.
    candidates: dict[str, tuple[float, Path, str]] = {}  # name -> (mtime, path, owner)
    for owner, d in targets:
        for name, spath in _iter_skills(d):
            mt = newest_mtime(spath)
            if name not in candidates or mt > candidates[name][0]:
                candidates[name] = (mt, spath, owner)

    if not candidates:
        LOG.info("no skills found across tools")
        return

    # 2. Update the hub canonical copy for each skill (newest-wins).
    for name, (mt, spath, owner) in sorted(candidates.items()):
        src_hash = sha256_dir(spath)
        hub_dest = hub_skills / name
        if sha256_dir(hub_dest) != src_hash:
            ctx.record(f"skill '{name}': hub <- {owner} (newest)")
            _copy_skill(spath, hub_dest, ctx)
        ctx.state.manifest_set(f"skill:{name}", mt, src_hash)

    # 3. Fan out canonical hub skills into each tool's (first) skills dir.
    for tool in ctx.tools.values():
        if not tool.enabled:
            continue
        dirs = _skill_dirs_for(tool)
        if not dirs:
            continue
        dest_root = dirs[0]
        if not ctx.writable(tool):
            continue
        for name in sorted(candidates):
            hub_dest = hub_skills / name
            tool_skill = dest_root / name
            if sha256_dir(tool_skill) == sha256_dir(hub_dest):
                continue
            ctx.record(f"skill '{name}': {tool.name} <- hub")
            if ctx.apply:
                dest_root.mkdir(parents=True, exist_ok=True)
                _copy_skill(hub_dest, tool_skill, ctx)
        _touch_cursor_manifest(tool, dest_root, ctx)


def _touch_cursor_manifest(tool, dest_root: Path, ctx: Ctx) -> None:
    """Refresh Cursor's own .sync-manifest.json lastSyncedAt so it plays nice."""
    if tool.name != "cursor":
        return
    manifest = dest_root / ".sync-manifest.json"
    if manifest.exists():
        ctx.note("cursor: left existing .sync-manifest.json in place")
