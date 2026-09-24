# Codex and Claude Code adapters

These are capability declarations for **two** supported executors. Each describes possible instruction, skills and configuration surfaces; the files alone do not prove a client loaded them. During materialization select Codex, Claude Code or both; copy only chosen instructions/settings/skills, adapting native capabilities and retaining the shared TASK_POLICY. Main is one role: Medium only after all E1 gates, High by default, XHigh for deep work. Standard/Economy changes consumption strategy without lowering any required effort or check.

For every declared surface, record separately:

- provider documentation for the current client;
- files actually emitted into the project;
- observation from that client/version/OS/session, including whether effort was applied, instructions and skills loaded, tools permitted, and isolation enforced.

Until a runtime probe is performed, mark effective settings **unknown**. CLI behavior cannot be generalized to IDE/cloud. Do not treat a textual prohibition as the same as an OS sandbox, or install optional hooks, subagents or MCP services merely because a vendor supports them. Scope and permissions remain task specific. If required capability is unavailable, choose a verified equivalent or block the affected action.

Preset precedence is `task > ignored local > project > standard`; the static shared resolver in the Setup/Console helps display that choice, while executor-specific controls must be applied and verified in the chosen surface. Do not encode a subscription plan or a permanent model name here.
