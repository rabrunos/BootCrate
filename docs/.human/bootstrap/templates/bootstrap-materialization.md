# [<TARGET_VERSION>] Materialize Project Baseline

Current version: <DOWNSTREAM_BASELINE_OR_NOT_YET_VERSIONED>
Target version: <NEW_PROJECT_TARGET_VERSION>
Repository basis: <BRANCH/SHA>

Owner-approved direction: <INTENT_AND_RESOLVED_DECISIONS>
Verified remote facts: <ONLY_MATERIAL_EVIDENCE>
Local discovery: <none|targeted|deep>; <BLOCKING_QUESTIONS_AND_STOPPING_CONDITION>
Execution: <E1|E2|E3>; Main <medium|high|xhigh>; risk <normal|elevated>
Enabled harnesses: <Codex|Claude Code|both>
Languages: repository <...>; final report <...>
Version source/convention: <NATIVE_SOURCE_OR_MINIMAL_VERSION>
Security: <EXPOSURE_DATA_INPUTS_SELECTED_MODULES_REVIEW_REQUIREMENTS>
Services: <MINIMAL_CAPABILITIES_OPERATING_MODEL_OPERATOR_COST_AND_EXIT_CONSTRAINTS_OR_NONE>
Authorized GitHub/Git actions: <EXACT_LABEL/ISSUE/MILESTONE/COMMIT/PUSH_ACTIONS_OR_NONE>
Relevant Issue: <URL_OR_EXACT_BLOCKER>
Consumption preset: <standard|economy>; execution permissions: <protected_manual|protected_auto|full_access>; Console: <yes|no>
Distribution: <none|selected_destination_AND_FIELD_CONTRACTS>

## 1. Verify local truth

Inspect branch/HEAD/status/diff and preserve unrelated work. Confirm the current downstream version; do not inherit the BootCrate package version as the new product's initial version. Compare supplied basis SHA to local changes.

## 2. Complete bounded discovery

Answer only the remaining local questions. Verify actual SDK/runtime/manifests/toolchain/target representations. Prefer supported APIs before owner-authorized reverse engineering. Keep raw binaries/decompiled/log evidence local and reduce it deterministically.

If evidence changes a consequential product/security/service assumption, stop that decision and return it to the owner. Do not silently invent approval. Provider research does not authorize infrastructure changes or paid accounts.

## 3. Select security and services before finalizing the baseline

Read `docs/.ai/SECURITY_BASELINE.md`; select only applicable modules from `docs/.human/bootstrap/knowledge/security/`. Use assets, actors, entry points and trust boundaries, not a fixed stack checklist. Research current primary guidance and actual framework capabilities.

Promote a compact project-specific control map into durable context when needed. Each selected control must have an implementation location and verification approach. Define negative tests for authorization, malformed input, file/network boundaries, secret leakage and resource limits. Open risks stay in Issues, not parallel status files.

Use `knowledge/service-selection.md` from this bootstrap directory to resolve required capabilities, managed/self-hosted/hybrid responsibility, total cost, limits, recovery and provider exit. Do not add services a project does not need or promise free/unlimited capacity. Sensitive/public deployments require an operator and independent review proportional to risk.

## 4. Materialize only the necessary project

Create source/manifests/tests, one canonical version source and stable normalized `project-profile.json` matching its schema (v3 for a new materialization). Rewrite the root `PROJECT_GUIDE.md` for the real project and preserve that path as the stable ChatGPT entry point. Populate security and any selected services; do not duplicate current version, findings/status, secrets or actual machine paths in the profile. Keep GitHub Issues and ChatGPT as fixed method values; select only Codex/Claude Code as executors. Resolve consumption separately from Main effort, and resolve execution permissions separately from both and from implementation autonomy. New or legacy-unresolved projects use `protected_manual`; Full Access requires explicit risk acknowledgement and never supplies task authorization.

Adapt orchestration, TASK_POLICY, SECURITY_BASELINE, CONTEXT_INDEX, fallback planning and the prompt templates. Choose native build/test/run/doctor/package/install/diagnostics capabilities only where useful. No extra runtime solely for a downstream BootCrate convention.

Keep one Main with Medium/High/XHigh mapping: High default, Medium only through every quality gate, XHigh for deep ambiguity. Verify effective settings and supported effort controls. Scout stays read/search-only; Worker runs bounded commands. Remove unused roles/harnesses/skills; no permanent reviewer, telemetry, MCP, checkpoint, migration manager or tracked last report by default.

Create a concise canonical changelog entry for the first integrated project version. Do not inherit BootCrate's `VERSION` or `CHANGELOG.md` as the product's own history. When distribution is selected, define candidate identity, actual destinations/channels, field formats, shared receipts and a preflight/confirmation path. Materialize provider-specific operations only after validating their actual API/surface; a product without distribution receives no uploader or receipt ledger. If the owner selected the Project Console, copy only `docs/.human/bootstrap/console/{index.html,styles.css,console.js,preset.js,execution-profile.js}` to `project-console/` and verify it still runs by local file. Otherwise omit it entirely.

## 5. Configure machine-local resources safely

Track the requirement/resolver and keep values in ignored `.local/config/` or a native local mechanism. Use explicit override, validated persisted config, bounded detection, then guided/actionable setup. Invalid explicit overrides must fail, not switch targets. Validate identity/manifests, handle multiple/no candidates and never hang in CI.

Test absent/stale/invalid config, unique/multiple/no candidates, overrides and non-interactive behavior with disposable fixtures. Never delete owner state. Use secret facilities for credentials, not plain path config; never print real values to verify their presence.

## 6. Provision only authorized repository metadata

Keep the existing BootCrate Issue Forms unchanged unless a separately scoped change is requested. Reconcile `.github/labels.yml` idempotently via an available authenticated write capability. Create missing labels, update intended metadata, preserve unrelated labels and verify before creating requested Issues/Milestones. Do not copy upstream example Issues.

If write authorization is missing, report the exact blocker rather than claim success or make the owner recreate labels manually. Branch protections, production settings and service purchases need their own explicit approval; do not impose mandatory PRs silently.

## 7. Validate, prune, commit, report

- Run deterministic schema/config, build, behavior and selected security checks. Failed required checks block completion. Report unavailable checks precisely.
- Verify secret-free source/packages, intended privileges and applicable negative/restore/rollback tests. A self-test pass is not a security audit or production approval.
- Confirm version/mirrors, canonical changelog entry, tracked/untracked scope and `git diff --check`.
- Preserve and validate the rewritten root `PROJECT_GUIDE.md`. Remove the complete `docs/.human/bootstrap/` tree, raw intake and `.github/workflows/bootcrate-validate.yml`. The bootstrap verifier, dependencies, scenario fixtures and evaluation tooling do not belong in the new project's normal runtime.
- Remove disabled adapters/unused scripts/forms/skills; promote only selected controls and needed tooling before deleting their generic source library.
- If retaining the Windows execution resolver's `--clear-local` commands, promote `resolve.py` and `_windows_mutation.py` into the same directory and test the copied commands after pruning. Clearing fails closed without the native helper.
- Rewrite README for the real project; remove BootCrate version/history/branding/provenance unless attribution was requested.
- Verify no dangling reference to removed bootstrap content. Run `verify-materialized.py <downstream-root>` from a retained copy of validation tooling and then the final project's own checks after pruning; do not retain bootstrap just to satisfy its self-test. Structural success does not certify behavior or production readiness.
- Commit/push only as authorized, using the target token. Never publish/deploy during validation.

Final response: exact target-token H1, owner report language, materialized scope/security/service decisions, observed version, checks and limitations, actual Git/Issue results. No tracked report file. Owner/ChatGPT reviews acceptance and any manual smoke before Issue closure.
