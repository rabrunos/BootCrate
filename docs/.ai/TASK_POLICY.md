# Task Policy — materialization skeleton

Vendor-neutral rules for turning an owner request into the least expensive reliable execution contract.

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
Task / Goal
Repository basis (when useful)
Likely location or exact target
Scope boundary
Validation
Git/Issue action if any
```

### Extended contract — usually E2/E3

Add only what the task actually needs:

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
