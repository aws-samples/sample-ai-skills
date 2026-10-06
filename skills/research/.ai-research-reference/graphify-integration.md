# Graphify Integration Reference

Shared consumption logic for ai-code-* skills that optionally use a project's graphify knowledge graph.

## Detection

Check for `graphify-out/graph.json` in the project root.
- If file exists: graph is available. Proceed with consumption.
- If file does not exist: skip all graph steps. Proceed normally.

## CLI Availability

Before issuing `graphify query` commands, check CLI availability:
- Run: `command -v graphify` (or `which graphify`)
- If available: use `graphify query "<question>"` for targeted queries
- If NOT available: fall back to reading `graphify-out/GRAPH_REPORT.md` directly

## Consumption Pattern

1. **Read GRAPH_REPORT.md** — Extract god nodes, community summaries, and surprising connections. This provides broad architectural orientation (~200-500 tokens relevant content).

2. **Issue targeted queries** (if CLI available) — Use `graphify query "<feature-specific question>"` for focused context. Limit to 1-3 queries per skill invocation.

3. **Integrate findings** — Use graph data to:
   - Identify which modules/files are most relevant (research, design)
   - Understand architectural hubs the feature must integrate with (design, plan)
   - Verify integration points during implementation (implement)
   - Map module boundaries for documentation (as-built)

## Usage by Activity

| Activity | What to extract from graph |
|-------|---------------------------|
| Research | Architecture overview, relevant communities, dependencies for the feature scope |
| Architecture design | God nodes (architectural hubs), community boundaries, surprising cross-module connections |
| Planning | Dependency relationships, integration points, module boundaries for phasing |
| Implementation | "What else touches this?" queries during integration verification |
| As-built documentation | Community structure → module boundaries, god nodes → key components |

## Example Query Output

A `graphify query` response typically returns relevant nodes and relationships in prose form. The exact format may vary by graph size and query, but expect structured text describing:
- Matched entities (files, concepts, modules)
- Relationships between them (imports, calls, depends-on, relates-to)
- Confidence tags (EXTRACTED from code vs. INFERRED from context)

Extract the architectural facts; discard formatting details.

## Fallback Behavior

- If `graphify-out/graph.json` missing → skip all graph steps silently
- If `graphify` CLI unavailable → read GRAPH_REPORT.md directly
- If GRAPH_REPORT.md also missing → skip graph context entirely
- If `graphify query` returns error → proceed without graph context
- Never block on graph failures. Graph context is supplementary, not critical.

## Token Budget

- GRAPH_REPORT.md read: target ~500 tokens of extracted content (god nodes + communities)
- Each `graphify query`: expect ~200-1000 tokens per response
- Total graph context per skill invocation: cap at ~2000 tokens
- If graph report is very large (>3000 tokens), extract only: god nodes list, community names, and surprising connections
