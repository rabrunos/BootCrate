# Release Task Template

Start from `base.md` and add:
- exact integrated version and frozen candidate commit/payload/artifact digests;
- canonical changes included since each destination/channel's confirmed baseline;
- preview and verified renderer/byte limits for each actual destination field;
- packaging/integrity checks and native service health checks where deployment is selected;
- preflight that cannot mutate remote state;
- independently confirmed receipts and reconciliation for each destination;
- explicit owner authorization required for real publication;
- duplicate/partial/unknown result handling, serialization and separate rollback authorization.

A successful build/package is not a published release.
Release tasks are normally `risk: elevated` even when implementation effort is low.
