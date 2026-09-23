# Infrastructure / self-hosting security module

Select for managed hosting, VPS, containers, databases, queues, automations and CI. Managed hosting shifts some responsibilities; it does not secure application authorization or data handling for the owner.

## Minimum operating plan

Define who owns patching, access, secrets, backups, restore tests, monitoring, incident response and billing/abuse limits. When no capable operator is available, reconsider self-hosting or stop before deployment; do not silently assign responsibility to the coding agent.

Use maintained images/runtime versions, least-privilege service identities and segmented networking. Keep databases/admin dashboards off the public internet unless explicitly necessary and protected. Avoid privileged containers, host mounts and exposed container-engine sockets. Containers are not an absolute sandbox.

Use scoped administration access, secure authentication, TLS renewal and firewall rules with a recovery path. Never lock out the owner or modify live firewall/DNS without an authorized plan. Separate production from development and do not provide production credentials to ordinary code sessions.

Set memory/CPU/storage/request limits. Keep audited access records without secrets. Encrypt sensitive backups, separate key access, define recovery objectives and demonstrate restoration into an isolated environment. A successful backup command is not evidence that restoration works.

## CI and supply chain

Use minimum workflow token permissions, pin external actions by full commit SHA, and review updates. Do not expose secrets to untrusted pull-request code or use privileged PR triggers to execute it. Never interpolate untrusted PR text into shell source. Prefer short-lived deployment identity over long-lived credentials. Keep publication separate from validation.

For solo workflows, blocking force-push and branch deletion can be useful. Required checks or mandatory PRs change how direct writes work: choose them explicitly after a check exists and verify the actual connector workflow. Do not enforce branch settings automatically from this template.

## Verification

Check intended ports only, non-public data services, effective privileges, image/dependency scans, synthetic secret redaction, restore/rollback evidence, rate/cost limits and expired/revoked credential handling. Do not test on production by default.

References:
- https://docs.github.com/en/actions/reference/security/secure-use
- https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
