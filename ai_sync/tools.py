"""Per-tool registry: resolved paths, capability flags, running-process detection."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .util import LOG


@dataclass
class Tool:
    name: str
    enabled: bool
    cfg: dict = field(default_factory=dict)

    def path(self, key: str) -> Path | None:
        v = self.cfg.get(key)
        return Path(v) if isinstance(v, str) else None

    def paths(self, key: str) -> list[Path]:
        v = self.cfg.get(key)
        if isinstance(v, str):
            return [Path(v)]
        if isinstance(v, list):
            return [Path(p) for p in v]
        return []

    def flag(self, key: str, default: bool = True) -> bool:
        return bool(self.cfg.get(key, default))

    @property
    def process_names(self) -> list[str]:
        return list(self.cfg.get("process_names", []))


def load_tools(cfg: dict) -> dict[str, Tool]:
    tools: dict[str, Tool] = {}
    for name, tcfg in (cfg.get("tools") or {}).items():
        tcfg = tcfg or {}
        tools[name] = Tool(name=name, enabled=bool(tcfg.get("enabled", True)), cfg=tcfg)
    return tools


# --------------------------------------------------------------------------- #
# Running-process detection (Windows). Used to skip writes to open tools.
# --------------------------------------------------------------------------- #
def _running_image_names() -> set[str]:
    """Return the set of running process image names (lowercased), via tasklist."""
    try:
        out = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        LOG.warning("Could not enumerate processes (%s); running-app guard disabled", exc)
        return set()
    names: set[str] = set()
    for line in out.stdout.splitlines():
        line = line.strip().strip('"')
        if not line:
            continue
        image = line.split('","')[0].strip('"').lower()
        if image.endswith(".exe"):
            image = image[:-4]
        names.add(image)
    return names


class RunningGuard:
    """Caches the running-process snapshot for one sync run."""

    def __init__(self) -> None:
        self._running = _running_image_names()

    def is_running(self, tool: Tool) -> bool:
        for pname in tool.process_names:
            if pname.lower() in self._running:
                return True
        return False
