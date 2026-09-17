# BootCrate Bootstrap Workspace

This directory exists only to create/materialize a downstream project.

## Start here

If you are starting a new project from BootCrate, read:

**[`START_HERE.md`](START_HERE.md)**

It is the operational onboarding guide covering:

- GitHub repository preparation;
- ChatGPT Project setup and project-only memory;
- GitHub connection and ChatGPT Project instructions;
- optional Codex/Claude/local/cloud setup;
- intake;
- discovery;
- materialization;
- validation and final pruning.

Do not start product implementation before completing the relevant bootstrap phases.

Normal downstream development should not load this directory. Successful materialization removes this entire directory and the raw intake; Git history preserves the origin.

## Contents

- `START_HERE.md` — step-by-step onboarding and bootstrap procedure.
- `app/` — offline bilingual project intake.
- `schemas/` — deterministic structure for exported intake.
- `knowledge/` — bootstrap heuristics for ChatGPT/materialization, not project facts.
- `library/` — canonical Main/Worker/Scout and skill semantics used to generate only the required harness adapters.
- `templates/` — ChatGPT Project and materialization handoff templates.

## Boundary

The app collects intent, preferences, constraints, and known facts. It does **not** choose architecture.

ChatGPT is the normal primary orchestrator:
1. inspect GitHub;
2. read the intake;
3. research material unknowns;
4. discuss options with the owner;
5. resolve decisions;
6. promote open work into GitHub Issues when appropriate;
7. produce a proportional materialization contract.
