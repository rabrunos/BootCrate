# Release Task Template

Start from `base.md` and add:
- exact release/version target;
- payload source of truth;
- changelog/release-note policy;
- packaging/integrity checks;
- preflight/dry-run requirements;
- publication destinations;
- explicit owner authorization required for real publication;
- duplicate/partial-publication/rollback protections when relevant.

A successful build/package is not a published release.
Release tasks are normally `risk: elevated` even when implementation effort is low.
