---
name: conversation-history
description: Condense multi-turn conversation context, track active session objectives, and minimize token usage. Pairs with memory to promote durable lessons and project state, and with graphify to replace bulky file reads with focused graph queries. Use when a session grows long, during multi-phase tasks, when managing conversation context, or when resuming work.
---

# Conversation History Skill

Manage live session context to prevent token waste and goal drift.

Raw conversation transcripts quickly bloat with tool outputs, file contents, compiler diagnostics, and intermediate exploratory turns. This causes context rot: the model re-reads files it already saw, loses sight of the original task, and burns tokens on stale history.

This skill operates across two levels:
1. **Intra-session working context**: Anchoring immediate objectives and pruning noisy tool outputs during execution.
2. **Project decision log (`CONVERSATION_HISTORY.md`)**: Maintaining a committed chronological log in the repository that enables fast rehydration, records scope boundaries, and preserves exact verification proofs.

## Non-Interference Rules (Zero Overhead)

1. **Never hunt for missing stores**: If `~/.agents/memory/` or `MEMORY.md` is missing, skip it silently in zero turns. Never shell out looking for `install.sh` or attempt to bootstrap an external store.
2. **Never hunt for missing graphs**: If `graphify-out/graph.json` does not exist, skip it silently. Do not run commands to build or install a graph during task execution.
3. **No automatic memory promotion**: Transient npm errors, build quirks, and local environment hiccups are not cross-project gotchas. Never chain into `memory-authoring` automatically at task completion. Only promote when explicitly instructed by the user.
4. **Clean finish**: When verification passes, record the outcome and stop. Never invent exit side quests.

## When to use

- A conversation reaches 15+ turns or accumulates large tool outputs (test suites, build logs, file dumps).
- You notice the agent re-reading previously loaded files or drifting from the core task.
- Beginning a multi-phase implementation where each phase builds on previous decisions.
- Starting a fresh session and needing to rehydrate project context with minimal token spend.
- Winding down a session to record settled decisions, code changes, and test proofs in `CONVERSATION_HISTORY.md`.

## Don't use for

- Global cross-project rules: use `memory-authoring` only when specifically prompted.
- Simple single-turn commands or quick lookups that conclude immediately.
- Code commit logs or git history: git tracks its own commits.

## Core Pillars

### 1. Active Objectives Ledger
Keep a concise, 10 to 15 line objective block active in working memory. When turns accumulate, refresh this block to prevent goal drift:
- **Primary Goal**: One clear sentence defining the end state.
- **Current Phase**: The specific subtask currently in flight.
- **Completed Steps**: Concise checklist of verified milestones.
- **Settled Decisions**: Locked architectural choices, preventing re-litigation.
- **Blockers & Open Questions**: Concrete roadblocks requiring user input or investigation.

See [references/objective-ledger.md](references/objective-ledger.md) and [templates/objective-anchor.md](templates/objective-anchor.md).

### 2. Project Decision Log (CONVERSATION_HISTORY.md)
Maintain a committed markdown decision log in the repository (e.g. `CONVERSATION_HISTORY.md` or `docs/CONVERSATION_HISTORY.md`).
- **Zero-token-waste rehydration**: A fresh agent reads the latest 2 or 3 entries to understand full context in under 1,500 tokens, avoiding transcript dumps.
- **Chronological record**: Formatted by date and topic (`## YYYY-MM-DD: Topic`).
- **Core fields**: Captures user intent, scope inclusions/exclusions, architectural shortcuts, touched files, root causes for fixes, and exact verification numbers.

See [references/project-decision-log.md](references/project-decision-log.md) and [templates/conversation-history-entry.md](templates/conversation-history-entry.md).

### 3. Pairing with Memory (Passive and Scoped)
- **Local first**: Active task progress, immediate tool results, and the project decision log belong to conversation history.
- **No unrequested chaining**: Do not load or invoke `memory-authoring` unless the user explicitly asks to save a memory.
- **Selective hydration**: If `MEMORY.md` exists on disk, read only the specific matching entry relevant to the active goal. If `MEMORY.md` does not exist, do not search for it.

See [references/memory-pairing.md](references/memory-pairing.md).

### 4. Pairing with Graphify (Passive and Scoped)
- When `graphify-out/graph.json` exists in the workspace: run `graphify query "<concept>"` or `graphify path "<nodeA>" "<nodeB>"` instead of reading large directories.
- When absent: skip silently. Proceed with standard targeted file reads.

See [references/graphify-pairing.md](references/graphify-pairing.md).

### 5. Compaction and Token Reduction
Cut context consumption before output quality degrades:
- **Tool output condensation**: Never repeat raw test sweeps or grep outputs. Summarize in 1 to 2 lines (example: "Ran 48 tests: 47 passed, 1 failed in auth_guard due to 401 status; fixed in middleware.py").
- **Rolling state checkpoints**: After concluding an investigation or subtask, summarize the completed arc into a state checkpoint and proceed from the synthesized state.
- **Context rot split**: When a session reaches high cumulative weight (40+ turns, heavy file churn), emit a self-contained handoff prompt and continue in a clean session.

See [references/compaction-protocols.md](references/compaction-protocols.md), [templates/compaction-checkpoint.md](templates/compaction-checkpoint.md), and [templates/session-handoff.md](templates/session-handoff.md).

## Decision Tree

1. **Starting work:**
   - If `CONVERSATION_HISTORY.md` exists, read recent entries to rehydrate context.
   - Establish the Active Objectives Ledger ([templates/objective-anchor.md](templates/objective-anchor.md)).
   - If `graphify-out/graph.json` exists, use graph queries. If absent, skip.
   - If `MEMORY.md` exists, check relevant lines. If absent, skip.

2. **Mid-task execution (every 10-15 turns or after large operations):**
   - Synthesize tool outputs into concise findings.
   - Update completed steps in the ledger.
   - Stay focused on the immediate task.

3. **Signs of context rot (re-reading files, circular reasoning, token limits):**
   - Produce a rolling checkpoint ([templates/compaction-checkpoint.md](templates/compaction-checkpoint.md)).
   - If splitting the session: write a clean handoff prompt ([templates/session-handoff.md](templates/session-handoff.md)) following `docs/context-rot.md`.

4. **Task completion:**
   - Verify all primary objectives in the ledger are satisfied.
   - Append a structured entry to `CONVERSATION_HISTORY.md` ([templates/conversation-history-entry.md](templates/conversation-history-entry.md)) if the repository maintains one.
   - Stop and deliver the work. Do not auto-chain into external tools or memory authoring.

## References

- [references/objective-ledger.md](references/objective-ledger.md): Structure and lifecycle of the Active Objectives Ledger.
- [references/project-decision-log.md](references/project-decision-log.md): Standards for maintaining repository CONVERSATION_HISTORY.md files.
- [references/memory-pairing.md](references/memory-pairing.md): Protocol for strictly scoped memory pairing.
- [references/graphify-pairing.md](references/graphify-pairing.md): Using graphify knowledge graphs to prune conversation context.
- [references/compaction-protocols.md](references/compaction-protocols.md): Heuristics for condensing tool outputs and turn history.

## Templates

- [templates/objective-anchor.md](templates/objective-anchor.md): Template for tracking active goals and constraints.
- [templates/conversation-history-entry.md](templates/conversation-history-entry.md): Template for appending entries to project CONVERSATION_HISTORY.md.
- [templates/compaction-checkpoint.md](templates/compaction-checkpoint.md): Template for intermediate state synthesis.
- [templates/session-handoff.md](templates/session-handoff.md): Template for clean session transitions.
