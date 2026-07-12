"""Persisted sync state: manifest (for newest-wins), inject-ledger, project-map."""
from __future__ import annotations

from pathlib import Path

from .util import read_json, write_json


class State:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.state_dir = data_dir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.manifest: dict = read_json(self.state_dir / "manifest.json", {}) or {}
        self.ledger: dict = read_json(self.state_dir / "inject-ledger.json", {}) or {}
        self.project_map: dict = read_json(self.state_dir / "project-map.json", {}) or {}

    # -- manifest: item -> {mtime, hash}. Drives hub-managed deletes & change detection.
    def manifest_get(self, key: str) -> dict | None:
        return self.manifest.get(key)

    def manifest_set(self, key: str, mtime: float, hexhash: str | None) -> None:
        self.manifest[key] = {"mtime": mtime, "hash": hexhash}

    def hub_managed_keys(self, prefix: str) -> set[str]:
        return {k for k in self.manifest if k.startswith(prefix)}

    # -- inject-ledger: dedup/loop guard. key = derived synthetic id.
    def injected(self, key: str) -> bool:
        return key in self.ledger

    def mark_injected(self, key: str, meta: dict) -> None:
        self.ledger[key] = meta

    # -- project map: canonical key -> per-tool representations.
    def map_project(self, canonical: str, tool: str, repr_value: str) -> None:
        self.project_map.setdefault(canonical, {})[tool] = repr_value

    def save(self) -> None:
        write_json(self.state_dir / "manifest.json", self.manifest)
        write_json(self.state_dir / "inject-ledger.json", self.ledger)
        write_json(self.state_dir / "project-map.json", self.project_map)


def canonical_project_key(path: str) -> str:
    """Lowercased, forward-slashed, trailing-slash-free absolute project key."""
    p = (path or "").replace("\\", "/").rstrip("/")
    return p.lower()
