# Version, candidate and delivery contract

A project has one canonical version source. Every accepted integrated version has a short effect-focused entry in its canonical changelog, even when it never ships. An Issue remains the operational work record; a changelog is product history. Work targets in parallel may use unique native prerelease versions tied to their existing Issues, then a separately authorized integration gets an official version. If the ecosystem cannot express exclusive work versions, coordinate numeric targets serially. Never treat `1.4.1+devA` and `1.4.1+devB` as ordered releases, rename earlier commit tokens or force-push to resolve a race.

The read-only `coordination.py` gate accepts an export of version assignments from the **existing Issues** (`[{"issue":"#42","target":"1.3.0-alpha.1","status":"assigned"}]`) plus the proposed Issue/target and expected/observed remote HEAD. It blocks reused abandoned targets, collisions, two active targets for the same Issue and stale HEAD. For example: `python coordination.py --assignments assignments.json --issue '#43' --target 1.3.0-alpha.2 --expected-head <full-SHA> --observed-head <full-SHA>`. A `READY` response is a proposal, not an atomic reservation: the authorized single writer records the assignment in the Issue and rechecks remote HEAD before integration.

## Canonical notes and preview

The reference preflight accepts a restricted Markdown changelog, newest version first:

```markdown
# Changelog

## v1.2 — Search

<!-- change:#42/1 audience:public -->
- Corrigidos filtros ao reabrir a busca.
```

Use a unique change ID to track a correction across destinations and cherry-picks. The metadata line may be omitted for a simple sequential history; then the ID is derived from version and bullet position. `maintainers` notes remain in the history but are omitted from public destinations. Only headings, metadata and plain bullet lines with simple emphasis, inline code and HTTPS links are supported by the reference parser. Inline code is tokenized before other markup, so link/emphasis characters inside it remain literal; escaping and unclosed syntax are deterministic. Unsupported syntax fails rather than disappearing. Parallel work may write Issue-specific fragments and deterministically produce this single changelog at integration; it must not maintain a second manual text. A structured native source is also valid with an adapter.

The reference preflight at `delivery.py` accepts:

- candidate JSON: version, 40-character source commit, payload SHA-256, per-destination artifact SHA-256, included change IDs and integration order;
- target JSON: destination ID, channel, verified field format (`markdown`, `plain` or a field tested for `bbcode`), byte limit and baseline declaration (`never_published` only when actually known);
- receipts JSON: sanitized, structured events exported from the project's **single chosen shared record** (normally a Release Issue), with `schema: bootcrate-receipt/v1`, unique attempt ID, destination/channel, candidate identity, artifact digest, status, source of observation, native evidence reference, observation time, integration order and included change IDs. A later event for the same attempt reconciles an earlier unknown outcome without rewriting history.

Example: `python delivery.py --candidate candidate.json --receipts receipts.json --target target.json --changelog CHANGELOG.md`. It emits `READY` with preview and note digest, `SKIP` for an identical confirmed candidate, or `BLOCK` for divergent/unknown state. Receipt reduction groups by attempt, validates the full candidate/destination/channel identity, accepts unknown-to-confirmed reconciliation in timestamp order, and blocks confirmed/failed contradictions or identity reuse. The candidate version must have a canonical changelog entry whose declared changes are included in the frozen candidate. It does **not** upload, check the authenticity of Issue authors or prove remote state. The publisher must authenticate the author/source, reconcile the actual provider, serialize all authorized entrypoints by resource/channel, verify approvals and the frozen candidate again, perform the operation, and record a receipt only after sufficient native confirmation. A timeout between upload and receipt is unknown; do not retry blindly.

Select each provider **and its actual field** during materialization. A GitHub Release, service deployment, installer download and marketplace description have different semantics. A product with no distribution keeps the version and changelog but no uploader or fictitious receipt. A delivery with multiple destinations cannot use one destination's success as another's receipt. Capture partial success without a version bump that would change the shipped bytes. Editorial correction of notes alone is a separate authorized operation.

When one provider event is expected to start another publisher, verify that event actually fires with the selected GitHub token/permissions and provider semantics. Prefer an explicit coordinated chain when the trigger is not reliable. Serialize by destination resource/channel across local and CI entrypoints; a CI concurrency group alone does not lock another machine.

The notes should say what changed and under what relevant condition, usually one concise sentence per result. Include migration and security warnings when needed. Do not copy a file list, private log, speculative benefit or internal implementation diary into public notes. Renderers change presentation, not approved facts; validate a field's real markup behavior before enabling BBCode or provider-specific upload.
