# Start Here — BootCrate Project Bootstrap

Use this guide when starting a **new downstream project from BootCrate**.

Do not begin product implementation before completing the discovery/materialization flow. BootCrate is intentionally generic until the owner and ChatGPT resolve the actual project.

## Result you are trying to reach

You begin with:

```text
generic BootCrate repository
```

and end with:

```text
project-specific repository
├── real implementation-agent rules
├── real ChatGPT orchestration context
├── real prompt templates
├── only the needed Codex/Claude adapters
├── project-specific scripts/validation
├── project-specific Issue model
└── no BootCrate/bootstrap residue
```

The normal chain is:

```text
Owner
  ↓
ChatGPT Project
  ↓
GitHub repository + Issues + research
  ↓
owner-approved project design
  ↓
materialization task
  ↓
Codex or Claude Code
  ↓
validated project baseline
```

# Phase 0 — Prepare the project repository

## 1. Create the real GitHub repository

Create the GitHub repository that will become the actual project.

Examples:

```text
owner/MyGame
owner/MyWebApp
owner/MyMod
```

Do **not** develop a downstream product directly inside the upstream `rabrunos/BootCrate` repository.

You may get the BootCrate files into the new repository by copying them, using a GitHub template/fork workflow, or another Git workflow you understand.

The important final state is:

```text
GitHub:
owner/MyProject

Local:
a checkout whose origin points to owner/MyProject
```

## 2. Put the BootCrate baseline in the repository and push it

Before the discovery conversation becomes authoritative, make sure the BootCrate baseline is visible in GitHub.

ChatGPT uses GitHub as its canonical observable repository state.

At this stage, the owner does **not** need to manually recreate BootCrate labels, Milestones, or Issues in the new repository. Live GitHub metadata is reconciled later by the materialization task after ChatGPT has decided what the actual project needs.

The expected solo-development discipline is:

```text
GitHub ≈ local checkout
```

Local uncommitted changes may temporarily be newer, but GitHub should normally represent the latest stable project state available to ChatGPT.

## 3. Keep the local checkout

Codex/Claude will work from an execution checkout, not by repeatedly downloading repository files from GitHub.

Executors must verify local:

```text
branch
HEAD
git status
git diff
```

before changing files.

# Phase 1 — Create the ChatGPT Project

ChatGPT is the **primary orchestrator** in the normal BootCrate workflow.

## 4. Create one ChatGPT Project for this repository

In ChatGPT:

```text
New project
→ name it after the project
```

Recommended:

```text
Project name = the project/repository name
```

## 5. Use project-only memory

Open the ChatGPT Project settings and select **project-only memory**.

The goal is isolation:

```text
this project's chats/files/context
        ↓
available inside this project

unrelated ChatGPT conversations/memory
        ↓
not used as project context
```

Do not use ChatGPT memory as the project's source of truth.

Persistent project knowledge belongs in:

```text
GitHub repository
GitHub Issues
```

Project memory exists to make the ongoing conversation convenient, not to replace versioned state.

## 6. Connect GitHub to ChatGPT

Make sure ChatGPT has access to the project's repository through the GitHub app/plugin available in your ChatGPT account.

Authorize the **actual downstream repository**, for example:

```text
owner/MyProject
```

not only `rabrunos/BootCrate`.

ChatGPT must be able to inspect the current repository before giving project-specific technical direction.

Do not upload duplicate repository snapshots into the ChatGPT Project merely to replace normal GitHub access.

Use file uploads when they provide evidence that is not already available through GitHub, such as:

```text
project-intake.json
logs
screenshots
local-only reports
private evidence intentionally supplied by the owner
```

## 7. Install the BootCrate ChatGPT Project instructions

Open:

```text
docs/.human/bootstrap/templates/chatgpt-project-instructions.md
```

Copy the text inside its code block into the ChatGPT Project instructions.

Replace:

```text
Repository: <OWNER/REPOSITORY>.
```

with the actual repository:

```text
Repository: owner/MyProject.
```

Keep these project instructions short.

They are only the entry point telling ChatGPT where the real project context lives.

Do not copy the entire repository documentation into ChatGPT Project instructions.

## 8. Existing bootstrap discussion may be moved into the project

If you already discussed this project in a normal ChatGPT conversation, you may move that conversation into the ChatGPT Project.

After moving, continue the project work there so later conversations share the same project-scoped context.

# Phase 2 — Choose implementation harnesses

The owner chooses which implementation environment(s) will actually be used.

BootCrate supports:

```text
Codex
Claude Code
or both
```

Do not enable/configure every possible harness merely because BootCrate contains starter adapters.

## 9. Local Codex / IDE

If using Codex locally, the repository already contains the bootstrap surfaces:

```text
AGENTS.md
.codex/
.agents/
```

The materialization task will convert/prune them for the real project.

## 10. Claude Code

If using Claude Code, the repository already contains:

```text
CLAUDE.md
.claude/
```

The materialization task will convert/prune them for the real project.

## 11. Optional cloud execution

Cloud execution is optional.

If you use a Codex/Claude cloud or web execution environment:

- connect/authorize the actual project repository using the current product workflow;
- use the same repository rules and task contracts;
- do not create a second permanent project-state system inside the cloud executor;
- remember that cloud execution may consume separate plan/usage limits.

BootCrate does not require cloud execution.

The durable project context remains GitHub + tracked repository files + Issues.

# Phase 3 — Complete the project intake

## 12. Open the intake app locally

Open:

```text
docs/.human/bootstrap/app/index.html
```

It is intentionally local/offline. No server is required for the normal bootstrap app.

## 13. Answer what you know

The app asks about product intent, target/platform, existing products or external targets, technology preferences, security/data constraints, validation, GitHub workflow, AI workflow, and local-only evidence/tooling.

`Unknown` / `Não sei` is a valid answer.

Do not research technical questions only to satisfy the form. ChatGPT is expected to research material unknowns later.

The intake records owner intent; it does **not** choose architecture.

## 14. Export the final JSON

Use:

```text
Export final JSON
```

The app blocks export while required visible answers are missing. Hidden conditional answers are not exported.

The result is the **RAW** bootstrap layer.

## 15. Do not make the raw intake permanent project state

Preferred workflow:

- keep the exported JSON outside tracked repository files, or under ignored local storage;
- upload it to the ChatGPT Project;
- remove/discard it after successful materialization.

The normalized project profile will preserve the stable conclusions that matter.

# Phase 4 — Discovery with ChatGPT

## 16. Start the bootstrap conversation inside the ChatGPT Project

Upload the exported intake and ask ChatGPT to begin BootCrate discovery.

A minimal message is enough:

```text
This is the initial project intake.
Follow the repository's BootCrate bootstrap process.
Analyze the intake, inspect the current GitHub repository, research material unknowns,
and discuss the project with me before generating any materialization task.
```

## 17. ChatGPT performs the expensive discovery work

ChatGPT should use its abundant orchestration capacity to resolve what can be verified remotely before spending implementation-agent capacity.

Typical work:

```text
read intake
read GitHub
read relevant BootCrate bootstrap knowledge
research current official docs/tooling
compare technology options
identify unknowns and risks
discuss product/architecture choices with owner
define validation approach
decide Codex/Claude/both
decide Main/Worker/Scout needs
define the final Issue Forms/labels/Milestones taxonomy
define initial Epics/Features/Tasks/Bugs/Investigations where useful
```

ChatGPT should not pretend to verify facts that only the execution environment can observe. Those are marked for local verification later.

## 18. Reach explicit owner agreement

Do not materialize while important product/architecture decisions are still unresolved.

The target is:

```text
OWNER INTENT
+
RESEARCHED TECHNICAL REALITY
+
OWNER APPROVAL
=
approved project definition
```

Open implementation work/status belongs in GitHub Issues when appropriate. Do not create duplicate roadmap/status/checkpoint documents.

# Phase 5 — Materialize the project

## 19. Establish project versioning and ask ChatGPT for the materialization task

Every BootCrate project must have one canonical version source before normal development begins.

ChatGPT and the materialization task select the appropriate source:

```text
ecosystem-native metadata when available
        ↓ otherwise
minimal VERSION file
```

The first mutating materialization contract receives a Target Version. That exact version token is preserved in the prompt, any continuations, the main implementation commit, and the final report.

Versioning is mandatory even for static/file-only projects. Publication is separate and remains optional/explicitly authorized.


After agreement, ChatGPT uses:

```text
docs/.human/bootstrap/templates/bootstrap-materialization.md
```

to produce the first implementation contract.

That contract should be resolved and proportional, not a generic instruction dump.

## 20. Run the task in the chosen executor

Use Codex or Claude Code.

The executor:

1. verifies local execution state;
2. confirms any facts that were marked local-only;
3. materializes the approved architecture;
4. creates/adapts only useful project tooling;
5. adapts the final Issue Forms and `.github/labels.yml`;
6. reconciles the **live GitHub labels** to that desired state using an authenticated writable GitHub interface available to the executor;
7. verifies the live labels, then creates requested Milestones/Issues/comments from the materialization contract;
8. validates the resulting project;
9. performs the requested commit/push actions;
10. produces the final report in the owner-selected language.

### GitHub metadata is bootstrap work, not owner busywork

The normal path must not tell the owner to click through GitHub and manually create project labels one by one.

The executor should use the least-complex authenticated GitHub write path already available, such as:

```text
native GitHub integration / plugin
        ↓ otherwise
GitHub CLI (`gh`)
        ↓ otherwise
GitHub REST API
```

Do not introduce MCP or a permanent GitHub automation framework merely to provision labels.

Label synchronization must be safe to run more than once:

```text
missing required label    → create
same label, wrong metadata → update
unrelated existing label  → preserve by default
```

After synchronization, list/verify the actual repository labels before creating Issues whose forms reference them.

If no authenticated GitHub write path is available, report that bootstrap is blocked on **GitHub write authorization/tooling**. The owner may need to authorize a connector or authenticate `gh`, but manual label-by-label creation is not the intended BootCrate workflow.

## 21. Return the implementation report to ChatGPT

The normal review loop is:

```text
executor report
      ↓
Owner
      ↓
ChatGPT
      ↓
GitHub/Issue review
      ↓
accept / follow-up / owner smoke
```

ChatGPT/owner normally decides Issue closure after actual acceptance and required manual smoke.

# Phase 6 — Prune and finish bootstrap

Successful materialization is not complete while generic BootCrate residue remains.

## 22. Remove bootstrap-only content

The materialization task must remove:

```text
docs/.human/bootstrap/
raw project-intake.json
generic BootCrate README/history/branding
disabled harness configuration
unused agents
unused skills
unused scripts
irrelevant Issue Forms
irrelevant release/tooling material
```

Examples:

```text
Codex-only → remove Claude configuration.
Claude-only → remove Codex configuration.
No Scout need → remove Scout.
No release automation → do not retain generic release tooling.
```

## 23. Keep only project-specific context

The final repository should contain only what normal development needs.

Typical durable structure:

```text
project source/config/tests
AGENTS.md and/or CLAUDE.md
docs/.ai/orchestration.md
docs/.ai/CONTEXT_INDEX.md
docs/.ai/TASK_POLICY.md
project-specific prompt templates
docs/.ai/project-profile.json
useful scripts
useful agents/skills
GitHub Issue model
```

The exact final structure depends on the project.

## 24. Confirm the bootstrap is finished

A project is ready for normal development when:

- GitHub reflects the materialized baseline;
- local checkout is clean/synchronized as expected;
- enabled implementation harnesses load their intended configuration;
- validation baseline passes;
- ChatGPT Project instructions point to the final repository;
- normal development no longer needs `docs/.human/bootstrap/`;
- tracked files contain no unintended BootCrate/bootstrap history.

Git history is the bootstrap audit trail.

# Normal development after bootstrap

From this point onward:

```text
Owner
  ↓
ChatGPT
  ↓
GitHub + relevant Issues
  ↓
smallest sufficient task contract
  ↓
Codex / Claude
  ↓
local verification + implementation + validation
  ↓
commit/push/report
  ↓
Owner / ChatGPT review
```

Small tasks still may pass through ChatGPT.

The optimization is not to skip ChatGPT. The optimization is to make the executor receive only the reasoning and context it actually needs.

# Quick checklist

Before discovery:

- [ ] Real GitHub repository exists.
- [ ] BootCrate baseline is pushed.
- [ ] Local checkout points to the real project repository.
- [ ] ChatGPT Project created.
- [ ] Project-only memory selected.
- [ ] GitHub access authorized for the repository.
- [ ] ChatGPT Project instructions installed with the correct `owner/repository`.
- [ ] Intended executor(s) chosen.
- [ ] Optional cloud executor connected only if desired.

Before materialization:

- [ ] Intake exported.
- [ ] Intake given to ChatGPT.
- [ ] ChatGPT inspected GitHub.
- [ ] Important unknowns researched.
- [ ] Owner decisions resolved.
- [ ] Relevant Issues created/updated where appropriate.
- [ ] Canonical version source/convention decided.
- [ ] Materialization Target Version assigned.
- [ ] Materialization contract generated only after agreement.

After materialization:

- [ ] Canonical version source equals the materialization Target Version.
- [ ] Prompt/commit/report preserve the same Target Version token.
- [ ] Deterministic validation passed or limitations are explicit.
- [ ] Baseline committed and pushed.
- [ ] Live GitHub labels match the final `.github/labels.yml`.
- [ ] Required initial Milestones/Issues were created programmatically, or the approved plan explicitly requires none.
- [ ] Owner/ChatGPT reviewed the result.
- [ ] Bootstrap directory removed.
- [ ] Raw intake removed.
- [ ] Unused harnesses/agents/skills/forms/scripts removed.
- [ ] README rewritten for the real project.
- [ ] No unintended BootCrate residue remains.
