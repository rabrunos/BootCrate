# Context Index — materialization skeleton

Small mutable routing map for project knowledge.

Do not store project status, roadmap, open work, or task history here. GitHub Issues own those.

During materialization, replace the examples with the project's real context map:

- `project-profile.json` — stable normalized project identity, constraints, toolchain, workflow/version configuration.
- source architecture map — architecture/cross-module work.
- validation/tooling map — build/test/dev-environment tasks.
- external-target/native/runtime map — only for relevant integration/modding/native work.
- API/framework map — only when repeated API discovery would otherwise consume context.
- command cookbook — only when lifecycle/build/run/install operations are non-obvious.
- data/save/release maps — only when the project actually has those domains.
- human design material — ChatGPT/owner only unless an implementation task explicitly needs a promoted subset.

Discovery may create these maps, but only when future tasks benefit from them. The goal is selective context loading, not documentation generation or discovery by brute force.
