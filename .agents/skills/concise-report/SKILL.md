---
name: concise-report
description: Summarize a project implementation, validation or requested execution result concisely, with the exact observed Git/Issue actions and remaining checks. Use for a final task report, not to create a tracked status document.
---

For a tracked implementation, start the report H1 with its assigned `[<TARGET_VERSION>]` token and use the configured report language. For read-only work, do not invent a Target Version or claim an implementation happened.

State the changed behavior, observed version/commit, checks actually run (with failures, blocked or not-run checks distinct), remaining manual smoke, and actual Git/Issue outcomes. Say what still needs acceptance; a successful structural check is not proof of product behavior or security review. Sanitize logs and paths; do not paste secrets or private records.

Return the report as a response after the authorized actions. Do not create a tracked last-report file or duplicate active Issue state.
