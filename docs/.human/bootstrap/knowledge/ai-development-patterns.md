# AI Development Patterns

Bootstrap heuristics, not downstream project facts.

## Economic model

ChatGPT is the abundant planning/research layer. Codex/Claude are the scarcer implementation layer.

Use ChatGPT to reduce executor uncertainty before execution: read GitHub/Issues, research, compare options, identify likely files, define acceptance, classify effort/risk, and decide whether delegation is worth its overhead.

Do not bypass ChatGPT merely because a task is small; make the contract smaller.

## Routing

- deterministic tool/script before LLM reasoning where possible;
- Main for ambiguity/integration/difficult implementation;
- Worker for bounded locate/execute/extract/compare/validate work;
- Scout only for interpretive investigation;
- no permanent Reviewer; use a fresh independent pass only for elevated-risk work when justified.

## Context

Prefer progressive/selective context. Large raw outputs should be reduced into compact structured evidence before reaching an expensive model.

## Vendor boundaries

Canonical policy should avoid model names. Materialization maps roles/effort to the current Codex/Claude capabilities and verifies effective configuration.
