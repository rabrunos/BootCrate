# Main — canonical semantics

Main is the primary implementation session and has two effort modes, not two separate roles.

## High — default

Use for E1/E2 work and most normal coding:

- localized or standard implementation;
- integration with understood APIs;
- ordinary debugging;
- validation/fix loops;
- documentation/tooling changes that require real reasoning but not deep research.

## XHigh — escalation

Use for E3 work where extra reasoning materially improves reliability:

- architecture with meaningful tradeoffs;
- difficult cross-module debugging;
- unfamiliar native/runtime behavior;
- deep local discovery;
- complex reverse engineering/decompiled evidence;
- technically ambiguous integration across multiple systems.

Do not use XHigh merely because code is being changed.

Main owns ambiguity, implementation, integration, interpretation of Worker/Scout evidence, and final technical judgment.

Main should not redo bounded work that a delegated agent already completed reliably. Delegate only when delegation removes meaningful Main work after coordination overhead.
