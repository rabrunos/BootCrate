# Context Index — materialization skeleton

Small mutable routing map for project knowledge.

Do not store project status, roadmap, open work, or task history here. GitHub Issues own those.

During materialization, replace the examples with the project's real context map:

- `project-profile.json` — stable normalized project identity, constraints, toolchain, workflow configuration.
- architecture map — read only for architecture/cross-module work.
- validation/tooling map — read for build/test/dev-environment tasks.
- external-target/native map — read only for relevant integration/modding/native tasks.
- human design material — ChatGPT/owner only unless an implementation task explicitly needs a promoted subset.

The goal is selective context loading, not documentation discovery by brute force.
