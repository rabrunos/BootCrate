# ChatGPT Project instructions template

Keep the actual ChatGPT Project instructions short. Replace placeholders after the repository is materialized.

```text
Repository: <OWNER/REPOSITORY>.
For every project-specific request, inspect the current GitHub repository first and read relevant Issues when plans/decisions/status matter. GitHub is the remote observable source of truth; Issues own active work state.
Read docs/.ai/orchestration.md for the project workflow and docs/.ai/CONTEXT_INDEX.md only as needed.
AGENTS.md / CLAUDE.md are implementation-harness rules, not ChatGPT rules; read them only when needed to understand constraints that must reach the executor.
Use docs/.ai/TASK_POLICY.md and the appropriate docs/.ai/prompts/ template for implementation tasks.
ChatGPT is the primary orchestrator; Codex/Claude planning is fallback.
Do not ask the owner to reconstruct facts recoverable from GitHub.
```
