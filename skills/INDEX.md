# Skills Catalog & Management Guide

This document is the canonical index of AI agent skills across harnesses.

---

## Architecture & Policy

- **First-Party Authored Skills**: Authored skills created specifically for this workflow live directly in `skills/` in this repository:
  - [`screencast-tutorial`](screencast-tutorial/SKILL.md) — Generic narrated web walkthrough automation pipeline (Playwright + TTS + FFmpeg + YouTube).
  - [`context-rot-prevention`](context-rot-prevention/SKILL.md) — Work splitting and nested session management for long sessions.
  - [`de-claude`](de-claude/SKILL.md) — Removes Claude/AI conversational boilerplate and tells.
  - [`conversation-history`](conversation-history/SKILL.md) — Decision logging and cross-agent context reduction.
- **External & Vendor Skills**: **Never commit external skill trees directly into this repository.** External skills have their own upstream repositories. Vendoring them here breaks their update paths (`skills update`, git tracking, or npm releases). Instead, manage and install external skills globally or per-project using the `skills` CLI.

---

## Installing & Updating Skills

Use the `skills` CLI to discover, install, and update external skills:

```bash
# Search for skills
skills find <query>

# Install a skill package globally for all agents
skills add <package> -g --all

# Update installed skills to the latest upstream versions
skills update -g

# List installed skills
skills list -g
```

---

## External Skills Catalog

### 1. Code Quality, Philosophy & Defensive Coding

| Skill | Upstream / Package | Description |
|---|---|---|
| `ponytail` | Ponytail suite | Lazy Senior Dev mode: YAGNI, standard library reuse, deletion over addition. |
| `karpathy-guidelines` | Andrej Karpathy guidelines | Defensive coding, minimal surgical edits, and goal-driven test verification. |
| `antislop` | Antislop toolkit | Eliminates generic AI filler, comments, and repetitive prose. |
| `safe-refactor` | Refactoring patterns | Restructure code while strictly preserving existing behavior with proof. |
| `surgical-patch` | Surgical patching | Narrowest responsible layer fixes; avoid touching adjacent unchanged code. |
| `systematic-debugging` | Debugging protocol | Root-cause hypothesis testing and reproduction before making edits. |

### 2. Vercel & Modern Frontend

| Skill | Upstream / Package | Description |
|---|---|---|
| `vercel-react-best-practices` | `vercel-labs/agent-skills` | React 19 performance, server components, and state discipline. |
| `vercel-composition-patterns` | `vercel-labs/agent-skills` | Scalable component composition patterns without prop drilling. |
| `deploy-to-vercel` | `vercel-labs/agent-skills` | Vercel deployment automation and preview orchestration. |
| `web-design-guidelines` | Web interface guidelines | UX, accessibility, focus states, and tap target audits. |
| `frontend-design` | Design systems | Distinctive aesthetic direction, typography, and anti-template layouts. |

### 3. Backend & Cloud Infrastructure

| Skill | Upstream / Package | Description |
|---|---|---|
| `convex` | Convex platform | Reactive TypeScript backend, auth, scheduling, and component workflows. |
| `wrangler` | Cloudflare | Cloudflare Workers, KV, R2, D1, Vectorize, and Pages deployments. |
| `cloudflare-one` | Cloudflare Zero Trust | Access, Gateway, WARP, Tunnel, and identity posture configuration. |
| `aws-cloudformation` | AWS CloudFormation | Infrastructure as Code validation, linting, and failure remediation. |
| `aws-sdk-js-v3-usage` | AWS SDK JS v3 | Type-safe AWS SDK client integration and runtime validation. |

### 4. gstack Suite (Autonomous Engineering & QA)

| Skill | Upstream / Package | Description |
|---|---|---|
| `gstack` | gstack suite | Main router for review, QA, browse, canary, shipping, and design. |
| `gstack-review` | gstack suite | Pre-landing diff review for SQL safety, side effects, and boundary violations. |
| `gstack-browse` | gstack suite | Headless browser execution and interaction testing with console capture. |
| `gstack-cso` | gstack suite | Security audits, OWASP top 10 review, and threat modeling. |
| `gstack-canary` | gstack suite | Post-deploy canary monitoring, error baseline tracking, and regressions. |

### 5. Mobile & Android

| Skill | Upstream / Package | Description |
|---|---|---|
| `android-clean-architecture` | Android developer kit | Clean Architecture patterns, module structure, and UseCases for Kotlin/Compose. |
| `android-jetpack-compose` | Android developer kit | Declarative UI patterns, state hoisting, and recomposition optimization. |
| `edge-to-edge` | Android developer kit | Adaptive edge-to-edge window insets and IME handling. |
| `camerax` | Android developer kit | Low-level CameraX integration and asynchronous capture lifecycles. |
| `r8-analyzer` | Android developer kit | Proguard / R8 keep rules optimization and redundant rule removal. |

### 6. Shopify & E-Commerce

| Skill | Upstream / Package | Description |
|---|---|---|
| `shopify-development` | Shopify Agentic Kit | Theme App Extensions, Storefront API, GraphQL admin, and Shopify CLI workflows. |
| `shopify-liquid` | Shopify Theme Kit | Liquid templates, sections, schema blocks, and performance optimization. |

---

## Adding New Skills

When creating a new custom skill:
1. Initialize with `skills init <skill-name>` or scaffold a folder under `skills/<skill-name>/`.
2. Provide a valid `SKILL.md` with standard YAML frontmatter (`name` and `description`).
3. Ensure no local secrets, `.env` files, or compiled binaries (`*.exe`) are committed.
