# ChatGPT Orchestration — materialization skeleton

This file becomes the concise project-specific orchestration contract after materialization.

## Normal chain

1. Owner states the desired outcome.
2. ChatGPT inspects the current GitHub repository and relevant Issues.
3. ChatGPT researches external facts when needed.
4. ChatGPT resolves product/architecture ambiguity with the owner.
5. ChatGPT reads the canonical version source and decides root mutation vs continuation/read-only.
6. ChatGPT classifies execution effort E0–E3, Main effort High/XHigh, risk, and local discovery none/targeted/deep.
7. ChatGPT uses `TASK_POLICY.md` and the appropriate prompt template.
8. ChatGPT produces the smallest sufficient implementation contract.
9. Executor verifies local truth and performs only the requested local discovery.
10. Executor materializes/implements, validates, versions, commits/pushes, and performs explicit Issue actions.
11. Owner sends the result/report back to ChatGPT when review/follow-up is needed.
12. Owner/ChatGPT normally decides Issue closure after acceptance/manual smoke.

## Intelligence compression

ChatGPT should resolve everything it can verify remotely before consuming implementation-agent capacity:

- owner intent and decisions;
- current GitHub code/docs/history;
- relevant Issues and acceptance criteria;
- current official documentation/research;
- uploaded/sanitized logs or screenshots;
- likely code locations/integration choices;
- viable alternatives and risks;
- acceptance/validation plan;
- Target Version;
- E0–E3 and Main High/XHigh;
- local discovery depth/questions;
- whether Worker/Scout is worth coordination cost.

Do not pretend to verify local-only facts. Mark only the specific local questions that remain.

## Local discovery routing

Use `none` when local exploration adds no material value.

Use `targeted` for known stacks where toolchain/runtime/path/command/API confirmation is needed.

Use `deep` for external/native/modding/reverse-engineering or difficult local-only behavior where evidence must be gathered before a reliable baseline can be chosen.

Discovery refines technical implementation inside owner-approved direction. It does not silently reopen product decisions.

## Repository freshness

When practical, include the GitHub commit SHA used as repository basis. The executor compares it to local HEAD and inspects local changes rather than re-reading the repository remotely.

## Facts

Use only distinctions needed by the task:

- `Owner decision`
- `Verified`
- `Local verification required`
- `Assumption`

Avoid elaborate confidence metadata for obvious facts.

## Target Version identity

For every mutating root task, ChatGPT assigns Target Version before execution.

```text
PROMPT        # [v0.5] ...
CONTINUATION  # [v0.5] ...
COMMIT        [v0.5] ...
REPORT        # [v0.5] ...
```

Only the token must match. Continuations/corrections for the same unaccepted target retain it. A new independent mutation receives a new Target Version.

## No ChatGPT bypass fast path

Small tasks still may pass through ChatGPT. Optimize by shortening the contract, not by spending executor reasoning on discovery ChatGPT can do first.

## Issues

GitHub Issues own active work state. Do not generate project-status/roadmap/decision-index files that duplicate them.
