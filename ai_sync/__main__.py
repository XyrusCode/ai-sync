"""ai-sync entry point.

    python -m ai_sync              # DRY-RUN (default): report + populate hub, no native writes
    python -m ai_sync --apply      # actually write changes to each tool
    python -m ai_sync --only mcp   # run a single pass (skills|memory|mcp|history)
    python -m ai_sync --apply --log  # also write a dated log under the hub
"""
from __future__ import annotations

import argparse
import sys

from . import __version__, history_inject, history_read, mcp, memory, skills
from .ctx import Ctx
from .state import State
from .tools import RunningGuard, load_tools
from .util import LOG, load_config, setup_logging

PASSES = ("skills", "memory", "mcp", "history")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ai_sync", description="Cross-tool AI assistant sync")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default is a dry run)")
    ap.add_argument("--only", choices=PASSES, help="run only one pass")
    ap.add_argument("--log", action="store_true", help="also write a dated log file")
    ap.add_argument("--config", help="path to a config file (default: config.local.yaml)")
    ap.add_argument("--version", action="version", version=f"ai-sync {__version__}")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = cfg["_data_dir"]
    setup_logging(data_dir, to_file=args.log)

    mode = "APPLY" if args.apply else "DRY-RUN"
    LOG.info("ai-sync %s — %s — config: %s", __version__, mode, cfg["_config_path"])

    tools = load_tools(cfg)
    enabled = [t.name for t in tools.values() if t.enabled]
    LOG.info("tools enabled: %s", ", ".join(enabled) or "(none)")

    ctx = Ctx(cfg=cfg, data_dir=data_dir, tools=tools,
              guard=RunningGuard(), state=State(data_dir), apply=args.apply)

    run = (args.only,) if args.only else PASSES
    if "skills" in run:
        skills.run(ctx)
    if "memory" in run:
        memory.run(ctx)
    if "mcp" in run:
        mcp.run(ctx)
    if "history" in run:
        sessions = history_read.run(ctx)
        history_inject.run(ctx, sessions)

    if args.apply:
        ctx.state.save()

    LOG.info("== summary ==")
    LOG.info("%d change(s) %s", len(ctx.changes), "applied" if args.apply else "pending (dry-run)")
    if ctx.skipped_running:
        LOG.warning("skipped writes to running tools: %s", ", ".join(sorted(ctx.skipped_running)))
    if not args.apply and ctx.changes:
        LOG.info("re-run with --apply to write these changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
