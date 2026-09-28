# BootCrate Bootstrap Architecture

BootCrate is the reusable product, not a downstream project that must bootstrap itself.

```text
Owner intent → offline intake → ChatGPT + verified GitHub/Issues
→ new project baseline OR isolated Adoption Sandbox
→ approved scope, risks, version and selected capabilities
→ product-specific source, controls, tests and harnesses
→ structural + native behavior checks → prune bootstrap
→ accepted delta in original (adoption) → authorized Git/Issue actions
```

Main is one role with Medium / High / XHigh effort. High remains default; Medium is gated by evidence and strong validation. Worker performs bounded mechanical work, Scout interprets read-only evidence. No extra Main agents or automatic fan-out.

Standard/Economy are consumption strategies independent of effort. Technical execution permissions are independent again: task override, ignored local override, then the protected/manual safe default. Requested and effective permissions are separate observations; no permission profile grants task or publication authority. A small optional Console may survive pruning; the Setup never does. The version/changelog belongs to every integrated project state, while a frozen candidate and confirmed destination receipts describe later distribution. No publisher exists for a product without distribution.

The project profile contains stable version/security/service configuration, not maintenance history or work status. Issues own active work. Local resources are discovered/configured per machine; secrets are separately protected.

Bootstrap self-tests and scenario-evaluation tools live under this directory and are removed from downstream projects along with their bootstrap-only workflow. They test the reusable product; they are not telemetry or a project-state system. A generated project receives only its own applicable tests/controls.
