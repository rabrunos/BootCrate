# Codex and Claude Code adapters

These are capability declarations for **two** supported executors. Each describes possible instruction, skills and configuration surfaces; the files alone do not prove a client loaded them. During materialization select Codex, Claude Code or both; copy only chosen instructions/settings/skills, adapting native capabilities and retaining the shared TASK_POLICY. Main is one role: Medium only after all E1 gates, High by default, XHigh for deep work. Standard/Economy changes consumption strategy without lowering any required effort or check.

For every declared surface, record separately:

- provider documentation for the current client;
- files actually emitted into the project;
- observation from that client/version/OS/session, including whether effort was applied, instructions and skills loaded, tools permitted, and isolation enforced.

Until a runtime probe is performed, mark effective settings **unknown**. CLI behavior cannot be generalized to IDE/cloud. Do not treat a textual prohibition as the same as an OS sandbox, or install optional hooks, subagents or MCP services merely because a vendor supports them. Scope and permissions remain task specific. If required capability is unavailable, choose a verified equivalent or block the affected action.

Consumption precedence is `task > ignored local > project > standard`. Execution-permission precedence is separately `task > ignored local > protected_manual`; autonomy, effort and consumption never widen it. `resolve.py` validates the ignored `.local/config/execution-profile.json`, exposes the exact native action and can clear that one local file, but it does not launch a client or claim the request was applied. Full Access requires explicit risk acknowledgement. Unsupported Protected Automatic Review blocks instead of falling through to Full Access.

The mappings are based on the official [Codex configuration reference](https://developers.openai.com/docs/config-file/config-reference), [Codex sandboxing guidance](https://developers.openai.com/docs/sandboxing), [Claude Code permissions](https://code.claude.com/docs/en/permissions) and [Claude Code sandboxing](https://code.claude.com/docs/en/sandboxing). Treat them as a versioned adapter contract, then observe the installed client/surface: CLI behavior cannot be generalized to IDE/cloud, managed policy and deny rules may prevail, and requested/effective must be reported separately. Do not encode a subscription plan or permanent model name here.
