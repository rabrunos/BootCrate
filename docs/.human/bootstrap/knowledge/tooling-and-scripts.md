# Tooling and Script Heuristics

Prefer the project's native ecosystem rather than adding a second runtime only for automation.

Examples:
- Web/Node → TypeScript/Node tooling often provides excellent deterministic validation.
- .NET → dotnet/C#/PowerShell as appropriate.
- C++ → CMake/presets plus minimal platform scripting.
- Python → Python.
- Rust → Cargo ecosystem.

Canonical capabilities to consider, not blindly create:
- `doctor` — environment readiness;
- `build` — fresh build;
- `test` — automated tests;
- `validate` — project acceptance checks;
- `run` — runtime/dev server;
- `package` — distributable payload;
- `install` — local deployment/install;
- `diagnostics` — collect/sanitize/compact evidence;
- `publish` — external publication, preflight-safe by default and owner-authorized for real publication.

Do not create empty scripts for capabilities the project does not need.
