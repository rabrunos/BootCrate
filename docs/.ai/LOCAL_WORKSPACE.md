# Local Workspace — materialization skeleton

`.local/` is ignored and reserved for machine-local/private/generated state.

Possible project-specific subdirectories:

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

Materialization should document/create only the subdirectories the actual project uses.

Local discovery may place installed-target indexes, extracted/decompiled evidence, SDK/tool downloads, symbol/resource indexes, screenshots/video, and investigation outputs here.

Prefer compact structured evidence for AI consumption. Keep raw logs, large extracted/decompiled trees, caches, binaries, credentials, and machine-specific data out of Git.

Promote only stable reusable conclusions into tracked project maps/scripts.
