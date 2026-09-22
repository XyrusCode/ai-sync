# Memory Pairing Protocol

This document defines how `conversation-history` pairs with the `memory` store (`~/.agents/memory/`, `MEMORY.md`, and `memory-authoring`).

## The Core Distinction

| Property | Conversation History | Memory Store |
|---|---|---|
| **Scope** | Current session or active task | Cross-session, durable across weeks/months |
| **Storage** | Live context, working memory, transcripts | `~/.agents/memory/<type>_<slug>.md` |
| **Index** | Active Objectives Ledger | `MEMORY.md` index file |
| **Content** | Tool outputs, turn-by-turn steps, debug traces | Rules, preferences, gotchas, architecture plans |
| **Retention** | Pruned or compacted as turns advance | Persists until explicitly updated or consolidated |

## Non-Interference Guardrails

1. **Never hunt for missing memory stores**: If `~/.agents/memory/` or `MEMORY.md` does not already exist on disk, do nothing. Never run shell commands, check for `install.sh`, or attempt to bootstrap a missing store.
2. **High bar for promotion**: Normal execution events are never memories:
   - Routine test run failures and subsequent fixes are not memories.
   - Transient npm, yarn, or pnpm version/script quirks are not cross-project gotchas.
   - Temporary build or compiler errors are not memories.
   - Scratchpad notes or unverified hypotheses belong in conversation history only.
3. **No automatic chaining**: Never invoke or load `memory-authoring` at the end of a session unless the user explicitly requested a memory to be saved.

## When Promotion is Appropriate

Only promote knowledge to `~/.agents/memory/` under two specific conditions:
1. The user explicitly says "remember this", "save this feedback", or "add this gotcha to memory".
2. An architectural invariant has been established and agreed with the user as a permanent cross-project standard.

When authorized, use the matching template from `memory-authoring` and add a single index line under 150 characters to `MEMORY.md`.

## Selective Hydration

Do not load all memory files into context at the start of a conversation. Follow this selective retrieval pattern:

1. Check if `MEMORY.md` exists. If not, stop and proceed with the task.
2. Read only the specific index lines matching the active goal.
3. Incorporate the constraint into the Active Objectives Ledger under "Locked Decisions".
4. Keep all other memory files unread.
