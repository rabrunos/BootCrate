# Web Development Heuristics

Verify current ecosystem choices during discovery.

- For substantial JavaScript-family applications, strongly consider TypeScript as a deterministic type-validation layer.
- Use reproducible dependency/lockfile practices.
- Define canonical typecheck/lint/test/build/run/E2E commands as applicable.
- Separate unit/integration/browser validation.
- Do not claim visual correctness from build/typecheck alone.
- Keep secrets/local environment overrides out of Git.
- Prefer schema validation at external boundaries.
