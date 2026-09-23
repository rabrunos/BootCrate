# Task Policy — materialization skeleton

Vendor-neutral execution policy. Quality and safety take priority over marginal savings.

## Version identity

Every materialized project has one canonical project version source, including static sites, documentation and tooling projects. Prefer native metadata; use a minimal `VERSION` only when needed.

Every independent root task that mutates tracked project state receives an orchestrator-assigned Target Version before execution. Prompt H1, implementation commit subject and final report H1 preserve `# [<TARGET_VERSION>] <TITLE>` / `[<TARGET_VERSION>]` literally. The rest of each title is free.

State the observed baseline version and repository-basis SHA when available. The executor verifies local HEAD/status/diff and never silently chooses a different target. The version source stores the version in its native format (for example `0.7`); the title may add the agreed `v` prefix. Required mirrors must agree.

Continuations and corrective work for the same unaccepted target retain that target. Abandoned targets are not reassigned to different work; record assignments/abandonment in the existing task/Issue history when needed, not a new registry. Accepted or externally distributed artifacts are not silently replaced: subsequent changes receive a new version. Commits distinguish intermediate revisions within an unfinished target.

Read-only investigation, discussion, local setup and Issue-only actions do not bump version. Persisting tracked findings is a mutation. Versioning never authorizes publication.

## Main: three effort levels, one role

Main retains the task context at all levels. Do not create three Main agents or duplicate the investigation.

| Class | Default execution | Escalation |
| --- | --- | --- |
| E0: deterministic | Direct canonical command; Worker only when useful | Main if output requires judgment |
| E1: narrow | Medium only when every eligibility condition below is satisfied; otherwise High | High on unexpected uncertainty |
| E2: normal implementation | High | XHigh for unresolved complex interactions |
| E3: deep/ambiguous | XHigh, or the highest verified supported equivalent | Stop for owner decisions/evidence that reasoning cannot replace |

### Medium eligibility — all required

- Scope, desired behavior and acceptance are already resolved.
- Stack/API and affected boundaries are understood; no material research or local unknown remains.
- No authentication, authorization, tenant isolation, cryptography, secrets, untrusted-input boundary, destructive migration, production access or release-security change.
- Changes are reversible and do not introduce a new architecture/dependency/service boundary.
- Focused deterministic checks directly cover the changed behavior and likely regressions; passing lint alone is insufficient.

Medium is an option, not an automatic discount for short tasks or few changed lines. When evidence is insufficient, choose High. Security-sensitive implementation has a High minimum; complex security design normally requires XHigh plus independent review, not merely more reasoning.

### Escalation without quality loss

Unexpected ambiguity, contradictory evidence, an unexplained failing check or newly discovered security impact invalidates the original selection. Reassess before further edits; do not repeat blind attempts or weaken tests. Increase effort using the harness's supported session control when available. If the executor cannot change effective effort, report the needed setting and pause the affected work instead of claiming it switched. Preserve the same active Target Version.

The contract describes desired effort; it cannot itself change a model setting. Verify available levels and effective settings for the selected model/client. Never fabricate a vendor option, add API spending, change subscriptions or relax permissions to achieve an effort tier.

## Direct execution lane

ChatGPT remains the default orchestrator when work requires discovery, product or architecture decisions, coordination, or material judgment. The owner may intentionally send E0 and eligible E1 work directly to an executor when the desired behavior and scope are already resolved and validation is deterministic.

Direct execution is not eligible when work involves material research, product/architecture choice, authentication or authorization, cryptography or secrets, a changed trust boundary, destructive migration, production access, provisioning or publication. Unexpected ambiguity exits the direct lane and returns the task to normal orchestration.

Direct execution does not bypass version identity, local-truth checks, security rules, validation, Git authorization or reporting. When the project's next Target Version is not deterministic from an established convention, the owner/orchestrator assigns it first. A trivial contract should remain trivial: version, goal, scope, validation and authorized Git actions are sufficient.

## Discovery and risk are separate

Local discovery: `none` (normal truth gate only), `targeted` (specific known-stack checks), or `deep` (unfamiliar/native/external behavior). State blocking questions and a stopping condition. Do not repeat research already verified remotely.

Risk: `normal` or `elevated`. A simple production operation can be elevated without requiring deep reasoning. Extra reasoning does not replace authorization, isolation, evidence or review.

## Delegation

Default to no subagent. Worker handles bounded locate/execute/extract/compare/test tasks. Scout interprets a narrow evidence set using read/search tools. Main owns integration and final judgment. Delegate only when it removes more work than coordination creates. No recursive fan-out by default; no permanent Reviewer. A fresh-context independent review is requested for consequential security/architecture changes when useful.

## Security and services

Load `SECURITY_BASELINE.md` and only the applicable materialized controls when attack surfaces change. Derive risk from exposure, data and operations rather than owner knowledge of security terms. Never reduce mandatory controls to meet a budget. Record unresolved material risks in Issues; do not publish while required security checks or approvals are missing.

Select external services by capability, operating responsibility, total cost, recovery and exit requirements. Prefer no service when none is needed. Provider selection is research, not permission to provision, purchase or deploy.

## Machine-local portability

Track resource requirements/resolvers, not machine values. Use explicit override, validated ignored config, bounded auto-detection, then guided/actionable setup. Invalid explicit overrides must fail rather than silently select another target. Test missing/stale/ambiguous configuration with temporary fixtures, never by deleting owner state. Secrets require their own protected mechanism, not plain local path configuration.

## Proportional contracts and reports

Use the smallest sufficient contract. A compact mutation contract needs version identity, goal, affected scope, relevant validation and requested Git/Issue actions. Include execution/discovery/security details only where they change the work; defaults are inherited, not repeated as empty headings.

Extended contracts add verified facts, local questions, non-goals, compatibility, acceptance, security controls/tests, service/operation constraints and review requirements only as needed.

The final report is an ephemeral response after the requested Git actions. Include the exact target token, changed behavior, checks actually run, failures/unverified items, commit/push result and explicit Issue actions. Do not generate a tracked last-report or parallel work-state file.
