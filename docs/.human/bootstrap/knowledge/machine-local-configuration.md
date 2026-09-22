# Machine-Local Configuration Heuristics

Machine-local configuration makes a project portable across developer machines without leaking one machine's paths/settings into Git.

## Core rule

> Track the requirement and resolver; ignore the machine-specific value.

Typical resources:

- installed game/application root;
- SDK/compiler/editor path;
- emulator/device;
- external executable/tool;
- local service/database endpoint;
- platform-specific developer resource.

## Desired flow

```text
explicit override
      ↓
valid persisted local config
      ↓
safe auto-detection
      ↓
guided configuration / actionable error
```

The exact mechanism should follow the project's native ecosystem.

## Persisted values

Use ignored `.local/config/` by default when a native project-local mechanism is not better.

Do not commit sample files containing developer-specific absolute paths. If examples are useful, document keys/placeholders in tracked docs or schema instead.

## Detection

Auto-detection is useful when it is reliable and cheap.

For each candidate:

- validate more than directory existence;
- check expected executable/manifest/project signature;
- check compatible version when material;
- reject stale or wrong installations.

If exactly one valid candidate is found, the project may persist it automatically.

If multiple valid candidates are found, prefer explicit selection rather than arbitrary choice.

If none are found, explain what was checked and how to configure manually.

## Guided configuration

Prefer a guided/native setup command such as `doctor --configure` when it reduces owner friction.

The command can accept/choose a path, validate it, and persist the machine-local value.

Advanced users/CI should be able to use an explicit environment/CLI override where appropriate.

## Validation matrix

When machine-local state is required, safely test:

1. valid persisted config;
2. missing config;
3. stale/invalid config;
4. one auto-detected valid candidate;
5. multiple valid candidates;
6. no valid candidate;
7. explicit override;
8. non-interactive behavior.

Use temporary config roots, fixtures, dry-runs, or dependency injection where practical. Never delete or overwrite the owner's real local configuration merely to test setup behavior.

## Spire/mod-style example

Tracked project knowledge may say:

```text
resource: game_root
valid when:
  expected game executable exists
  expected manifest/metadata matches
detection:
  launcher/library metadata
  known platform install roots
local persistence:
  .local/config/project.json
```

A developer can install the game in any supported location. The repository remains unchanged; each checkout resolves its own `game_root`.
