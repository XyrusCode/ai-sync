# Project Decision Log (`conversation-history/`)

The project decision log is a committed directory, `conversation-history/`, at the repository root. It holds one markdown file per calendar day - `conversation-history/YYYY-MM-DD.md` - so all agentic work on the same day lands in one human-readable file, no matter how many sessions ran.

It serves as the durable chronological source of truth across sessions, agents, and days. Instead of relying on volatile, multi-thousand token chat transcripts, agents append a concise entry to the current day file whenever a session finishes or reaches an inflection point.

## Why This Works

1. **Zero-token-waste rehydration**: When starting a fresh session, reading the latest 1 or 2 day files re-establishes the complete project context in under 1,500 tokens.
2. **Irreversible scope boundaries**: Captures explicit trade-offs, deferred features, and accepted constraints so subsequent sessions never re-open settled debates.
3. **Accountability and proof**: Records exact root causes, bug fixes, files touched, and test verification metrics.
4. **Daily human-readable history**: One file per day reads like a work log; session headings show exactly where context restarted and which agent ran.

## Day File Structure

```
conversation-history/
├── 2026-10-25.md
├── 2026-10-26.md
└── ...
```

Each day file follows this shape:

```markdown
# 2026-10-26

## Session 09:14 · claude

### Refactor the billing service
- **User Intent**: ...
- **Verification & Test Results**: ...

## Session 14:02 · codex

### Fix flaky auth test
- **User Intent**: ...
```

- The first session of the day creates the file with a `# YYYY-MM-DD` heading.
- Every later session - resumed context or fresh start - opens its own `## Session HH:MM · <tool>` heading in the same file. Use 24-hour local time and the agent tool name; omit `· <tool>` when the tool is unknown.
- Each topic entry inside a session uses the fields from [templates/conversation-history-entry.md](../templates/conversation-history-entry.md): User Intent, Scope Decisions, Key Decisions and Shortcuts, Implementation Details, Diagnostics and Root Cause, Verification and Test Results.

## Legacy Conversion (Single File → Directory)

When the skill is invoked in a repository that has `CONVERSATION_HISTORY.md` (root or `docs/`) or `conversation-history.md`, but no `conversation-history/` directory, convert before writing anything new so old and new records stay connected:

1. Create `conversation-history/`.
2. Legacy entries are headed `## YYYY-MM-DD: Topic`. Split them by that date into `conversation-history/YYYY-MM-DD.md`, giving each day file a `# YYYY-MM-DD` heading.
3. Put migrated entries under a `## Session (migrated)` heading when no session time was recorded; preserve entry text verbatim otherwise.
4. Verify every legacy entry landed in a day file (entry counts match) before touching the old file.
5. Delete the legacy file so the directory is the single home.

If both the directory and a legacy file exist, merge the legacy entries into their dated files first, then delete the legacy file. Never leave two parallel records.

## Lifecycle and Workflow

1. **Session Start**:
   - If `conversation-history/` exists, read the most recent 1 or 2 day files to rehydrate context.
   - Else if a legacy single file exists, run the conversion above, then read the newest day file.
   - Initialize the intra-session Active Objectives Ledger based on the log's state.

2. **Mid-Session / Interruption**:
   - If a session is interrupted (for example, reaching token or rate limits), record the exact resume point and open choices in a temporary checkpoint (like `CEO_INTERRUPTED.md`) and note it in the day file.

3. **Session Wind Down**:
   - Before ending the session, compose a new entry using [templates/conversation-history-entry.md](../templates/conversation-history-entry.md).
   - Append it under the current session heading in `conversation-history/YYYY-MM-DD.md`; create the day file if it does not exist yet.
   - Commit the updated day file alongside the code changes.
