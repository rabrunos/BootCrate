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

## Live GitHub metadata

Repository files and live GitHub metadata are different things.

Tracked files such as:

```text
.github/ISSUE_TEMPLATE/*.yml
.github/labels.yml
```

travel with Git history/copies, but live repository objects such as Issues, Milestones, and label definitions belong to the destination repository.

BootCrate therefore does not depend on the exact metadata inheritance behavior of forks, templates, ZIP uploads, or future GitHub changes.

During materialization:

1. ChatGPT decides the final project Issue taxonomy and required initial work.
2. The executor adapts Issue Forms and `.github/labels.yml`.
3. `.github/labels.yml` becomes the declarative desired state for project labels.
4. The executor uses an authenticated GitHub write capability to reconcile the actual repository labels.
5. Reconciliation creates missing labels, updates configured metadata, and preserves unrelated labels by default.
6. The executor verifies the live labels before creating Issues that reference them.
7. It then creates only the Milestones/Issues/comments explicitly requested by the approved materialization contract.

This synchronization must be idempotent so retrying materialization does not duplicate or damage repository metadata.

The owner may need to authorize the GitHub integration or authenticate a CLI, but manually recreating the label catalog is not the intended workflow.
