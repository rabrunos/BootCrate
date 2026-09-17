# BootCrate Bootstrap Architecture

BootCrate itself may be broad; a downstream materialized project must be narrow.

```text
Owner intent
   ↓
offline intake (RAW)
   ↓
ChatGPT + GitHub + Issues + external research
   ↓
owner-approved architecture
   ↓
normalized project profile (stable facts only)
   ↓
materialization contract
   ↓
Codex or Claude Code
   ↓
pruned final repository
```

Normal downstream tasks repeat only the lower-cost planning/execution loop:

```text
Owner
  ↓
ChatGPT (abundant planning/compression)
  ↓
proportional task contract
  ↓
local truth gate
  ↓
Main + optional Worker/Scout
  ↓
deterministic validation
  ↓
report → Owner/ChatGPT → Issue follow-up/closure
```

No extra project-state database is required. Git and GitHub Issues are the durable history/state mechanisms.
