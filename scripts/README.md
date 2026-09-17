# Canonical Project Capabilities

This bootstrap does not guess the final project's scripting runtime.

Materialization may create only the capabilities that apply:

- `doctor` — verify development environment/toolchain/external paths.
- `build` — produce a fresh build/output.
- `test` — automated tests.
- `validate` — project-defined acceptance checks.
- `run` — launch runtime/dev server.
- `package` — construct distributable payload.
- `install` — local install/deploy when relevant.
- `diagnostics` — collect/sanitize/compact evidence.
- `publish` — external publication; preflight-safe by default, real publication only with explicit owner authorization.

Use the ecosystem-native language/tooling where practical. Do not add a second runtime solely to satisfy this convention, and do not create empty scripts for unused capabilities.
