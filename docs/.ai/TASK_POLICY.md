# Task Policy — materialization skeleton

Vendor-neutral rules for turning an owner request into the least expensive reliable execution contract.

## Mandatory project versioning

Every project materialized by BootCrate is versioned, including projects that only contain static files, documentation, scripts, configuration, or tooling.

Each project has exactly one canonical version source. Prefer the ecosystem-native source when one exists. If no natural source exists, materialization creates the smallest suitable source such as `VERSION`.

### Target Version

Every independent root implementation contract that mutates tracked project state receives a Target Version chosen by the orchestrator before execution.

Rules:

- prompt H1: `# [<TARGET_VERSION>] <TITLE>`;
- state current accepted version and Target Version;
- executor never chooses or silently changes Target Version;
- main implementation commit starts with `[<TARGET_VERSION>]`;
- final report H1 starts with the same token;
- canonical version source equals Target Version before completion;
- assigned Target Versions are not reused for another root task.

Continuations, implementation corrections, and owner-smoke fixes for the same unaccepted target reuse the existing Target Version.

Planning, repository inspection, owner smoke, reporting, Issue-only actions, and strictly read-only investigations do not increment the version. If tracked project state is written, the task is mutating and needs a new Target Version.

Versioning is not publication. Real publication remains separately authorized.

## Execution effort

### E0 — deterministic

A known script/tool/check performs essentially all work. Prefer Worker or direct deterministic execution. Main supervises only when needed.

### E1 — narrow

Localized, well-understood work with little ambiguity.

**Main effort: High** by default. Usually no subagent.

### E2 — standard

Normal implementation work, integration, validation, or debugging.

**Main effort: High** by default. Worker may be used when bounded work can be delegated cheaply.

### E3 — deep

Architecture, difficult debugging, unfamiliar/native behavior, complex cross-module logic, deep local discovery, or complex reverse engineering.

**Main effort: XHigh** by default when the selected harness currently supports it reliably. Scout may be useful. If the harness uses different effort names, materialization maps XHigh to the closest verified equivalent.

High/XHigh are effort modes of Main, not separate agents. XHigh is not the default for all coding.

## Local discovery

The orchestrator also classifies local discovery:

- `none` — no material local unknowns beyond normal truth checks;
- `targeted` — confirm known toolchain/runtime/paths/commands/integration points;
- `deep` — investigate unfamiliar/native/external targets, binaries, decompiled evidence, or ambiguous local-only behavior.

Local discovery should answer specific blocking questions and stop. Do not explore broadly merely because tools are available.

## Risk

Risk is independent of effort:

- `normal`
- `elevated`

Elevated risk may justify stronger mechanical restrictions, additional validation, explicit owner approval, or an independent fresh-context review. It does not automatically require XHigh.

## Delegation

Default to no subagent.

Use Worker when a bounded task can be moved out of Main without duplicating Main work.

Use Scout only when evidence requires interpretation beyond Worker and spending Main context on raw exploration would be inefficient.

Do not create a permanent Reviewer role; request an independent review pass only for elevated-risk work when it adds value.

## Contract proportionality

Use the smallest contract that is executable without guesswork. Remove empty sections.

### Compact contract — usually E0/E1

```text
# [<TARGET_VERSION>] <TITLE>
Current version
Target version
Goal
Execution: E-level + Main effort + local discovery
Repository basis (when useful)
Likely location or exact target
Scope boundary
Validation
Git/Issue action if any
```

### Extended contract — usually E2/E3

Use the same identity/execution fields, then add only what the task actually needs:

```text
Owner decisions
Verified facts
Local verification required
Local discovery questions
Assumptions
Acceptance criteria
Non-goals
Compatibility/safety constraints
Risk
Delegation guidance when non-default
Validation delta
Commit/push
Exact Issue actions
Final report requirements
```

## Remote versus local truth

ChatGPT may pre-resolve remote facts, but the executor must verify:

- local HEAD/branch/status/diff;
- canonical version source;
- local uncommitted work;
- local-only configuration/tools;
- installed SDKs/game/runtime/binaries;
- local logs/decompiled evidence not provided to ChatGPT;
- actual build/tests/runtime/graphical behavior.

A task contract must not ask the executor to rediscover remote facts without a reason.
