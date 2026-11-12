@AGENTS.md

## Claude Code specific
- Roles run as subagents (`.claude/agents/`); delegate work to the matching one.

## Required tooling
These four tools exist to save tokens and to keep a knowledge base of the project. They are not optional: the main session and every subagent use them. If one is missing or inactive, say so at the start of the work and give the fix (see `README.md`); do not silently work without it, and do not skip or reword these rules.
- **graphify** (knowledge graph, `graphify-out/`): when searching code or docs, run `graphify query "<question>"` before grep/glob/read, and use `graphify explain` / `graphify path` for relationships. After changing code, run `graphify update .`. If `graphify-out/graph.json` is missing, build it first with `graphify update .`.
- **rtk** (condensed command output): run commands normally and treat the condensed output as complete. Use `rtk bypass <cmd>` only when the result is unusable (empty when output was expected, contradicting its exit code, garbled), never as a precaution.
- **ponytail** (plugin; smallest complete change, short replies): follow its active mode for every coding task, including the closing line on what was skipped and the risks.
- **caveman** (plugin; terse replies): follow its active mode.
