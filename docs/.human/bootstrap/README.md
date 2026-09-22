# BootCrate Bootstrap Workspace

This directory exists only to create/materialize a downstream project.

## Start here

If you are starting a new project from BootCrate, read:

**[`START_HERE.md`](START_HERE.md)**

For the complete execution/materialization model and possible outputs, read:

**[`MATERIALIZATION_MAP.md`](MATERIALIZATION_MAP.md)**

It covers how remote planning, local discovery, agent effort, generated project maps/scripts, GitHub metadata, validation, and pruning fit together.

Normal downstream development should not load this directory. Successful materialization removes this entire directory and the raw intake; Git history preserves the origin.

## Contents

- `START_HERE.md` — step-by-step onboarding and bootstrap procedure.
- `MATERIALIZATION_MAP.md` — complete materialization pipeline and artifact catalog.
- `app/` — offline bilingual project intake.
- `schemas/` — deterministic structure for exported intake.
- `knowledge/` — bootstrap heuristics for ChatGPT/materialization, not project facts.
- `library/` — canonical Main/Worker/Scout and skill semantics.
- `templates/` — ChatGPT Project and materialization handoff templates.

## Boundary

The app collects intent, preferences, constraints, and known facts. It does **not** choose architecture.

ChatGPT is the normal primary orchestrator:

1. inspect GitHub;
2. read the intake;
3. research material unknowns;
4. discuss options with the owner;
5. resolve product/architecture direction;
6. classify execution effort and local discovery;
7. produce a proportional materialization contract.

The executor then verifies local truth, performs only the required local discovery, specializes the baseline, validates it, and prunes bootstrap-only material.
