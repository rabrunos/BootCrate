# Task Policy — materialization skeleton

Vendor-neutral rules for turning an owner request into the least expensive reliable execution contract.

## Mandatory project versioning

Every project materialized by BootCrate is versioned, including projects that only contain static files, documentation, scripts, configuration, or tooling.

Each project has exactly one canonical version source. Prefer the ecosystem-native source when one exists (for example `package.json`, `.csproj`, `Cargo.toml`, `pyproject.toml`, or a product manifest). If no natural source exists, materialization creates the smallest suitable source such as `VERSION`.

### Target Version

Every independent **root implementation contract** that mutates tracked project state receives a Target Version chosen by the orchestrator before execution.

The Target Version identifies the project state the contract intends to produce.

Rules:

- prompt H1: `# [<TARGET_VERSION>] <TITLE>`;
- the contract states both current accepted version and Target Version;
- the executor never chooses or changes the Target Version independently;
- the main implementation commit subject starts with the exact `[<TARGET_VERSION>]` token;
- the final report H1 starts with the same exact token;
- the canonical version source must equal the Target Version before a mutating task is complete;
- once a Target Version is assigned to a root task, do not reuse it for a different root task, even if the original target is abandoned.

### Continuations

A continuation is additional context, correction, or instruction for the same active unaccepted target.

Continuations, implementation corrections, and owner-smoke fixes preserve the existing Target Version. They do not create a new version merely because another prompt/message was sent.

A materially independent root task receives a new Target Version.

### Read-only work

Planning, repository inspection, owner smoke, reporting, Issue-only actions, and strictly read-only investigations do not increment the project version.

If an investigation or other task writes persistent tracked project state, it becomes a mutating task and requires a new Target Version.

### Versioning is not publication

A project may advance through multiple accepted versions without publishing a release or external artifact. Real publication remains separately authorized.

## Execution effort

### E0 — deterministic
A known script/tool/check can perform essentially all of the work. The executor should not spend meaningful reasoning rediscovering the procedure.

### E1 — narrow
Localized, well-understood work with little ambiguity. Usually no subagent. Context should be extremely narrow.

### E2 — standard
Normal implementation work. Main handles it; Worker may be used when bounded exploration/execution would actually save Main capacity.

### E3 — deep
Architecture, difficult debugging, unfamiliar/native behavior, complex cross-module logic, or other high-ambiguity work. Strong Main reasoning is justified; Scout may be useful.

These classes describe required execution intelligence, not vendor/model names. Materialization maps them to currently available models/effort levels.

## Risk

Risk is independent of effort:

- `normal`
- `elevated`

Elevated risk may justify stronger mechanical restrictions, additional validation, explicit owner approval, or an independent fresh-context review. It does not automatically require the most expensive model.

## Delegation

Default to no subagent.

Use Worker when a bounded task can be moved out of Main without duplicating Main work.
Use Scout only when interpretation is genuinely needed and Main + Worker would be inefficient.
Do not create a permanent Reviewer role; request an independent review pass only for elevated-risk work when it adds value.

## Contract proportionality

Use the smallest contract that is executable without guesswork. Remove empty sections.

### Compact contract — usually E0/E1

```text
# [<TARGET_VERSION>] <TITLE>
Current version
Target version
Goal
Repository basis (when useful)
Likely location or exact target
Scope boundary
Validation
Git/Issue action if any
```

### Extended contract — usually E2/E3

Use the same versioned H1/current/target fields, then add only what the task actually needs:

```text
Owner decisions
Verified facts
Local verification required
Assumptions
Acceptance criteria
Non-goals
Compatibility/safety constraints
Execution effort + risk
Delegation guidance when non-default
Validation delta
Commit/push
Exact Issue actions
Final report requirements
```

## Remote versus local truth

ChatGPT may pre-resolve remote facts, but the executor must verify:

- local HEAD/branch/status/diff;
- local uncommitted work;
- local-only configuration/tools;
- installed SDKs/game/runtime/binaries;
- local logs/decompiled evidence not provided to ChatGPT;
- actual build/tests/runtime/graphical behavior.

A task contract must not ask the executor to rediscover remote facts without a reason.
