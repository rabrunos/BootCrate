# Multiplayer / native security module

Select for remote peers, user-hosted sessions, game servers, leaderboards and native binary parsers. A friend's LAN client is still outside the host's trust boundary.

- The client requests an action; the authoritative service/host validates identity, permissions, timing and legal state transitions. Never accept peer-provided administrator roles, filesystem paths or arbitrary commands.
- Bound packet/frame sizes, nesting, decompression, allocation, rate and concurrency; enforce timeouts and replay/sequence handling where needed. Authenticate/encrypt channels with maintained protocols appropriate to the threat model.
- Parse explicit versioned message schemas. Avoid general object deserialization and executable payloads. Separate protocol parsing from privileged filesystem/process operations.
- Isolate the host process from unrelated user files and credentials. Mod loaders and third-party plugins are code execution surfaces, not trustworthy just because they are local.
- For native code, use memory-safe components where practical and available compiler hardening, sanitizers and fuzzing at risky parsers. Bounds checks and ownership/lifetime rules remain necessary.
- A public leaderboard requires authenticated writes, server-side validation, quotas and abuse handling. Client-reported scores cannot be made authoritative by hiding a key in the game. Document integrity limits for peer-hosted games rather than claiming cheating is impossible.

Verification: malformed/truncated packets, unauthorized operations, impossible transitions, replay, excessive rates, huge fields and unsafe paths must be rejected without crashes, host file access or command execution. Fuzz only owned/authorized isolated targets; no scanning third-party game servers.

References:
- https://csrc.nist.gov/projects/ssdf
- https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
