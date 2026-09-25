# Base Task Contract

Use `../TASK_POLICY.md`. Remove unused sections; never repeat the entire policy library in an execution prompt. For read-only work identify the observed revision instead of promising a new version.

## Compact mutation shape

```text
# [<TARGET_VERSION>] <TITLE>
Current version: <OBSERVED_BASELINE_VERSION>
Target version: <TARGET_VERSION>
Goal: <EXACT_OUTCOME>
Scope: <TARGET_AND_DO_NOT_TOUCH>
Relevant Issue: <ISSUE_URL_OR_EXACT_ACCESS_BLOCKER>
Validation: <CHECKS_THAT_PROVE_THE_CHANGE>
Git / Issue actions: <ONLY_AUTHORIZED_ACTIONS>
```

## Add only material deltas

- Repository basis: <BRANCH/SHA used by planner>.
- Owner decisions / verified facts / local questions / assumptions.
- Execution: effort <E0|E1|E2|E3>, Main <medium|high|xhigh>, risk <normal|elevated>.
- Consumption preset <standard|economy> and override source when relevant; it never lowers required effort.
- Medium eligibility: <brief evidence all gates hold; otherwise use High>.
- Local discovery: <none|targeted|deep>, bounded questions and stopping condition.
- Security: <changed boundaries, selected controls, negative tests, release blockers, review>.
- Services: <approved capability/operating model/operator; provisioning authorization remains separate>.
- Acceptance / non-goals / compatibility / required version mirrors.
- Delivery candidate/destinations/changelog/receipt boundaries only when the project distributes.
- Delegation: <omit for default none; only bounded Worker/Scout work>.
- Commit/push and exact Issue actions; closure only when authorized.

## Continuation

```text
# [<ACTIVE_TARGET_VERSION>] Continuation — <DELTA>
<NEW_EVIDENCE_OR_SCOPE_CLARIFICATION>
```

Keep the same target while finishing that unaccepted work. Escalation changes effective effort, not identity.

## Final report contract

Respond with H1 starting with the exact version token in the owner's report language. Include material changes, observed version, validation actually run, failures/unverified checks, security limitations, commit/push and requested Issue actions. No secrets, raw successful logs or tracked last-report file. Never claim an unavailable effort switch or an unperformed production/security test.
