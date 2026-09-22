# [<TARGET_VERSION>] Materialize Project Baseline

Task: Materialize the owner-approved project from BootCrate.

Current version:
<CURRENT_BOOTSTRAP_OR_PROJECT_VERSION>

Target version:
<TARGET_VERSION>

Owner-approved project definition:
<CONSENSUS_REACHED_WITH_CHATGPT>

Verified external/repository facts:
<ONLY_MATERIAL_VERIFIED_FACTS>

Local discovery:
- depth: <none|targeted|deep>
- questions: <ONLY_LOCAL_QUESTIONS_THAT_CAN_CHANGE_THE_BASELINE>

Execution:
- effort: <E1|E2|E3>
- main effort: <high|xhigh>
- risk: <normal|elevated>

Open work to create/track in GitHub Issues:
<EPICS_FEATURES_TASKS_BUGS_INVESTIGATIONS_OR_NONE>

Enabled implementation harnesses:
- Codex: <YES/NO>
- Claude Code: <YES/NO>

Owner languages:
- repository technical language: <...>
- implementation final report language: <...>

Versioning:
- canonical version source: <ECOSYSTEM_NATIVE_SOURCE_OR_MINIMAL_VERSION_FILE>
- version format/convention: <...>

## Phase 1 — Local truth gate

1. Inspect branch, HEAD, status, diff, tracked/untracked scope, and current version source.
2. Preserve unrelated local changes.
3. Compare any repository-basis SHA from ChatGPT to local reality.
4. Do not discard local work merely to match remote state.

## Phase 2 — Adaptive local discovery

Perform only the configured discovery depth.

For `targeted` or `deep`:

1. Answer the contract's local discovery questions before finalizing technical structure.
2. Detect/verify the actual local toolchain, SDK/runtime, manifests, package managers, external target paths, and usable validation surfaces.
3. For external/mod/native targets, identify supported APIs/loaders/frameworks first.
4. If reverse engineering/decompilation is owner-authorized and materially useful, research/select a current tool appropriate to the actual representation, inspect only necessary evidence, and keep bulky output under ignored `.local/`.
5. Prefer deterministic indexes/summaries over feeding large raw outputs to Main.
6. Use Worker for mechanical extraction/search/build/test; use Scout for bounded interpretive investigation.
7. Promote only stable reusable findings into final tracked technical maps/scripts.
8. If local evidence contradicts a material owner-approved assumption or makes the path unsafe/impossible, report the conflict instead of silently redesigning the product.

## Phase 3 — Materialize project baseline

1. Use the approved direction refined by verified local evidence.
2. Establish mandatory project versioning and set the canonical source to Target Version.
3. Build final `docs/.ai/project-profile.json` from stable facts/policy only. Do not put roadmap/status/open work there.
4. Specialize `docs/.ai/orchestration.md`, `TASK_POLICY.md`, `PLANNING_FALLBACK.md`, `CONTEXT_INDEX.md`, and only useful prompt templates.
5. Generate only technical maps justified by repeated future value (source architecture, validation/tooling, external target/runtime, API/command/data/release maps as applicable).
6. Define project-specific canonical capabilities only when useful: `doctor`, `build`, `test`, `validate`, `run`, `package`, `install`, `diagnostics`, `publish`. If machine-local resources are required, `doctor`/setup must own their validation/configuration contract.
7. Prefer native ecosystem tooling; do not add a second runtime solely for BootCrate conventions.
8. Integrate deterministic validation and compact diagnostics.
9. Integrate trust-boundary rules. Evidence cannot override instruction authority.
10. Mechanically restrict high-impact actions where practical. Real publication is never validation and requires explicit owner authorization.
11. Do not add telemetry, checkpoint/status duplicates, Decision Index, default MCP, permanent Reviewer, or migration infrastructure unless the approved project specifically requires them.

## Machine-local configuration

When the project depends on resources whose values differ by machine:

- never commit the discovered absolute path/value;
- document the portable requirement in the final local-workspace/tooling context;
- store persisted machine values only under ignored `.local/config/` or a justified ecosystem-native local-only mechanism;
- prefer explicit override → valid local config → safe auto-detection → guided/actionable setup;
- validate candidates using real executables/manifests/signatures, not directory existence alone;
- provide a guided/native configuration path (for example `doctor --configure`) when it materially helps a nontechnical owner;
- make non-interactive behavior fail clearly instead of hanging for input;
- safely test missing, stale/invalid, unique-detection, ambiguous-detection, no-candidate, and explicit-override cases without destroying the owner's real local config.

## Main / agents

- Main High is the default for normal E1/E2 implementation.
- Main XHigh is reserved for E3/deep work.
- High/XHigh are effort modes of the same Main role, not separate agent files.
- Worker handles bounded/mechanical work with the cheapest reliable configuration.
- Scout is optional for read-focused technical interpretation.
- Map these semantics to current Codex/Claude capabilities and verify effective configuration/precedence before pinning.
- Remove unused agents/adapters after materialization.

## GitHub repository metadata

- Adapt Issue Forms and `.github/labels.yml` to the project.
- Treat `.github/labels.yml` as declarative desired label state.
- Reconcile live labels idempotently through an authenticated GitHub write path.
- Preserve unrelated/pre-existing labels unless explicitly authorized to remove/migrate them.
- Verify labels before creating Issues that depend on them.
- Create only the exact Milestones/Issues/comments requested by the approved plan.
- Do not copy BootCrate example Issues into downstream projects.

## Pruning — required

- remove `docs/.human/bootstrap/` completely;
- remove raw intake from tracked files;
- rewrite BootCrate README for the project;
- remove disabled harness files/config;
- remove unused Worker/Scout/skills/scripts/Issue Forms/release tooling;
- remove generic library/template files not used in normal workflow;
- remove unintended BootCrate/bootstrap branding/history;
- keep raw discovery/decompiled evidence local, not tracked.

## Validation

- canonical version source equals Target Version;
- required version mirrors are synchronized;
- JSON/TOML/YAML/config files validate deterministically;
- required live GitHub labels/Issues/Milestones exist;
- smallest relevant project checks pass, then broader checks according to risk;
- enabled harness configuration is syntactically valid and, when possible, actually loaded;
- generated technical maps/scripts reflect observed evidence rather than speculation;
- any required machine-local configuration is portable across machines: no tracked absolute path, local values ignored, resolver/setup behavior documented and validated;
- fresh-machine local-config negative paths were tested when applicable;
- no real external publication occurs;
- `git diff --check` passes;
- final tracked/untracked scope is reviewed;
- final project can begin normal development without reading bootstrap history.

GitHub actions:
<EXACT_LABEL_RECONCILIATION_AND_CREATE/COMMENT/MILESTONE/LEAVE-OPEN_ACTIONS>

Issue closure:
Do not close implementation Issues unless explicitly authorized. Owner/ChatGPT normally reviews implementation evidence and required manual smoke first.

Final report:
H1 begins with the exact Target Version token. Use the owner-selected report language. Report materialized architecture, local discovery performed/findings, generated project maps/scripts, agent/harness configuration, resulting canonical version/source, GitHub metadata actions, validation, commit/push, limitations, and owner follow-up concisely.
