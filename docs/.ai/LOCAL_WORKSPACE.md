# Local Workspace — materialization skeleton

`.local/` is ignored and reserved for machine-local/private/generated state. It is never the source of shared project truth.

## Tracked contract versus local values

A materialized project that depends on machine-specific resources separates:

```text
TRACKED
docs/.ai/LOCAL_WORKSPACE.md
doctor/setup/run/install logic
validation rules
expected local keys/resources

IGNORED
.local/config/
actual paths and machine-specific values
```

Examples of local values:

- installed game/engine/editor location;
- SDK/toolchain path not stable across machines;
- emulator/device selection;
- local database/service endpoint;
- external executable/tool path;
- local-only feature flags needed for development.

Do not store credentials/secrets in plain local config merely because the directory is ignored. Use the platform/project's appropriate secret mechanism.

## Resolution precedence

Unless the project has a stronger ecosystem-native convention, prefer:

1. explicit command-line or environment override;
2. existing valid persisted local config;
3. safe automatic detection;
4. guided configuration or actionable failure.

A stored value must be validated before use. A stale path must not silently win over a valid detected installation.

## Guided setup

When useful, materialization should provide a native equivalent of:

```text
doctor
doctor --configure
```

A nontechnical owner should not need to hand-edit JSON merely to point the project at an installed game/SDK/tool.

A guided flow may:

- auto-detect candidates;
- validate signatures/manifests/executables rather than only checking directory existence;
- automatically persist one unambiguous valid candidate;
- ask the user to choose when multiple valid candidates exist;
- accept an explicit path when detection fails;
- write only machine-local values to `.local/config/`.

Non-interactive/CI use should fail clearly rather than blocking on an interactive prompt.

## Fresh-machine behavior

Projects that require local configuration should validate, without destroying the owner's actual config:

- valid config present;
- config absent;
- config present but stale/invalid;
- exactly one valid auto-detected candidate;
- multiple valid candidates;
- no candidate found;
- explicit override;
- non-interactive failure path when interaction would otherwise be required.

Use temporary config roots/fixtures/dry-run mechanisms where practical to simulate these cases.

## Possible project-specific subdirectories

```text
.local/
  config/
  tools/
  research/
    raw/
    indexes/
    summaries/
  logs/
    raw/
    sanitized/
    summaries/
  cache/
  artifacts/
  temp/
```

Materialization should document/create only the behaviors the actual project uses. Empty local directories do not need to be committed.

Local discovery may place installed-target indexes, extracted/decompiled evidence, SDK/tool downloads, symbol/resource indexes, screenshots/video, and investigation outputs here.

Prefer compact structured evidence for AI consumption. Keep raw logs, large extracted/decompiled trees, caches, binaries, credentials, and machine-specific data out of Git.

Promote only stable reusable conclusions into tracked project maps/scripts.
