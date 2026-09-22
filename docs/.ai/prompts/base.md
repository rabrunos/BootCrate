# Base Task Contract

Use `../TASK_POLICY.md`. Remove every section the task does not need.

For a mutating root task, the H1 and version fields are mandatory. Continuations preserve the active Target Version. Strictly read-only work may identify the version being observed without creating a new target.

## Compact shape

# [<TARGET_VERSION>] <SHORT_TITLE>

Current version:
<CURRENT_ACCEPTED_VERSION>

Target version:
<TARGET_VERSION>

Goal:
<EXACT_OUTCOME>

Repository basis:
<OPTIONAL_GITHUB_BRANCH_AND_SHA_USED_BY_ORCHESTRATOR>

Target / likely location:
<ONLY_WHEN_KNOWN_AND_USEFUL>

Scope boundary:
<DO_NOT_TOUCH_OR_NONE>

Validation:
<MINIMUM_RELEVANT_CHECK>

Git / Issue action:
<ONLY_WHEN_REQUIRED>

## Extended additions

Add only as needed:

Owner decisions:
<RESOLVED_PRODUCT_OR_ARCHITECTURE_DECISIONS>

Verified facts:
<REMOTE_FACTS_ALREADY_VERIFIED>

Local verification required:
<LOCAL_ONLY_FACTS_THE_EXECUTOR_MUST_CONFIRM>

Assumptions:
<ONLY_REAL_UNVERIFIED_ASSUMPTIONS>

Acceptance criteria:
- <MEASURABLE_CRITERION>
- canonical version source equals <TARGET_VERSION> for a mutating root task

Non-goals:
- <EXPLICIT_NON_GOAL>

Execution policy:
- effort: <E0|E1|E2|E3>
- risk: <normal|elevated>
- delegation: <OMIT_WHEN_DEFAULT_NONE>
- independent review: <OMIT_UNLESS_REQUIRED>

Task-specific constraints:
<ONLY_CONSTRAINTS_NOT_ALREADY_OWNED_BY_REPOSITORY_RULES>

Validation delta:
<CHECKS_BEYOND_REPOSITORY_BASELINE>

Commit and push:
<REQUIREMENT; MUTATING ROOT TASK COMMIT SUBJECT STARTS WITH [<TARGET_VERSION>]>

GitHub Issue actions:
<EXACT_COMMENT/UPDATE/LEAVE-OPEN ACTIONS; CLOSURE ONLY WHEN EXPLICITLY AUTHORIZED>

Final report:
<PROJECT-PROFILE REPORT LANGUAGE; H1 STARTS WITH EXACT [<TARGET_VERSION>] TOKEN; concise behavior/files, version source, validation, commit/push, Issue actions, limitations/follow-up>
