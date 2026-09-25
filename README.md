# BootCrate

BootCrate is a stack-neutral starting system for AI-assisted software projects. It supplies discovery, policies and reusable skeletons, not one fixed application stack.

**Starting or adopting a project? Open [BootCrate Setup](docs/.human/bootstrap/app/index.html).** It records intent, separates new products from existing code, and prepares a GitHub/ChatGPT handoff. The Setup cannot verify remote access or decide architecture by itself. [START_HERE](docs/.human/bootstrap/START_HERE.md) gives the complete procedure.

The template is the product being maintained here. A downstream project adapts it and removes generic bootstrap material; maintaining BootCrate itself does not run that materialization workflow.

## Workflow

```text
Owner → ChatGPT → current GitHub/Issues + research + owner agreement
→ smallest sufficient versioned contract → Codex or Claude Code
→ local truth + bounded discovery → implementation + validation
→ authorized commit/push → final response → owner/ChatGPT review
```

ChatGPT is the normal planning layer for work that needs discovery, decisions or coordination. Fully resolved deterministic E0/eligible E1 work may go directly to an executor when the owner intentionally chooses that lane; all versioning, safety and validation rules still apply. Codex/Claude planning remains a fallback. Durable knowledge is in the repository; active work and acceptance are in Issues. Local checkout is execution reality and is checked before edits. No parallel work-state, checkpoint or last-report file is required.

GitHub Issues are required for executable tasks. Keep continuations, implementation evidence and required manual smoke in the relevant Issue; accept and close only after the criteria are observed. Issue Forms remain the existing Epic, Feature, Task, Bug, Investigation, Refactor and Release forms. Tooling can use Task; no new form is required for each capability.

## Context and version identity

Raw intake becomes a stable normalized project profile after discussion/research. Each execution receives only its necessary subset, not all answers or the entire knowledge library.

Every materialized project is versioned, even HTML-only, documentation and tooling projects. Use one native version source or a minimal `VERSION`. New mutating root tasks receive a Target Version; continuations preserve the same unaccepted target. Prompt/commit/report share `[<TARGET_VERSION>]`, while titles may differ. Read-only work/local setup do not bump version; versioning does not authorize publication.

Parallel work needs exclusive targets and serialized integration. Every integrated version has a concise changelog entry even if internal or unpublished. A prepared, verified candidate is frozen separately from per-destination publication; each destination needs its own confirmed receipt and changelog interval. Unknown remote outcomes block a blind retry. A project without distribution has no uploader or publication ledger. See the [delivery contract](docs/.human/bootstrap/delivery/README.md).

## Quality-first reasoning

Main is one role with three effort levels:

| Level | Use |
| --- | --- |
| Medium | Resolved, familiar, reversible work with direct deterministic coverage and no sensitive-boundary change |
| High | Default for normal implementation and judgment |
| XHigh | Deep ambiguity, difficult architecture/debugging and complex security/native work |

[TASK_POLICY](docs/.ai/TASK_POLICY.md) defines all eligibility and escalation rules. Uncertainty falls back to High. A prompt cannot itself switch model effort: use supported client settings and verify the effective choice.

Worker handles bounded mechanical execution; Scout interprets scoped read-only evidence. Delegation is optional and must replace work, not multiply it. No permanent reviewer or automatic fan-out is required.

The Padrão (`standard`) and Econômico (`economy`) consumption presets select how much optional delegation/context to use. They preserve the same Main effort, security, validation and authorization. A task override precedes an ignored local override, then the project's default, then Padrão. The selected executor must verify its effective settings; a requested XHigh is not proof the client applied it.

## Security by attack surface

[SECURITY_BASELINE](docs/.ai/SECURITY_BASELINE.md) supplies a small universal core. Discovery selects only relevant web/API, desktop/mobile, multiplayer/native, infrastructure and sensitive-data controls. The owner describes users/data/operations, not vulnerability names.

Materialization links selected controls to implementations and negative tests: authorization, injection/XSS, input/parser limits, host/file/process boundaries, secret leakage, recovery and abuse controls as applicable. Security, functional validation and explicit deployment approval are separate gates. No model/template/scanner guarantees vulnerability-free software or compliance.

Secrets do not belong in source, logs, prompts, reports, artifacts or client applications. `.env` and common private-key/credential paths are ignored; placeholder-only examples may be tracked. Ignore rules are not access control. Use scoped local/CI/production secret facilities, verify effective agent restrictions and rotate exposed credentials.

## Local discovery and another computer

Local discovery is `none`, `targeted` or `deep`, answering only blocking questions. Verify actual runtime/API/representation before selecting inspection/decompilation tools; prefer supported extension points and use reverse engineering only when authorized.

Track resource requirements/resolvers, not machine-specific absolute paths. Keep actual values in ignored `.local/config/` or a native equivalent. Prefer explicit override → validated config → bounded detection → guided/actionable setup. Reject invalid overrides, handle ambiguous candidates and never hang in CI. Test new-machine paths safely with disposable fixtures.

`.local/` may hold only necessary config, tools, research/indexes, diagnostics, caches and artifacts. Credentials require separate appropriate protection. See [LOCAL_WORKSPACE](docs/.ai/LOCAL_WORKSPACE.md).

## External services and operating cost

[Service selection](docs/.human/bootstrap/knowledge/service-selection.md) starts with needs such as persistence, authentication, scores, storage or jobs. Compare no service, managed, self-hosted and hybrid using total cost, operator responsibility, recovery, scale and exit strategy.

No provider, database or VPS is mandatory. Free software is not cost-free operation and no provider is assumed unlimited. Research current terms/limits during discovery. Do not provision paid services, change live infrastructure or deploy merely because an option was selected.

## What a project receives

Use the [materialization map](docs/.human/bootstrap/MATERIALIZATION_MAP.md). Keep only relevant source/manifests/tests, enabled harnesses/skills, stable profile/context/policies, selected security controls, required tooling and GitHub metadata.

For an existing codebase, first use an [Adoption Sandbox](docs/.human/bootstrap/adoption/README.md) that leaves the original root intact. Preserve useful scripts and product knowledge, replace conflicting old method instructions, validate the complete selected configuration, then transfer only an approved delta and recheck the original. The temporary [managed-file upgrade](docs/.human/bootstrap/upgrade/README.md) applies only before materialization. The [Project Console](docs/.human/bootstrap/console/README.md) is an optional small output, separate from the discarded Setup.

Possible capabilities are doctor, build, test, validate, run, package, install, diagnostics and publish. They are not a requirement to create nine scripts or introduce another runtime.

Codex uses `AGENTS.md`, `.codex/` and `.agents/skills/`. Claude uses `CLAUDE.md` and `.claude/`; the shared import avoids needless rule duplication. Formats and effective settings must be verified against the installed client, not assumed from valid TOML/JSON alone.

## GitHub setup

Issue Forms cover Epic, Feature, Task, Bug, Investigation, Refactor and Release. Tooling normally uses Task. Milestones are delivery groupings, not another status file.

`.github/labels.yml` is desired metadata. During materialization the executor creates/updates the required live labels, preserves unrelated labels and verifies results before creating the exact approved Issues/Milestones. Fork/ZIP creation is not assumed to provision metadata. Missing authentication is a setup blocker, not a request for the owner to recreate every label manually.

## Validation of this reusable template

[Validation guide](docs/.human/bootstrap/validation/README.md) provides one local/CI command for schemas, JSON/TOML/YAML, question/schema consistency, skills, policy invariants, secret-pattern smoke checks, links and intake tests. CI uses read-only permissions and pinned external actions; it does not publish or spend model credits.

[Scenario evals](docs/.human/bootstrap/evals/README.md) distinguish deterministic fixture/grader tests, actual model-plan evaluation and real isolated materialization. Passing the first layer does not prove the latter two or certify security.

The intake now records repository situation, separate external integration, distribution, consumption preset and optional Console. It removes choices that could turn off the method. An imported v1 intake that conflicts with required Issues/ChatGPT needs visible confirmation; the file itself is not rewritten. Missing security/hosting intentions are resolved in conversation using the [coverage guide](docs/.human/bootstrap/knowledge/discovery-coverage.md).

## Pruning and boundaries

After downstream materialization remove `docs/.human/bootstrap/`, raw intake, `.github/workflows/bootcrate-validate.yml`, unused adapters/roles/forms/tooling and generic BootCrate identity/version/history. Promote only necessary project controls/tests first, verify links and run the final project's own checks. Do not copy bootstrap evaluation data or maintenance state into the new product.

No AI telemetry, checkpoint database, Decision Index, MCP setup, permanent Reviewer, migration framework or tracked last-report is added by default. Reports remain responses containing the actual commit/push outcome; Issues remain active-work truth.

Technical content defaults to English and owner-facing reports to pt-BR, configurable in the materialized profile. This package is **BootCrate v0.9**; `VERSION` is its canonical version source.
