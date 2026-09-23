# Sensitive data / payment boundaries

Select for personal identity, birth dates, private documents, health/financial information or payment flows. Ask for data categories and purposes, not real records.

Minimize collection and retention; separate identifiers from public profiles. Map data flows, roles, tenant boundaries, processors, region requirements, deletion/export and backup retention. Use synthetic data in tests and redact logs/analytics/error reports.

Use authenticated encrypted transport and established encryption/key-management facilities where the risk requires them. Encryption does not replace authorization, data minimization or key separation. Plan access audits, credential/key rotation and incident handling.

Prefer payment-provider hosted/tokenized flows. Do not collect/store card verification codes or raw payment details as a bootstrap convenience. Verify signed payment events server-side and protect against replay and duplicate fulfillment. Scope any payment/compliance requirements using current primary standards and qualified advice before real transactions; never claim compliance from a template.

Verification must include cross-user/tenant access denial, redaction, retention/deletion behavior, backup access, key separation and duplicate/invalid payment events when applicable. Public use with sensitive data needs independent review and an approved operating plan.

References:
- https://owasp.org/projects/asvs
- https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
