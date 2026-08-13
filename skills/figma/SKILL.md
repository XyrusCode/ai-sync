---
name: figma
description: Figma design integration — fetch design context, generate designs, and manipulate Figma files via the Figma MCP server
version: 1.0.0
author: opencode
type: skill
category: design
tags:
  - figma
  - design
  - ui
  - prototyping
---

# Figma Design Skill

> **Purpose**: Connect to Figma via the Figma MCP server to read design context, generate new designs, and automate Figma workflows.

---

## Prerequisites

- Figma MCP must be configured in `opencode.json` with `type: "remote"` and `url: "https://mcp.figma.com/mcp"`
- OAuth must be completed (browser-based auth flow)

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `get_screenshot` | Render a node as PNG (supports Figma design, FigJam, Slides) |
| `get_design_context` | Fetch design structure, layers, styles, text from a Figma file |
| `get_metadata` | Get file metadata (name, last modified, etc.) |
| `get_variable_defs` | List design token variables and their values |
| `get_figjam` | Retrieve FigJam board content |
| `get_code_connect_map` | View existing code-to-design mappings |
| `get_code_connect_suggestions` | Get AI suggestions for code connect mappings |
| `get_context_for_code_connect` | Get context data needed for code connect |
| `whoami` | Show current authenticated Figma user |
| `generate_figma_design` | Capture/import a web page as a Figma design |
| `generate_diagram` | Generate a diagram in Figma/FigJam |
| `add_code_connect_map` | Link a code component to a Figma node |
| `send_code_connect_mappings` | Batch-upload code connect mappings |
| `use_figma` | General-purpose read/write — create/edit/delete any Figma object |
| `get_libraries` | List available design system libraries |
| `search_design_system` | Search design system components and styles |
| `create_new_file` | Create a new Figma file |
| `upload_assets` | Upload image assets to Figma |

---

## Common Workflows

### Design-to-Code
1. `get_design_context` with a Figma file URL/node ID
2. Implement the component matching the design specs
3. `add_code_connect_map` to link code back to the Figma node

### Code-to-Design
1. Build a UI component
2. `generate_figma_design` to create a matching Figma frame
3. Refine visually in Figma

### Design System Sync
1. `get_libraries` + `search_design_system` to find components
2. `get_variable_defs` to read design tokens
3. Generate component code matching the tokens
4. `use_figma` to update variables/styles if needed

### Screenshot & Review
1. `get_screenshot` on a design node
2. Review the rendered output
3. `use_figma` to suggest edits or `get_design_context` for specs
