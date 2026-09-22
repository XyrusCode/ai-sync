# Graphify Pairing Protocol

This document defines how `conversation-history` pairs with `graphify` (`graphify-out/graph.json` and the `graphify` skill) to minimize context and token usage during code exploration and architectural tasks.

## The Context Challenge

Exploring codebases through standard file reads quickly swamps the context window:
- A single controller file can take 1,500 tokens.
- Reading 10 files across a service boundary consumes 15,000+ tokens.
- Tracing callers via raw grep leaves dozens of noisy lines in the conversation log.

When `graphify` is present, you replace raw code ingestion with targeted graph traversals.

## Graph Traversal Rules

### 1. Check for Existing Graph
Before reading large source files, check if `graphify-out/graph.json` exists in the repository root.
- If present, use graph queries before using file search tools.
- If absent, skip silently in zero turns. Proceed with standard targeted file reads. Never run commands to generate or install a graph during task execution.

### 2. Querying Instead of Ingesting
Use the graphify CLI or NetworkX traversal to retrieve scoped subgraphs:
- **Concept and domain questions**: Run `graphify query "<question>"`. This traverses related communities and returns a concise, bounded answer rather than pages of raw code.
- **Dependency and flow questions**: Run `graphify path "<SourceComponent>" "<TargetComponent>"`. This reveals bridge nodes and coupling points between two parts of the system.
- **Component definitions**: Run `graphify explain "<NodeName>"`. This provides an immediate structural summary with cited `source_location` coordinates.

### 3. Entity Anchoring
In the Active Objectives Ledger, reference the specific graph entity IDs (nodes and community labels) rather than writing long prose descriptions of system architecture.

Example:
- Verbose approach (wastes 200 tokens every turn): "We are modifying the UserAuthenticationController which imports JwtTokenGenerator and dispatches to DatabaseUserRepository via the UserRepositoryInterface..."
- Graph-anchored approach (wastes 25 tokens): "Focus: Node `UserAuthenticationController` (Community 2: Auth Pipeline), bridging to `DatabaseUserRepository`."

### 4. Graph Maintenance
When code edits are complete:
- If a graph already existed, run `graphify update .` to re-extract AST structural changes for modified files.
- If no graph existed, do nothing.
