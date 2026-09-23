# Desktop / mobile security module

Select for imported files, IPC, URL handlers, browser extensions, plugins, mobile APIs or local privileged operations. Add web-api controls when a web view or remote service is involved.

- Request minimum OS/browser/device permissions; separate UI and privileged operations. Do not run the application elevated merely to simplify installation.
- Validate IPC sender, message schema and authorization. Treat deep links, intents, URL schemes, clipboard, imported files and plugin messages as untrusted.
- Constrain paths and archive extraction; bound parsing/decompression. Never pass filenames or document fields through an interpolated shell command.
- Isolate untrusted web content from native bridges; do not expose filesystem/process APIs to arbitrary pages. Prefer maintained sandboxed web-view settings.
- Store sensitive local data using OS-backed facilities where appropriate. Never embed private backend/service keys in a client binary. Verify transport certificates.
- Authenticate update origin and integrity; separate install/update permission from ordinary use. Test interrupted/invalid updates and rollback without bypassing signatures.
- For mobile, select applicable MASVS storage, crypto, auth, network, platform and privacy requirements. Assess backups, screenshots and logging exposure.

Verification includes malformed file/IPC inputs, oversized payloads, traversal, unauthorized bridge calls, minimum permissions and secret-free packages. A local-only app is not automatically safe from hostile files.

Reference: https://mas.owasp.org/MASVS/
