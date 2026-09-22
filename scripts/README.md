# Canonical Project Capabilities

This bootstrap does not guess the final project's scripting runtime.

Materialization may create only the capabilities that apply:

- `doctor` — environment readiness, required tools/SDKs, and external target resources.
- `build` — produce a fresh build/output.
- `test` — automated tests.
- `validate` — project-defined acceptance checks.
- `run` — launch runtime/dev server/target workflow.
- `package` — construct distributable payload.
- `install` — local deployment/install when relevant.
- `diagnostics` — collect/sanitize/compact evidence.
- `publish` — external publication; preflight-safe by default, real publication only with explicit owner authorization.

## Doctor / local configuration

When machine-local resources are required, `doctor` is the preferred owner-facing readiness entry point.

The project may expose a native equivalent of:

```text
doctor
doctor --configure
```

Expected behavior:

- validate existing persisted local values before use;
- support explicit environment/CLI overrides when useful;
- safely auto-detect known resources where practical;
- automatically persist a single unambiguous valid candidate when appropriate;
- guide selection/configuration when multiple/no candidates exist;
- produce actionable errors with attempted detection sources and the exact recovery command;
- never require interactive input in CI/non-interactive mode;
- never commit machine-local paths.

External-target/mod projects may additionally need native ecosystem commands for locating the target, indexing relevant symbols/resources, installing the mod/plugin, launching the target, or collecting logs. Prefer folding those behaviors into canonical capabilities rather than creating a large unrelated script catalog.

Use the ecosystem-native language/tooling where practical. Do not add a second runtime solely to satisfy this convention, and do not create empty scripts for unused capabilities.
