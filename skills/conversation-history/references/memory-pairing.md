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

## What Stays in Conversation History (Ephemeral)

Never write these to permanent memory:
- Temporary test run failures that were immediately fixed.
- Raw file listings or exploratory bash command output.
- In-progress code snippets that are about to change.
- Unverified hypotheses explored during debugging.

## What Promotes to Memory (Durable)

Promote knowledge to `~/.agents/memory/` using the 6 canonical types from `memory-authoring`:

1. **User preferences (`user_*`)**: User working habits, tooling preferences, preferred CLI flags.
2. **Behavioral rules (`feedback_*`)**: Explicit corrections or rules stated by the user (for example, "never run full test suite without -k filter").
3. **Project milestones (`project_*`)**: Locked architectural choices, milestone completions, release schedules.
4. **Recurring bugs and traps (`gotcha_*`)**: Non-obvious failures, silent environment quirks, third-party library bugs and their fixes.
5. **Architectural shapes (`pattern_*`)**: Established structural patterns, reusable data flow conventions.
6. **External pointers (`reference_*`)**: URLs, external cluster configs, service dependencies.

## Promotion Workflow

When a conversation settles a durable item:

1. **Identify the signal**: The user provides explicit feedback, or a debugging investigation uncovers a tricky environment gotcha.
2. **Formulate the memory**: Draft the entry using the matching template from `memory-authoring`:
   - Must have required YAML frontmatter (`name`, `description`, `metadata.type`).
   - Body must include context, root cause, and how to apply.
3. **Commit the memory file**: Write to `~/.agents/memory/<type>_<slug>.md`.
4. **Index in MEMORY.md**: Add a single index line under 150 characters to `MEMORY.md`.
5. **Drop from active conversation**: Once saved to disk, remove the verbose backstory from the conversation ledger. Reference only the memory slug.

## Selective Hydration

Do not load all memory files into context at the start of a conversation. Follow this selective retrieval pattern:

1. Read `MEMORY.md` lines relevant to the user's prompt.
2. If an index line directly matches the task domain (for example, `gotcha_composer_unpublished_lock.md` when running PHP builds), read only that specific file.
3. Incorporate the constraint into the Active Objectives Ledger under "Locked Decisions".
4. Keep the remaining memory files unread until specifically required.
