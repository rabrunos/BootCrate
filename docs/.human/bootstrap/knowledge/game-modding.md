# Game Modding Heuristics

Research official SDK/mod support, community loaders/frameworks, engine/runtime, compatibility, distribution constraints, installed assemblies/assets/symbols, logging, and launch/install workflow.

Prefer supported extension points over patches.

During materialization, use targeted or deep local discovery when the mod depends on the installed game/runtime:

1. identify the actual engine/runtime/language representation;
2. locate the installed target and relevant manifests/binaries/resources;
3. determine whether official/community APIs already expose the needed behavior;
4. when reverse engineering is necessary and owner-authorized, select current tooling appropriate to the representation rather than assuming one decompiler fits the engine;
5. inspect/index only the evidence needed to establish stable integration points;
6. keep bulk extracted/decompiled data local;
7. generate project-specific target locator, install/run/log/diagnostics scripts and technical maps only when they will prevent repeated discovery.

If local evidence is version-sensitive, record the observed target/tool version in the relevant project map or diagnostics output.

Do not treat decompiler output as source-of-truth behavior without runtime/caller/lifecycle validation where material.
