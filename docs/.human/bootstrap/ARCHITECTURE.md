# BootCrate Bootstrap Architecture

BootCrate is the reusable product, not a downstream project that must bootstrap itself.

```text
Owner intent → offline intake → ChatGPT + GitHub/Issues/research
→ resolved direction + security surfaces + service/operation decisions
→ compact versioned materialization contract
→ local truth + bounded discovery
→ project-specific source, controls, tests, tooling and harness settings
→ validation → prune generic bootstrap → commit/push → response report
```

Main is one role with Medium / High / XHigh effort. High remains default; Medium is gated by evidence and strong validation. Worker performs bounded mechanical work, Scout interprets read-only evidence. No extra Main agents or automatic fan-out.

The project profile contains stable version/security/service configuration, not maintenance history or work status. Issues own active work. Local resources are discovered/configured per machine; secrets are separately protected.

Bootstrap self-tests and scenario-evaluation tools live under this directory and are removed from downstream projects along with their bootstrap-only workflow. They test the reusable product; they are not telemetry or a project-state system. A generated project receives only its own applicable tests/controls.
