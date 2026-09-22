# BootCrate Bootstrap Architecture

BootCrate itself may be broad; a downstream materialized project must be narrow.

## Bootstrap compiler

```text
Owner intent
   ↓
offline intake (RAW)
   ↓
ChatGPT + GitHub + Issues + external research
   ↓
owner-approved technical direction
   ↓
normalized project profile
   ↓
materialization contract
   ↓
LOCAL TRUTH GATE
branch / HEAD / status / diff / installed environment
   ↓
ADAPTIVE LOCAL DISCOVERY
none / targeted / deep
   ↓
evidence reduction + technical specialization
   ↓
project-specific baseline materialization
   ↓
validation + GitHub metadata + versioned commit
   ↓
pruning
   ↓
final project
```

ChatGPT should resolve everything reliably observable remotely before execution. The executor should not repeat that research without a reason.

The executor owns facts that only the local environment can prove: installed SDKs/tools, binaries, local target files, decompiled evidence, machine paths, actual build/test/runtime behavior, and local-only diagnostics.

## Adaptive local discovery

Discovery depth is proportional:

- **none** — existing repository and remote evidence are sufficient;
- **targeted** — inspect a known framework/toolchain/runtime and establish the correct commands/integration points;
- **deep** — investigate unfamiliar or external systems, modding/native targets, binaries, runtime lifecycle, decompiled evidence, or ambiguous local failures.

Discovery is not permission to redesign the product. It refines technical implementation inside the owner-approved direction. If local evidence invalidates a material assumption, the executor reports the conflict instead of silently inventing a different product.

## Execution topology

```text
Main
├── High   — normal E1/E2 implementation
├── XHigh  — E3/deep implementation or investigation
├── Worker — bounded deterministic/mechanical work
└── Scout  — optional evidence-focused interpretation
```

High/XHigh are effort modes of Main, not separate roles. This avoids duplicated prompts/configuration while allowing expensive reasoning only where it materially improves results.

## Steady-state development

```text
Owner
  ↓
ChatGPT
  ├── reads GitHub/Issues
  ├── resolves remote facts
  ├── assigns Target Version for mutations
  ├── selects E0–E3
  ├── selects Main High/XHigh
  └── selects local discovery none/targeted/deep
  ↓
proportional task contract
  ↓
local truth gate
  ↓
Main + optional Worker/Scout
  ↓
deterministic validation
  ↓
versioned commit + report
  ↓
Owner/ChatGPT review
```

No extra project-state database is required. Git, the canonical version source, and GitHub Issues are the durable history/state mechanisms.
