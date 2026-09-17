# GitHub Work Model

## ChatGPT view

GitHub repository is ChatGPT's canonical observable project state. The owner keeps it synchronized with local work as part of the normal solo workflow.

ChatGPT reads the repository before project-specific technical guidance and reads relevant Issues when current plans/decisions/status matter.

## Executor view

Codex/Claude work from the local checkout and inspect branch, HEAD, status, and diff before changes. Local uncommitted work is never discarded merely to match remote GitHub.

A ChatGPT task may include the GitHub basis SHA. Local execution checks that basis instead of re-downloading repository files unnecessarily.

## Issues

GitHub Issues are the only active-work state system BootCrate requires:

- Milestone — delivery target/window;
- Epic — large coordinated outcome;
- Feature — capability;
- Task — bounded executable work, including tooling;
- Bug — defect;
- Investigation — evidence/decision work;
- Refactor — structural behavior-preserving work;
- Release — release tracking.

Implementation agents update/comment only when the active contract says so. Owner/ChatGPT normally decides closure after implementation evidence and required manual validation are reviewed.
