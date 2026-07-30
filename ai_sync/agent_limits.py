"""agent-limits bridge — read rate-limit event logs and status caches.

Reads the ~/.agents/data/agent-limits TSV event logs and per-agent status
caches into the hub so the daily sync report includes rate-limit health
alongside history and config changes. This pass is purely observational:
it never writes to agent-limits data files.
"""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path

from .ctx import Ctx
from .util import LOG, read_json, write_json

EVENT_LOG = "events.tsv"
STATUS_CACHE = "status.json"


def _read_events_tsv(path: Path) -> list[dict]:
    """Parse a TSV event log into list of dicts."""
    if not path.is_file():
        return []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(raw), delimiter="\t")
        return [row for row in reader]
    except (OSError, csv.Error) as exc:
        LOG.warning("agent-limits: could not read %s: %s", path, exc)
        return []


def _read_status_json(path: Path) -> dict | None:
    """Read a per-agent status cache JSON file."""
    return read_json(path)


def run(ctx: Ctx) -> None:
    LOG.info("== Pass: agent-limits ==")
    data_root = ctx.cfg.get("agent_limits_data")
    if not data_root:
        LOG.info("agent_limits_data not configured; skipping")
        return
    root = Path(data_root)
    if not root.is_dir():
        LOG.info("agent_limits_data dir not found at %s; skipping", root)
        return

    hub_dir = ctx.data_dir / "agent-limits"
    summary: dict[str, dict] = {}

    for agent_dir in sorted(root.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent = agent_dir.name
        events_path = agent_dir / EVENT_LOG
        status_path = agent_dir / STATUS_CACHE

        events = _read_events_tsv(events_path)
        status = _read_status_json(status_path)

        if not events and not status:
            continue

        rec: dict = {"agent": agent}

        if status:
            rec["status"] = {
                k: v for k, v in status.items()
                if k in ("availability", "last_event", "reset_at", "budget_remaining")
            }

        if events:
            rec["event_count"] = len(events)
            rec["events"] = events[-50:]  # keep last 50

        summary[agent] = rec
        LOG.info("  %-12s %d events, status=%s", agent, len(events),
                 status.get("availability", "?") if status else "no-cache")

    if summary:
        out = hub_dir / "rate-limits.json"
        write_json(out, summary)
        ctx.note(f"agent-limits: {len(summary)} agents with data written to hub")
    else:
        ctx.note("agent-limits: no rate-limit data found")
