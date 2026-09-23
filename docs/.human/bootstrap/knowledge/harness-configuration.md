# Harness configuration verification

Canonical effort means Medium / High / XHigh, not a permanently fixed vendor model. Keep High as the default; use supported per-session controls after applying TASK_POLICY eligibility.

Current examples to verify against the installed client before use:

- Codex CLI: `codex -c model_reasoning_effort="medium"` (or `high` / supported `xhigh`). IDE sessions use their supported effort selector. Do not put named CLI profiles in project config and assume they are loaded; the current reference reserves profile selection/files for user configuration.
- Claude Code: `claude --effort medium` (or supported `high` / higher equivalent); verify `/status`, the effective effort control and `claude doctor`. Do not assume every model supports every label.

The active prompt does not reconfigure an already running model. When a switch is unavailable, ask for the setting needed and do not claim it happened. Never change account plans, inject an API key or enable billable services to satisfy a routing choice.

## Security verification

The included Scout allows only read/search tools in Claude; Codex Scout uses a read-only sandbox. These are different mechanisms. Verify effective capabilities on the actual OS/client, including installed plugins and overriding user/managed settings.

Codex keeps workspace-write with network disabled for sandbox commands, on-request approval and core-only environment inheritance. That does not deny every file read or constrain every connector. Production secrets must remain outside the agent workspace/access path. If stronger filesystem restrictions are needed, use the current supported OS/managed permission mechanism rather than inventing a project config key.

Claude's `.env` read denials include nested files and may also deny `.env.example`; a tracked non-secret config schema can describe the keys. Tool denials are not a guarantee against every shell/plugin path. Verify using synthetic canaries and do not relax the boundary to inspect a real credential.

The bootstrap enables Claude Code's supported sandbox as a baseline while still allowing the normal permission system to request unsandboxed execution when necessary. During materialization, verify current client/OS support. For projects whose threat model requires a stronger boundary, disable unsandboxed-command fallback; require sandbox availability only when the selected platform actually supports it and absence of that isolation must block work. Treat these vendor keys as current adapter details, not permanent BootCrate invariants.

Keep agent concurrency conservative. Unused adapters/roles must be pruned. Do not add new MCP connections just to test configuration.

Primary documentation (recheck on client upgrades):
- https://developers.openai.com/codex/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/sandboxing
