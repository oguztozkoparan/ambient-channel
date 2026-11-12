@AGENTS.md

## Claude Code specific
- Roles run as subagents (`.claude/agents/`); delegate work to the matching one.

## Required tooling
These four tools exist to save tokens and to keep a knowledge base of the project. They are not optional: the main session and every subagent use them. If one is missing or inactive, say so at the start of the work and give the fix (see `README.md`); do not silently work without it, and do not skip or reword these rules.
- **graphify** (knowledge graph, `graphify-out/`): follow the `## graphify` section below (written by `graphify claude install`). If `graphify-out/graph.json` is missing, build it first with `graphify update .`.
- **rtk** (condensed command output): run commands normally and treat the condensed output as complete. Use `rtk bypass <cmd>` only when the result is unusable (empty when output was expected, contradicting its exit code, garbled), never as a precaution.
- **ponytail** (plugin; smallest complete change, short replies): follow its active mode for every coding task, including the closing line on what was skipped and the risks.
- **caveman** (plugin; terse replies): follow its active mode.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.
