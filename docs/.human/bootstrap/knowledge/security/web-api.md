# Web / API security module

Select for browser interfaces, APIs, SaaS, webhooks and browser-extension backends. Research the current framework safeguards and applicable ASVS requirements; keep only relevant controls in the materialized security map.

## Design and implementation

- Use framework auto-escaping and context-appropriate output encoding; prefer text sinks. Sanitize intentionally supported HTML with a maintained library. Avoid untrusted `innerHTML`, dynamic script/template evaluation and unsafe URL schemes. CSP is defense in depth, not a fix for unsafe rendering.
- Parameterize database queries; allowlist identifiers/operators that cannot be parameterized. Validate NoSQL query structure instead of accepting user-supplied operators. Disable unnecessary XML external entities/DTDs.
- Authenticate using maintained mechanisms and authorize every protected operation/object. Tenant identity comes from the authenticated session, not an arbitrary request field. Test horizontal and vertical privilege changes.
- Protect cookie-backed state changes against CSRF. Use appropriate Secure/HttpOnly/SameSite cookie settings and explicit session expiry/revocation. CORS is not authorization; never use wildcard credentialed origins.
- Bound uploads by bytes/type/decoding cost; generate storage names, prevent traversal, store away from executable/web-root paths and authorize downloads. Treat archive and document parsers as attack surfaces.
- Prevent SSRF using constrained destinations/protocols and egress restrictions. Revalidate redirects/resolved addresses where necessary; block unintended internal/metadata endpoints and bound response sizes/timeouts.
- Authenticate webhooks and verify signatures, freshness and replay/idempotency. Rate-limit expensive or abuse-prone endpoints; do not trust hidden form fields, client roles, scores or prices.
- Disable production debug output and default credentials; verify TLS, secure headers, dependency versions and the distributed client bundle for secrets.

## Required negative checks when applicable

Stored/reflected/DOM markup remains data; malformed query/operator input fails; one user/tenant cannot read another's object; unauthorized requests fail closed; CSRF fails; oversized uploads and unsafe paths fail; disallowed outbound destinations fail; replayed webhooks do not duplicate side effects.

Use synthetic data and authorized local/test deployments. Public deployment requires the separate release gate.

## Primary references

- https://owasp.org/projects/asvs
- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
