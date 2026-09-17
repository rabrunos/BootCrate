# Local Workspace — materialization skeleton

`.local/` is ignored and reserved for machine-local/private/generated state.

Possible project-specific subdirectories:

```text
.local/
  config/
  logs/
    raw/
    sanitized/
    summaries/
  tools/
  research/
  cache/
  artifacts/
  temp/
```

Materialization should document only the subdirectories the actual project uses.

Prefer compact structured evidence for AI consumption. Keep raw logs, large extracted/decompiled trees, caches, binaries, and machine-specific data out of Git.
