# Materialization Map

This document maps what BootCrate may inspect, generate, keep, or remove. It is bootstrap-only and is deleted from downstream projects after successful materialization.

## Principle

> Discover broadly, materialize narrowly.

BootCrate does not generate the same tree for every technology. ChatGPT resolves intent and remote facts; the executor inspects local reality; the materializer creates only the artifacts justified by the actual project.

## Materialization pipeline

```text
1. owner-approved direction
2. local truth gate
3. local discovery: none | targeted | deep
4. compact evidence
5. technical specialization
6. project baseline
7. canonical capabilities
8. AI harness/context
9. GitHub metadata
10. deterministic validation
11. prune bootstrap/unused adapters
12. Target Version commit + report
```

## Final project artifacts

### Core project state

Every materialized project normally has:

- one canonical version source;
- project source/config/assets appropriate to its stack;
- a rewritten project `README.md`;
- `.gitignore` rules for generated/private/local state;
- `docs/.ai/project-profile.json` with stable normalized policy/facts;
- concise orchestration/task/context routing needed by ChatGPT and the selected implementation harness.

The exact build manifest is ecosystem-specific: examples include package manifests, project files, engine metadata, extension manifests, plugin manifests, or a minimal `VERSION` for file-only projects.

### Harness artifacts — conditional

Keep only enabled harnesses.

Codex may keep:

```text
AGENTS.md
.codex/config.toml
.codex/agents/*.toml
.agents/skills/*/SKILL.md
```

Claude Code may keep:

```text
CLAUDE.md
.claude/settings.json
.claude/agents/*.md
.claude/skills/*/SKILL.md
```

Worker/Scout and individual skills are removed when the project does not benefit from them.

### Project knowledge generated from discovery — conditional

Create small technical maps only when they save future rediscovery. Typical examples:

```text
docs/.ai/source-architecture.md
docs/.ai/validation-tooling.md
docs/.ai/external-target.md
docs/.ai/runtime-lifecycle.md
docs/.ai/api-map.md
docs/.ai/command-cookbook.md
docs/.ai/data-save-map.md
docs/.ai/release-packaging.md
```

Names are examples, not required filenames. `CONTEXT_INDEX.md` points to whatever the project actually needs.

Do not store active status/roadmaps in these files. Issues own active work.

### Canonical capabilities/scripts — conditional

Materialization may create native scripts/commands for:

- `doctor`
- `build`
- `test`
- `validate`
- `run`
- `package`
- `install`
- `diagnostics`
- `publish`

Only create capabilities that have real value. Prefer the project's native ecosystem instead of introducing a second runtime.

For external-target/mod projects, useful project-specific capabilities may also locate the target, index symbols/resources, launch with the mod/plugin installed, or collect/sanitize runtime diagnostics.

### GitHub repository metadata — conditional

The final project may materialize:

- Issue Forms;
- labels reconciled from `.github/labels.yml`;
- Milestones;
- initial Epics/Features/Tasks/Bugs/Investigations;
- CI workflows;
- release workflows only if the project needs them.

The owner should not manually reproduce metadata that the executor can create safely.

### Local-only discovery/evidence

Never commit bulky/raw local evidence merely to help AI.

```text
.local/
  config/
  tools/
  research/
    raw/
    indexes/
    summaries/
  logs/
    raw/
    sanitized/
    summaries/
  cache/
  artifacts/
  temp/
```

Examples include game binaries, SDK extracts, decompiled trees, symbol indexes, package caches, raw logs, screenshots/video, generated test artifacts, and temporary research tools.

Promote only stable compact conclusions into tracked technical maps.

## Examples by project kind

**Game mod / external target:** inspect target version, engine/runtime, supported mod API/loader, installed assemblies/resources, lifecycle, launch/install/log flow, and authorized decompilation evidence. Generate only the maps/scripts needed to avoid repeating that work.

**Game project:** detect engine/toolchain/version, project structure, headless/build/test/export paths, asset/scene conventions, persistence, packaging, and platform-specific validation.

**Browser extension:** establish manifest version, package/build pipeline if any, browser test/smoke path, permissions, packaging, and store-publication boundary.

**Windows/Desktop app:** establish SDK/runtime, build/test/run/package/install paths, installer/signing boundaries, platform APIs, and diagnostics.

**Web/backend:** establish package manager/runtime, lockfile, typecheck/lint/test/build/run, browser/E2E when useful, schema/data migration boundaries, and deployment/publish separation.

**CLI/library:** establish native package manifest, test/build/package commands, API/compatibility boundaries, and release mechanics.

## Pruning

Materialization is incomplete until:

- bootstrap-only files are removed;
- disabled harnesses/agents/skills are removed;
- unused generic scripts/forms/tooling are removed;
- raw intake is removed;
- the README describes the actual project;
- tracked files contain no unintended BootCrate/bootstrap residue.
