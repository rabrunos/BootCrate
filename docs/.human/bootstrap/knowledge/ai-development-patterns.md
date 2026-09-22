# AI Development Patterns

Bootstrap heuristics, not downstream project facts.

## Economic model

ChatGPT is the abundant planning/research layer. Codex/Claude are the scarcer implementation layer.

Use ChatGPT to reduce executor uncertainty before execution: read GitHub/Issues, research current tooling, compare options, identify likely integration points, define acceptance, assign Target Version, classify effort/risk/local-discovery depth, and decide whether delegation is worth its overhead.

Do not bypass ChatGPT merely because a task is small; make the contract smaller.

## Main effort

Main is one role with two normal effort modes:

- **High** — default for ordinary implementation, validation, E1/E2 work, and most coding.
- **XHigh** — reserve for E3 work where deeper reasoning materially helps: architecture, difficult cross-module debugging, unfamiliar/native systems, complex reverse engineering, or deep local discovery.

Do not create separate High/XHigh Main agent definitions. They share the same role/context; only effort changes.

Materialization maps these semantics to current harness capabilities. If a provider does not expose the exact label, use the closest reliable equivalent and document the mapping.

## Delegation

- deterministic tool/script before LLM reasoning where possible;
- Worker for bounded locate/execute/extract/compare/build/test work;
- Scout only for read-focused interpretation that is too ambiguous for Worker but should not consume Main context;
- Main integrates evidence and owns implementation/final judgment;
- no permanent Reviewer; use a fresh independent pass only for elevated-risk work when justified.

Subagents should replace Main work, not duplicate it.

## Local discovery

Remote intelligence should not be repeated locally. Local discovery exists specifically for facts unavailable to ChatGPT.

Use the smallest sufficient depth:

- none;
- targeted;
- deep.

Raw local evidence should be reduced/indexed before expensive reasoning whenever practical.

## Context

Prefer progressive/selective context. Large raw outputs should be reduced into compact structured evidence before reaching an expensive model.

## Vendor boundaries

Canonical policy avoids model names. Materialization verifies current Codex/Claude model aliases, effort levels, precedence, sandbox/permissions, and effective loaded configuration before pinning vendor adapters.
