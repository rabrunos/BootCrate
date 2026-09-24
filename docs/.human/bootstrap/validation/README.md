# Bootstrap self-validation

This is tooling for the reusable template, not a downstream dependency or an AI telemetry system. Remove this directory and `.github/workflows/bootcrate-validate.yml` during downstream materialization.

Requirements: Python 3.11+ and Node.js 20+. The offline intake still needs only a browser; validation tools do not become a requirement for people merely answering it.

From the repository root, in an isolated environment:

```text
python -m pip install -r docs/.human/bootstrap/validation/requirements.txt
python docs/.human/bootstrap/validation/validate.py
```

Checks include JSON/TOML/YAML syntax and duplicates, schema consistency, v3 profile and v2 compatibility, mandatory Issues/ChatGPT invariants, data-only questions and dependency cycles, unchanged Issue Forms/labels, skill and Console preset parity, relative Markdown links, conservative Codex/Claude adapter invariants, ignored secret/local paths, secret-pattern smoke checks and deterministic intake/adoption/delivery/upgrade/eval regressions.

The validator does not fetch schemas, invoke model APIs, provision services, publish or inspect production credentials. JSON Schema validates structure; the shared finalized-profile gate rejects unresolved placeholders, exposure, version and required local references:

```text
python docs/.human/bootstrap/validation/validate.py --materialized-profile <profile.json>
```

That gate validates a profile, not the project's actual security implementation.

## Browser smoke (maintenance-only)

`test-browser.cjs` exercises the Setup and optional Console through `file://`, including required-field errors, old-intake confirmation and a local profile import. Use the fixed Playwright version in this directory's maintenance-only `package.json`, install a compatible browser in a disposable maintenance environment, then run `npm run test:browser`. This is not part of the downstream runtime or normal CI; if the browser cannot be installed, record the browser smoke as **not run**. Pair automation with keyboard, screen-reader, reflow/zoom and error recovery inspection before making any WCAG conformance claim.

For a disposable downstream materialization, run the post-pruning smoke verifier:

```text
python docs/.human/bootstrap/validation/verify-materialized.py <downstream-root>
```

Run it from a retained copy of the bootstrap validation tooling **after** pruning. It requires a complete profile, canonical version file and selected control map, checks that bootstrap-only content/workflow and generic package identity are gone, and inventories tracked plus nonignored untracked files without reading ignored secrets. `--json` emits check IDs and `pass/fail/not_run` statuses. It returns 0 for structural success, 1 for a structural failure and 2 if the command cannot evaluate the supplied root. Product build/smoke/security checks remain `not_run` until performed by native project tools. Python is required only for this retained maintenance verifier, not the resulting product runtime.

## CI

The workflow runs on push, pull request and manual dispatch with `contents: read`, no secrets, no publishing and full-SHA-pinned setup actions. It also runs a pinned Gitleaks binary, checks its published SHA-256 before extraction and scans repository history with redacted output. Update tool pins deliberately after checking upstream changes.

The lightweight local secret-pattern checks are regression smoke tests, not a replacement for Gitleaks or a complete secret audit. To run the same maintained scanner locally after installing/verifying it:

```text
gitleaks git --redact --no-banner --log-opts=--all .
```

Never print an actual finding's value into public reports. Revoke exposed credentials before considering history cleanup.

## What a green result does not prove

It does not run Codex/Claude, verify effective permissions on another OS, measure model quality, materialize every project kind, test production infrastructure or perform a penetration test. Scenario fixtures and grader regression tests are not completed model evals. See `../evals/README.md`.

Branch protections are not changed by this workflow. Required status checks affect direct pushes and should be enabled only through an explicit owner decision after the check is operational.
