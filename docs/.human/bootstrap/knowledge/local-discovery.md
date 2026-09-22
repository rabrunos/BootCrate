# Local Discovery Heuristics

Local discovery fills the gap between remote planning and executable reality.

It is part of materialization when local facts can change the correct technical baseline. It is not a license for broad exploration on every project.

## Discovery levels

### none

Use when the repository, owner decisions, and remote evidence already determine the implementation path. The executor still performs the local truth gate.

### targeted

Use when a known stack/integration needs local confirmation:

- installed SDK/runtime/compiler/package manager;
- real project/manifest version;
- filesystem paths;
- build/test/run commands;
- browser/engine/IDE tooling;
- external service/client availability;
- exact package/API versions;
- target launch/install/log locations.

### deep

Use only when the implementation depends on evidence that cannot be responsibly inferred remotely:

- unfamiliar native/runtime behavior;
- modding against a locally installed target;
- reverse engineering/decompilation explicitly allowed by the owner;
- engine/resource/package inspection;
- ambiguous binary/assembly/API boundaries;
- difficult local-only failures;
- undocumented or Early Access behavior.

Deep discovery normally maps to E3/Main XHigh, with Worker/Scout used to reduce raw exploration.

## Procedure

1. Inspect branch/HEAD/status/diff and preserve unrelated local work.
2. Identify the smallest local questions that block correct materialization.
3. Prefer official/supported APIs and metadata first.
4. Inspect local manifests, SDKs, binaries, assemblies, resources, logs, or runtime output only as needed.
5. When reverse engineering is authorized, choose a current proven tool appropriate to the target representation. Verify the tool and target format instead of assuming an engine implies one decompiler.
6. Keep bulky/raw evidence under ignored `.local/`.
7. Build deterministic indexes/summaries when raw evidence is large.
8. Separate observation from inference.
9. Promote only stable reusable conclusions into tracked project maps/scripts.
10. If local evidence contradicts an owner-approved assumption or makes the approved path unsafe/impossible, report the conflict instead of silently redesigning the product.

## Domain examples

**Godot/external game:** determine whether relevant behavior lives in GDScript resources, C#/.NET assemblies, GDExtension/native code, an official mod API, or a community loader before choosing extraction/decompilation tooling. Inspect only the needed symbols/resources and keep bulk recovered output local.

**Unity/.NET target:** inspect managed assemblies/metadata and supported extension points before patching. Use current .NET-aware inspection/decompilation tooling when authorized.

**Browser extension:** confirm manifest version, browser targets, dev-load workflow, build pipeline, permissions, and available browser automation before generating scripts.

**Windows/Desktop:** confirm SDK/runtime/toolchain, packaging/installer requirements, platform APIs, signing boundary, and run/debug/diagnostic commands.

**Web/backend:** confirm installed/runtime versions, package manager/lockfile, database/service dependencies, migration commands, and browser/E2E availability.

## Outputs

Local discovery may justify generating:

- a source/runtime/external-target map;
- a command cookbook;
- target locator/doctor script;
- build/test/run/install/diagnostics helpers;
- compact symbol/resource/API indexes;
- validation smoke scripts;
- environment requirements.

Do not generate any of these merely because they exist in this list.
