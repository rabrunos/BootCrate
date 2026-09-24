---
name: safe-validation
description: Run or interpret relevant project checks and manual smoke evidence, including read-only investigations that explicitly need existing tests. Use when validation is requested or required for acceptance; never use a check to trigger publication.
---

Select checks from the changed behavior, risk and actual product capabilities. Run focused deterministic checks first, then broaden only for a concrete remaining risk or required gate. Compare before/after when adopting an existing codebase, and repeat applicable checks in the original after applying an approved sandbox delta.

Record command/environment, result and limitations. Distinguish `pass`, `fail`, `blocked`, `not_run` and `not_applicable`; justify non-applicability. A screenshot, marker, mock or structural checker has a narrower meaning than a real product smoke. Give the owner only the manual steps still needed with preconditions and expected results. Never report an unexecuted check as passed or perform upload/deploy as validation.
