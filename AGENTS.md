# AGENTS — Global instructions and critical rules

## PR/MR Creation — CLI Auto-Detection

When creating a pull request or merge request, detect the remote and use the appropriate CLI:

- **GitHub** (`github.com`) → Use `gh pr create`
- **Azure DevOps** (`dev.azure.com` or `*.visualstudio.com`) → Use `az repos pr create`
- **GitLab** (`gitlab.com` or self-hosted) → Use `gl mr create`

**Implementation:**
1. Check the repo remote with `git remote get-url origin`
2. Route to the appropriate CLI based on domain
3. If CLI is not installed, assist with manual creation via web UI
4. Assume CLIs are installed; they are standard on this machine

## Critical Rules

- Prevent context rot: When a session grows heavy (many turns, many files, re-deriving state), split the work into a fresh, nested context before output quality degrades. Use a native nested-session primitive if available; otherwise emit a self-contained handoff prompt. Checkpoint before splitting. See `docs/context-rot.md` for full procedure and templates.

- Never commit directly to main. Always create a branch and open a Pull Request for review and CI before merging. This repository enforces review-first changes.

## Tool Usage & Ecosystem Guidelines

All agent harnesses have access to the following shared tools and services. Use them when applicable:

### Graphify (Codebase Knowledge Graph)

Knowledge graph engine and MCP service (`graphify-mcp`) at `graphify-out/` mapping god nodes, communities, and cross-file dependencies.

Rules:
- For codebase questions, first run `graphify query "<question>"` when `graphify-out/graph.json` exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation instead of raw source browsing.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

### Ponytail (Lazy Senior Dev Mode)

Before writing any code, stop at the first rung that holds:
1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse existing helpers/patterns, do not rewrite.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

Rules:
- No unrequested abstractions, no speculative boilerplate, no premature generalization.
- Deletion over addition. Boring over clever. Fewest files possible.
- Root cause over symptom: fix bugs where shared callers route through.
- Active via `/ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, and `ponytail-help`.

### OmniRoute (Model Gateway & Routing)

OmniRoute manages unified model routing across providers with health tracking, fallback cascades, and MCP tooling (`omniroute --mcp`).

Rules:
- When routing model calls across multiple providers or configuring fallback cascades, query OmniRoute endpoints and providers via `omniroute` CLI or its MCP server.
- Verify provider health and route availability using `omniroute doctor`.
- Use OmniRoute instead of hardcoding provider-specific URLs or secrets when multi-provider orchestration is required.

### Agent Skills (Standard Skills Library)

Agent skills are managed globally through the `skills` CLI with standard packages from Vercel Labs and Anthropic.

Rules:
- Before hand-rolling complex multi-step routines, inspect available skills using `skills list` or `skills find <query>`.
- Use `skills add <package>` or `skills check` when missing required domain-specific workflows.
- Keep skill references aligned across agent harnesses by syncing through `ai-sync`.

### Karpathy Guidelines (Defensive Coding & Verification)

Guidelines derived from Andrej Karpathy to reduce common LLM coding pitfalls. Available via the `karpathy-guidelines` skill.

Rules:
- Think before coding: State assumptions explicitly. Surface tradeoffs, push back on overcomplicated designs, and ask for clarification instead of guessing.
- Simplicity first: Write the minimum code that solves the problem. No speculative abstractions, unrequested configurability, or defensive handling for impossible cases.
- Surgical changes: Touch only what the task requires. Avoid modifying adjacent formatting, styles, or comments. Leave existing dead code unless asked.
- Goal-driven execution: Define verifiable success criteria before running changes. Loop through failing tests, fixes, and re-verification until goals pass.

