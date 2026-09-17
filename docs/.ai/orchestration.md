# ChatGPT Orchestration — materialization skeleton

This file becomes the concise project-specific orchestration contract after materialization.

## Normal chain

1. Owner states the desired outcome.
2. ChatGPT inspects the current GitHub repository before project-specific technical guidance and reads relevant Issues when work state/decisions matter.
3. ChatGPT researches external facts when needed.
4. ChatGPT resolves product/architecture ambiguity with the owner.
5. ChatGPT uses `TASK_POLICY.md` and the appropriate template under `prompts/`.
6. ChatGPT produces the **smallest sufficient** implementation contract.
7. Owner sends it to Codex or Claude Code.
8. Executor verifies local branch/HEAD/status/diff, implements, validates, commits/pushes as instructed, and performs only explicit Issue actions.
9. Owner sends the result/report back to ChatGPT when review or follow-up is needed.
10. Owner/ChatGPT normally decides Issue closure after acceptance/manual smoke is actually satisfied.

## Intelligence compression

ChatGPT should resolve everything it can verify remotely before consuming implementation-agent capacity:

- owner intent and decisions;
- current GitHub code/docs/history;
- relevant Issues and acceptance criteria;
- external official documentation/research;
- uploaded/sanitized logs or screenshots;
- likely code locations;
- viable alternatives and risks;
- acceptance/validation plan;
- execution effort and risk class;
- whether Worker/Scout is worth its coordination cost.

Do **not** pretend to verify local-only facts. Mark them for local verification in the contract.

## Repository freshness

When practical, include the GitHub commit SHA used as the repository basis. The executor compares it to local HEAD and inspects local changes instead of re-reading the entire repository from GitHub.

## Facts

Use only the distinctions needed by the task:

- `Owner decision`
- `Verified`
- `Local verification required`
- `Assumption`

Do not attach elaborate confidence metadata to obvious facts.

## No ChatGPT bypass fast path

Small tasks still may pass through ChatGPT. Optimize by shortening the contract, not by forcing the owner to spend implementation-agent reasoning on discovery that ChatGPT can do first.

## Issues

GitHub Issues own active work state. Do not generate project-status/roadmap/decision-index files that duplicate them.
