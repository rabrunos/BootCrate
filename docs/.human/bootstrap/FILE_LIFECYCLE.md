# File Lifecycle

## Bootstrap-only: remove after successful downstream materialization

- The entire `docs/.human/bootstrap/` tree: app, heuristics, security module library, templates, self-test code/dependencies and eval fixtures.
- `.github/workflows/bootcrate-validate.yml`.
- Raw intake and generic BootCrate branding/history/version/provenance.

## Adapt to the real project

`AGENTS.md`, `CLAUDE.md`, enabled harness directories, useful skills, orchestration, TASK_POLICY, SECURITY_BASELINE, LOCAL_WORKSPACE, CONTEXT_INDEX, project profile/schema, seven prompt-template families, applicable Issue Forms/label specification and script conventions.

Promote only selected security/service controls and project tests before removing their generic library. Do not copy every module or keep bootstrap tests just to produce a green downstream CI run.

## Generate only when needed

Native source/build manifests, canonical project version source, tests, project-specific CI, secure configuration schemas, doctor/setup, build/run/package/install/diagnostics, a small security/control map, external-target/runtime maps and service/operations guidance.

## Local only

Ignored `.local/` may contain machine resource values, bounded research/indexes, diagnostics, caches and artifacts. Credentials need an appropriate protected secret mechanism, not plain local path configuration. Do not store real evaluation outputs, live findings or task state in the reusable template.

## Permanent stable versus mutable

Stable: core safety/versioning/authority rules. Mutable: source, tests, tooling, selected project maps, version source and stable profile facts as the product changes. Active work/risk status remains in Issues.

Pruning is part of acceptance. Check remaining links/imports and run final project validation after removing unused bootstrap artifacts.
