"""Run context shared by every pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .state import State
from .tools import RunningGuard, Tool
from .util import LOG, backup_file, now_ts


@dataclass
class Ctx:
    cfg: dict
    data_dir: Path
    tools: dict[str, Tool]
    guard: RunningGuard
    state: State
    apply: bool
    run_ts: str = field(default_factory=now_ts)
    changes: list[str] = field(default_factory=list)
    skipped_running: set[str] = field(default_factory=set)

    def record(self, msg: str) -> None:
        self.changes.append(msg)
        LOG.info(("APPLY " if self.apply else "DRY   ") + msg)

    def note(self, msg: str) -> None:
        LOG.info(msg)

    def writable(self, tool: Tool) -> bool:
        """False if the tool is currently running (skip writes to avoid corruption)."""
        if self.guard.is_running(tool):
            if tool.name not in self.skipped_running:
                self.skipped_running.add(tool.name)
                LOG.warning("SKIP writes to %s — app is running", tool.name)
            return False
        return True

    def backup(self, original) -> None:
        if self.apply:
            dest = backup_file(self.data_dir, self.run_ts, original)
            if dest:
                LOG.info("backed up %s", original)
